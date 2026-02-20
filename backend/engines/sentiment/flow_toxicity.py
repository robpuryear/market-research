import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import logging

from backend.models.sentiment import FlowToxicityData
from backend.core import cache, rate_limiter

logger = logging.getLogger(__name__)


def _toxicity_regime(pin: float) -> tuple[str, str]:
    if pin < 0.2:
        return "Low", "Normal retail flow; low informed trading probability"
    elif pin < 0.4:
        return "Moderate", "Mixed flow; some directional positioning detected"
    elif pin < 0.6:
        return "High", "Elevated informed trading; potential insider/institutional activity"
    return "Extreme", "Extreme imbalance; strong directional bet by informed traders"


async def compute(ticker: str) -> FlowToxicityData:
    cache_key = f"flow_toxicity_{ticker}"
    cached = cache.get(cache_key, "flow")
    if cached:
        return FlowToxicityData(**cached)

    rate_limiter.acquire("yfinance")

    try:
        # Use 1-minute bars for PIN approximation
        hist = yf.download(ticker, period="1d", interval="1m", auto_adjust=True, progress=False)

        if hist.empty or len(hist) < 10:
            return _placeholder(ticker)

        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)

        close = hist["Close"]
        volume = hist["Volume"]
        price_changes = close.diff()

        # Classify bars as buy/sell pressure based on price direction
        buy_volume = volume[price_changes > 0].sum()
        sell_volume = volume[price_changes < 0].sum()
        total_volume = float(volume.sum())

        if total_volume == 0:
            return _placeholder(ticker)

        # PIN approximation: |buys - sells| / (buys + sells)
        imbalance = abs(float(buy_volume) - float(sell_volume))
        pin_score = round(imbalance / (float(buy_volume) + float(sell_volume) + 1e-10), 4)

        regime, interpretation = _toxicity_regime(pin_score)

        result = FlowToxicityData(
            ticker=ticker,
            pin_score=pin_score,
            buy_volume=round(float(buy_volume), 0),
            sell_volume=round(float(sell_volume), 0),
            total_volume=round(total_volume, 0),
            toxicity_regime=regime,
            interpretation=interpretation,
            timestamp=datetime.now(timezone.utc),
        )

        cache.set(cache_key, result.model_dump())
        return result

    except Exception as e:
        logger.warning(f"Error computing flow toxicity for {ticker}: {e}")
        return _placeholder(ticker)


def _placeholder(ticker: str) -> FlowToxicityData:
    return FlowToxicityData(
        ticker=ticker,
        pin_score=0.25,
        buy_volume=0.0,
        sell_volume=0.0,
        total_volume=0.0,
        toxicity_regime="Low",
        interpretation="Insufficient intraday data",
        timestamp=datetime.now(timezone.utc),
    )
