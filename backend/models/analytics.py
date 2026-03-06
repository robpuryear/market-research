from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class MLSignal(BaseModel):
    signal_type: str    # "RSI Divergence", "MACD Cross", "BB Squeeze", "Golden Cross", "Death Cross"
    direction: str      # "bullish" | "bearish"
    description: str


class MLSignalsData(BaseModel):
    ticker: str
    signals: List[MLSignal]
    rsi: float
    signal_count: int
    timestamp: datetime


class SqueezeScore(BaseModel):
    ticker: str
    squeeze_score: float
    short_interest_pct: Optional[float] = None
    short_ratio: Optional[float] = None
    volume_ratio: float
    options_unusual: bool = False


class CorrelationMatrix(BaseModel):
    tickers: List[str]
    matrix: List[List[float]]
    timestamp: datetime


class EarningsCalendarEntry(BaseModel):
    ticker: str
    earnings_date: str
    days_until: int


class ScanCandidate(BaseModel):
    """A stock candidate from market scanning with opportunity scores."""
    ticker: str
    company_name: str
    price: float
    volume_ratio: float
    squeeze_score: float
    ml_signals: List[MLSignal]
    bullish_signal_count: int
    bearish_signal_count: int
    unusual_options_count: int
    iv_rank: float
    composite_score: float
    short_interest_pct: Optional[float] = None
    market_cap: Optional[float] = None
    sector: Optional[str] = None
    timestamp: datetime


class TrendingStock(BaseModel):
    """A stock gaining social + technical momentum."""
    ticker: str
    company_name: str
    price: float
    change_pct: float
    volume_ratio: float
    # Per-source signals
    reddit_mentions: int
    reddit_sentiment: float   # -1.0 to +1.0
    news_mentions: int        # Alpha Vantage financial news article count
    finviz_mentions: int      # Finviz news headline mention count
    yahoo_trending: bool      # in Yahoo Finance trending list
    buzz_sources: List[str]   # which sources picked this up, e.g. ["Reddit","Finviz","Yahoo"]
    momentum_score: float     # 0–100
    on_watchlist: bool
    timestamp: datetime


class SentimentComponent(BaseModel):
    """Individual component of composite sentiment"""
    name: str
    score: float  # -1.0 to +1.0
    weight: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    description: str


class CompositeSentiment(BaseModel):
    """Composite sentiment score combining multiple factors"""
    ticker: str
    composite_score: float  # -100 to +100
    composite_label: str  # "Very Bearish" | "Bearish" | "Neutral" | "Bullish" | "Very Bullish"
    confidence: float  # 0.0 to 1.0
    components: List[SentimentComponent]
    timestamp: datetime
