"""
Economic Calendar Engine

Fetches upcoming macro event dates from official government sources:
  - CPI (Consumer Price Index) — BLS release schedule
  - Jobs Report (Employment Situation) — BLS release schedule
  - FOMC decision dates — Federal Reserve calendar

All three sources are public government pages with no API key required.
Results cached 24 hours since these schedules rarely change.
"""
import asyncio
import logging
import re
from datetime import date, datetime, timezone
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

# Month name → number for regex parsing
_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


def _parse_bls_dates(html: str) -> List[date]:
    """
    Extract dates from BLS release schedule pages.
    BLS format: 'Wednesday, March 11, 2026' or 'March 11, 2026'
    """
    today = date.today()
    found: List[date] = []

    # Pattern: optional weekday, then Month DD, YYYY
    pattern = re.compile(
        r'(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday),\s+)?'
        r'(January|February|March|April|May|June|July|August|'
        r'September|October|November|December)\s+(\d{1,2}),\s+(20\d{2})',
        re.IGNORECASE,
    )
    for m in pattern.finditer(html):
        month_str, day_str, year_str = m.group(1), m.group(2), m.group(3)
        month = _MONTHS.get(month_str.lower())
        if not month:
            continue
        try:
            d = date(int(year_str), month, int(day_str))
            if d >= today:
                found.append(d)
        except ValueError:
            continue

    return sorted(set(found))


def _parse_fomc_dates(html: str) -> List[date]:
    """
    Extract FOMC decision dates from the Fed calendar page.

    The page uses structured divs per meeting:
      <div class="fomc-meeting__month ..."><strong>March</strong></div>
      <div class="fomc-meeting__date ...">17-18</div>

    Month and day are in separate elements. Year comes from the nearest
    preceding section header like '2026 FOMC Meetings'.
    Second day of a range is the decision day.
    """
    today = date.today()
    found: List[date] = []

    # Split into per-year sections
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
            # day_str is like "27-28" or "28" or "17-18*"
            day_clean = re.sub(r'[^0-9\-]', '', day_str)
            parts = day_clean.split('-')
            try:
                decision_day = int(parts[-1])  # last number = decision day
                d = date(year, month, decision_day)
                if d >= today:
                    found.append(d)
            except (ValueError, IndexError):
                continue

    return sorted(set(found))


async def _get(url: str) -> str:
    async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


async def _fetch_cpi_dates() -> List[date]:
    try:
        html = await _get("https://www.bls.gov/schedule/news_release/cpi.htm")
        dates = _parse_bls_dates(html)
        logger.info(f"CPI: found {len(dates)} upcoming dates")
        return dates
    except Exception as e:
        logger.warning(f"CPI schedule fetch failed: {e}")
        return []


async def _fetch_jobs_dates() -> List[date]:
    try:
        html = await _get("https://www.bls.gov/schedule/news_release/empsit.htm")
        dates = _parse_bls_dates(html)
        logger.info(f"Jobs: found {len(dates)} upcoming dates")
        return dates
    except Exception as e:
        logger.warning(f"Jobs schedule fetch failed: {e}")
        return []


async def _fetch_fomc_dates() -> List[date]:
    try:
        html = await _get(
            "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
        )
        dates = _parse_fomc_dates(html)
        logger.info(f"FOMC: found {len(dates)} upcoming dates")
        return dates
    except Exception as e:
        logger.warning(f"FOMC schedule fetch failed: {e}")
        return []


async def get_economic_calendar(max_events: int = 6) -> List[dict]:
    """
    Returns upcoming macro events sorted by date.
    Each event: {name, event_type, date (YYYY-MM-DD), days_until, description}
    """
    cache_key = "economic_calendar"
    cached = cache.get(cache_key, "earnings")  # 24h TTL (reuses earnings category)
    if cached:
        return cached

    today = date.today()

    cpi_dates, jobs_dates, fomc_dates = await asyncio.gather(
        _fetch_cpi_dates(),
        _fetch_jobs_dates(),
        _fetch_fomc_dates(),
    )

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
