import logging
from datetime import datetime, timezone
from typing import List, Optional

import httpx

from models.sentiment import NewsSentimentData, NewsArticle
from core import cache, rate_limiter

logger = logging.getLogger(__name__)

AV_BASE = "https://www.alphavantage.co/query"

# AV sentiment label -> float midpoint (for averaging)
LABEL_SCORES = {
    "Bullish": 0.75,
    "Somewhat-Bullish": 0.35,
    "Neutral": 0.0,
    "Somewhat-Bearish": -0.35,
    "Bearish": -0.75,
}


async def fetch_news_sentiment(ticker: str) -> Optional[NewsSentimentData]:
    """Returns news sentiment from Alpha Vantage, or None if no key configured."""
    from config import settings

    if not settings.alpha_vantage_api_key:
        logger.warning(f"Alpha Vantage API key not configured, skipping news sentiment for {ticker}")
        return None

    cache_key = f"av_news_{ticker}"
    cached = cache.get(cache_key, "sentiment")
    if cached:
        return NewsSentimentData(**cached)

    rate_limiter.acquire("alpha_vantage")

    try:
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": ticker,
            "sort": "LATEST",
            "limit": "50",
            "apikey": settings.alpha_vantage_api_key,
        }
        logger.info(f"Fetching Alpha Vantage news for {ticker}")

        # Retry up to 2 times with longer timeout
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.get(AV_BASE, params=params)
                    logger.info(f"Alpha Vantage response status: {resp.status_code}")
                    resp.raise_for_status()
                    data = resp.json()

                    # Check for API error messages
                    if "Error Message" in data or "Note" in data:
                        logger.error(f"Alpha Vantage API error for {ticker}: {data}")
                        return None

                    break  # Success, exit retry loop
            except (httpx.ConnectTimeout, httpx.ReadTimeout) as timeout_err:
                if attempt == 0:
                    logger.warning(f"Alpha Vantage timeout for {ticker}, retrying... ({timeout_err})")
                    continue
                else:
                    raise  # Re-raise on final attempt

        # AV returns {"Information": "..."} when rate-limited or key is invalid
        if "Information" in data or "Note" in data:
            msg = data.get("Information") or data.get("Note", "")
            logger.warning(f"Alpha Vantage news limit/key issue for {ticker}: {msg}")
            return None

        feed = data.get("feed", [])
        if not feed:
            return None

        articles: List[NewsArticle] = []
        score_sum = 0.0

        for item in feed:
            # Find ticker-specific sentiment
            ticker_sentiments = item.get("ticker_sentiment", [])
            ticker_score: Optional[float] = None
            ticker_label: Optional[str] = None
            ticker_relevance: float = 0.0

            for ts in ticker_sentiments:
                if ts.get("ticker", "").upper() == ticker.upper():
                    try:
                        ticker_score = float(ts.get("ticker_sentiment_score", 0))
                        ticker_label = ts.get("ticker_sentiment_label", "Neutral")
                        ticker_relevance = float(ts.get("relevance_score", 0))
                    except (ValueError, TypeError):
                        pass
                    break

            # Fall back to overall sentiment if ticker-specific not found
            if ticker_score is None:
                try:
                    ticker_score = float(item.get("overall_sentiment_score", 0))
                    ticker_label = item.get("overall_sentiment_label", "Neutral")
                    ticker_relevance = 0.3
                except (ValueError, TypeError):
                    ticker_score = 0.0
                    ticker_label = "Neutral"

            score_sum += ticker_score

            articles.append(NewsArticle(
                title=(item.get("title") or "")[:160],
                url=item.get("url") or "",
                source=item.get("source") or "",
                sentiment_score=round(ticker_score, 4),
                sentiment_label=ticker_label or "Neutral",
                relevance_score=round(ticker_relevance, 4),
                published_at=item.get("time_published") or "",
            ))

        if not articles:
            return None

        avg_score = round(score_sum / len(articles), 4)

        # Map avg score to label
        if avg_score >= 0.35:
            avg_label = "Bullish"
        elif avg_score >= 0.05:
            avg_label = "Somewhat-Bullish"
        elif avg_score <= -0.35:
            avg_label = "Bearish"
        elif avg_score <= -0.05:
            avg_label = "Somewhat-Bearish"
        else:
            avg_label = "Neutral"

        result = NewsSentimentData(
            ticker=ticker,
            avg_sentiment_score=avg_score,
            sentiment_label=avg_label,
            article_count=len(articles),
            articles=articles[:20],   # cap at 20 for response size
            timestamp=datetime.now(timezone.utc),
        )
        cache.set(cache_key, result.model_dump())
        return result

    except Exception as e:
        logger.error(f"Alpha Vantage news sentiment failed for {ticker}: {type(e).__name__}: {e}", exc_info=True)
        stale = cache.get_stale(cache_key)
        if stale:
            return NewsSentimentData(**stale)
        return None
