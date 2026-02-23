"""
Strategy Data Models

Models for custom trading strategies with technical indicator conditions.
"""

from pydantic import BaseModel
from typing import Optional, List, Union
from datetime import datetime


class IndicatorCondition(BaseModel):
    """Technical indicator condition"""
    indicator: str  # "rsi" | "macd" | "ma" | "bb" | "volume" | "price"
    operator: str   # "above" | "below" | "crosses_above" | "crosses_below" | "between"
    value: Optional[float] = None
    value_high: Optional[float] = None  # For "between" operator
    period: Optional[int] = None  # For MA, RSI periods


class PricePatternCondition(BaseModel):
    """Price pattern condition"""
    pattern: str  # "golden_cross" | "death_cross" | "macd_cross" | "bb_squeeze"
    direction: Optional[str] = None  # "bullish" | "bearish"


class ConditionGroup(BaseModel):
    """Group of conditions with logic operator"""
    logic: str  # "AND" | "OR"
    conditions: List[Union[IndicatorCondition, PricePatternCondition]]


class Strategy(BaseModel):
    """Trading strategy definition"""
    id: str
    name: str
    description: Optional[str] = None
    entry_conditions: ConditionGroup
    exit_conditions: Optional[ConditionGroup] = None
    enabled: bool = True
    scope: str = "watchlist"  # "watchlist" | "market"
    generate_alerts: bool = False
    created_at: datetime
    last_run: Optional[datetime] = None
    hits_today: int = 0
    total_hits: int = 0


class StrategyResult(BaseModel):
    """Strategy execution result"""
    id: str
    strategy_id: str
    ticker: str
    matched_at: datetime
    entry_conditions_met: bool
    exit_conditions_met: bool
    current_price: float
    indicator_values: dict  # Stores computed indicator values
    signal_strength: float  # 0-100 confidence score
