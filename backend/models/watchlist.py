from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class EarningsEntry(BaseModel):
    date: str
    eps_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    surprise_pct: Optional[float] = None


class OptionsFlowData(BaseModel):
    ticker: str
    expiry: str
    strike: float
    option_type: str  # "call" | "put"
    volume: int
    open_interest: int
    volume_oi_ratio: float
    premium_total: float
    is_unusual: bool
    timestamp: datetime


class StockData(BaseModel):
    ticker: str
    price: float
    change_pct: float
    volume: float
    avg_volume: float
    volume_ratio: float
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    short_interest_pct: Optional[float] = None
    analyst_rating: Optional[str] = None  # "Strong Buy" | "Buy" | "Hold" | "Sell"
    price_target: Optional[float] = None
    earnings_date: Optional[str] = None
    options_unusual: bool = False
    insider_activity: Optional[str] = None  # "buying" | "selling" | "neutral"
    squeeze_score: Optional[float] = None  # 0-100
    timestamp: datetime


class StockDetailData(BaseModel):
    ticker: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    price: float
    change_pct: float
    volume: float
    avg_volume: float
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    pb_ratio: Optional[float] = None
    debt_to_equity: Optional[float] = None
    revenue_growth: Optional[float] = None
    short_interest_pct: Optional[float] = None
    short_ratio: Optional[float] = None
    analyst_rating: Optional[str] = None
    price_target: Optional[float] = None
    price_target_low: Optional[float] = None
    price_target_high: Optional[float] = None
    earnings_date: Optional[str] = None
    earnings_surprise_pct: Optional[float] = None
    profit_margin: Optional[float] = None
    return_on_equity: Optional[float] = None
    return_on_assets: Optional[float] = None
    dividend_yield: Optional[float] = None
    free_cash_flow: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    earnings_history: List[EarningsEntry] = []
    insider_transactions: List[dict] = []
    institutional_ownership_pct: Optional[float] = None
    unusual_options: List[OptionsFlowData] = []
    timestamp: datetime
