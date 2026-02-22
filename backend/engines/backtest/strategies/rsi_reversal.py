"""
RSI Reversal Strategy

Buy when RSI crosses below oversold threshold (e.g., 30).
Sell when RSI crosses above overbought threshold (e.g., 70).
"""

import logging
from typing import List, Tuple
import pandas as pd

from models.backtest import BacktestConfig, Trade

logger = logging.getLogger(__name__)


async def execute(df: pd.DataFrame, config: BacktestConfig) -> Tuple[List[Trade], List[float]]:
    """
    Execute RSI reversal strategy.

    Entry: RSI crosses below oversold level
    Exit: RSI crosses above overbought level OR stop-loss/take-profit

    Returns:
        - List of trades
        - Equity curve (portfolio value over time)
    """
    trades = []
    equity_curve = []

    cash = config.initial_capital
    position = None  # Current open position {shares, entry_price, entry_date, entry_idx}

    for i, (date, row) in enumerate(df.iterrows()):
        current_price = row['close']
        rsi = row.get('rsi', None)

        # Skip if RSI not calculated yet
        if rsi is None or pd.isna(rsi):
            equity_curve.append(cash)
            continue

        # Check for entry signal (no position and RSI oversold)
        if position is None and rsi < config.rsi_oversold:
            # Enter on next day's open
            if i + 1 < len(df):
                next_open = df.iloc[i + 1]['open']
                actual_buy_price = next_open * (1 + config.commission + config.slippage)

                # Calculate position size
                capital_to_use = cash * config.position_size
                shares = int(capital_to_use / actual_buy_price)

                if shares > 0:
                    cost = shares * actual_buy_price
                    commission = cost * config.commission

                    cash -= (cost + commission)

                    position = {
                        'shares': shares,
                        'entry_price': next_open,
                        'entry_date': df.index[i + 1],
                        'entry_idx': i + 1,
                        'commission_paid': commission,
                    }

                    logger.debug(
                        f"{date.strftime('%Y-%m-%d')}: RSI {rsi:.1f} - "
                        f"BUY {shares} shares at ${next_open:.2f}"
                    )

        # Check for exit signals (have position)
        elif position is not None:
            should_exit = False
            exit_reason = None

            # RSI overbought signal
            if rsi > config.rsi_overbought:
                should_exit = True
                exit_reason = f"RSI overbought ({rsi:.1f} > {config.rsi_overbought})"

            # Stop loss
            if config.stop_loss is not None:
                loss_pct = (current_price - position['entry_price']) / position['entry_price']
                if loss_pct <= -config.stop_loss:
                    should_exit = True
                    exit_reason = f"Stop loss ({loss_pct:.2%})"

            # Take profit
            if config.take_profit is not None:
                gain_pct = (current_price - position['entry_price']) / position['entry_price']
                if gain_pct >= config.take_profit:
                    should_exit = True
                    exit_reason = f"Take profit ({gain_pct:.2%})"

            # Exit on last day
            if i == len(df) - 1:
                should_exit = True
                exit_reason = "End of backtest period"

            if should_exit:
                # Exit at next day's open (or current close if last day)
                if i + 1 < len(df):
                    exit_price = df.iloc[i + 1]['open']
                    exit_date = df.index[i + 1]
                else:
                    exit_price = current_price
                    exit_date = date

                actual_sell_price = exit_price * (1 - config.commission - config.slippage)

                proceeds = position['shares'] * actual_sell_price
                commission = proceeds * config.commission

                cash += (proceeds - commission)

                # Calculate P&L
                pnl = (exit_price - position['entry_price']) * position['shares']
                pnl -= (position['commission_paid'] + commission)
                return_pct = (exit_price - position['entry_price']) / position['entry_price']

                hold_days = (exit_date - position['entry_date']).days

                # Record trade
                trade = Trade(
                    entry_date=position['entry_date'].strftime('%Y-%m-%d'),
                    exit_date=exit_date.strftime('%Y-%m-%d'),
                    entry_price=position['entry_price'],
                    exit_price=exit_price,
                    shares=position['shares'],
                    pnl=pnl,
                    return_pct=return_pct,
                    hold_days=hold_days,
                    entry_reason=f"RSI oversold",
                    exit_reason=exit_reason,
                    commission_paid=position['commission_paid'] + commission,
                )
                trades.append(trade)

                logger.debug(
                    f"{exit_date.strftime('%Y-%m-%d')}: {exit_reason} - "
                    f"SELL {position['shares']} shares at ${exit_price:.2f}, "
                    f"P&L: ${pnl:.2f} ({return_pct:.2%})"
                )

                position = None

        # Update equity curve
        if position is not None:
            position_value = position['shares'] * current_price
            total_value = cash + position_value
        else:
            total_value = cash

        equity_curve.append(total_value)

    logger.info(f"RSI Reversal: Completed {len(trades)} trades")

    return trades, equity_curve
