"""Twitter/X sentiment placeholder — returns mock structure until bearer token is provided."""
from datetime import datetime, timezone
from typing import List
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


async def fetch_mentions(ticker: str) -> dict:
    """Placeholder for Twitter/X mention data."""
    return {
        "ticker": ticker,
        "mention_count_24h": None,
        "sentiment_score": None,
        "trending_rank": None,
        "is_placeholder": True,
        "message": "Configure TWITTER_BEARER_TOKEN in .env to enable Twitter sentiment",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
