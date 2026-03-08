import asyncio
import gc
import logging
from datetime import datetime, timezone
from typing import List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from models.reports import SchedulerJobInfo

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="America/New_York")


async def _refresh_market_snapshot():
    try:
        from engines.market_data import macro
        from core.cache import invalidate
        invalidate("macro_snapshot")
        await macro.fetch_snapshot()
        logger.debug("Market snapshot refreshed")
    except Exception as e:
        logger.error(f"Scheduler: market snapshot failed: {e}")


async def _refresh_watchlist():
    try:
        from engines.watchlist import price_data
        from core.cache import invalidate
        invalidate("watchlist_bulk")
        await price_data.bulk_fetch()
        logger.debug("Watchlist refreshed")
    except Exception as e:
        logger.error(f"Scheduler: watchlist refresh failed: {e}")
    finally:
        gc.collect()


async def _refresh_sectors():
    try:
        from engines.market_data import sectors
        from core.cache import invalidate
        invalidate("sector_rotation")
        await sectors.fetch_rotation()
        logger.debug("Sectors refreshed")
    except Exception as e:
        logger.error(f"Scheduler: sectors failed: {e}")


async def _refresh_reddit():
    try:
        from engines.sentiment import reddit
        from core.cache import invalidate
        invalidate("reddit_sentiment")
        await reddit.fetch_trending()
        logger.debug("Reddit sentiment refreshed")
    except Exception as e:
        logger.error(f"Scheduler: reddit failed: {e}")


async def _refresh_breadth():
    try:
        from engines.market_data import breadth
        from core.cache import invalidate
        invalidate("market_breadth")
        await breadth.fetch_breadth()
        logger.debug("Market breadth refreshed")
    except Exception as e:
        logger.error(f"Scheduler: breadth refresh failed: {e}")


async def _generate_daily_report():
    try:
        from report_engine import generator
        await generator.generate_report_a(standalone=True)
        logger.info("Scheduled daily report generated")
    except Exception as e:
        logger.error(f"Scheduler: daily report failed: {e}")


async def _generate_analytics_report():
    try:
        from report_engine import generator
        await generator.generate_report_b(standalone=True)
        logger.info("Scheduled analytics report generated")
    except Exception as e:
        logger.error(f"Scheduler: analytics report failed: {e}")


async def _generate_scanner_report():
    try:
        from report_engine import generator
        await generator.generate_scanner_report(standalone=True)
        logger.info("Scheduled scanner report generated")
    except Exception as e:
        logger.error(f"Scheduler: scanner report failed: {e}")
    finally:
        gc.collect()


async def _refresh_analytics():
    try:
        from engines.analytics import short_squeeze, correlation
        from core.cache import invalidate
        invalidate("squeeze_scores")
        invalidate("correlation_matrix")
        await short_squeeze.score_all()
        await correlation.compute_matrix()
        logger.info("Analytics scores refreshed")
    except Exception as e:
        logger.error(f"Scheduler: analytics refresh failed: {e}")


async def _evaluate_alerts():
    try:
        from engines.alerts.evaluator import evaluate_all_alerts
        from db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await evaluate_all_alerts(session)
        logger.debug("Alert evaluation completed")
    except Exception as e:
        logger.error(f"Scheduler: alert evaluation failed: {e}")


async def _run_enabled_strategies():
    """Run all enabled strategies"""
    try:
        from engines.strategy import strategy_manager, strategy_evaluator
        from engines.alerts import alert_manager
        from core import watchlist_manager, stock_universe
        from db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            strategies = await strategy_manager.get_all_strategies(session)
            enabled_strategies = [s for s in strategies if s.enabled]

            if not enabled_strategies:
                return

            logger.info(f"Running {len(enabled_strategies)} enabled strategies")

            for strategy in enabled_strategies:
                try:
                    tickers = watchlist_manager.get_tickers() if strategy.scope == "watchlist" else stock_universe.get_all_tickers()

                    if not tickers:
                        continue

                    results = await strategy_evaluator.run_strategy_scan(strategy, tickers, session)

                    if strategy.generate_alerts and results:
                        for result in results:
                            try:
                                await alert_manager.create_alert(session, {
                                    "ticker": result.ticker,
                                    "alert_type": "signal",
                                    "condition": {
                                        "signal_type": "strategy",
                                        "operator": "fired",
                                        "threshold": None,
                                        "direction": None,
                                    },
                                    "message": f"Strategy '{strategy.name}' matched (signal strength: {result.signal_strength})",
                                })
                            except Exception as e:
                                logger.error(f"Failed to create alert for {result.ticker}: {e}")

                    logger.info(f"Strategy '{strategy.name}' completed: {len(results)} matches")

                except Exception as e:
                    logger.error(f"Failed to run strategy '{strategy.name}': {e}")

            # Reset daily hit counters at midnight
            now = datetime.now(timezone.utc)
            if now.hour == 0 and now.minute < 15:
                await strategy_manager.reset_daily_hits(session)

    except Exception as e:
        logger.error(f"Scheduler: strategy execution failed: {e}")


def setup_scheduler():
    """Register all scheduled jobs."""
    # Market snapshot: every 5 min (lightweight — just a few yfinance calls)
    scheduler.add_job(
        _refresh_market_snapshot,
        IntervalTrigger(minutes=5),
        id="market_snapshot",
        name="Market Snapshot Refresh",
        replace_existing=True,
    )

    # Watchlist: every 10 min, offset by 2 min so it doesn't fire with snapshot
    # (bulk yf.download is memory-intensive — 5 min was too aggressive)
    scheduler.add_job(
        _refresh_watchlist,
        IntervalTrigger(minutes=10, start_date="2000-01-01 00:02:00"),
        id="watchlist",
        name="Watchlist Price Refresh",
        replace_existing=True,
    )

    # Sectors: every 10 min, offset by 4 min
    scheduler.add_job(
        _refresh_sectors,
        IntervalTrigger(minutes=10, start_date="2000-01-01 00:04:00"),
        id="sectors",
        name="Sector Rotation Refresh",
        replace_existing=True,
    )

    # Market breadth: every 10 min, offset by 6 min
    scheduler.add_job(
        _refresh_breadth,
        IntervalTrigger(minutes=10, start_date="2000-01-01 00:06:00"),
        id="breadth",
        name="Market Breadth Refresh",
        replace_existing=True,
    )

    # Reddit: every 30 min, offset by 8 min
    scheduler.add_job(
        _refresh_reddit,
        IntervalTrigger(minutes=30, start_date="2000-01-01 00:08:00"),
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

    # Alert evaluation: every 5 minutes
    scheduler.add_job(
        _evaluate_alerts,
        IntervalTrigger(minutes=5),
        id="alert_evaluation",
        name="Alert Evaluation",
        replace_existing=True,
    )

    # Strategy execution: every 15 minutes during market hours
    scheduler.add_job(
        _run_enabled_strategies,
        IntervalTrigger(minutes=15),
        id="strategy_execution",
        name="Strategy Execution",
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
