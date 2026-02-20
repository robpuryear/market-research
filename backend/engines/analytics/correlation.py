import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict
import logging

from backend.core import cache, rate_limiter
from backend.config import settings

logger = logging.getLogger(__name__)


async def compute_matrix() -> Dict:
    cache_key = "correlation_matrix"
    cached = cache.get(cache_key, "technicals")
    if cached:
        return cached

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

        closes = {}
        for ticker in tickers:
            try:
                if ticker in data.columns.get_level_values(0):
                    s = data[ticker]["Close"].dropna()
                    if not s.empty:
                        closes[ticker] = s
            except Exception:
                pass

        if len(closes) < 2:
            return {"tickers": tickers, "matrix": {}, "timestamp": datetime.now(timezone.utc).isoformat()}

        df = pd.DataFrame(closes)
        corr = df.pct_change().dropna().corr()

        matrix = {}
        for t1 in corr.index:
            matrix[t1] = {}
            for t2 in corr.columns:
                matrix[t1][t2] = round(float(corr.loc[t1, t2]), 3)

        result = {
            "tickers": list(corr.index),
            "matrix": matrix,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        cache.set(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"Error computing correlation matrix: {e}")
        return {"tickers": tickers, "matrix": {}, "timestamp": datetime.now(timezone.utc).isoformat()}
