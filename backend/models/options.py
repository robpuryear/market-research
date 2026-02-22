"""
Options Data Models

Models for options chain, contracts, Greeks, and analytics.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime


class OptionContract(BaseModel):
    """Individual option contract with Greeks"""
    symbol: str  # e.g., "AAPL250321C00150000"
    strike: float
    expiration: str  # ISO date string
    contract_type: str  # "call" or "put"

    # Pricing
    bid: Optional[float] = None
    ask: Optional[float] = None
    last: Optional[float] = None
    mark: Optional[float] = None  # (bid + ask) / 2

    # Volume & Interest
    volume: Optional[int] = 0
    open_interest: Optional[int] = 0

    # Greeks
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None

    # Analysis
    in_the_money: bool = False
    intrinsic_value: float = 0.0
    extrinsic_value: float = 0.0
    moneyness: str = "OTM"  # "ITM", "ATM", "OTM"

    # Metadata
    days_to_expiration: Optional[int] = None
    percent_change: Optional[float] = None


class OptionsChain(BaseModel):
    """Complete options chain for a ticker and expiration"""
    ticker: str
    spot_price: float
    expiration: str

    calls: List[OptionContract]
    puts: List[OptionContract]

    # Summary stats
    total_call_volume: int = 0
    total_put_volume: int = 0
    total_call_oi: int = 0
    total_put_oi: int = 0
    put_call_volume_ratio: Optional[float] = None
    put_call_oi_ratio: Optional[float] = None

    timestamp: datetime


class OptionsAnalytics(BaseModel):
    """Advanced options analytics for a ticker"""
    ticker: str
    spot_price: float

    # IV Metrics
    iv_rank: Optional[float] = None  # 0-100
    iv_percentile: Optional[float] = None  # 0-100
    current_iv: Optional[float] = None  # 30-day ATM IV
    hv_30day: Optional[float] = None  # 30-day historical volatility

    # Market Metrics
    put_call_ratio: Optional[float] = None
    max_pain: Optional[float] = None
    gamma_exposure: Optional[float] = None

    # Nearest expiration data
    nearest_expiration: Optional[str] = None
    days_to_expiration: Optional[int] = None

    timestamp: datetime


class SpreadLeg(BaseModel):
    """Single leg of an options spread"""
    strike: float
    contract_type: str  # "call" or "put"
    action: str  # "buy" or "sell"
    quantity: int
    price: float  # premium paid/received

    # Contract details
    expiration: str
    delta: Optional[float] = None


class SpreadAnalysis(BaseModel):
    """Analysis of an options spread strategy"""
    spread_type: str  # "bull_call", "bear_put", "iron_condor", etc.
    ticker: str
    spot_price: float

    legs: List[SpreadLeg]

    # P&L Analysis
    max_profit: float
    max_loss: float
    breakeven_points: List[float]
    net_debit_credit: float  # negative = debit, positive = credit

    # Greeks for entire spread
    net_delta: Optional[float] = None
    net_gamma: Optional[float] = None
    net_theta: Optional[float] = None
    net_vega: Optional[float] = None

    # Risk metrics
    risk_reward_ratio: Optional[float] = None
    probability_of_profit: Optional[float] = None

    # P&L diagram data (for frontend charting)
    price_points: List[float] = []  # Stock prices
    pnl_at_expiration: List[float] = []  # P&L at each price

    timestamp: datetime


class ExpirationDate(BaseModel):
    """Available expiration date with metadata"""
    date: str  # ISO date string
    days_until: int
    is_weekly: bool
    is_monthly: bool
    is_quarterly: bool


class UnusualOptionsActivity(BaseModel):
    """Unusual options activity detection"""
    ticker: str
    contract_symbol: str
    strike: float
    expiration: str
    contract_type: str

    # Activity metrics
    volume: int
    open_interest: int
    volume_oi_ratio: float  # Red flag if > 2

    # Pricing
    premium: float
    total_premium: float  # volume * premium * 100

    # Classification
    activity_type: str  # "sweep", "block", "unusual_volume", "iv_spike"
    sentiment: str  # "bullish", "bearish", "neutral"

    # Context
    spot_price: float
    iv_rank: Optional[float] = None

    timestamp: datetime
