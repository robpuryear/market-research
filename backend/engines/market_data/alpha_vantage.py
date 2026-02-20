import logging
from typing import List, Optional

import httpx

from backend.models.watchlist import EarningsEntry
from backend.core import cache, rate_limiter

logger = logging.getLogger(__name__)

AV_BASE = "https://www.alphavantage.co/query"


async def fetch_earnings(ticker: str) -> Optional[List[EarningsEntry]]:
    """Returns last 8 quarters of earnings, or None if no key / any error."""
    from backend.config import settings

    if not settings.alpha_vantage_api_key:
        return None

    cache_key = f"av_earnings_{ticker}"
    cached = cache.get(cache_key, "earnings")
    if cached:
        return [EarningsEntry(**e) for e in cached]

    rate_limiter.acquire("alpha_vantage")

    try:
        params = {
            "function": "EARNINGS",
            "symbol": ticker,
            "apikey": settings.alpha_vantage_api_key,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(AV_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()

        quarterly = data.get("quarterlyEarnings", [])
        if not quarterly:
            return None

        entries = []
        for q in quarterly[:8]:
            try:
                est = q.get("estimatedEPS")
                act = q.get("reportedEPS")
                surp = q.get("surprisePercentage")
                entries.append(EarningsEntry(
                    date=str(q.get("fiscalDateEnding", "")),
                    eps_estimate=float(est) if est not in (None, "None", "") else None,
                    eps_actual=float(act) if act not in (None, "None", "") else None,
                    surprise_pct=float(surp) / 100 if surp not in (None, "None", "") else None,
                ))
            except Exception:
                continue

        cache.set(cache_key, [e.model_dump() for e in entries])
        return entries

    except Exception as e:
        logger.warning(f"Alpha Vantage earnings fetch failed for {ticker}: {e}")
        return None
