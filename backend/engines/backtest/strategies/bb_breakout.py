"""
Bollinger Band Breakout Strategy

Buy when price breaks above upper band (momentum breakout).
Sell when price crosses back below middle band (mean reversion exit).

Alternative mode: Mean reversion - buy when price touches lower band,
sell when it reaches middle or upper band.
"""

import logging
from typing import List, Tuple
import pandas as pd

from models.backtest import BacktestConfig, Trade

logger = logging.getLogger(__name__)


async def execute(df: pd.DataFrame, config: BacktestConfig) -> Tuple[List[Trade], List[float]]:
    """
    Execute Bollinger Band breakout strategy.

    Entry: Price breaks above upper band (or touches lower band for mean reversion)
    Exit: Price crosses below middle band OR stop-loss/take-profit

    Returns:
        - List of trades
        - Equity curve (portfolio value over time)
    """
    trades = []
    equity_curve = []

    cash = config.initial_capital
    position = None

    # Determine mode: breakout (default) or mean_reversion
    mode = getattr(config, 'bb_mode', 'breakout')

    for i, (date, row) in enumerate(df.iterrows()):
        current_price = row['close']
        bb_upper = row.get('bb_upper', None)
        bb_middle = row.get('bb_middle', None)
        bb_lower = row.get('bb_lower', None)

        # Skip if Bollinger Bands not calculated yet
        if bb_upper is None or bb_middle is None or bb_lower is None:
            equity_curve.append(cash)
            continue
        if pd.isna(bb_upper) or pd.isna(bb_middle) or pd.isna(bb_lower):
            equity_curve.append(cash)
            continue

        # Get previous values
        if i > 0:
            prev_close = df.iloc[i - 1]['close']
            prev_bb_upper = df.iloc[i - 1].get('bb_upper', None)
            prev_bb_middle = df.iloc[i - 1].get('bb_middle', None)
            prev_bb_lower = df.iloc[i - 1].get('bb_lower', None)
        else:
            prev_close = None
            prev_bb_upper = None
            prev_bb_middle = None
            prev_bb_lower = None

        # Check for entry signal
        if position is None and prev_close is not None:
            should_enter = False
            entry_signal = ""

            if mode == 'breakout':
                # Breakout mode: buy when price breaks above upper band
                if prev_close <= prev_bb_upper and current_price > bb_upper:
                    should_enter = True
                    entry_signal = f"BB breakout (price {current_price:.2f} > upper {bb_upper:.2f})"
            else:
                # Mean reversion mode: buy when price touches lower band
                if current_price <= bb_lower:
                    should_enter = True
                    entry_signal = f"BB oversold (price {current_price:.2f} <= lower {bb_lower:.2f})"

            if should_enter:
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
                            'entry_signal': entry_signal,
                        }

                        logger.debug(
                            f"{date.strftime('%Y-%m-%d')}: {entry_signal} - "
                            f"BUY {shares} shares at ${next_open:.2f}"
                        )

        # Check for exit signals
        elif position is not None:
            should_exit = False
            exit_reason = None

            # Exit when price crosses below middle band
            if prev_close is not None and prev_bb_middle is not None:
                if mode == 'breakout':
                    # Breakout exit: price falls back below middle band
                    if prev_close >= prev_bb_middle and current_price < bb_middle:
                        should_exit = True
                        exit_reason = f"BB reversal (price {current_price:.2f} < middle {bb_middle:.2f})"
                else:
                    # Mean reversion exit: price reaches middle or upper band
                    if current_price >= bb_middle:
                        should_exit = True
                        exit_reason = f"BB mean reversion (price {current_price:.2f} >= middle {bb_middle:.2f})"

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
                    entry_reason=position['entry_signal'],
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

    logger.info(f"Bollinger Band {mode.capitalize()}: Completed {len(trades)} trades")

    return trades, equity_curve
