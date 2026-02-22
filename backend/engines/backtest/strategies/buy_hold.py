"""
Buy-and-Hold Strategy

Simple baseline strategy: buy at start, hold until end.
"""

import logging
from typing import List, Tuple
import pandas as pd

from models.backtest import BacktestConfig, Trade

logger = logging.getLogger(__name__)


async def execute(df: pd.DataFrame, config: BacktestConfig) -> Tuple[List[Trade], List[float]]:
    """
    Execute buy-and-hold strategy.

    Buys at the first available price and holds until the end.

    Returns:
        - List of trades
        - Equity curve (portfolio value over time)
    """
    trades = []
    equity_curve = []

    cash = config.initial_capital
    shares = 0
    position_value = 0.0

    for i, (date, row) in enumerate(df.iterrows()):
        # Buy on first day
        if i == 0:
            entry_price = row['open']
            # Apply commission and slippage
            actual_buy_price = entry_price * (1 + config.commission + config.slippage)

            # Buy max shares with available capital
            shares = int((cash * config.position_size) / actual_buy_price)
            cost = shares * actual_buy_price
            commission = cost * config.commission

            cash -= (cost + commission)
            position_value = shares * entry_price

            # Record trade (exit will be filled at end)
            trade = Trade(
                entry_date=date.strftime('%Y-%m-%d'),
                entry_price=entry_price,
                shares=shares,
                entry_reason="Buy-and-hold entry",
                commission_paid=commission,
            )
            trades.append(trade)

            logger.info(
                f"Buy-and-hold: Bought {shares} shares at ${entry_price:.2f} "
                f"(${actual_buy_price:.2f} after costs)"
            )

        # Update position value
        position_value = shares * row['close']
        total_value = cash + position_value
        equity_curve.append(total_value)

    # Sell on last day
    if shares > 0 and len(df) > 0:
        last_date = df.index[-1]
        exit_price = df.iloc[-1]['close']

        # Apply commission and slippage
        actual_sell_price = exit_price * (1 - config.commission - config.slippage)

        proceeds = shares * actual_sell_price
        commission = proceeds * config.commission

        cash += (proceeds - commission)

        # Update final trade
        entry_price = trades[0].entry_price
        pnl = (exit_price - entry_price) * shares - trades[0].commission_paid - commission
        return_pct = (exit_price - entry_price) / entry_price

        hold_days = (last_date - pd.to_datetime(trades[0].entry_date)).days

        trades[0].exit_date = last_date.strftime('%Y-%m-%d')
        trades[0].exit_price = exit_price
        trades[0].pnl = pnl
        trades[0].return_pct = return_pct
        trades[0].hold_days = hold_days
        trades[0].exit_reason = "Buy-and-hold exit (end of period)"
        trades[0].commission_paid += commission

        logger.info(
            f"Buy-and-hold: Sold {shares} shares at ${exit_price:.2f}, "
            f"P&L: ${pnl:.2f} ({return_pct:.2%})"
        )

    # Ensure equity curve has same length as dataframe
    if len(equity_curve) != len(df):
        logger.warning(f"Equity curve length mismatch: {len(equity_curve)} vs {len(df)}")

    return trades, equity_curve
