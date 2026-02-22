"""
Historical Data Fetcher for Backtesting

Fetches and caches historical OHLCV data with technical indicators.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
import yfinance as yf
import pandas as pd
import numpy as np

from core import cache

logger = logging.getLogger(__name__)


async def fetch_historical_data(
    ticker: str,
    start_date: str,
    end_date: str,
    include_indicators: bool = True
) -> Optional[pd.DataFrame]:
    """
    Fetch historical OHLCV data with technical indicators.

    Returns DataFrame with columns:
    - Date (index)
    - Open, High, Low, Close, Volume
    - RSI, MACD, MACD_Signal, MACD_Hist
    - MA_20, MA_50, MA_200
    - BB_Upper, BB_Middle, BB_Lower
    """
    cache_key = f"backtest_hist_{ticker}_{start_date}_{end_date}"
    cached = cache.get(cache_key, "analytics")

    if cached:
        logger.info(f"Using cached historical data for {ticker}")
        df = pd.DataFrame(cached)
        # Restore datetime index (was reset for caching)
        # Check for 'Date' (yfinance default) or 'date' or 'index'
        date_col = None
        for col in ['Date', 'date', 'index']:
            if col in df.columns:
                date_col = col
                break
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)
        return df

    try:
        logger.info(f"Fetching historical data for {ticker} from {start_date} to {end_date}")

        # Fetch data from yfinance
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date, auto_adjust=True)

        if df.empty:
            logger.error(f"No historical data found for {ticker}")
            return None

        # Clean up column names
        df.columns = [col.lower() for col in df.columns]

        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            logger.error(f"Missing required columns for {ticker}")
            return None

        if include_indicators:
            df = _calculate_indicators(df)

        # Cache the data
        cache_data = df.reset_index().to_dict('records')
        cache.set(cache_key, cache_data)

        logger.info(f"Fetched {len(df)} days of data for {ticker}")
        return df

    except Exception as e:
        logger.error(f"Failed to fetch historical data for {ticker}: {e}")
        return None


def _calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate technical indicators"""

    # RSI
    df['rsi'] = _calculate_rsi(df['close'], period=14)

    # MACD
    ema_12 = df['close'].ewm(span=12, adjust=False).mean()
    ema_26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_12 - ema_26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # Moving Averages
    df['ma_20'] = df['close'].rolling(window=20).mean()
    df['ma_50'] = df['close'].rolling(window=50).mean()
    df['ma_200'] = df['close'].rolling(window=200).mean()

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

    return df


def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_returns(prices: pd.Series) -> pd.Series:
    """Calculate daily returns"""
    return prices.pct_change()


def calculate_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculate annualized volatility"""
    return returns.std() * np.sqrt(periods_per_year)


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.02,
    periods_per_year: int = 252
) -> float:
    """
    Calculate Sharpe ratio (risk-adjusted returns)

    risk_free_rate: Annual risk-free rate (default 2%)
    """
    excess_returns = returns - (risk_free_rate / periods_per_year)
    if returns.std() == 0:
        return 0.0

    sharpe = (excess_returns.mean() / returns.std()) * np.sqrt(periods_per_year)
    return sharpe


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    """
    Calculate maximum drawdown (worst peak-to-trough decline)

    Returns the drawdown as a positive percentage (e.g., 0.25 = 25% drawdown)
    """
    cumulative_max = equity_curve.expanding().max()
    drawdown = (equity_curve - cumulative_max) / cumulative_max
    max_dd = abs(drawdown.min())
    return max_dd


def calculate_cagr(
    start_value: float,
    end_value: float,
    num_years: float
) -> float:
    """Calculate Compound Annual Growth Rate"""
    if num_years == 0 or start_value == 0:
        return 0.0

    cagr = (end_value / start_value) ** (1 / num_years) - 1
    return cagr
