import asyncio
import gc
import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
from typing import List, Optional
import logging

from models.watchlist import StockData
from core import cache, rate_limiter, watchlist_manager

logger = logging.getLogger(__name__)

_RATING_MAP = {
    "strong_buy": "Strong Buy",
    "buy": "Buy",
    "hold": "Hold",
    "underperform": "Sell",
    "sell": "Strong Sell",
    "neutral": "Hold",
}


def _normalize_rec(key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    return _RATING_MAP.get(key.lower().replace(" ", "_"))


def _sanitize(v) -> Optional[float]:
    try:
        f = float(v)
        return None if (f != f) else f  # NaN check
    except (TypeError, ValueError):
        return None


def _squeeze(short_pct, short_ratio, vol_ratio) -> Optional[float]:
    if short_pct is None and short_ratio is None:
        return None
    score = 0.0
    if short_pct:
        score += min(40, short_pct * 100 * 2)
    if short_ratio:
        score += min(30, short_ratio * 3)
    if vol_ratio and vol_ratio > 1:
        score += min(20, (vol_ratio - 1) * 10)
    return round(min(100, max(0, score)), 1)


def _fetch_info_sync(ticker: str) -> dict:
    """Synchronous yfinance info fetch — run via asyncio.to_thread."""
    try:
        return yf.Ticker(ticker).info or {}
    except Exception as e:
        logger.debug(f"info fetch failed for {ticker}: {e}")
        return {}


async def bulk_fetch() -> List[StockData]:
    cached = cache.get("watchlist_bulk", "watchlist")
    if cached:
        return [StockData(**s) for s in cached]

    rate_limiter.acquire("yfinance")
    tickers = watchlist_manager.get_tickers()

    if not tickers:
        return []

    # --- Step 1: bulk OHLCV via yf.download ---
    try:
        data = yf.download(
            tickers,
            period="3mo",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
        )
    except Exception as e:
        logger.error(f"yf.download failed: {e}")
        stale = cache.get_stale("watchlist_bulk")
        if stale:
            return [StockData(**s) for s in stale]
        raise

    ohlcv: dict[str, dict] = {}
    for ticker in tickers:
        try:
            if len(tickers) == 1:
                hist = data.dropna(how="all")
            elif ticker in data.columns.get_level_values(0):
                hist = data[ticker].dropna(how="all")
            else:
                continue

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

            ohlcv[ticker] = {
                "price": round(price, 2),
                "change_pct": change_pct,
                "volume": vol,
                "avg_volume": avg_vol,
                "volume_ratio": vol_ratio,
            }
        except Exception as e:
            logger.warning(f"OHLCV processing failed for {ticker}: {e}")

    # Free the large DataFrame now that we've extracted all values
    del data
    gc.collect()

    if not ohlcv:
        stale = cache.get_stale("watchlist_bulk")
        if stale:
            return [StockData(**s) for s in stale]
        return []

    # --- Step 2: per-ticker .info in parallel (fundamentals) ---
    sem = asyncio.Semaphore(4)

    async def fetch_info(t: str) -> tuple[str, dict]:
        async with sem:
            info = await asyncio.to_thread(_fetch_info_sync, t)
            return t, info

    info_results = await asyncio.gather(*[fetch_info(t) for t in ohlcv.keys()])
    info_map = {t: info for t, info in info_results}

    # --- Step 3: merge ---
    result: List[StockData] = []
    for ticker, price_data_dict in ohlcv.items():
        info = info_map.get(ticker, {})
        short_pct = _sanitize(info.get("shortPercentOfFloat"))
        short_ratio = _sanitize(info.get("shortRatio"))
        vol_ratio = price_data_dict["volume_ratio"]

        result.append(StockData(
            ticker=ticker,
            price=price_data_dict["price"],
            change_pct=price_data_dict["change_pct"],
            volume=price_data_dict["volume"],
            avg_volume=price_data_dict["avg_volume"],
            volume_ratio=vol_ratio,
            market_cap=_sanitize(info.get("marketCap")),
            pe_ratio=_sanitize(info.get("trailingPE")),
            short_interest_pct=short_pct,
            analyst_rating=_normalize_rec(info.get("recommendationKey")),
            price_target=_sanitize(info.get("targetMeanPrice")),
            earnings_date=None,
            options_unusual=False,
            insider_activity=None,
            squeeze_score=_squeeze(short_pct, short_ratio, vol_ratio),
            timestamp=datetime.now(timezone.utc),
        ))

    cache.set("watchlist_bulk", [s.model_dump() for s in result])
    return result
