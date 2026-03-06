"""
Alert Evaluator - Check if alert conditions are met.

Runs periodically via scheduler; evaluates all enabled alerts.
"""

import logging
from typing import Tuple
from datetime import datetime, timezone

import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession

from models.alerts import Alert, PriceCondition, SignalCondition, EarningsCondition
from engines.alerts.alert_manager import (
    get_all_alerts, update_alert, create_notification,
)
from engines.analytics import ml_signals
from engines.watchlist import earnings_calendar

logger = logging.getLogger(__name__)


async def evaluate_all_alerts(session: AsyncSession) -> None:
    """Evaluate all enabled alerts and trigger notifications."""
    alerts = await get_all_alerts(session)
    enabled = [a for a in alerts if a.enabled]
    logger.info(f"Evaluating {len(enabled)} enabled alerts")

    for alert in enabled:
        try:
            triggered, message, data = await _evaluate_alert(alert)
            if triggered:
                await create_notification(session, alert, message, data)
                await update_alert(session, alert.id, {
                    "triggered_at": datetime.now(timezone.utc),
                    "trigger_count": alert.trigger_count + 1,
                    "last_checked": datetime.now(timezone.utc),
                })
                logger.info(f"Alert triggered: {alert.ticker} - {message}")
            else:
                await update_alert(session, alert.id, {
                    "last_checked": datetime.now(timezone.utc),
                })
        except Exception as e:
            logger.error(f"Error evaluating alert {alert.id}: {e}", exc_info=True)


async def _evaluate_alert(alert: Alert) -> Tuple[bool, str, dict]:
    if alert.alert_type == "price":
        return await _evaluate_price_alert(alert)
    elif alert.alert_type == "signal":
        return await _evaluate_signal_alert(alert)
    elif alert.alert_type == "earnings":
        return await _evaluate_earnings_alert(alert)
    return False, "", {}


async def _evaluate_price_alert(alert: Alert) -> Tuple[bool, str, dict]:
    try:
        condition = PriceCondition(**alert.condition)
        ticker = alert.ticker
        stock = yf.Ticker(ticker)
        info = stock.info or {}
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not current_price:
            hist = stock.history(period="1d")
            if not hist.empty:
                current_price = float(hist["Close"].iloc[-1])
        if not current_price:
            return False, "", {}

        if condition.condition_type == "above":
            if current_price > condition.threshold:
                return True, f"{ticker} is now ${current_price:.2f} (above ${condition.threshold:.2f})", {"price": current_price, "ticker": ticker}
        elif condition.condition_type == "below":
            if current_price < condition.threshold:
                return True, f"{ticker} is now ${current_price:.2f} (below ${condition.threshold:.2f})", {"price": current_price, "ticker": ticker}
        elif condition.condition_type == "pct_change":
            hist = stock.history(period="2d")
            if len(hist) < 2:
                return False, "", {}
            prev_close = float(hist["Close"].iloc[-2])
            pct_change = ((current_price - prev_close) / prev_close) * 100
            if abs(pct_change) >= condition.percentage:
                direction = "up" if pct_change > 0 else "down"
                return True, f"{ticker} moved {abs(pct_change):.2f}% {direction} to ${current_price:.2f}", {"price": current_price, "ticker": ticker}

        return False, "", {}
    except Exception as e:
        logger.error(f"Error evaluating price alert for {alert.ticker}: {e}")
        return False, "", {}


async def _evaluate_signal_alert(alert: Alert) -> Tuple[bool, str, dict]:
    try:
        condition = SignalCondition(**alert.condition)
        ticker = alert.ticker

        if condition.signal_type == "rsi":
            signals_data = await ml_signals.run_all(ticker)
            rsi = signals_data.get("rsi_current", 50)
            if condition.operator == "below" and rsi < condition.threshold:
                return True, f"{ticker} RSI is {rsi:.1f} (oversold at <{condition.threshold})", {"rsi": rsi, "ticker": ticker}
            elif condition.operator == "above" and rsi > condition.threshold:
                return True, f"{ticker} RSI is {rsi:.1f} (overbought at >{condition.threshold})", {"rsi": rsi, "ticker": ticker}

        elif condition.signal_type == "ml_signal":
            signals_data = await ml_signals.run_all(ticker)
            raw_signals = signals_data.get("signals", [])
            matching = [s for s in raw_signals if not condition.direction or condition.direction.lower() in s.lower()]
            if matching:
                return True, f"{ticker} signals: {', '.join(matching[:3])}", {"signals": matching, "ticker": ticker}

        return False, "", {}
    except Exception as e:
        logger.error(f"Error evaluating signal alert for {alert.ticker}: {e}")
        return False, "", {}


async def _evaluate_earnings_alert(alert: Alert) -> Tuple[bool, str, dict]:
    try:
        condition = EarningsCondition(**alert.condition)
        calendar = await earnings_calendar.get_earnings_calendar()
        ticker_entries = [e for e in calendar if e["ticker"] == alert.ticker]
        if not ticker_entries:
            return False, "", {}
        entry = ticker_entries[0]
        days_until = entry["days_until"]
        if days_until == condition.days_before:
            return True, f"{alert.ticker} earnings in {days_until} day{'s' if days_until != 1 else ''} ({entry['earnings_date']})", {"days_until": days_until, "earnings_date": entry["earnings_date"], "ticker": alert.ticker}
        return False, "", {}
    except Exception as e:
        logger.error(f"Error evaluating earnings alert for {alert.ticker}: {e}")
        return False, "", {}
