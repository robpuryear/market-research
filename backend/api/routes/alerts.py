"""
Alerts API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from models.alerts import Alert, AlertNotification
from engines.alerts import alert_manager
from db.session import get_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


class CreateAlertRequest(BaseModel):
    ticker: str
    alert_type: str
    condition: dict
    notification_methods: List[str] = ["in_app"]
    message: Optional[str] = None


@router.get("/", response_model=List[Alert])
async def get_alerts(session: AsyncSession = Depends(get_session)):
    try:
        return await alert_manager.get_all_alerts(session)
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Alert)
async def create_alert(
    req: CreateAlertRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await alert_manager.create_alert(session, req.model_dump())
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}", response_model=Alert)
async def get_alert(alert_id: str, session: AsyncSession = Depends(get_session)):
    alert = await alert_manager.get_alert(session, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}", response_model=Alert)
async def update_alert(
    alert_id: str,
    updates: dict,
    session: AsyncSession = Depends(get_session),
):
    alert = await alert_manager.update_alert(session, alert_id, updates)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, session: AsyncSession = Depends(get_session)):
    success = await alert_manager.delete_alert(session, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "deleted", "alert_id": alert_id}


@router.get("/notifications/", response_model=List[AlertNotification])
async def get_notifications(
    limit: int = 50,
    unread_only: bool = False,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await alert_manager.get_notifications(session, limit, unread_only)
    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/notifications/{notif_id}/read")
async def mark_notification_read(
    notif_id: str,
    session: AsyncSession = Depends(get_session),
):
    success = await alert_manager.mark_notification_read(session, notif_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "marked_read", "notification_id": notif_id}
