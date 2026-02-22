"""
Alert Evaluator - Check if alert conditions are met

Runs periodically via scheduler, evaluates all enabled alerts.
"""

import logging
from typing import Tuple
from models.alerts import Alert, PriceCondition, SignalCondition, EarningsCondition
from engines.alerts.alert_manager import get_all_alerts, update_alert, create_notification
from engines.analytics import ml_signals
from engines.watchlist import earnings_calendar
from datetime import datetime, timezone
import yfinance as yf

logger = logging.getLogger(__name__)


async def evaluate_all_alerts():
    """Evaluate all enabled alerts and trigger notifications"""
    alerts = get_all_alerts()
    enabled = [a for a in alerts if a.enabled]

    logger.info(f"Evaluating {len(enabled)} enabled alerts")

    for alert in enabled:
        try:
            triggered, message, data = await _evaluate_alert(alert)

            if triggered:
                # Create notification
                create_notification(alert, message, data)

                # Update alert metadata
                update_alert(alert.id, {
                    "triggered_at": datetime.now(timezone.utc).isoformat(),
                    "trigger_count": alert.trigger_count + 1,
                    "last_checked": datetime.now(timezone.utc).isoformat(),
                })

                logger.info(f"Alert triggered: {alert.ticker} - {message}")
            else:
                # Just update last_checked
                update_alert(alert.id, {
                    "last_checked": datetime.now(timezone.utc).isoformat()
                })

        except Exception as e:
            logger.error(f"Error evaluating alert {alert.id}: {e}", exc_info=True)


async def _evaluate_alert(alert: Alert) -> Tuple[bool, str, dict]:
    """
    Evaluate a single alert.

    Returns:
        (triggered: bool, message: str, data: dict)
    """
    if alert.alert_type == "price":
        return await _evaluate_price_alert(alert)
    elif alert.alert_type == "signal":
        return await _evaluate_signal_alert(alert)
    elif alert.alert_type == "earnings":
        return await _evaluate_earnings_alert(alert)

    return False, "", {}


async def _evaluate_price_alert(alert: Alert) -> Tuple[bool, str, dict]:
    """Evaluate price-based alert"""
    try:
        condition = PriceCondition(**alert.condition)
        ticker = alert.ticker

        # Get current price
        stock = yf.Ticker(ticker)
        info = stock.info or {}
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')

        if not current_price:
            # Fallback to history
            hist = stock.history(period="1d")
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])

        if not current_price:
            logger.warning(f"Could not get price for {ticker}")
            return False, "", {}

        # Check condition
        if condition.condition_type == "above":
            triggered = current_price > condition.threshold
            if triggered:
                message = f"{ticker} is now ${current_price:.2f} (above ${condition.threshold:.2f})"
            else:
                return False, "", {}

        elif condition.condition_type == "below":
            triggered = current_price < condition.threshold
            if triggered:
                message = f"{ticker} is now ${current_price:.2f} (below ${condition.threshold:.2f})"
            else:
                return False, "", {}

        elif condition.condition_type == "pct_change":
            # Get previous close
            hist = stock.history(period="2d")
            if len(hist) < 2:
                return False, "", {}
            prev_close = float(hist['Close'].iloc[-2])
            pct_change = ((current_price - prev_close) / prev_close) * 100
            triggered = abs(pct_change) >= condition.percentage
            if triggered:
                direction = "up" if pct_change > 0 else "down"
                message = f"{ticker} moved {abs(pct_change):.2f}% {direction} to ${current_price:.2f}"
            else:
                return False, "", {}

        else:
            return False, "", {}

        data = {"price": current_price, "ticker": ticker}
        return triggered, message, data

    except Exception as e:
        logger.error(f"Error evaluating price alert for {alert.ticker}: {e}")
        return False, "", {}


async def _evaluate_signal_alert(alert: Alert) -> Tuple[bool, str, dict]:
    """Evaluate technical signal alert"""
    try:
        condition = SignalCondition(**alert.condition)
        ticker = alert.ticker

        if condition.signal_type == "rsi":
            # Get ML signals which include RSI
            signals_data = await ml_signals.run_all(ticker)
            rsi = signals_data.get("rsi_current", 50)

            if condition.operator == "below":
                triggered = rsi < condition.threshold
                if triggered:
                    message = f"{ticker} RSI is {rsi:.1f} (oversold at <{condition.threshold})"
                else:
                    return False, "", {}
            elif condition.operator == "above":
                triggered = rsi > condition.threshold
                if triggered:
                    message = f"{ticker} RSI is {rsi:.1f} (overbought at >{condition.threshold})"
                else:
                    return False, "", {}
            else:
                return False, "", {}

            data = {"rsi": rsi, "ticker": ticker}
            return triggered, message, data

        elif condition.signal_type == "ml_signal":
            # Check if any ML signals fired with matching direction
            signals_data = await ml_signals.run_all(ticker)
            raw_signals = signals_data.get("signals", [])

            matching_signals = []
            if condition.direction:
                for sig in raw_signals:
                    if condition.direction.lower() in sig.lower():
                        matching_signals.append(sig)
            else:
                matching_signals = raw_signals

            triggered = len(matching_signals) > 0
            if triggered:
                message = f"{ticker} signals: {', '.join(matching_signals[:3])}"
            else:
                return False, "", {}

            data = {"signals": matching_signals, "ticker": ticker}
            return triggered, message, data

        return False, "", {}

    except Exception as e:
        logger.error(f"Error evaluating signal alert for {alert.ticker}: {e}")
        return False, "", {}


async def _evaluate_earnings_alert(alert: Alert) -> Tuple[bool, str, dict]:
    """Evaluate earnings-based alert"""
    try:
        condition = EarningsCondition(**alert.condition)
        ticker = alert.ticker

        # Get earnings calendar
        calendar = await earnings_calendar.get_earnings_calendar()

        # Find this ticker's earnings
        ticker_earnings = [e for e in calendar if e["ticker"] == ticker]
        if not ticker_earnings:
            return False, "", {}

        entry = ticker_earnings[0]
        days_until = entry["days_until"]

        # Check if we should trigger (trigger only once when reaching threshold)
        # Avoid re-triggering every 5 minutes
        triggered = days_until == condition.days_before
        if triggered:
            message = f"{ticker} earnings in {days_until} day{'s' if days_until != 1 else ''} ({entry['earnings_date']})"
            data = {"days_until": days_until, "earnings_date": entry["earnings_date"], "ticker": ticker}
            return triggered, message, data

        return False, "", {}

    except Exception as e:
        logger.error(f"Error evaluating earnings alert for {alert.ticker}: {e}")
        return False, "", {}
