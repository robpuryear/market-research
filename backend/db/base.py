"""
SQLAlchemy ORM table definitions.

Pydantic models (in models/) are for API I/O.
These ORM classes are for DB I/O only.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Boolean, Column, DateTime, Double, Integer,
    String, Text, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class WatchlistRow(Base):
    __tablename__ = "watchlist"

    ticker = Column(String(10), primary_key=True)
    added_at = Column(DateTime(timezone=True), nullable=False,
                      default=lambda: datetime.now(timezone.utc))


class PositionRow(Base):
    __tablename__ = "positions"

    id = Column(String(36), primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    quantity = Column(Double, nullable=False)
    avg_cost_basis = Column(Double, nullable=False)
    entry_date = Column(String(10), nullable=False)
    last_updated = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(10), nullable=False)  # "open" | "closed"


class TransactionRow(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True)
    position_id = Column(String(36), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False)
    quantity = Column(Double, nullable=False)
    price = Column(Double, nullable=False)
    total_value = Column(Double, nullable=False)
    commission = Column(Double, nullable=False, default=0.0)
    date = Column(String(10), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text, nullable=True)


class StrategyRow(Base):
    __tablename__ = "strategies"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    entry_conditions = Column(JSONB, nullable=False)
    exit_conditions = Column(JSONB, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    scope = Column(String(20), nullable=False, default="watchlist")
    generate_alerts = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    last_run = Column(DateTime(timezone=True), nullable=True)
    hits_today = Column(Integer, nullable=False, default=0)
    total_hits = Column(Integer, nullable=False, default=0)


class StrategyResultRow(Base):
    __tablename__ = "strategy_results"

    id = Column(String(36), primary_key=True)
    strategy_id = Column(String(36), ForeignKey("strategies.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    ticker = Column(String(10), nullable=False)
    matched_at = Column(DateTime(timezone=True), nullable=False, index=True)
    entry_conditions_met = Column(Boolean, nullable=False)
    exit_conditions_met = Column(Boolean, nullable=False)
    current_price = Column(Double, nullable=False)
    indicator_values = Column(JSONB, nullable=False)
    signal_strength = Column(Double, nullable=False)


class AlertRow(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True)
    ticker = Column(String(10), nullable=False, index=True)
    alert_type = Column(String(20), nullable=False)
    condition = Column(JSONB, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    notification_methods = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    last_checked = Column(DateTime(timezone=True), nullable=True)
    triggered_at = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, nullable=False, default=0)
    message = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)


class NotificationRow(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True)
    alert_id = Column(String(36), ForeignKey("alerts.id", ondelete="CASCADE"),
                      nullable=False, index=True)
    ticker = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(String(20), nullable=False)
    triggered_at = Column(DateTime(timezone=True), nullable=False, index=True)
    read = Column(Boolean, nullable=False, default=False)
    data = Column(JSONB, nullable=False, default=dict)


class BacktestResultRow(Base):
    __tablename__ = "backtest_results"

    id = Column(String(36), primary_key=True)
    strategy_type = Column(String(50), nullable=False)
    ticker = Column(String(10), nullable=False, index=True)
    start_date = Column(String(10), nullable=False)
    end_date = Column(String(10), nullable=False)
    total_return = Column(Double, nullable=False)
    sharpe_ratio = Column(Double, nullable=False)
    max_drawdown = Column(Double, nullable=False)
    total_trades = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    result_json = Column(JSONB, nullable=False)


class ReportRow(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True)
    type = Column(String(20), nullable=False, index=True)
    ticker = Column(String(10), nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=False, index=True)
    path = Column(Text, nullable=False)
    file_size_kb = Column(Double, nullable=True)
    title = Column(Text, nullable=False)
