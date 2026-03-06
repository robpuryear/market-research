"""
Alert Manager - PostgreSQL-backed CRUD for alerts and notifications.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import AlertRow, NotificationRow
from models.alerts import Alert, AlertNotification

logger = logging.getLogger(__name__)


def _alert_row_to_model(row: AlertRow) -> Alert:
    return Alert(
        id=row.id,
        ticker=row.ticker,
        alert_type=row.alert_type,
        condition=row.condition,
        enabled=row.enabled,
        notification_methods=row.notification_methods,
        created_at=row.created_at,
        last_checked=row.last_checked,
        triggered_at=row.triggered_at,
        trigger_count=row.trigger_count,
        message=row.message,
        metadata=row.metadata_ or {},
    )


def _notif_row_to_model(row: NotificationRow) -> AlertNotification:
    return AlertNotification(
        id=row.id,
        alert_id=row.alert_id,
        ticker=row.ticker,
        message=row.message,
        alert_type=row.alert_type,
        triggered_at=row.triggered_at,
        read=row.read,
        data=row.data or {},
    )


async def create_alert(session: AsyncSession, alert_data: dict) -> Alert:
    alert_data.pop("id", None)
    alert_data.pop("created_at", None)
    row = AlertRow(
        id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        ticker=alert_data["ticker"],
        alert_type=alert_data["alert_type"],
        condition=alert_data["condition"],
        enabled=alert_data.get("enabled", True),
        notification_methods=alert_data.get("notification_methods", ["in_app"]),
        message=alert_data.get("message"),
        metadata_=alert_data.get("metadata", {}),
    )
    session.add(row)
    await session.commit()
    logger.info(f"Created alert {row.id} for {row.ticker}")
    return _alert_row_to_model(row)


async def get_all_alerts(session: AsyncSession) -> List[Alert]:
    result = await session.execute(select(AlertRow))
    return [_alert_row_to_model(r) for r in result.scalars().all()]


async def get_alert(session: AsyncSession, alert_id: str) -> Optional[Alert]:
    row = await session.get(AlertRow, alert_id)
    return _alert_row_to_model(row) if row else None


async def update_alert(session: AsyncSession, alert_id: str, updates: dict) -> Optional[Alert]:
    row = await session.get(AlertRow, alert_id)
    if not row:
        return None
    if "enabled" in updates:
        row.enabled = updates["enabled"]
    if "condition" in updates:
        row.condition = updates["condition"]
    if "last_checked" in updates:
        val = updates["last_checked"]
        row.last_checked = datetime.fromisoformat(val.replace("Z", "+00:00")) if isinstance(val, str) else val
    if "triggered_at" in updates:
        val = updates["triggered_at"]
        row.triggered_at = datetime.fromisoformat(val.replace("Z", "+00:00")) if isinstance(val, str) else val
    if "trigger_count" in updates:
        row.trigger_count = updates["trigger_count"]
    if "message" in updates:
        row.message = updates["message"]
    await session.commit()
    logger.info(f"Updated alert {alert_id}")
    return _alert_row_to_model(row)


async def delete_alert(session: AsyncSession, alert_id: str) -> bool:
    row = await session.get(AlertRow, alert_id)
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    logger.info(f"Deleted alert {alert_id}")
    return True


async def create_notification(
    session: AsyncSession,
    alert: Alert,
    message: str,
    data: dict,
) -> AlertNotification:
    row = NotificationRow(
        id=str(uuid.uuid4()),
        alert_id=alert.id,
        ticker=alert.ticker,
        message=message,
        alert_type=alert.alert_type,
        triggered_at=datetime.now(timezone.utc),
        read=False,
        data=data,
    )
    session.add(row)
    await session.commit()
    logger.info(f"Created notification for alert {alert.id}: {message}")
    return _notif_row_to_model(row)


async def get_notifications(
    session: AsyncSession,
    limit: int = 50,
    unread_only: bool = False,
) -> List[AlertNotification]:
    q = select(NotificationRow).order_by(desc(NotificationRow.triggered_at)).limit(limit)
    if unread_only:
        q = q.where(NotificationRow.read == False)  # noqa: E712
    result = await session.execute(q)
    return [_notif_row_to_model(r) for r in result.scalars().all()]


async def mark_notification_read(session: AsyncSession, notif_id: str) -> bool:
    row = await session.get(NotificationRow, notif_id)
    if not row:
        return False
    row.read = True
    await session.commit()
    logger.info(f"Marked notification {notif_id} as read")
    return True
