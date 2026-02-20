from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class IVAnalytics(BaseModel):
    ticker: str
    atm_iv: float
    iv_rank: float               # 0–100 where current IV sits vs realized vol proxy
    expected_move_1w: float      # price * atm_iv * sqrt(7/365)
    expected_move_1m: float      # price * atm_iv * sqrt(30/365)
    put_call_skew: float         # OTM put IV - OTM call IV
    term_structure: List[float]  # ATM IV per nearest 4 expiries
    timestamp: datetime


class IndexData(BaseModel):
    ticker: str
    price: float
    change_pct: float
    ma_20: Optional[float] = None
    ma_50: Optional[float] = None
    ma_200: Optional[float] = None
    above_200ma: Optional[bool] = None
    support: List[float] = []
    resistance: List[float] = []
    rsi: Optional[float] = None
    volume: Optional[float] = None
    volume_ratio: Optional[float] = None


class MarketSnapshot(BaseModel):
    vix: float
    vix_regime: str  # "Low" | "Elevated" | "High" | "Extreme"
    fear_greed_approx: float  # 0-100
    yield_10y: Optional[float] = None
    yield_2y: Optional[float] = None
    yield_spread: Optional[float] = None  # 10Y - 2Y
    market_regime: str  # "Bull" | "Bear" | "Neutral" | "Volatile"
    spy: IndexData
    qqq: IndexData
    iwm: IndexData
    timestamp: datetime


class TechnicalData(BaseModel):
    ticker: str
    dates: List[str]
    opens: List[float]
    highs: List[float]
    lows: List[float]
    closes: List[float]
    volumes: List[float]
    ma_20: List[Optional[float]]
    ma_50: List[Optional[float]]
    ma_200: List[Optional[float]]
    rsi: List[Optional[float]]
    macd_line: List[Optional[float]]
    macd_signal: List[Optional[float]]
    macd_histogram: List[Optional[float]]
    bb_upper: List[Optional[float]]
    bb_middle: List[Optional[float]]
    bb_lower: List[Optional[float]]
    support_levels: List[float]
    resistance_levels: List[float]
    current_signal: str  # "bullish" | "bearish" | "neutral"


class OptionsGreeks(BaseModel):
    ticker: str
    expiry: str
    max_pain: Optional[float] = None
    gamma_exposure: Optional[float] = None
    put_call_ratio: Optional[float] = None
    total_call_oi: Optional[int] = None
    total_put_oi: Optional[int] = None


class SectorData(BaseModel):
    ticker: str
    name: str
    price: float
    change_1d: float
    change_5d: float
    change_1m: float
    vs_spy_1d: float  # relative to SPY
    vs_spy_5d: float
    vs_spy_1m: float


class MarketBreadth(BaseModel):
    advancers: int
    decliners: int
    unchanged: int
    advance_decline_ratio: float
    pct_above_20ma: float
    pct_above_50ma: float
    pct_above_200ma: float
    new_highs_52w: int
    new_lows_52w: int
    avg_rsi: float
    breadth_score: float   # 0–100 composite
    timestamp: datetime
