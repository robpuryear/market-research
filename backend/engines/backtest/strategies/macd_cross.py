"""
MACD Crossover Strategy

Buy when MACD line crosses above signal line (bullish crossover).
Sell when MACD line crosses below signal line (bearish crossover).
"""

import logging
from typing import List, Tuple
import pandas as pd

from models.backtest import BacktestConfig, Trade

logger = logging.getLogger(__name__)


async def execute(df: pd.DataFrame, config: BacktestConfig) -> Tuple[List[Trade], List[float]]:
    """
    Execute MACD crossover strategy.

    Entry: MACD crosses above signal line
    Exit: MACD crosses below signal line OR stop-loss/take-profit

    Returns:
        - List of trades
        - Equity curve (portfolio value over time)
    """
    trades = []
    equity_curve = []

    cash = config.initial_capital
    position = None

    for i, (date, row) in enumerate(df.iterrows()):
        current_price = row['close']
        macd = row.get('macd', None)
        macd_signal = row.get('macd_signal', None)

        # Skip if MACD not calculated yet
        if macd is None or macd_signal is None or pd.isna(macd) or pd.isna(macd_signal):
            equity_curve.append(cash)
            continue

        # Get previous values for crossover detection
        if i > 0:
            prev_macd = df.iloc[i - 1].get('macd', None)
            prev_signal = df.iloc[i - 1].get('macd_signal', None)
        else:
            prev_macd = None
            prev_signal = None

        # Check for bullish crossover (entry signal)
        if position is None and prev_macd is not None and prev_signal is not None:
            # Bullish crossover: MACD crosses above signal
            if prev_macd <= prev_signal and macd > macd_signal:
                # Enter on next day's open
                if i + 1 < len(df):
                    next_open = df.iloc[i + 1]['open']
                    actual_buy_price = next_open * (1 + config.commission + config.slippage)

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
                            f"{date.strftime('%Y-%m-%d')}: MACD bullish cross "
                            f"({macd:.3f} > {macd_signal:.3f}) - BUY {shares} shares at ${next_open:.2f}"
                        )

        # Check for exit signals
        elif position is not None:
            should_exit = False
            exit_reason = None

            # Bearish crossover: MACD crosses below signal
            if prev_macd is not None and prev_signal is not None:
                if prev_macd >= prev_signal and macd < macd_signal:
                    should_exit = True
                    exit_reason = f"MACD bearish cross ({macd:.3f} < {macd_signal:.3f})"

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

                # Handle timezone
                entry_dt = position['entry_date']
                exit_dt = exit_date
                if hasattr(entry_dt, 'tz') and entry_dt.tz is not None:
                    entry_dt = entry_dt.tz_localize(None)
                if hasattr(exit_dt, 'tz') and exit_dt.tz is not None:
                    exit_dt = exit_dt.tz_localize(None)
                hold_days = (exit_dt - entry_dt).days

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
                    entry_reason="MACD bullish crossover",
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

    logger.info(f"MACD Crossover: Completed {len(trades)} trades")

    return trades, equity_curve
