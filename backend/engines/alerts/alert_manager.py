"""
Alert Manager - CRUD operations for alerts

Stores alerts in JSON file at data/alerts.json
"""

import json
import os
from typing import List, Optional
from models.alerts import Alert, AlertNotification
from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

ALERTS_FILE = "data/alerts.json"
NOTIFICATIONS_FILE = "data/notifications.json"


def create_alert(alert_data: dict) -> Alert:
    """Create a new alert"""
    alerts = _load_alerts()
    alert = Alert(
        id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        **alert_data
    )
    alerts.append(alert.model_dump())
    _save_alerts(alerts)
    logger.info(f"Created alert {alert.id} for {alert.ticker}")
    return alert


def get_all_alerts() -> List[Alert]:
    """Get all alerts"""
    return [Alert(**a) for a in _load_alerts()]


def get_alert(alert_id: str) -> Optional[Alert]:
    """Get alert by ID"""
    alerts = _load_alerts()
    for a in alerts:
        if a["id"] == alert_id:
            return Alert(**a)
    return None


def update_alert(alert_id: str, updates: dict) -> Optional[Alert]:
    """Update an alert"""
    alerts = _load_alerts()
    for i, a in enumerate(alerts):
        if a["id"] == alert_id:
            alerts[i].update(updates)
            _save_alerts(alerts)
            logger.info(f"Updated alert {alert_id}")
            return Alert(**alerts[i])
    return None


def delete_alert(alert_id: str) -> bool:
    """Delete an alert"""
    alerts = _load_alerts()
    filtered = [a for a in alerts if a["id"] != alert_id]
    if len(filtered) < len(alerts):
        _save_alerts(filtered)
        logger.info(f"Deleted alert {alert_id}")
        return True
    return False


def create_notification(alert: Alert, message: str, data: dict) -> AlertNotification:
    """Create a notification from a triggered alert"""
    notifs = _load_notifications()
    notif = AlertNotification(
        id=str(uuid.uuid4()),
        alert_id=alert.id,
        ticker=alert.ticker,
        message=message,
        alert_type=alert.alert_type,
        triggered_at=datetime.now(timezone.utc),
        data=data
    )
    notifs.append(notif.model_dump())
    _save_notifications(notifs)
    logger.info(f"Created notification for alert {alert.id}: {message}")
    return notif


def get_notifications(limit: int = 50, unread_only: bool = False) -> List[AlertNotification]:
    """Get recent notifications"""
    notifs = _load_notifications()
    if unread_only:
        notifs = [n for n in notifs if not n.get("read", False)]
    notifs.sort(key=lambda x: x["triggered_at"], reverse=True)
    return [AlertNotification(**n) for n in notifs[:limit]]


def mark_notification_read(notif_id: str) -> bool:
    """Mark notification as read"""
    notifs = _load_notifications()
    for i, n in enumerate(notifs):
        if n["id"] == notif_id:
            notifs[i]["read"] = True
            _save_notifications(notifs)
            logger.info(f"Marked notification {notif_id} as read")
            return True
    return False


def _load_alerts() -> list:
    """Load alerts from JSON file"""
    if not os.path.exists(ALERTS_FILE):
        return []
    try:
        with open(ALERTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading alerts: {e}")
        return []


def _save_alerts(alerts: list):
    """Save alerts to JSON file"""
    try:
        os.makedirs(os.path.dirname(ALERTS_FILE), exist_ok=True)
        with open(ALERTS_FILE, "w") as f:
            json.dump(alerts, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving alerts: {e}")


def _load_notifications() -> list:
    """Load notifications from JSON file"""
    if not os.path.exists(NOTIFICATIONS_FILE):
        return []
    try:
        with open(NOTIFICATIONS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading notifications: {e}")
        return []


def _save_notifications(notifs: list):
    """Save notifications to JSON file"""
    try:
        os.makedirs(os.path.dirname(NOTIFICATIONS_FILE), exist_ok=True)
        with open(NOTIFICATIONS_FILE, "w") as f:
            json.dump(notifs, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving notifications: {e}")
