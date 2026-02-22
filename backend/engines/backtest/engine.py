"""
Core Backtesting Engine

Executes trading strategies on historical data and calculates performance metrics.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
import pandas as pd
import numpy as np
import uuid

from models.backtest import BacktestConfig, BacktestResult, Trade
from engines.backtest.historical_data import (
    fetch_historical_data,
    calculate_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_cagr,
)
from engines.backtest.strategies import buy_hold, rsi_reversal

logger = logging.getLogger(__name__)


async def run_backtest(config: BacktestConfig) -> BacktestResult:
    """
    Execute a backtest with the given configuration.

    Returns complete backtest results with trades and metrics.
    """
    logger.info(f"Starting backtest: {config.strategy_type} on {config.ticker}")

    # Fetch historical data
    df = await fetch_historical_data(
        config.ticker,
        config.start_date,
        config.end_date,
        include_indicators=True
    )

    if df is None or df.empty:
        raise ValueError(f"No historical data available for {config.ticker}")

    # Select strategy
    if config.strategy_type == "buy_hold":
        trades, equity_curve = await buy_hold.execute(df, config)
    elif config.strategy_type == "rsi_reversal":
        trades, equity_curve = await rsi_reversal.execute(df, config)
    else:
        raise ValueError(f"Unknown strategy type: {config.strategy_type}")

    # Calculate benchmark (buy-and-hold)
    benchmark_return = _calculate_benchmark(df, config)

    # Calculate performance metrics
    metrics = _calculate_metrics(
        trades=trades,
        equity_curve=equity_curve,
        config=config,
        df=df,
    )

    # Build result
    result = BacktestResult(
        config=config,
        trades=trades,
        final_value=equity_curve[-1] if equity_curve else config.initial_capital,
        total_return=metrics['total_return'],
        annual_return=metrics['annual_return'],
        sharpe_ratio=metrics['sharpe_ratio'],
        max_drawdown=metrics['max_drawdown'],
        volatility=metrics['volatility'],
        total_trades=metrics['total_trades'],
        winning_trades=metrics['winning_trades'],
        losing_trades=metrics['losing_trades'],
        win_rate=metrics['win_rate'],
        avg_win=metrics['avg_win'],
        avg_loss=metrics['avg_loss'],
        avg_win_loss_ratio=metrics['avg_win_loss_ratio'],
        profit_factor=metrics['profit_factor'],
        equity_curve=equity_curve,
        dates=[d.strftime('%Y-%m-%d') for d in df.index],
        drawdown_curve=metrics['drawdown_curve'],
        benchmark_return=benchmark_return,
        alpha=metrics['total_return'] - benchmark_return,
        start_date=config.start_date,
        end_date=config.end_date,
        total_days=len(df),
        timestamp=datetime.now(timezone.utc),
    )

    logger.info(
        f"Backtest complete: {metrics['total_trades']} trades, "
        f"{metrics['total_return']:.2%} return, Sharpe: {metrics['sharpe_ratio']:.2f}"
    )

    return result


def _calculate_benchmark(df: pd.DataFrame, config: BacktestConfig) -> float:
    """Calculate buy-and-hold return for benchmark"""
    if df.empty:
        return 0.0

    start_price = df['close'].iloc[0]
    end_price = df['close'].iloc[-1]

    # Account for transaction costs
    buy_cost = start_price * (1 + config.commission + config.slippage)
    sell_proceeds = end_price * (1 - config.commission - config.slippage)

    return_pct = (sell_proceeds - buy_cost) / buy_cost
    return return_pct


def _calculate_metrics(
    trades: List[Trade],
    equity_curve: List[float],
    config: BacktestConfig,
    df: pd.DataFrame,
) -> dict:
    """Calculate all performance metrics"""

    # Trade statistics
    total_trades = len([t for t in trades if t.exit_date is not None])
    winning_trades = len([t for t in trades if t.pnl > 0])
    losing_trades = len([t for t in trades if t.pnl < 0])

    win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

    wins = [t.pnl for t in trades if t.pnl > 0]
    losses = [abs(t.pnl) for t in trades if t.pnl < 0]

    avg_win = sum(wins) / len(wins) if wins else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0
    avg_win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0.0

    gross_profit = sum(wins)
    gross_loss = sum(losses)
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

    # Portfolio metrics
    if not equity_curve or len(equity_curve) < 2:
        return {
            'total_return': 0.0,
            'annual_return': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_win_loss_ratio': avg_win_loss_ratio,
            'profit_factor': profit_factor,
            'drawdown_curve': [],
        }

    equity_series = pd.Series(equity_curve)
    returns = equity_series.pct_change().dropna()

    total_return = (equity_curve[-1] - config.initial_capital) / config.initial_capital

    # Calculate number of years
    num_days = len(df)
    num_years = num_days / 252  # Trading days per year

    annual_return = calculate_cagr(config.initial_capital, equity_curve[-1], num_years)

    sharpe_ratio = calculate_sharpe_ratio(returns) if len(returns) > 0 else 0.0

    max_drawdown = calculate_max_drawdown(equity_series)

    volatility = calculate_volatility(returns) if len(returns) > 0 else 0.0

    # Calculate drawdown curve for visualization
    cumulative_max = equity_series.expanding().max()
    drawdown_curve = ((equity_series - cumulative_max) / cumulative_max).tolist()

    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'volatility': volatility,
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'avg_win_loss_ratio': avg_win_loss_ratio,
        'profit_factor': profit_factor,
        'drawdown_curve': drawdown_curve,
    }
