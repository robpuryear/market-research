"""Persistent watchlist management — PostgreSQL backed."""

import logging
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import WatchlistRow

logger = logging.getLogger(__name__)

# Module-level cache so sync callers (price_data, etc.) still work.
# Refreshed on every add/remove and on startup via refresh_cache().
_tickers_cache: List[str] = ["IBM", "CVNA", "NVDA", "TSLA", "AAPL", "SPY", "QQQ", "IWM"]


def get_tickers() -> List[str]:
    """Sync accessor — returns in-memory cache. Refreshed after DB writes."""
    return list(_tickers_cache)


def get_all() -> List[dict]:
    """Sync accessor returning list of dicts for backward-compat callers."""
    return [{"ticker": t} for t in _tickers_cache]


async def refresh_cache(session: AsyncSession) -> None:
    """Reload _tickers_cache from DB. Called on startup and after mutations."""
    global _tickers_cache
    result = await session.execute(select(WatchlistRow.ticker))
    _tickers_cache = [r[0] for r in result.fetchall()]
    logger.debug(f"Watchlist cache refreshed: {len(_tickers_cache)} tickers")


async def get_tickers_async(session: AsyncSession) -> List[str]:
    """Async DB read — returns current tickers."""
    result = await session.execute(select(WatchlistRow.ticker))
    return [r[0] for r in result.fetchall()]


async def add_ticker(session: AsyncSession, ticker: str) -> bool:
    """Add ticker. Returns True if added, False if already exists."""
    ticker = ticker.strip().upper()
    if not ticker:
        return False
    existing = await session.get(WatchlistRow, ticker)
    if existing:
        return False
    session.add(WatchlistRow(ticker=ticker, added_at=datetime.now(timezone.utc)))
    await session.commit()
    await refresh_cache(session)
    logger.info(f"Added {ticker} to watchlist")
    return True


async def remove_ticker(session: AsyncSession, ticker: str) -> bool:
    """Remove ticker. Returns True if removed, False if not found."""
    ticker = ticker.strip().upper()
    existing = await session.get(WatchlistRow, ticker)
    if not existing:
        return False
    await session.delete(existing)
    await session.commit()
    await refresh_cache(session)
    logger.info(f"Removed {ticker} from watchlist")
    return True


async def ticker_exists(session: AsyncSession, ticker: str) -> bool:
    """Check if ticker is in the watchlist."""
    ticker = ticker.strip().upper()
    return await session.get(WatchlistRow, ticker) is not None
