import asyncio
import logging
from datetime import datetime, timezone
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from backend.models.reports import SchedulerJobInfo

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="America/New_York")


async def _refresh_market_snapshot():
    try:
        from backend.engines.market_data import macro
        from backend.core.cache import invalidate
        invalidate("macro_snapshot")
        await macro.fetch_snapshot()
        logger.debug("Market snapshot refreshed")
    except Exception as e:
        logger.error(f"Scheduler: market snapshot failed: {e}")


async def _refresh_watchlist():
    try:
        from backend.engines.watchlist import price_data
        from backend.core.cache import invalidate
        invalidate("watchlist_bulk")
        await price_data.bulk_fetch()
        logger.debug("Watchlist refreshed")
    except Exception as e:
        logger.error(f"Scheduler: watchlist refresh failed: {e}")


async def _refresh_sectors():
    try:
        from backend.engines.market_data import sectors
        from backend.core.cache import invalidate
        invalidate("sector_rotation")
        await sectors.fetch_rotation()
        logger.debug("Sectors refreshed")
    except Exception as e:
        logger.error(f"Scheduler: sectors failed: {e}")


async def _refresh_reddit():
    try:
        from backend.engines.sentiment import reddit
        from backend.core.cache import invalidate
        invalidate("reddit_sentiment")
        await reddit.fetch_trending()
        logger.debug("Reddit sentiment refreshed")
    except Exception as e:
        logger.error(f"Scheduler: reddit failed: {e}")


async def _refresh_breadth():
    try:
        from backend.engines.market_data import breadth
        from backend.core.cache import invalidate
        invalidate("market_breadth")
        await breadth.fetch_breadth()
        logger.debug("Market breadth refreshed")
    except Exception as e:
        logger.error(f"Scheduler: breadth refresh failed: {e}")


async def _generate_daily_report():
    try:
        from backend.report_engine import generator
        await generator.generate_report_a(standalone=True)
        logger.info("Scheduled daily report generated")
    except Exception as e:
        logger.error(f"Scheduler: daily report failed: {e}")


async def _generate_analytics_report():
    try:
        from backend.report_engine import generator
        await generator.generate_report_b(standalone=True)
        logger.info("Scheduled analytics report generated")
    except Exception as e:
        logger.error(f"Scheduler: analytics report failed: {e}")


async def _generate_scanner_report():
    try:
        from backend.report_engine import generator
        await generator.generate_scanner_report(standalone=True)
        logger.info("Scheduled scanner report generated")
    except Exception as e:
        logger.error(f"Scheduler: scanner report failed: {e}")


async def _refresh_analytics():
    try:
        from backend.engines.analytics import short_squeeze, correlation
        from backend.core.cache import invalidate
        invalidate("squeeze_scores")
        invalidate("correlation_matrix")
        await short_squeeze.score_all()
        await correlation.compute_matrix()
        logger.info("Analytics scores refreshed")
    except Exception as e:
        logger.error(f"Scheduler: analytics refresh failed: {e}")


def setup_scheduler():
    """Register all scheduled jobs."""
    # Market snapshot: every 5 min
    scheduler.add_job(
        _refresh_market_snapshot,
        IntervalTrigger(minutes=5),
        id="market_snapshot",
        name="Market Snapshot Refresh",
        replace_existing=True,
    )

    # Watchlist: every 5 min
    scheduler.add_job(
        _refresh_watchlist,
        IntervalTrigger(minutes=5),
        id="watchlist",
        name="Watchlist Price Refresh",
        replace_existing=True,
    )

    # Sectors: every 10 min
    scheduler.add_job(
        _refresh_sectors,
        IntervalTrigger(minutes=10),
        id="sectors",
        name="Sector Rotation Refresh",
        replace_existing=True,
    )

    # Market breadth: every 10 min
    scheduler.add_job(
        _refresh_breadth,
        IntervalTrigger(minutes=10),
        id="breadth",
        name="Market Breadth Refresh",
        replace_existing=True,
    )

    # Reddit: every 30 min
    scheduler.add_job(
        _refresh_reddit,
        IntervalTrigger(minutes=30),
        id="reddit",
        name="Reddit Sentiment Refresh",
        replace_existing=True,
    )

    # Report A: 6:30 AM ET (pre-market) + 5:00 PM ET (post-market), Mon-Fri
    scheduler.add_job(
        _generate_daily_report,
        CronTrigger(day_of_week="mon-fri", hour=6, minute=30, timezone="America/New_York"),
        id="report_a_premarket",
        name="Daily Report (Pre-Market)",
        replace_existing=True,
    )
    scheduler.add_job(
        _generate_daily_report,
        CronTrigger(day_of_week="mon-fri", hour=17, minute=0, timezone="America/New_York"),
        id="report_a_postmarket",
        name="Daily Report (Post-Market)",
        replace_existing=True,
    )

    # Report B: 4:30 PM ET Mon-Fri
    scheduler.add_job(
        _generate_analytics_report,
        CronTrigger(day_of_week="mon-fri", hour=16, minute=30, timezone="America/New_York"),
        id="report_b",
        name="Analytics Report (EOD)",
        replace_existing=True,
    )

    # Market Scanner Report: 4:45 PM ET Mon-Fri
    scheduler.add_job(
        _generate_scanner_report,
        CronTrigger(day_of_week="mon-fri", hour=16, minute=45, timezone="America/New_York"),
        id="scanner_report",
        name="Market Scanner Report (EOD)",
        replace_existing=True,
    )

    # Analytics scores (squeeze + correlation): 4:30 PM ET Mon-Fri
    scheduler.add_job(
        _refresh_analytics,
        CronTrigger(day_of_week="mon-fri", hour=16, minute=30, timezone="America/New_York"),
        id="analytics_scores",
        name="Analytics Scores Refresh",
        replace_existing=True,
    )


def get_job_info() -> List[dict]:
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": next_run.isoformat() if next_run else None,
            "status": "scheduled" if next_run else "paused",
        })
    return jobs


def start():
    setup_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))


def stop():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
