"""Rule-based ML signals: RSI divergence, MACD crossovers, Bollinger Band squeeze."""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict
import logging

from core import cache, rate_limiter

logger = logging.getLogger(__name__)


def _detect_rsi_divergence(close: pd.Series, rsi: pd.Series) -> str | None:
    """Detect bullish/bearish RSI divergence over last 20 bars."""
    if len(close) < 20:
        return None
    c = close.iloc[-20:]
    r = rsi.iloc[-20:]
    price_trend = c.iloc[-1] - c.iloc[0]
    rsi_trend = r.iloc[-1] - r.iloc[0]

    if price_trend < 0 and rsi_trend > 5:
        return "RSI Bullish Divergence"
    if price_trend > 0 and rsi_trend < -5:
        return "RSI Bearish Divergence"
    return None


def _detect_macd_cross(macd: pd.Series, signal: pd.Series) -> str | None:
    if len(macd) < 2:
        return None
    if macd.iloc[-1] > signal.iloc[-1] and macd.iloc[-2] <= signal.iloc[-2]:
        return "MACD Bullish Crossover"
    if macd.iloc[-1] < signal.iloc[-1] and macd.iloc[-2] >= signal.iloc[-2]:
        return "MACD Bearish Crossover"
    return None


def _detect_bb_squeeze(close: pd.Series, bb_upper: pd.Series, bb_lower: pd.Series) -> str | None:
    """Detect Bollinger Band squeeze (low volatility, potential breakout)."""
    bandwidth = (bb_upper - bb_lower) / close
    avg_bw = bandwidth.rolling(20).mean()
    if bandwidth.iloc[-1] < avg_bw.iloc[-1] * 0.7:
        return "BB Squeeze (Breakout Pending)"
    return None


def _detect_golden_death_cross(close: pd.Series) -> str | None:
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()
    if len(ma50.dropna()) < 2 or len(ma200.dropna()) < 2:
        return None
    if ma50.iloc[-1] > ma200.iloc[-1] and ma50.iloc[-2] <= ma200.iloc[-2]:
        return "Golden Cross (MA50 > MA200)"
    if ma50.iloc[-1] < ma200.iloc[-1] and ma50.iloc[-2] >= ma200.iloc[-2]:
        return "Death Cross (MA50 < MA200)"
    return None


async def run_all(ticker: str) -> Dict:
    cache_key = f"ml_signals_{ticker}"
    cached = cache.get(cache_key, "technicals")
    if cached:
        return cached

    rate_limiter.acquire("yfinance")

    try:
        hist = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True, progress=False)
        if hist.empty:
            return {"ticker": ticker, "signals": [], "signal_count": 0}

        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)

        close = hist["Close"]
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - 100 / (1 + rs)

        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9).mean()

        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        bb_upper = sma20 + 2 * std20
        bb_lower = sma20 - 2 * std20

        signals = []
        for detector in [
            lambda: _detect_rsi_divergence(close, rsi),
            lambda: _detect_macd_cross(macd, macd_signal),
            lambda: _detect_bb_squeeze(close, bb_upper, bb_lower),
            lambda: _detect_golden_death_cross(close),
        ]:
            result = detector()
            if result:
                signals.append(result)

        # RSI overbought/oversold
        rsi_val = float(rsi.iloc[-1]) if not rsi.empty else 50
        if rsi_val > 70:
            signals.append(f"RSI Overbought ({rsi_val:.0f})")
        elif rsi_val < 30:
            signals.append(f"RSI Oversold ({rsi_val:.0f})")

        result = {
            "ticker": ticker,
            "signals": signals,
            "signal_count": len(signals),
            "rsi_current": round(rsi_val, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        cache.set(cache_key, result)
        return result

    except Exception as e:
        logger.error(f"Error running ML signals for {ticker}: {e}")
        return {"ticker": ticker, "signals": [], "signal_count": 0}
