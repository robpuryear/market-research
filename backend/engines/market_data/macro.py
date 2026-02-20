import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Optional
import logging

from models.market import MarketSnapshot, IndexData
from core import cache, rate_limiter

logger = logging.getLogger(__name__)

MACRO_TICKERS = ["^VIX", "SPY", "QQQ", "IWM", "^TNX", "^IRX"]


def _vix_regime(vix: float) -> str:
    if vix < 15:
        return "Low"
    elif vix < 25:
        return "Elevated"
    elif vix < 35:
        return "High"
    return "Extreme"


def _fear_greed(vix: float, spy_change: float) -> float:
    """Approximate CNN Fear & Greed using VIX and momentum."""
    # VIX component: lower VIX = more greed (inverted, scaled 0-50)
    vix_component = max(0, min(50, (40 - vix) / 40 * 50))
    # Momentum component: positive SPY = more greed
    momentum_component = max(0, min(50, 25 + spy_change * 5))
    return round(vix_component + momentum_component, 1)


def _market_regime(vix: float, spy_change_pct: float, above_200ma: bool) -> str:
    if vix > 30:
        return "Volatile"
    if above_200ma and spy_change_pct > 0:
        return "Bull"
    if not above_200ma and spy_change_pct < 0:
        return "Bear"
    return "Neutral"


def _local_extrema(series: pd.Series, order: int = 10) -> tuple[list, list]:
    """Find local support and resistance levels."""
    prices = series.dropna().values
    support, resistance = [], []
    for i in range(order, len(prices) - order):
        window = prices[i - order: i + order + 1]
        if prices[i] == min(window):
            support.append(round(float(prices[i]), 2))
        elif prices[i] == max(window):
            resistance.append(round(float(prices[i]), 2))
    # Return last 3 unique levels
    return sorted(set(support))[-3:], sorted(set(resistance))[:3]


def _build_index_data(ticker: str, hist: pd.DataFrame) -> IndexData:
    if hist.empty:
        return IndexData(ticker=ticker, price=0.0, change_pct=0.0)

    close = hist["Close"]
    price = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else price
    change_pct = round((price - prev) / prev * 100, 2) if prev != 0 else 0.0

    ma20 = float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None
    ma50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else None
    ma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
    above_200 = (price > ma200) if ma200 else None

    volume = float(hist["Volume"].iloc[-1]) if "Volume" in hist else None
    avg_vol = float(hist["Volume"].rolling(20).mean().iloc[-1]) if "Volume" in hist else None
    vol_ratio = round(volume / avg_vol, 2) if (volume and avg_vol and avg_vol > 0) else None

    support, resistance = _local_extrema(close)

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi_val = float(100 - 100 / (1 + rs.iloc[-1])) if not rs.empty else None

    return IndexData(
        ticker=ticker,
        price=round(price, 2),
        change_pct=change_pct,
        ma_20=round(ma20, 2) if ma20 else None,
        ma_50=round(ma50, 2) if ma50 else None,
        ma_200=round(ma200, 2) if ma200 else None,
        above_200ma=above_200,
        support=support,
        resistance=resistance,
        rsi=round(rsi_val, 1) if rsi_val else None,
        volume=volume,
        volume_ratio=vol_ratio,
    )


async def fetch_snapshot() -> MarketSnapshot:
    cached = cache.get("macro_snapshot", "snapshot")
    if cached:
        return MarketSnapshot(**cached)

    rate_limiter.acquire("yfinance")

    try:
        data = yf.download(
            MACRO_TICKERS,
            period="1y",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
        )

        def get_hist(sym: str) -> pd.DataFrame:
            if sym in data.columns.get_level_values(0):
                df = data[sym].dropna(how="all")
                return df
            return pd.DataFrame()

        vix_hist = get_hist("^VIX")
        spy_hist = get_hist("SPY")
        qqq_hist = get_hist("QQQ")
        iwm_hist = get_hist("IWM")
        tnx_hist = get_hist("^TNX")
        irx_hist = get_hist("^IRX")

        vix = float(vix_hist["Close"].iloc[-1]) if not vix_hist.empty else 20.0
        yield_10y = float(tnx_hist["Close"].iloc[-1]) if not tnx_hist.empty else None
        yield_2y = float(irx_hist["Close"].iloc[-1]) if not irx_hist.empty else None
        yield_spread = round(yield_10y - yield_2y, 3) if (yield_10y and yield_2y) else None

        spy_data = _build_index_data("SPY", spy_hist)
        qqq_data = _build_index_data("QQQ", qqq_hist)
        iwm_data = _build_index_data("IWM", iwm_hist)

        # If SPY price is zero, yfinance returned empty data (rate-limited).
        # Don't cache bad data — fall back to stale cache instead.
        if spy_data.price == 0.0:
            stale = cache.get_stale("macro_snapshot")
            if stale:
                logger.info("yfinance returned empty data; returning stale macro snapshot")
                return MarketSnapshot(**stale)
            logger.warning("yfinance returned empty data and no stale cache exists")

        snapshot = MarketSnapshot(
            vix=round(vix, 2),
            vix_regime=_vix_regime(vix),
            fear_greed_approx=_fear_greed(vix, spy_data.change_pct),
            yield_10y=round(yield_10y, 3) if yield_10y else None,
            yield_2y=round(yield_2y, 3) if yield_2y else None,
            yield_spread=yield_spread,
            market_regime=_market_regime(vix, spy_data.change_pct, spy_data.above_200ma or False),
            spy=spy_data,
            qqq=qqq_data,
            iwm=iwm_data,
            timestamp=datetime.now(timezone.utc),
        )

        if spy_data.price > 0.0:
            cache.set("macro_snapshot", snapshot.model_dump())
        return snapshot

    except Exception as e:
        logger.error(f"Error fetching macro snapshot: {e}")
        stale = cache.get_stale("macro_snapshot")
        if stale:
            logger.info("Returning stale macro snapshot")
            return MarketSnapshot(**stale)
        raise
