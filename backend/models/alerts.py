"""
Alert Data Models

Models for alerts, conditions, and notifications.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PriceCondition(BaseModel):
    """Price alert condition"""
    condition_type: str  # "above" | "below" | "pct_change" | "ma_cross"
    threshold: Optional[float] = None
    percentage: Optional[float] = None
    ma_period: Optional[int] = None


class SignalCondition(BaseModel):
    """Technical signal alert condition"""
    signal_type: str  # "rsi" | "macd" | "ml_signal" | "unusual_options"
    operator: str     # "above" | "below" | "equals" | "fired"
    threshold: Optional[float] = None
    direction: Optional[str] = None  # "bullish" | "bearish"


class EarningsCondition(BaseModel):
    """Earnings alert condition"""
    days_before: int  # Trigger X days before earnings
    notify_on_surprise: bool = False
    surprise_threshold: float = 10.0  # %


class Alert(BaseModel):
    """User alert"""
    id: str
    ticker: str
    alert_type: str  # "price" | "signal" | "earnings"
    condition: dict  # Serialized condition (PriceCondition, SignalCondition, or EarningsCondition)
    enabled: bool = True
    notification_methods: List[str] = ["in_app"]
    created_at: datetime
    last_checked: Optional[datetime] = None
    triggered_at: Optional[datetime] = None
    trigger_count: int = 0
    message: Optional[str] = None  # Custom message
    metadata: dict = {}


class AlertNotification(BaseModel):
    """Triggered alert notification"""
    id: str
    alert_id: str
    ticker: str
    message: str
    alert_type: str
    triggered_at: datetime
    read: bool = False
    data: dict = {}  # Context data (price, signal details, etc.)
