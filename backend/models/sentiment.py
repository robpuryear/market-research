from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class RedditPost(BaseModel):
    title: str
    subreddit: str
    score: int
    url: str
    tickers_mentioned: List[str]
    sentiment: str  # "positive" | "negative" | "neutral"
    created_utc: float


class TickerMention(BaseModel):
    ticker: str
    mention_count: int
    sentiment_score: float  # -1.0 to 1.0
    positive_count: int
    negative_count: int
    neutral_count: int


class RedditSentimentData(BaseModel):
    top_posts: List[RedditPost]
    ticker_mentions: List[TickerMention]
    trending_tickers: List[str]
    total_posts_analyzed: int
    subreddits: List[str]
    timestamp: datetime


class FlowToxicityData(BaseModel):
    ticker: str
    pin_score: float  # 0.0 to 1.0 (Probability of Informed Trading)
    buy_volume: float
    sell_volume: float
    total_volume: float
    toxicity_regime: str  # "Low" | "Moderate" | "High" | "Extreme"
    interpretation: str
    timestamp: datetime


class DarkPoolData(BaseModel):
    ticker: str
    dark_pool_volume: Optional[float] = None
    dark_pool_pct: Optional[float] = None
    block_trades: List[dict] = []
    sentiment: Optional[str] = None  # "bullish" | "bearish" | "neutral"
    is_placeholder: bool = True
    timestamp: datetime


class StockTwitsSentiment(BaseModel):
    ticker: str
    bullish_count: int
    bearish_count: int
    total_messages: int
    sentiment_ratio: float   # bullish / (bullish + bearish), 0.0-1.0
    sentiment_label: str     # "Bullish" | "Bearish" | "Neutral"
    recent_messages: List[str]
    timestamp: datetime


class NewsArticle(BaseModel):
    title: str
    url: str
    source: str
    sentiment_score: float
    sentiment_label: str
    relevance_score: float
    published_at: str


class NewsSentimentData(BaseModel):
    ticker: str
    avg_sentiment_score: float
    sentiment_label: str
    article_count: int
    articles: List[NewsArticle]
    timestamp: datetime
