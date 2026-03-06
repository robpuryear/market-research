"""
Database initialization and one-time JSON migration.

Called on startup. Safe to run repeatedly (idempotent).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import (
    Base,
    WatchlistRow, PositionRow, TransactionRow,
    StrategyRow, StrategyResultRow,
    AlertRow, NotificationRow,
    ReportRow,
)
from db.session import engine, AsyncSessionLocal

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


async def init_db() -> None:
    """Create all tables and seed from JSON files if tables are empty."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    async with AsyncSessionLocal() as session:
        await _seed_all(session)
        await _cleanup_orphaned_reports(session)
        # Warm the in-memory watchlist cache
        from core.watchlist_manager import refresh_cache
        await refresh_cache(session)


async def _seed_all(session: AsyncSession) -> None:
    await _seed_watchlist(session)
    await _seed_positions(session)
    await _seed_transactions(session)
    await _seed_strategies(session)
    await _seed_strategy_results(session)
    await _seed_alerts(session)
    await _seed_notifications(session)
    await _seed_reports(session)


async def _seed_watchlist(session: AsyncSession) -> None:
    f = DATA_DIR / "watchlist.json"
    if not f.exists():
        return
    count = await session.scalar(select(func.count()).select_from(WatchlistRow))
    if count and count > 0:
        return
    try:
        data = json.loads(f.read_text())
        tickers = data.get("tickers", [])
        for t in tickers:
            session.add(WatchlistRow(ticker=t, added_at=datetime.now(timezone.utc)))
        await session.commit()
        logger.info(f"Seeded {len(tickers)} watchlist tickers from JSON")
        f.rename(f.with_suffix(".json.migrated"))
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to seed watchlist: {e}")


async def _seed_positions(session: AsyncSession) -> None:
    f = DATA_DIR / "positions.json"
    if not f.exists():
        return
    count = await session.scalar(select(func.count()).select_from(PositionRow))
    if count and count > 0:
        return
    try:
        rows = json.loads(f.read_text())
        _stored_fields = {"id", "ticker", "quantity", "avg_cost_basis",
                          "entry_date", "last_updated", "notes", "status"}
        for p in rows:
            d = {k: v for k, v in p.items() if k in _stored_fields}
            if isinstance(d.get("last_updated"), str):
                d["last_updated"] = datetime.fromisoformat(d["last_updated"].replace("Z", "+00:00"))
            session.add(PositionRow(**d))
        await session.commit()
        logger.info(f"Seeded {len(rows)} positions from JSON")
        f.rename(f.with_suffix(".json.migrated"))
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to seed positions: {e}")


async def _seed_transactions(session: AsyncSession) -> None:
    f = DATA_DIR / "transactions.json"
    if not f.exists():
        return
    count = await session.scalar(select(func.count()).select_from(TransactionRow))
    if count and count > 0:
        return
    try:
        rows = json.loads(f.read_text())
        _stored_fields = {"id", "position_id", "ticker", "transaction_type",
                          "quantity", "price", "total_value", "commission",
                          "date", "timestamp", "notes"}
        for t in rows:
            d = {k: v for k, v in t.items() if k in _stored_fields}
            if isinstance(d.get("timestamp"), str):
                d["timestamp"] = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00"))
            session.add(TransactionRow(**d))
        await session.commit()
        logger.info(f"Seeded {len(rows)} transactions from JSON")
        f.rename(f.with_suffix(".json.migrated"))
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to seed transactions: {e}")


async def _seed_strategies(session: AsyncSession) -> None:
    f = DATA_DIR / "strategies.json"
    if not f.exists():
        return
    count = await session.scalar(select(func.count()).select_from(StrategyRow))
    if count and count > 0:
        return
    try:
        rows = json.loads(f.read_text())
        for s in rows:
            row = StrategyRow(
                id=s["id"],
                name=s["name"],
                description=s.get("description"),
                entry_conditions=s["entry_conditions"],
                exit_conditions=s.get("exit_conditions"),
                enabled=s.get("enabled", True),
                scope=s.get("scope", "watchlist"),
                generate_alerts=s.get("generate_alerts", False),
                created_at=_parse_dt(s.get("created_at")),
                last_run=_parse_dt(s.get("last_run")) if s.get("last_run") else None,
                hits_today=s.get("hits_today", 0),
                total_hits=s.get("total_hits", 0),
            )
            session.add(row)
        await session.commit()
        logger.info(f"Seeded {len(rows)} strategies from JSON")
        f.rename(f.with_suffix(".json.migrated"))
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to seed strategies: {e}")


