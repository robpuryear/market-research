"""
Finnhub News Sentiment Engine

Uses Finnhub's free tier API for news and sentiment analysis.
Free tier: 60 requests/minute (much better than Alpha Vantage's 25/day)
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import httpx

from models.sentiment import NewsSentimentData, NewsArticle
from core import cache, rate_limiter

logger = logging.getLogger(__name__)

FINNHUB_BASE = "https://finnhub.io/api/v1"


async def fetch_news_sentiment(ticker: str) -> Optional[NewsSentimentData]:
    """
    Fetch news sentiment from Finnhub.
    Returns news with basic sentiment analysis based on article content.
    """
    from config import settings

    api_key = getattr(settings, 'finnhub_api_key', None)
    if not api_key:
        logger.warning(f"Finnhub API key not configured, skipping news sentiment for {ticker}")
        return None

    cache_key = f"finnhub_news_{ticker}"
    cached = cache.get(cache_key, "sentiment")
    if cached:
        return NewsSentimentData(**cached)

    rate_limiter.acquire("finnhub")

    try:
        # Get company news from last 7 days
        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=7)

        params = {
            "symbol": ticker,
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
        }

        headers = {
            "X-Finnhub-Token": api_key,
            "Accept": "application/json",
        }

        logger.info(f"Fetching Finnhub news for {ticker}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{FINNHUB_BASE}/company-news", params=params, headers=headers)
            logger.info(f"Finnhub response status: {resp.status_code}")
            resp.raise_for_status()
            data = resp.json()

            # Check for API errors
            if isinstance(data, dict) and "error" in data:
                logger.error(f"Finnhub API error for {ticker}: {data}")
                return None

        if not data or not isinstance(data, list):
            logger.warning(f"No news articles found for {ticker}")
            return None

        # Process articles and calculate sentiment
        articles: List[NewsArticle] = []
        sentiment_sum = 0.0

        for item in data[:20]:  # Limit to 20 most recent articles
            headline = item.get("headline", "")
            summary = item.get("summary", "")

            # Simple sentiment analysis based on keywords
            text = (headline + " " + summary).lower()
            sentiment_score = _calculate_sentiment_score(text)
            sentiment_sum += sentiment_score

            # Map score to label
            if sentiment_score >= 0.3:
                sentiment_label = "Bullish"
            elif sentiment_score >= 0.1:
                sentiment_label = "Somewhat-Bullish"
            elif sentiment_score <= -0.3:
                sentiment_label = "Bearish"
            elif sentiment_score <= -0.1:
                sentiment_label = "Somewhat-Bearish"
            else:
                sentiment_label = "Neutral"

            articles.append(NewsArticle(
                title=headline[:160],
                url=item.get("url", ""),
                source=item.get("source", "Unknown"),
                sentiment_score=round(sentiment_score, 4),
                sentiment_label=sentiment_label,
                relevance_score=1.0,  # Finnhub doesn't provide relevance scores
                published_at=datetime.fromtimestamp(item.get("datetime", 0)).strftime("%Y%m%dT%H%M%S"),
            ))

        if not articles:
            return None

        avg_score = round(sentiment_sum / len(articles), 4)

        # Map avg score to label
        if avg_score >= 0.3:
            avg_label = "Bullish"
        elif avg_score >= 0.1:
            avg_label = "Somewhat-Bullish"
        elif avg_score <= -0.3:
            avg_label = "Bearish"
        elif avg_score <= -0.1:
            avg_label = "Somewhat-Bearish"
        else:
            avg_label = "Neutral"

        result = NewsSentimentData(
            ticker=ticker,
            avg_sentiment_score=avg_score,
            sentiment_label=avg_label,
            article_count=len(articles),
            articles=articles,
            timestamp=datetime.now(timezone.utc),
        )

        cache.set(cache_key, result.model_dump())
        return result

    except httpx.TimeoutException:
        logger.error(f"Finnhub news timeout for {ticker}")
        stale = cache.get_stale(cache_key)
        if stale:
            return NewsSentimentData(**stale)
        return None
    except Exception as e:
        logger.error(f"Finnhub news sentiment failed for {ticker}: {type(e).__name__}: {e}", exc_info=True)
        stale = cache.get_stale(cache_key)
        if stale:
            return NewsSentimentData(**stale)
        return None


def _calculate_sentiment_score(text: str) -> float:
    """
    Simple keyword-based sentiment scoring.
    Returns score from -1.0 (very bearish) to +1.0 (very bullish)
    """
    # Bullish keywords
    bullish_words = [
        "surge", "soar", "rally", "gain", "jump", "climb", "rise", "boost", "upgrade",
        "beat", "exceed", "growth", "profit", "strong", "positive", "success", "win",
        "breakthrough", "record", "high", "bullish", "buy", "outperform"
    ]

    # Bearish keywords
    bearish_words = [
        "plunge", "crash", "fall", "drop", "decline", "lose", "loss", "weak", "miss",
        "downgrade", "cut", "slash", "negative", "concern", "worry", "risk", "threat",
        "low", "bearish", "sell", "underperform", "disappoint", "fail"
    ]

    bullish_count = sum(1 for word in bullish_words if word in text)
    bearish_count = sum(1 for word in bearish_words if word in text)

    total = bullish_count + bearish_count
    if total == 0:
        return 0.0

    # Calculate score with diminishing returns for multiple keywords
    net_sentiment = bullish_count - bearish_count
    score = net_sentiment / (total + 2)  # Normalize with dampening

    # Clamp to -1.0 to +1.0
    return max(-1.0, min(1.0, score))
