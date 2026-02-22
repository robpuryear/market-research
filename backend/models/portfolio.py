"""
Portfolio Data Models

Models for positions, transactions, and portfolio metrics.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class Position(BaseModel):
    """A stock position in the portfolio"""
    id: str
    ticker: str
    quantity: float  # Number of shares
    avg_cost_basis: float  # Average price paid per share
    entry_date: str  # YYYY-MM-DD
    last_updated: datetime
    notes: Optional[str] = None
    status: str  # "open" | "closed"

    # Calculated fields (not stored, computed on-the-fly)
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    days_held: Optional[int] = None


class Transaction(BaseModel):
    """A buy/sell transaction"""
    id: str
    position_id: str
    ticker: str
    transaction_type: str  # "buy" | "sell" | "dividend"
    quantity: float
    price: float
    total_value: float  # quantity * price
    commission: float = 0.0
    date: str  # YYYY-MM-DD
    timestamp: datetime
    notes: Optional[str] = None


class PortfolioSnapshot(BaseModel):
    """Daily snapshot of portfolio value"""
    date: str  # YYYY-MM-DD
    total_value: float
    cash: float
    invested_value: float
    unrealized_pnl: float
    realized_pnl: float
    positions_count: int
    timestamp: datetime


class PortfolioMetrics(BaseModel):
    """Portfolio performance metrics"""
    total_value: float
    cash: float
    invested_value: float
    total_cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    realized_pnl: float
    total_pnl: float  # realized + unrealized
    total_return_pct: float

    # Daily performance
    day_change: float
    day_change_pct: float

    # Position stats
    positions_count: int
    open_positions_count: int
    winning_positions_count: int
    losing_positions_count: int
    win_rate: float

    # Risk metrics (optional for v1)
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None
    beta: Optional[float] = None

    # Allocation
    largest_position_pct: float
    top_3_concentration: float
    sectors: dict = {}  # {sector: allocation_pct}

    timestamp: datetime


class PerformanceHistory(BaseModel):
    """Historical performance data"""
    dates: List[str]
    portfolio_values: List[float]
    benchmark_values: List[float]  # SPY returns
    daily_returns: List[float]
    drawdown: List[float]