async def _seed_strategy_results(session: AsyncSession) -> None:
    f = DATA_DIR / "strategy_results.json"
    if not f.exists():
        return
    count = await session.scalar(select(func.count()).select_from(StrategyResultRow))
    if count and count > 0:
        return
    try:
        rows = json.loads(f.read_text())
        # Only seed results whose strategy_id exists
        strategy_ids_result = await session.execute(select(StrategyRow.id))
        valid_ids = {r[0] for r in strategy_ids_result.fetchall()}
        seeded = 0
        for r in rows:
            if r.get("strategy_id") not in valid_ids:
                continue
            session.add(StrategyResultRow(
                id=r["id"],
                strategy_id=r["strategy_id"],
                ticker=r["ticker"],
                matched_at=_parse_dt(r["matched_at"]),
                entry_conditions_met=r.get("entry_conditions_met", True),
                exit_conditions_met=r.get("exit_conditions_met", False),
                current_price=r.get("current_price", 0.0),
                indicator_values=r.get("indicator_values", {}),
                signal_strength=r.get("signal_strength", 0.0),
            ))
            seeded += 1
        await session.commit()
        logger.info(f"Seeded {seeded} strategy results from JSON")
        f.rename(f.with_suffix(".json.migrated"))
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to seed strategy results: {e}")


async def _seed_alerts(session: AsyncSession) -> None:
    f = DATA_DIR / "alerts.json"
    if not f.exists():
        return
    count = await session.scalar(select(func.count()).select_from(AlertRow))
    if count and count > 0:
        return
    try:
        rows = json.loads(f.read_text())
        for a in rows:
            session.add(AlertRow(
                id=a["id"],
                ticker=a["ticker"],
                alert_type=a["alert_type"],
                condition=a["condition"],
                enabled=a.get("enabled", True),
                notification_methods=a.get("notification_methods", ["in_app"]),
                created_at=_parse_dt(a["created_at"]),
                last_checked=_parse_dt(a["last_checked"]) if a.get("last_checked") else None,
                triggered_at=_parse_dt(a["triggered_at"]) if a.get("triggered_at") else None,
                trigger_count=a.get("trigger_count", 0),
                message=a.get("message"),
                metadata_=a.get("metadata", {}),
            ))
        await session.commit()
        logger.info(f"Seeded {len(rows)} alerts from JSON")
        f.rename(f.with_suffix(".json.migrated"))
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to seed alerts: {e}")


async def _seed_notifications(session: AsyncSession) -> None:
    f = DATA_DIR / "notifications.json"
    if not f.exists():
        return
    count = await session.scalar(select(func.count()).select_from(NotificationRow))
    if count and count > 0:
        return
    try:
        rows = json.loads(f.read_text())
        alert_ids_result = await session.execute(select(AlertRow.id))
        valid_ids = {r[0] for r in alert_ids_result.fetchall()}
        seeded = 0
        for n in rows:
            if n.get("alert_id") not in valid_ids:
                continue
            session.add(NotificationRow(
                id=n["id"],
                alert_id=n["alert_id"],
                ticker=n["ticker"],
                message=n["message"],
                alert_type=n["alert_type"],
                triggered_at=_parse_dt(n["triggered_at"]),
                read=n.get("read", False),
                data=n.get("data", {}),
            ))
            seeded += 1
        await session.commit()
        logger.info(f"Seeded {seeded} notifications from JSON")
        f.rename(f.with_suffix(".json.migrated"))
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to seed notifications: {e}")


async def _seed_reports(session: AsyncSession) -> None:
    index_file = DATA_DIR / "reports" / "index.json"
    if not index_file.exists():
        return
    count = await session.scalar(select(func.count()).select_from(ReportRow))
    if count and count > 0:
        return
    try:
        rows = json.loads(index_file.read_text())
        seeded = 0
        for r in rows:
            path = Path(r.get("path", ""))
            if not path.exists():
                continue
            session.add(ReportRow(
                id=r["id"],
                type=r["type"],
                ticker=r.get("ticker"),
                generated_at=_parse_dt(r["generated_at"]),
                path=str(path),
                file_size_kb=r.get("file_size_kb"),
                title=r.get("title", ""),
            ))
            seeded += 1
        await session.commit()
        logger.info(f"Seeded {seeded} reports from JSON index")
        index_file.rename(index_file.with_suffix(".json.migrated"))
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to seed reports: {e}")


async def _cleanup_orphaned_reports(session: AsyncSession) -> None:
    """Remove report DB rows whose HTML files no longer exist on disk."""
    try:
        result = await session.execute(select(ReportRow))
        rows = result.scalars().all()
        removed = 0
        for row in rows:
            if not Path(row.path).exists():
                await session.delete(row)
                removed += 1
        if removed:
            await session.commit()
            logger.info(f"Cleaned up {removed} orphaned report entries")
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to cleanup orphaned reports: {e}")


def _parse_dt(value) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
