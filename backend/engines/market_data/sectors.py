import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
from typing import List
import logging

from backend.models.market import SectorData
from backend.core import cache, rate_limiter

logger = logging.getLogger(__name__)

SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Healthcare",
    "XLI": "Industrials",
    "XLC": "Communication",
    "XLY": "Consumer Discret.",
    "XLP": "Consumer Staples",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLB": "Materials",
}


async def fetch_rotation() -> List[SectorData]:
    cached = cache.get("sector_rotation", "sectors")
    if cached:
        return [SectorData(**s) for s in cached]

    rate_limiter.acquire("yfinance")

    tickers = list(SECTOR_ETFS.keys()) + ["SPY"]
    try:
        data = yf.download(
            tickers,
            period="2mo",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
        )

        def get_close(sym: str) -> pd.Series:
            try:
                if sym in data.columns.get_level_values(0):
                    return data[sym]["Close"].dropna()
            except Exception:
                pass
            return pd.Series(dtype=float)

        spy_close = get_close("SPY")
        if spy_close.empty:
            raise ValueError("SPY data unavailable")

        spy_1d = float(spy_close.pct_change().iloc[-1]) * 100 if len(spy_close) > 1 else 0
        spy_5d = float((spy_close.iloc[-1] / spy_close.iloc[-6] - 1) * 100) if len(spy_close) > 5 else 0
        spy_1m = float((spy_close.iloc[-1] / spy_close.iloc[-22] - 1) * 100) if len(spy_close) > 21 else 0

        result = []
        for etf, name in SECTOR_ETFS.items():
            s = get_close(etf)
            if s.empty:
                continue
            price = float(s.iloc[-1])
            ch_1d = float(s.pct_change().iloc[-1]) * 100 if len(s) > 1 else 0
            ch_5d = float((s.iloc[-1] / s.iloc[-6] - 1) * 100) if len(s) > 5 else 0
            ch_1m = float((s.iloc[-1] / s.iloc[-22] - 1) * 100) if len(s) > 21 else 0

            result.append(SectorData(
                ticker=etf,
                name=name,
                price=round(price, 2),
                change_1d=round(ch_1d, 2),
                change_5d=round(ch_5d, 2),
                change_1m=round(ch_1m, 2),
                vs_spy_1d=round(ch_1d - spy_1d, 2),
                vs_spy_5d=round(ch_5d - spy_5d, 2),
                vs_spy_1m=round(ch_1m - spy_1m, 2),
            ))

        cache.set("sector_rotation", [s.model_dump() for s in result])
        return result

    except Exception as e:
        logger.error(f"Error fetching sector rotation: {e}")
        stale = cache.get_stale("sector_rotation")
        if stale:
            logger.info("Returning stale sector data")
            return [SectorData(**s) for s in stale]
        raise
