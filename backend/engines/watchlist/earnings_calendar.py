"""Earnings calendar: upcoming earnings dates for all watchlist tickers."""
import yfinance as yf
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import logging

from backend.core import cache, rate_limiter
from backend.config import settings

logger = logging.getLogger(__name__)


def _parse_earnings_date(tk: yf.Ticker, ticker: str) -> str | None:
    """Try to get earnings date from calendar, then fall back to info."""
    try:
        cal = tk.calendar
        if cal is not None and not cal.empty:
            # DataFrame with columns as dates, rows as metrics (Earnings Date, etc.)
            if "Earnings Date" in cal.index:
                val = cal.loc["Earnings Date"].iloc[0]
                if val is not None:
                    if hasattr(val, "date"):
                        return val.date().isoformat()
                    return str(val)
    except Exception:
        pass

    try:
        info = tk.info or {}
        ed = info.get("earningsDate") or info.get("earningsTimestamp")
        if ed:
            if isinstance(ed, list) and len(ed) > 0:
                ed = ed[0]
            if isinstance(ed, (int, float)):
                return datetime.fromtimestamp(ed, tz=timezone.utc).date().isoformat()
            if hasattr(ed, "date"):
                return ed.date().isoformat()
    except Exception:
        pass

    return None


async def get_earnings_calendar() -> List[Dict]:
    cache_key = "earnings_calendar"
    cached = cache.get(cache_key, "earnings")
    if cached:
        return cached

    tickers = settings.tickers_list
    now = datetime.now(timezone.utc).date()
    cutoff = now + timedelta(days=60)
    results = []

    for ticker in tickers:
        rate_limiter.acquire("yfinance")
        try:
            tk = yf.Ticker(ticker)
            date_str = _parse_earnings_date(tk, ticker)
            if not date_str:
                continue

            earnings_date = datetime.fromisoformat(date_str).date()
            if earnings_date < now or earnings_date > cutoff:
                continue

            days_until = (earnings_date - now).days
            results.append({
                "ticker": ticker,
                "earnings_date": date_str,
                "days_until": days_until,
            })
        except Exception as e:
            logger.warning(f"Error fetching earnings date for {ticker}: {e}")

    results.sort(key=lambda x: x["earnings_date"])
    cache.set(cache_key, results)
    return results
