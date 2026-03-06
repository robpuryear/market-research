"""
Trending & Momentum Engine

Identifies stocks gaining social buzz + volume momentum by combining:
- Reddit mention velocity (wallstreetbets, stocks, investing)
- Price / volume data from yfinance
- Watchlist membership check
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional

import yfinance as yf

from core import cache, rate_limiter, watchlist_manager
from engines.sentiment.reddit import fetch_trending as fetch_reddit
from models.analytics import TrendingStock

logger = logging.getLogger(__name__)

# Common words falsely extracted as tickers — filter them out
_BLACKLIST = {
    "A", "I", "AM", "AT", "BE", "BY", "DO", "GO", "IF", "IN", "IS", "IT",
    "ME", "MY", "NO", "OF", "ON", "OR", "SO", "TO", "UP", "US", "WE",
    "ALL", "AND", "ARE", "FOR", "HAS", "HIM", "HIS", "HOW", "ITS", "NOT",
    "NOW", "OLD", "OUR", "OUT", "OWN", "SAY", "SHE", "THE", "TOO", "TWO",
    "USE", "WAS", "WAY", "WHO", "WHY", "YES", "YET",
    "CEO", "CFO", "COO", "CTO", "IPO", "SEC", "FDA", "IMO", "EOD", "EOY",
    "ATH", "ATL", "YTD", "QOQ", "YOY", "EPS", "FCF", "ROI", "BOE", "FED",
    "GDP", "CPI", "PCE", "ETF", "EFT", "OTC", "HODL", "FOMO", "YOLO",
}


async def _fetch_price(ticker: str) -> Optional[dict]:
    """Fetch basic price/volume data for a single ticker via yfinance."""
    try:
        rate_limiter.acquire("yfinance")
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not price or price <= 0:
            return None
        volume = float(info.get("volume") or 0)
        avg_volume = float(info.get("averageVolume") or 1)
        change_pct = float(info.get("regularMarketChangePercent") or 0)
        company_name = info.get("shortName") or info.get("longName") or ticker
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        return {
            "price": price,
            "change_pct": change_pct,
            "volume_ratio": volume_ratio,
            "company_name": company_name,
        }
    except Exception as e:
        logger.debug(f"Price fetch failed for {ticker}: {e}")
        return None


def _momentum_score(mention_count: int, reddit_sentiment: float, volume_ratio: float, change_pct: float) -> float:
    """
    0–100 momentum score.
    - Social buzz (55%): mention count + reddit sentiment
    - Volume spike (25%): volume vs average
    - Price momentum (20%): positive price change only
    """
    # Social: up to 40 pts for mentions, up to 15 pts for sentiment
    social_mentions = min(mention_count * 10, 40)
    social_sentiment = (reddit_sentiment + 1) / 2 * 15  # map -1..+1 → 0..15
    social_score = social_mentions + social_sentiment

    # Volume: up to 25 pts (3x avg vol → 20 pts, 5x → 25 pts max)
    vol_score = min(max((volume_ratio - 1) * 10, 0), 25)

    # Price momentum: only reward positive change, up to 20 pts
    price_score = min(max(change_pct * 2, 0), 20)

    return round(social_score + vol_score + price_score, 1)


async def get_trending(top_n: int = 15) -> List[TrendingStock]:
    cache_key = "trending_stocks"
    cached = cache.get(cache_key, "analytics")
    if cached:
        return [TrendingStock(**s) for s in cached]

    # 1. Get Reddit trending mentions
    try:
        reddit_data = await fetch_reddit()
    except Exception as e:
        logger.warning(f"Reddit fetch failed: {e}")
        return []

    # Filter blacklisted tokens and take top candidates by mention count
    mentions = [m for m in reddit_data.ticker_mentions if m.ticker not in _BLACKLIST]
    top_mentions = mentions[:min(top_n * 2, 30)]  # fetch extra, filter duds

    if not top_mentions:
        return []

    watchlist_tickers = set(watchlist_manager.get_tickers())

    # 2. Fetch price data in parallel (limit concurrency to avoid rate limits)
    semaphore = asyncio.Semaphore(5)

    async def fetch_with_sem(ticker: str):
        async with semaphore:
            return ticker, await _fetch_price(ticker)

    results = await asyncio.gather(*[fetch_with_sem(m.ticker) for m in top_mentions])

    # 3. Build TrendingStock list
    trending: List[TrendingStock] = []
    mention_map = {m.ticker: m for m in top_mentions}

    for ticker, price_data in results:
        if not price_data:
            continue
        m = mention_map[ticker]
        score = _momentum_score(
            m.mention_count,
            m.sentiment_score,
            price_data["volume_ratio"],
            price_data["change_pct"],
        )
        trending.append(TrendingStock(
            ticker=ticker,
            company_name=price_data["company_name"],
            price=round(price_data["price"], 2),
            change_pct=round(price_data["change_pct"], 2),
            volume_ratio=round(price_data["volume_ratio"], 2),
            reddit_mentions=m.mention_count,
            reddit_sentiment=round(m.sentiment_score, 3),
            momentum_score=score,
            on_watchlist=ticker in watchlist_tickers,
            timestamp=datetime.now(timezone.utc),
        ))

    trending.sort(key=lambda x: x.momentum_score, reverse=True)
    trending = trending[:top_n]

    cache.set(cache_key, [s.model_dump() for s in trending])
    return trending
