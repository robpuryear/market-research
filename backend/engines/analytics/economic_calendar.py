"""
Economic Calendar Engine

CPI and Jobs Report dates are hard-coded from the official BLS annual
release schedule (published each December, never changes mid-year).
BLS blocks automated HTTP requests from cloud IPs, so scraping is not viable.

FOMC decision dates are scraped live from the Federal Reserve website,
which does not block cloud requests.

Results cached 24 hours.
"""
import asyncio
import logging
import re
from datetime import date
from typing import List

import httpx

from core import cache

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

# ---------------------------------------------------------------------------
# Hard-coded BLS release schedules (BLS blocks cloud scraping)
# Source: https://www.bls.gov/schedule/news_release/cpi.htm
#         https://www.bls.gov/schedule/news_release/empsit.htm
# ---------------------------------------------------------------------------

_CPI_2026 = [
    date(2026,  1, 14),
    date(2026,  2, 11),
    date(2026,  3, 11),  # today
    date(2026,  4, 10),
    date(2026,  5, 12),
    date(2026,  6, 11),
    date(2026,  7, 15),
    date(2026,  8, 12),
    date(2026,  9, 11),
    date(2026, 10, 14),
    date(2026, 11, 12),
    date(2026, 12, 11),
]

_JOBS_2026 = [
    date(2026,  1,  9),
    date(2026,  2,  6),
    date(2026,  3,  6),
    date(2026,  4,  3),
    date(2026,  5,  8),
    date(2026,  6,  5),
    date(2026,  7, 10),  # Jul 3 is holiday observance for Jul 4 (Sat)
    date(2026,  8,  7),
    date(2026,  9,  4),
    date(2026, 10,  2),
    date(2026, 11,  6),
    date(2026, 12,  4),
]


def _upcoming(dates: List[date]) -> List[date]:
    today = date.today()
    return [d for d in dates if d >= today]


# ---------------------------------------------------------------------------
# FOMC — scraped live from federalreserve.gov (no IP blocks)
# ---------------------------------------------------------------------------

def _parse_fomc_dates(html: str) -> List[date]:
    """
    Fed page stores month in fomc-meeting__month div and day range in
    fomc-meeting__date div. Year comes from the section header.
    Second day of a two-day meeting is the decision day.
    """
    today = date.today()
    found: List[date] = []

    year_section_re = re.compile(r'(\d{4})\s+FOMC\s+Meetings', re.IGNORECASE)
    section_starts = [(m.start(), int(m.group(1))) for m in year_section_re.finditer(html)]

    month_re = re.compile(r'fomc-meeting__month[^>]*>.*?<strong>(.*?)</strong>', re.IGNORECASE | re.DOTALL)
    date_re  = re.compile(r'fomc-meeting__date[^>]*>([\d\-*]+)<', re.IGNORECASE)

    for i, (start, year) in enumerate(section_starts):
        end = section_starts[i + 1][0] if i + 1 < len(section_starts) else len(html)
        section = html[start:end]

        months = [m.group(1).strip() for m in month_re.finditer(section)]
        dates  = [m.group(1).strip() for m in date_re.finditer(section)]

        for month_str, day_str in zip(months, dates):
            month = _MONTHS.get(month_str.lower())
            if not month:
                continue
            day_clean = re.sub(r'[^0-9\-]', '', day_str)
            parts = day_clean.split('-')
            try:
                d = date(year, month, int(parts[-1]))
                if d >= today:
                    found.append(d)
            except (ValueError, IndexError):
                continue

    return sorted(set(found))


async def _fetch_fomc_dates() -> List[date]:
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
            resp = await client.get(
                "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
            )
            resp.raise_for_status()
            html = resp.text
        dates = _parse_fomc_dates(html)
        logger.info(f"FOMC: found {len(dates)} upcoming dates")
        return dates
    except Exception as e:
        logger.warning(f"FOMC schedule fetch failed: {e}")
        return []


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def get_economic_calendar(max_events: int = 6) -> List[dict]:
    """
    Returns upcoming macro events sorted by date.
    Each event: {name, event_type, date (YYYY-MM-DD), days_until, description}
    """
    cache_key = "economic_calendar"
    cached = cache.get(cache_key, "earnings")  # 24h TTL
    if cached:
        # Recalculate days_until in case cache is from yesterday
        today = date.today()
        for event in cached:
            event["days_until"] = (date.fromisoformat(event["date"]) - today).days
        return cached

    today = date.today()

    cpi_dates  = _upcoming(_CPI_2026)
    jobs_dates = _upcoming(_JOBS_2026)
    fomc_dates = await _fetch_fomc_dates()

    events: List[dict] = []

    for d in cpi_dates[:max_events]:
        events.append({
            "name": "CPI Report",
            "event_type": "cpi",
            "date": d.isoformat(),
            "days_until": (d - today).days,
            "description": "Consumer Price Index — measures inflation",
        })

    for d in jobs_dates[:max_events]:
        events.append({
            "name": "Jobs Report",
            "event_type": "jobs",
            "date": d.isoformat(),
            "days_until": (d - today).days,
            "description": "Nonfarm Payrolls — monthly employment data",
        })

    for d in fomc_dates[:max_events]:
        events.append({
            "name": "FOMC Decision",
            "event_type": "fomc",
            "date": d.isoformat(),
            "days_until": (d - today).days,
            "description": "Federal Reserve interest rate decision",
        })

    events.sort(key=lambda e: e["date"])

    cache.set(cache_key, events)
    return events
