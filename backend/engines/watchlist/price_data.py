import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
from typing import List
import logging

from backend.models.watchlist import StockData
from backend.core import cache, rate_limiter
from backend.config import settings

logger = logging.getLogger(__name__)


async def bulk_fetch() -> List[StockData]:
    cached = cache.get("watchlist_bulk", "watchlist")
    if cached:
        return [StockData(**s) for s in cached]

    rate_limiter.acquire("yfinance")
    tickers = settings.tickers_list

    try:
        data = yf.download(
            tickers,
            period="3mo",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
        )

        result = []
        for ticker in tickers:
            try:
                if ticker in data.columns.get_level_values(0):
                    hist = data[ticker].dropna(how="all")
                else:
                    hist = pd.DataFrame()

                if hist.empty:
                    continue

                close = hist["Close"]
                volume = hist["Volume"] if "Volume" in hist else pd.Series(dtype=float)

                price = float(close.iloc[-1])
                prev = float(close.iloc[-2]) if len(close) > 1 else price
                change_pct = round((price - prev) / prev * 100, 2) if prev != 0 else 0.0

                vol = float(volume.iloc[-1]) if not volume.empty else 0.0
                avg_vol = float(volume.rolling(20).mean().iloc[-1]) if not volume.empty else 0.0
                vol_ratio = round(vol / avg_vol, 2) if avg_vol > 0 else 1.0

                result.append(StockData(
                    ticker=ticker,
                    price=round(price, 2),
                    change_pct=change_pct,
                    volume=vol,
                    avg_volume=avg_vol,
                    volume_ratio=vol_ratio,
                    options_unusual=False,
                    timestamp=datetime.now(timezone.utc),
                ))
            except Exception as e:
                logger.warning(f"Error processing {ticker}: {e}")

        if result:
            cache.set("watchlist_bulk", [s.model_dump() for s in result])
        else:
            stale = cache.get_stale("watchlist_bulk")
            if stale:
                logger.info("yfinance returned no watchlist data; returning stale")
                return [StockData(**s) for s in stale]
        return result

    except Exception as e:
        logger.error(f"Error in bulk watchlist fetch: {e}")
        stale = cache.get_stale("watchlist_bulk")
        if stale:
            logger.info("Returning stale watchlist data")
            return [StockData(**s) for s in stale]
        raise
