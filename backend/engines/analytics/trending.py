"""
Trending & Momentum Engine

Aggregates social buzz from 4 sources, then enriches with price/volume data:
  1. Reddit   — r/wallstreetbets, r/stocks, r/investing (mention count + sentiment)
  2. Alpha Vantage News — financial news articles mentioning each ticker
  3. StockTwits Trending — official trending symbols list (no auth needed)
  4. Yahoo Finance Trending — Yahoo's US trending tickers (no auth needed)

Momentum score (0–100):
  Social (60 pts max): Reddit 25 + AV News 15 + StockTwits 12 + Yahoo 8
  Technical (40 pts max): Volume spike 25 + Price momentum 15
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

import httpx
import yfinance as yf

from core import cache, rate_limiter, watchlist_manager
from engines.sentiment.reddit import fetch_trending as fetch_reddit
from models.analytics import TrendingStock

logger = logging.getLogger(__name__)

_BLACKLIST = {
    "A", "I", "AM", "AT", "BE", "BY", "DO", "GO", "IF", "IN", "IS", "IT",
    "ME", "MY", "NO", "OF", "ON", "OR", "SO", "TO", "UP", "US", "WE",
    "ALL", "AND", "ARE", "FOR", "HAS", "HIM", "HIS", "HOW", "ITS", "NOT",
    "NOW", "OLD", "OUR", "OUT", "OWN", "SAY", "SHE", "THE", "TOO", "TWO",
    "USE", "WAS", "WAY", "WHO", "WHY", "YES", "YET",
    "CEO", "CFO", "COO", "CTO", "IPO", "SEC", "FDA", "IMO", "EOD", "EOY",
    "ATH", "ATL", "YTD", "QOQ", "YOY", "EPS", "FCF", "ROI", "BOE", "FED",
    "GDP", "CPI", "PCE", "ETF", "EFT", "OTC", "HODL", "FOMO", "YOLO",
    "EST", "UTC", "PST", "PT", "ET", "DD", "TL", "DR", "TA", "RH",
    "AI", "ML", "PE", "PO", "VC", "US", "UK",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; market-research/1.0)"}


# ---------------------------------------------------------------------------
# Source fetchers — each returns a dict or set, never raises
# ---------------------------------------------------------------------------

async def _fetch_reddit_buzz() -> Dict[str, dict]:
    """Returns {ticker: {mentions, sentiment}} from Reddit."""
    try:
        data = await fetch_reddit()
        return {
            m.ticker: {"mentions": m.mention_count, "sentiment": m.sentiment_score}
            for m in data.ticker_mentions
            if m.ticker not in _BLACKLIST
        }
    except Exception as e:
        logger.warning(f"Reddit buzz fetch failed: {e}")
        return {}


async def _fetch_av_news_buzz() -> Dict[str, int]:
    """
    Returns {ticker: article_count} from Alpha Vantage general news feed.
    One API call — no per-ticker quota burn.
    """
    from config import settings
    if not settings.alpha_vantage_api_key:
        return {}
    try:
        # Non-blocking acquire — skip AV rather than freezing the event loop
        # (AV free tier: 25 calls/day, refills at ~1 token/58 min)
        if not rate_limiter.acquire("alpha_vantage", block=False):
            logger.info("Alpha Vantage rate limit reached, skipping news buzz")
            return {}
        params = {
            "function": "NEWS_SENTIMENT",
            "sort": "LATEST",
            "limit": "50",
            "apikey": settings.alpha_vantage_api_key,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get("https://www.alphavantage.co/query", params=params)
            resp.raise_for_status()
            data = resp.json()

        if "Information" in data or "Note" in data or "Error" in data:
            return {}

        counts: Dict[str, int] = {}
        for article in data.get("feed", []):
            for ts in article.get("ticker_sentiment", []):
                t = ts.get("ticker", "").upper()
                if t and t not in _BLACKLIST and len(t) <= 5:
                    counts[t] = counts.get(t, 0) + 1
        return counts
    except Exception as e:
        logger.warning(f"AV news buzz fetch failed: {e}")
        return {}


async def _fetch_stocktwits_trending() -> Set[str]:
    """Returns set of tickers currently trending on StockTwits."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.stocktwits.com/api/2/trending/symbols.json",
                headers=HEADERS,
            )
            resp.raise_for_status()
            data = resp.json()
        symbols = data.get("symbols", [])
        return {s["symbol"].upper() for s in symbols if s.get("symbol")}
    except Exception as e:
        logger.warning(f"StockTwits trending fetch failed: {e}")
        return set()


