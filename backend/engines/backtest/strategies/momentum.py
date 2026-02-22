"""
Momentum Strategy

Buy when price momentum is strong and accelerating.
Sell when momentum weakens or reverses.

Uses multiple momentum indicators:
- ROC (Rate of Change)
- RSI for momentum confirmation
- Volume for confirmation
"""

import logging
from typing import List, Tuple
import pandas as pd
import numpy as np

from models.backtest import BacktestConfig, Trade

logger = logging.getLogger(__name__)


async def execute(df: pd.DataFrame, config: BacktestConfig) -> Tuple[List[Trade], List[float]]:
    """
    Execute momentum strategy.

    Entry: Strong positive momentum (ROC > threshold) + RSI confirming + volume surge
    Exit: Momentum weakens (ROC falls below exit threshold) OR stop-loss/take-profit

    Returns:
        - List of trades
        - Equity curve (portfolio value over time)
    """
    trades = []
    equity_curve = []

    cash = config.initial_capital
    position = None

    # Momentum thresholds (can be configured)
    roc_entry_threshold = getattr(config, 'roc_entry', 5.0)  # 5% positive ROC
    roc_exit_threshold = getattr(config, 'roc_exit', 0.0)     # Exit when ROC drops to 0
    rsi_min = getattr(config, 'momentum_rsi_min', 50.0)       # RSI should be above 50
    rsi_max = getattr(config, 'momentum_rsi_max', 80.0)       # But not overbought
    volume_threshold = getattr(config, 'volume_surge', 1.2)   # Volume 20% above average

    # Calculate ROC (Rate of Change over 10 days)
    roc_period = getattr(config, 'roc_period', 10)
    df['roc'] = ((df['close'] - df['close'].shift(roc_period)) / df['close'].shift(roc_period)) * 100

    # Calculate average volume (20-day)
    df['volume_ma'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma']

    for i, (date, row) in enumerate(df.iterrows()):
        current_price = row['close']
        roc = row.get('roc', None)
        rsi = row.get('rsi', None)
        volume_ratio = row.get('volume_ratio', None)

        # Skip if indicators not calculated yet
        if roc is None or rsi is None or volume_ratio is None:
            equity_curve.append(cash)
            continue
        if pd.isna(roc) or pd.isna(rsi) or pd.isna(volume_ratio):
            equity_curve.append(cash)
            continue

        # Get previous values
        if i > 0:
            prev_roc = df.iloc[i - 1].get('roc', None)
            prev_rsi = df.iloc[i - 1].get('rsi', None)
        else:
            prev_roc = None
            prev_rsi = None

        # Check for entry signal (no position)
        if position is None and prev_roc is not None:
            # Strong momentum conditions:
            # 1. ROC crosses above entry threshold (momentum accelerating)
            # 2. RSI in healthy momentum range (not oversold, not overbought)
            # 3. Volume surge confirming move
            momentum_strong = prev_roc <= roc_entry_threshold and roc > roc_entry_threshold
            rsi_healthy = rsi_min <= rsi <= rsi_max
            volume_surge = volume_ratio >= volume_threshold

            if momentum_strong and rsi_healthy and volume_surge:
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
                            f"{date.strftime('%Y-%m-%d')}: Strong momentum "
                            f"(ROC={roc:.2f}%, RSI={rsi:.1f}, Vol={volume_ratio:.2f}x) - "
                            f"BUY {shares} shares at ${next_open:.2f}"
                        )

        # Check for exit signals
        elif position is not None:
            should_exit = False
            exit_reason = None

            # Momentum weakening: ROC drops below exit threshold
            if prev_roc is not None:
                if prev_roc >= roc_exit_threshold and roc < roc_exit_threshold:
                    should_exit = True
                    exit_reason = f"Momentum fading (ROC={roc:.2f}% < {roc_exit_threshold}%)"

            # RSI overbought (momentum exhaustion)
            if rsi > 80.0:
                should_exit = True
                exit_reason = f"Momentum exhaustion (RSI={rsi:.1f})"

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
                    entry_reason="Strong momentum (ROC + RSI + volume)",
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

    logger.info(f"Momentum: Completed {len(trades)} trades")

    return trades, equity_curve
