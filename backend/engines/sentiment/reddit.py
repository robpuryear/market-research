import re
import httpx
from datetime import datetime, timezone
from typing import List, Dict
import logging

from models.sentiment import RedditSentimentData, RedditPost, TickerMention
from core import cache

logger = logging.getLogger(__name__)

SUBREDDITS = ["wallstreetbets", "stocks", "investing"]
TICKER_RE = re.compile(r'\b([A-Z]{2,5})\b')

# Reddit's public JSON API — no auth required, just a descriptive User-Agent
HEADERS = {
    "User-Agent": "python:market-intel:v1.0 (personal research tool)",
    "Accept": "application/json",
}

POSITIVE_WORDS = {
    "bull", "bullish", "moon", "buy", "long", "calls", "green", "gains",
    "profit", "rally", "upside", "rocket", "squeeze", "breakout", "growth",
    "strong", "surge", "soar", "beat", "outperform", "upgrade",
}
NEGATIVE_WORDS = {
    "bear", "bearish", "short", "puts", "red", "loss", "crash", "dump",
    "sell", "downside", "collapse", "recession", "correction", "weak",
    "miss", "downgrade", "drop", "tank", "plunge", "overvalued",
}

EXCLUDED_WORDS = {
    # Common English
    "THE", "AND", "FOR", "ARE", "YOU", "NOT", "ALL", "CAN", "HAS", "HAD",
    "ANY", "OUT", "NEW", "ONE", "NOW", "ITS", "BUT", "MAY", "WHO", "GET",
    "USE", "HOW", "SAY", "SET", "PUT", "END", "GOT", "DID", "LET", "ADD",
    "CUT", "BIG", "OLD", "TOO", "SHE", "HIM", "HIS", "WAY", "DAY", "MAN",
    "TOP", "OUR", "TWO", "HER", "HAS", "HAD", "WAS", "DID", "CAN", "HAD",
    "WILL", "BEEN", "HAVE", "FROM", "THAT", "THIS", "WITH", "WHAT", "WHEN",
    "THEY", "THEN", "THAN", "SOME", "ALSO", "JUST", "OVER", "BACK", "ONLY",
    "EVEN", "MOST", "MUCH", "MANY", "MORE", "LESS", "SAME", "SUCH", "EACH",
    "INTO", "VERY", "WELL", "GOOD", "HIGH", "LONG", "LAST", "NEXT", "WEEK",
    # Countries / geographies
    "US", "UK", "EU", "USA", "USD", "GBP", "EUR", "CAD", "AUD", "JPY",
    "ASIA", "CHINA",
    # Finance jargon (not tickers)
    "CEO", "CFO", "COO", "CTO", "IPO", "ATH", "ATL", "WSB", "IMO", "FYI",
    "FAQ", "YOY", "QOQ", "EPS", "GDP", "CPI", "FED", "SEC", "ETF", "OTC",
    "NYSE", "IRA", "APR", "APY", "ROI", "NAV", "AUM", "LLC", "INC", "LTD",
    "PLC", "PER", "NET", "TAX", "BUY", "SELL", "HOLD",
    # Crypto
    "ETH", "BTC", "NFT", "HODL", "FOMO", "YOLO", "DCA",
    # Internet slang
    "WTF", "LOL", "TBH", "DIY", "APE", "AGE", "LMAO", "IMHO",
}


def _sentiment_score(text: str) -> tuple[str, float]:
    words = set(text.lower().split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    total = pos + neg
    if total == 0:
        return "neutral", 0.0
    score = (pos - neg) / total
    if score > 0.2:
        return "positive", round(score, 3)
    elif score < -0.2:
        return "negative", round(score, 3)
    return "neutral", round(score, 3)


def _extract_tickers(text: str) -> List[str]:
    found = TICKER_RE.findall(text)
    return [t for t in found if t not in EXCLUDED_WORDS and len(t) >= 2][:5]


async def _fetch_subreddit(client: httpx.AsyncClient, subreddit: str, limit: int = 25) -> list:
    """Fetch hot posts from a subreddit using Reddit's public JSON API."""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json"
    params = {"limit": limit, "raw_json": 1}
    try:
        resp = await client.get(url, params=params, headers=HEADERS, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("children", [])
    except Exception as e:
        logger.warning(f"Failed to fetch r/{subreddit}: {e}")
        return []


async def fetch_trending() -> RedditSentimentData:
    cached = cache.get("reddit_sentiment", "sentiment")
    if cached:
        return RedditSentimentData(**cached)

    posts: List[RedditPost] = []
    mention_counts: Dict[str, Dict] = {}

    async with httpx.AsyncClient() as client:
        for sub_name in SUBREDDITS:
            children = await _fetch_subreddit(client, sub_name, limit=25)

            for child in children:
                post_data = child.get("data", {})
                title = post_data.get("title", "")
                selftext = post_data.get("selftext", "") or ""
                full_text = f"{title} {selftext}"

                sentiment, score = _sentiment_score(full_text)
                tickers = _extract_tickers(full_text)
                permalink = post_data.get("permalink", "")

                posts.append(RedditPost(
                    title=title[:200],
                    subreddit=sub_name,
                    score=int(post_data.get("score", 0)),
                    url=f"https://reddit.com{permalink}",
                    tickers_mentioned=tickers,
                    sentiment=sentiment,
                    created_utc=float(post_data.get("created_utc", 0)),
                ))

                for t in tickers:
                    if t not in mention_counts:
                        mention_counts[t] = {"count": 0, "pos": 0, "neg": 0, "neu": 0, "score_sum": 0.0}
                    mention_counts[t]["count"] += 1
                    mention_counts[t]["score_sum"] += score
                    if sentiment == "positive":
                        mention_counts[t]["pos"] += 1
                    elif sentiment == "negative":
                        mention_counts[t]["neg"] += 1
                    else:
                        mention_counts[t]["neu"] += 1

    if not posts:
        raise RuntimeError("Could not fetch any posts from Reddit — check your internet connection")

    ticker_mentions = [
        TickerMention(
            ticker=t,
            mention_count=v["count"],
            sentiment_score=round(v["score_sum"] / v["count"], 3) if v["count"] > 0 else 0.0,
            positive_count=v["pos"],
            negative_count=v["neg"],
            neutral_count=v["neu"],
        )
        for t, v in mention_counts.items()
    ]
    ticker_mentions.sort(key=lambda x: x.mention_count, reverse=True)
    trending = [m.ticker for m in ticker_mentions[:10]]

    result = RedditSentimentData(
        top_posts=posts[:20],
        ticker_mentions=ticker_mentions[:20],
        trending_tickers=trending,
        total_posts_analyzed=len(posts),
        subreddits=SUBREDDITS,
        timestamp=datetime.now(timezone.utc),
    )
    cache.set("reddit_sentiment", result.model_dump())
    return result
