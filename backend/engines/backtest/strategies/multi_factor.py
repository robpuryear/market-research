"""
Multi-Factor Strategy

Combines multiple technical signals for higher-confidence trades.
Uses a scoring system to decide when to enter/exit.

Factors considered:
- RSI (oversold/overbought)
- MACD (bullish/bearish crossover)
- Moving Average trend (MA50 vs MA200)
- Bollinger Bands (price position)
- Volume confirmation

Entry when score >= threshold (bullish signals align)
Exit when score drops below exit threshold or bearish signals dominate
"""

import logging
from typing import List, Tuple
import pandas as pd

from models.backtest import BacktestConfig, Trade

logger = logging.getLogger(__name__)


def calculate_signal_score(row, prev_row) -> float:
    """
    Calculate multi-factor signal score from -5 (very bearish) to +5 (very bullish).

    Each factor contributes -1, 0, or +1 to the score.
    """
    score = 0.0

    # Factor 1: RSI
    rsi = row.get('rsi', None)
    if rsi is not None and not pd.isna(rsi):
        if rsi < 30:
            score += 1  # Oversold = bullish
        elif rsi > 70:
            score -= 1  # Overbought = bearish

    # Factor 2: MACD
    macd = row.get('macd', None)
    macd_signal = row.get('macd_signal', None)
    if macd is not None and macd_signal is not None:
        if not pd.isna(macd) and not pd.isna(macd_signal):
            if macd > macd_signal:
                score += 1  # MACD above signal = bullish
            else:
                score -= 1  # MACD below signal = bearish

    # Factor 3: Moving Average trend
    ma_50 = row.get('ma_50', None)
    ma_200 = row.get('ma_200', None)
    if ma_50 is not None and ma_200 is not None:
        if not pd.isna(ma_50) and not pd.isna(ma_200):
            if ma_50 > ma_200:
                score += 1  # Golden cross = bullish
            else:
                score -= 1  # Death cross = bearish

    # Factor 4: Price vs Bollinger Bands
    close = row['close']
    bb_upper = row.get('bb_upper', None)
    bb_middle = row.get('bb_middle', None)
    bb_lower = row.get('bb_lower', None)
    if bb_upper is not None and bb_lower is not None and bb_middle is not None:
        if not pd.isna(bb_upper) and not pd.isna(bb_lower) and not pd.isna(bb_middle):
            bb_range = bb_upper - bb_lower
            if bb_range > 0:
                # Normalize position: 0 = lower band, 0.5 = middle, 1 = upper
                bb_position = (close - bb_lower) / bb_range
                if bb_position < 0.2:
                    score += 1  # Near lower band = oversold = bullish
                elif bb_position > 0.8:
                    score -= 1  # Near upper band = overbought = bearish

    # Factor 5: Volume confirmation
    volume = row.get('volume', None)
    volume_ma = row.get('volume_ma', None)
    if volume is not None and volume_ma is not None:
        if not pd.isna(volume) and not pd.isna(volume_ma) and volume_ma > 0:
            volume_ratio = volume / volume_ma
            if volume_ratio > 1.5:
                # High volume - amplifies current trend
                # Check if price is rising or falling
                if prev_row is not None:
                    prev_close = prev_row['close']
                    if close > prev_close:
                        score += 0.5  # High volume + rising = bullish
                    else:
                        score -= 0.5  # High volume + falling = bearish

    return score


async def execute(df: pd.DataFrame, config: BacktestConfig) -> Tuple[List[Trade], List[float]]:
    """
    Execute multi-factor strategy.

    Entry: Signal score >= entry_threshold (default 3.0)
    Exit: Signal score <= exit_threshold (default 0.0) OR stop-loss/take-profit

    Returns:
        - List of trades
        - Equity curve (portfolio value over time)
    """
    trades = []
    equity_curve = []

    cash = config.initial_capital
    position = None

    # Score thresholds
    entry_threshold = getattr(config, 'signal_entry_threshold', 3.0)
    exit_threshold = getattr(config, 'signal_exit_threshold', 0.0)

    # Calculate volume MA for volume factor
    df['volume_ma'] = df['volume'].rolling(window=20).mean()

    # Calculate signal scores for entire dataframe
    df['signal_score'] = 0.0
    for i in range(len(df)):
        prev_row = df.iloc[i - 1] if i > 0 else None
        df.iloc[i, df.columns.get_loc('signal_score')] = calculate_signal_score(df.iloc[i], prev_row)

    for i, (date, row) in enumerate(df.iterrows()):
        current_price = row['close']
        signal_score = row['signal_score']

        # Get previous score
        prev_score = df.iloc[i - 1]['signal_score'] if i > 0 else 0.0

        # Check for entry signal (no position)
        if position is None:
            # Entry when score crosses above threshold
            if prev_score < entry_threshold and signal_score >= entry_threshold:
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
                            'entry_score': signal_score,
                        }

                        logger.debug(
                            f"{date.strftime('%Y-%m-%d')}: Multi-factor bullish signal "
                            f"(score={signal_score:.1f}) - BUY {shares} shares at ${next_open:.2f}"
                        )

        # Check for exit signals
        elif position is not None:
            should_exit = False
            exit_reason = None

            # Exit when score drops below threshold
            if prev_score >= exit_threshold and signal_score < exit_threshold:
                should_exit = True
                exit_reason = f"Multi-factor bearish (score={signal_score:.1f})"

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
                    entry_reason=f"Multi-factor bullish (score={position['entry_score']:.1f})",
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

    logger.info(f"Multi-Factor: Completed {len(trades)} trades")

    return trades, equity_curve