async def _fetch_yahoo_trending() -> Set[str]:
    """Returns set of tickers from Yahoo Finance US trending list."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://query2.finance.yahoo.com/v1/finance/trending/US",
                headers=HEADERS,
            )
            resp.raise_for_status()
            data = resp.json()
        quotes = data.get("finance", {}).get("result", [{}])[0].get("quotes", [])
        return {q["symbol"].upper() for q in quotes if q.get("symbol")}
    except Exception as e:
        logger.warning(f"Yahoo Finance trending fetch failed: {e}")
        return set()


async def _fetch_price(ticker: str) -> Optional[dict]:
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


# ---------------------------------------------------------------------------
# Score calculation
# ---------------------------------------------------------------------------

def _momentum_score(
    reddit_mentions: int,
    news_mentions: int,
    stocktwits_trending: bool,
    yahoo_trending: bool,
    volume_ratio: float,
    change_pct: float,
) -> float:
    """
    0–100 momentum score.
    Social (60 pts max):  Reddit 25 + AV News 15 + StockTwits 12 + Yahoo 8
    Technical (40 pts max): Volume spike 25 + Price momentum 15
    """
    social = (
        min(reddit_mentions * 8, 25)
        + min(news_mentions * 5, 15)
        + (12 if stocktwits_trending else 0)
        + (8 if yahoo_trending else 0)
    )
    technical = (
        min(max((volume_ratio - 1) * 10, 0), 25)
        + min(max(change_pct * 1.5, 0), 15)
    )
    return round(min(social + technical, 100), 1)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def get_trending(top_n: int = 15) -> List[TrendingStock]:
    cache_key = "trending_stocks"
    cached = cache.get(cache_key, "analytics")
    if cached:
        return [TrendingStock(**s) for s in cached]

    # Fetch all 4 social sources in parallel
    reddit_buzz, av_news, st_trending, yf_trending = await asyncio.gather(
        _fetch_reddit_buzz(),
        _fetch_av_news_buzz(),
        _fetch_stocktwits_trending(),
        _fetch_yahoo_trending(),
    )

    # Build candidate universe: union of all sources, filtered + capped
    all_tickers: Set[str] = (
        set(reddit_buzz.keys())
        | set(av_news.keys())
        | st_trending
        | yf_trending
    )
    all_tickers = {t for t in all_tickers if t not in _BLACKLIST and 2 <= len(t) <= 5}

    # Score each candidate (without price) to pre-rank and limit yfinance calls
    def _pre_score(ticker: str) -> float:
        rd = reddit_buzz.get(ticker, {}).get("mentions", 0)
        nw = av_news.get(ticker, 0)
        st = ticker in st_trending
        yh = ticker in yf_trending
        return min(rd * 8, 25) + min(nw * 5, 15) + (12 if st else 0) + (8 if yh else 0)

    candidates = sorted(all_tickers, key=_pre_score, reverse=True)[:top_n * 2]

    if not candidates:
        return []

    watchlist_tickers = set(watchlist_manager.get_tickers())

    # Fetch price data with bounded concurrency
    semaphore = asyncio.Semaphore(5)

    async def fetch_with_sem(ticker: str) -> Tuple[str, Optional[dict]]:
        async with semaphore:
            return ticker, await _fetch_price(ticker)

    price_results = await asyncio.gather(*[fetch_with_sem(t) for t in candidates])

    trending: List[TrendingStock] = []
    for ticker, price_data in price_results:
        if not price_data:
            continue

        rd = reddit_buzz.get(ticker, {})
        reddit_mentions = rd.get("mentions", 0)
        reddit_sentiment = rd.get("sentiment", 0.0)
        news_mentions = av_news.get(ticker, 0)
        st = ticker in st_trending
        yh = ticker in yf_trending

        sources = []
        if reddit_mentions > 0:
            sources.append("Reddit")
        if news_mentions > 0:
            sources.append("News")
        if st:
            sources.append("StockTwits")
        if yh:
            sources.append("Yahoo")

        score = _momentum_score(
            reddit_mentions, news_mentions, st, yh,
            price_data["volume_ratio"], price_data["change_pct"],
        )

        trending.append(TrendingStock(
            ticker=ticker,
            company_name=price_data["company_name"],
            price=round(price_data["price"], 2),
            change_pct=round(price_data["change_pct"], 2),
            volume_ratio=round(price_data["volume_ratio"], 2),
            reddit_mentions=reddit_mentions,
            reddit_sentiment=round(reddit_sentiment, 3),
            news_mentions=news_mentions,
            stocktwits_trending=st,
            yahoo_trending=yh,
            buzz_sources=sources,
            momentum_score=score,
            on_watchlist=ticker in watchlist_tickers,
            timestamp=datetime.now(timezone.utc),
        ))

    trending.sort(key=lambda x: x.momentum_score, reverse=True)
    trending = trending[:top_n]

    cache.set(cache_key, [s.model_dump() for s in trending])
    return trending
