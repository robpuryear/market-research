"""
Alerts API Routes

Endpoints for creating and managing alerts and notifications.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from models.alerts import Alert, AlertNotification
from engines.alerts import alert_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class CreateAlertRequest(BaseModel):
    """Request body for creating an alert"""
    ticker: str
    alert_type: str  # "price" | "signal" | "earnings"
    condition: dict  # Condition object
    notification_methods: List[str] = ["in_app"]
    message: Optional[str] = None


@router.get("/", response_model=List[Alert])
async def get_alerts():
    """
    Get all alerts.

    Returns list of all user alerts (enabled and disabled).
    """
    try:
        return alert_manager.get_all_alerts()
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Alert)
async def create_alert(req: CreateAlertRequest):
    """
    Create a new alert.

    Request body:
    - ticker: Stock ticker symbol
    - alert_type: "price", "signal", or "earnings"
    - condition: Alert condition object (varies by type)
    - notification_methods: ["in_app"] (future: email, webhook)
    - message: Optional custom message
    """
    try:
        return alert_manager.create_alert(req.model_dump())
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}", response_model=Alert)
async def get_alert(alert_id: str):
    """Get alert by ID"""
    alert = alert_manager.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}", response_model=Alert)
async def update_alert(alert_id: str, updates: dict):
    """
    Update an alert.

    Common updates:
    - {"enabled": false} - Disable alert
    - {"enabled": true} - Re-enable alert
    - {"condition": {...}} - Update condition
    """
    alert = alert_manager.update_alert(alert_id, updates)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert"""
    success = alert_manager.delete_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "deleted", "alert_id": alert_id}


@router.get("/notifications/", response_model=List[AlertNotification])
async def get_notifications(limit: int = 50, unread_only: bool = False):
    """
    Get recent notifications.

    Query params:
    - limit: Max number of notifications to return (default 50)
    - unread_only: If true, only return unread notifications
    """
    try:
        return alert_manager.get_notifications(limit, unread_only)
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str):
    """Mark notification as read"""
    success = alert_manager.mark_notification_read(notif_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "marked_read", "notification_id": notif_id}
