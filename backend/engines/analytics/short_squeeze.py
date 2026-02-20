"""Short squeeze scoring: short interest % + volume ratio + options activity."""
import yfinance as yf
from datetime import datetime, timezone
from typing import List, Dict
import logging

from core import cache, rate_limiter
from config import settings

logger = logging.getLogger(__name__)


def _squeeze_score(
    short_pct: float | None,
    short_ratio: float | None,
    volume_ratio: float | None,
    has_unusual_options: bool = False,
) -> float:
    """Score 0-100 based on squeeze indicators."""
    score = 0.0

    # Short interest (0-40 pts)
    if short_pct is not None:
        score += min(40, short_pct * 100 * 2)  # 20% SI = 40 pts

    # Short ratio / days to cover (0-30 pts)
    if short_ratio is not None:
        score += min(30, short_ratio * 3)  # 10 days = 30 pts

    # Volume spike (0-20 pts)
    if volume_ratio is not None:
        score += min(20, (volume_ratio - 1) * 10)  # 3x vol = 20 pts

    # Unusual options (0-10 pts)
    if has_unusual_options:
        score += 10

    return round(min(100, max(0, score)), 1)


async def score_all() -> List[Dict]:
    cache_key = "squeeze_scores"
    cached = cache.get(cache_key, "fundamentals")
    if cached:
        return cached

    tickers = settings.tickers_list
    results = []

    for ticker in tickers:
        rate_limiter.acquire("yfinance")
        try:
            tk = yf.Ticker(ticker)
            info = tk.info or {}

            short_pct = info.get("shortPercentOfFloat")
            short_ratio = info.get("shortRatio")
            volume = info.get("volume") or 0
            avg_volume = info.get("averageVolume") or 1
            vol_ratio = volume / avg_volume if avg_volume > 0 else 1.0

            score = _squeeze_score(short_pct, short_ratio, vol_ratio)

            results.append({
                "ticker": ticker,
                "squeeze_score": score,
                "short_interest_pct": round(short_pct * 100, 1) if short_pct else None,
                "days_to_cover": round(short_ratio, 1) if short_ratio else None,
                "volume_ratio": round(vol_ratio, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.warning(f"Error scoring squeeze for {ticker}: {e}")

    results.sort(key=lambda x: x["squeeze_score"], reverse=True)
    cache.set(cache_key, results)
    return results
