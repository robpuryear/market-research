import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Optional, List
import logging

from models.market import TechnicalData
from core import cache, rate_limiter

logger = logging.getLogger(__name__)


def _safe_list(series: pd.Series) -> list:
    """Convert pandas series to list with None for NaN."""
    return [None if pd.isna(v) else round(float(v), 4) for v in series]


def _local_extrema(series: pd.Series, order: int = 10) -> tuple[list, list]:
    prices = series.dropna().values
    support, resistance = [], []
    for i in range(order, len(prices) - order):
        window = prices[i - order: i + order + 1]
        if prices[i] == min(window):
            support.append(round(float(prices[i]), 2))
        elif prices[i] == max(window):
            resistance.append(round(float(prices[i]), 2))
    return sorted(set(support))[-5:], sorted(set(resistance))[:5]


def _compute_signal(close: pd.Series, rsi: pd.Series, macd_line: pd.Series, macd_signal: pd.Series) -> str:
    """Rule-based signal."""
    try:
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi
        macd_cross_up = (macd_line.iloc[-1] > macd_signal.iloc[-1]) and (macd_line.iloc[-2] <= macd_signal.iloc[-2])
        macd_cross_down = (macd_line.iloc[-1] < macd_signal.iloc[-1]) and (macd_line.iloc[-2] >= macd_signal.iloc[-2])
        above_200 = close.iloc[-1] > close.rolling(200).mean().iloc[-1]

        bullish_signals = sum([
            current_rsi < 30,  # oversold
            macd_cross_up,
            above_200 and current_rsi > prev_rsi,
        ])
        bearish_signals = sum([
            current_rsi > 70,  # overbought
            macd_cross_down,
            not above_200 and current_rsi < prev_rsi,
        ])

        if bullish_signals >= 2:
            return "bullish"
        if bearish_signals >= 2:
            return "bearish"
    except Exception:
        pass
    return "neutral"


async def compute(ticker: str) -> TechnicalData:
    cache_key = f"technicals_{ticker}"
    cached = cache.get(cache_key, "technicals")
    if cached:
        return TechnicalData(**cached)

    rate_limiter.acquire("yfinance")

    try:
        hist = yf.download(ticker, period="1y", interval="1d", auto_adjust=True, progress=False)

        if hist.empty:
            raise ValueError(f"No data for {ticker}")

        # Flatten multi-index if needed
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)

        close = hist["Close"]
        open_ = hist["Open"]
        high = hist["High"]
        low = hist["Low"]
        volume = hist["Volume"]

        # Moving averages
        ma20 = close.rolling(20).mean()
        ma50 = close.rolling(50).mean()
        ma200 = close.rolling(200).mean()

        # RSI
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - 100 / (1 + rs)

        # MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        macd_signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd_hist = macd_line - macd_signal_line

        # Bollinger Bands
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        bb_upper = sma20 + 2 * std20
        bb_lower = sma20 - 2 * std20

        support, resistance = _local_extrema(close)
        signal = _compute_signal(close, rsi, macd_line, macd_signal_line)

        dates = [str(d.date()) for d in hist.index]

        tech = TechnicalData(
            ticker=ticker,
            dates=dates,
            opens=_safe_list(open_),
            highs=_safe_list(high),
            lows=_safe_list(low),
            closes=_safe_list(close),
            volumes=_safe_list(volume),
            ma_20=_safe_list(ma20),
            ma_50=_safe_list(ma50),
            ma_200=_safe_list(ma200),
            rsi=_safe_list(rsi),
            macd_line=_safe_list(macd_line),
            macd_signal=_safe_list(macd_signal_line),
            macd_histogram=_safe_list(macd_hist),
            bb_upper=_safe_list(bb_upper),
            bb_middle=_safe_list(sma20),
            bb_lower=_safe_list(bb_lower),
            support_levels=support,
            resistance_levels=resistance,
            current_signal=signal,
        )

        cache.set(cache_key, tech.model_dump())
        return tech

    except Exception as e:
        logger.error(f"Error computing technicals for {ticker}: {e}")
        raise
