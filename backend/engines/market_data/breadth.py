import logging
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import yfinance as yf

from backend.models.market import MarketBreadth
from backend.core import cache, rate_limiter

logger = logging.getLogger(__name__)

UNIVERSE = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA", "JPM", "V", "UNH",
    "XOM", "LLY", "JNJ", "MA", "AVGO", "PG", "HD", "CVX", "MRK", "ABBV",
    "COST", "PEP", "KO", "WMT", "BAC", "MCD", "CRM", "NFLX", "AMD", "TMO",
    "CSCO", "ABT", "LIN", "ORCL", "ACN", "DHR", "TXN", "AMGN", "NEE", "PM",
    "RTX", "HON", "QCOM", "UPS", "IBM", "CAT", "GS", "BLK", "SPGI", "AXP",
]


def _compute_rsi(series: pd.Series, period: int = 14) -> float:
    """Compute RSI for a price series, return last value."""
    try:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        last = rsi.dropna()
        return float(last.iloc[-1]) if len(last) > 0 else 50.0
    except Exception:
        return 50.0


def _compute_breadth(raw: pd.DataFrame) -> MarketBreadth:
    """Compute all breadth metrics from a downloaded DataFrame."""
    # Default yf.download layout (no group_by arg): outer level = Field, inner = Ticker
    # raw["Close"] → DataFrame with ticker symbols as columns
    if isinstance(raw.columns, pd.MultiIndex):
        close_df = raw["Close"]
    else:
        close_df = raw[["Close"]] if "Close" in raw.columns else raw

    close_df = close_df.dropna(how="all")
    total = len(close_df.columns)
    # Check both columns (tickers) AND rows (trading days) — yfinance returns
    # a DataFrame with ticker columns but 0 rows when all downloads fail
    if total == 0 or len(close_df) < 2:
        raise ValueError(f"Insufficient close data: {total} tickers, {len(close_df)} rows")

    last_close = close_df.iloc[-1]
    prev_close = close_df.iloc[-2] if len(close_df) >= 2 else last_close

    # Advancers / decliners
    diff = last_close - prev_close
    advancers = int((diff > 0).sum())
    decliners = int((diff < 0).sum())
    unchanged = int((diff == 0).sum())
    advance_decline_ratio = round(advancers / max(decliners, 1), 2)

    # Moving averages
    ma20 = close_df.rolling(20).mean().iloc[-1]
    ma50 = close_df.rolling(50).mean().iloc[-1]
    ma200 = close_df.rolling(200).mean().iloc[-1]

    valid_20 = (~ma20.isna()) & (~last_close.isna())
    valid_50 = (~ma50.isna()) & (~last_close.isna())
    valid_200 = (~ma200.isna()) & (~last_close.isna())

    pct_above_20ma = round(float((last_close[valid_20] > ma20[valid_20]).sum() / valid_20.sum() * 100), 1) if valid_20.sum() > 0 else 0.0
    pct_above_50ma = round(float((last_close[valid_50] > ma50[valid_50]).sum() / valid_50.sum() * 100), 1) if valid_50.sum() > 0 else 0.0
    pct_above_200ma = round(float((last_close[valid_200] > ma200[valid_200]).sum() / valid_200.sum() * 100), 1) if valid_200.sum() > 0 else 0.0

    # 52-week high/low (last 252 trading days)
    window = close_df.tail(252)
    high_52w = window.max()
    low_52w = window.min()
    new_highs = int((last_close >= high_52w * 0.99).sum())
    new_lows = int((last_close <= low_52w * 1.01).sum())

    # Average RSI across universe
    rsi_values = []
    for col in close_df.columns:
        series = close_df[col].dropna()
        if len(series) >= 16:
            rsi_values.append(_compute_rsi(series))
    avg_rsi = round(float(np.mean(rsi_values)) if rsi_values else 50.0, 1)

    # Composite breadth score (0–100)
    adv_ratio_norm = min(1.0, advancers / max(total, 1))
    breadth_score = round(
        (adv_ratio_norm * 30) + (pct_above_200ma / 100 * 40) + (avg_rsi / 100 * 30),
        1,
    )

    return MarketBreadth(
        advancers=advancers,
        decliners=decliners,
        unchanged=unchanged,
        advance_decline_ratio=advance_decline_ratio,
        pct_above_20ma=pct_above_20ma,
        pct_above_50ma=pct_above_50ma,
        pct_above_200ma=pct_above_200ma,
        new_highs_52w=new_highs,
        new_lows_52w=new_lows,
        avg_rsi=avg_rsi,
        breadth_score=breadth_score,
        timestamp=datetime.now(timezone.utc),
    )


async def fetch_breadth() -> MarketBreadth:
    cache_key = "market_breadth"
    cached = cache.get(cache_key, "breadth")
    if cached:
        return MarketBreadth(**cached)

    rate_limiter.acquire("yfinance")

    last_exc: Exception | None = None
    for attempt in range(2):
        if attempt > 0:
            time.sleep(3)
        try:
            # No group_by arg → default "column" layout: (Field, Ticker)
            # This makes raw["Close"] return a DataFrame with tickers as columns
            raw = yf.download(
                UNIVERSE,
                period="1y",
                interval="1d",
                progress=False,
                auto_adjust=True,
            )
            result = _compute_breadth(raw)
            cache.set(cache_key, result.model_dump())
            return result

        except Exception as e:
            last_exc = e
            logger.warning(f"Breadth engine attempt {attempt + 1} failed: {e}")

    logger.error(f"Breadth engine failed after retries: {last_exc}")
    stale = cache.get_stale(cache_key)
    if stale:
        logger.info("Returning stale breadth data")
        return MarketBreadth(**stale)
    raise last_exc
