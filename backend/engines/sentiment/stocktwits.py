import logging
from datetime import datetime, timezone
from typing import List

import httpx

from models.sentiment import StockTwitsSentiment
from core import cache, rate_limiter

logger = logging.getLogger(__name__)

BASE_URL = "https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"

HEADERS = {
    "User-Agent": "python:market-intel:v1.0 (personal research tool)",
    "Accept": "application/json",
}


async def fetch_stocktwits(ticker: str) -> StockTwitsSentiment:
    cache_key = f"stocktwits_{ticker}"
    cached = cache.get(cache_key, "sentiment")
    if cached:
        return StockTwitsSentiment(**cached)

    rate_limiter.acquire("stocktwits")

    try:
        url = BASE_URL.format(ticker=ticker)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=HEADERS)
            # StockTwits returns 404 for unknown tickers -- treat as empty
            if resp.status_code == 404:
                return _empty_result(ticker)
            resp.raise_for_status()
            data = resp.json()

        messages = data.get("messages", [])
        bullish = 0
        bearish = 0
        snippets: List[str] = []

        for msg in messages:
            entities = msg.get("entities") or {}
            sentiment_obj = entities.get("sentiment") or {}
            basic = sentiment_obj.get("basic", "")
            if basic == "Bullish":
                bullish += 1
            elif basic == "Bearish":
                bearish += 1

            body = (msg.get("body") or "").strip()
            if body and len(snippets) < 5:
                snippets.append(body[:120])

        total = len(messages)
        labeled_total = bullish + bearish
        ratio = round(bullish / labeled_total, 3) if labeled_total > 0 else 0.5

        if ratio >= 0.6:
            label = "Bullish"
        elif ratio <= 0.4:
            label = "Bearish"
        else:
            label = "Neutral"

        result = StockTwitsSentiment(
            ticker=ticker,
            bullish_count=bullish,
            bearish_count=bearish,
            total_messages=total,
            sentiment_ratio=ratio,
            sentiment_label=label,
            recent_messages=snippets,
            timestamp=datetime.now(timezone.utc),
        )
        cache.set(cache_key, result.model_dump())
        return result

    except Exception as e:
        logger.warning(f"StockTwits fetch failed for {ticker}: {e}")
        stale = cache.get_stale(cache_key)
        if stale:
            return StockTwitsSentiment(**stale)
        return _empty_result(ticker)


def _empty_result(ticker: str) -> StockTwitsSentiment:
    return StockTwitsSentiment(
        ticker=ticker,
        bullish_count=0,
        bearish_count=0,
        total_messages=0,
        sentiment_ratio=0.5,
        sentiment_label="Neutral",
        recent_messages=[],
        timestamp=datetime.now(timezone.utc),
    )
