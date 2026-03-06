"""
Strategy Manager - PostgreSQL-backed CRUD for strategies and results.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import StrategyRow, StrategyResultRow
from models.strategy import Strategy, StrategyResult

logger = logging.getLogger(__name__)


def _strategy_row_to_model(row: StrategyRow) -> Strategy:
    return Strategy(
        id=row.id,
        name=row.name,
        description=row.description,
        entry_conditions=row.entry_conditions,
        exit_conditions=row.exit_conditions,
        enabled=row.enabled,
        scope=row.scope,
        generate_alerts=row.generate_alerts,
        created_at=row.created_at,
        last_run=row.last_run,
        hits_today=row.hits_today,
        total_hits=row.total_hits,
    )


def _result_row_to_model(row: StrategyResultRow) -> StrategyResult:
    return StrategyResult(
        id=row.id,
        strategy_id=row.strategy_id,
        ticker=row.ticker,
        matched_at=row.matched_at,
        entry_conditions_met=row.entry_conditions_met,
        exit_conditions_met=row.exit_conditions_met,
        current_price=row.current_price,
        indicator_values=row.indicator_values,
        signal_strength=row.signal_strength,
    )


async def create_strategy(session: AsyncSession, strategy_data: dict) -> Strategy:
    strategy_data.pop("id", None)
    strategy_data.pop("created_at", None)
    entry = strategy_data.pop("entry_conditions")
    exit_conds = strategy_data.pop("exit_conditions", None)
    row = StrategyRow(
        id=str(uuid.uuid4()),
        created_at=datetime.now(timezone.utc),
        name=strategy_data["name"],
        description=strategy_data.get("description"),
        entry_conditions=entry.model_dump() if hasattr(entry, "model_dump") else entry,
        exit_conditions=exit_conds.model_dump() if hasattr(exit_conds, "model_dump") else exit_conds,
        enabled=strategy_data.get("enabled", True),
        scope=strategy_data.get("scope", "watchlist"),
        generate_alerts=strategy_data.get("generate_alerts", False),
    )
    session.add(row)
    await session.commit()
    logger.info(f"Created strategy {row.id}: {row.name}")
    return _strategy_row_to_model(row)


async def get_all_strategies(session: AsyncSession) -> List[Strategy]:
    result = await session.execute(select(StrategyRow))
    return [_strategy_row_to_model(r) for r in result.scalars().all()]


async def get_strategy(session: AsyncSession, strategy_id: str) -> Optional[Strategy]:
    row = await session.get(StrategyRow, strategy_id)
    return _strategy_row_to_model(row) if row else None


async def update_strategy(session: AsyncSession, strategy_id: str, updates: dict) -> Optional[Strategy]:
    row = await session.get(StrategyRow, strategy_id)
    if not row:
        return None
    for field in ("name", "description", "enabled", "scope", "generate_alerts"):
        if field in updates:
            setattr(row, field, updates[field])
    if "entry_conditions" in updates:
        val = updates["entry_conditions"]
        row.entry_conditions = val.model_dump() if hasattr(val, "model_dump") else val
    if "exit_conditions" in updates:
        val = updates["exit_conditions"]
        row.exit_conditions = val.model_dump() if hasattr(val, "model_dump") else val
    await session.commit()
    logger.info(f"Updated strategy {strategy_id}")
    return _strategy_row_to_model(row)


async def delete_strategy(session: AsyncSession, strategy_id: str) -> bool:
    row = await session.get(StrategyRow, strategy_id)
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    logger.info(f"Deleted strategy {strategy_id}")
    return True


async def save_result(session: AsyncSession, result: StrategyResult) -> None:
    row = StrategyResultRow(
        id=result.id,
        strategy_id=result.strategy_id,
        ticker=result.ticker,
        matched_at=result.matched_at,
        entry_conditions_met=result.entry_conditions_met,
        exit_conditions_met=result.exit_conditions_met,
        current_price=result.current_price,
        indicator_values=result.indicator_values,
        signal_strength=result.signal_strength,
    )
    session.add(row)
    await session.commit()
    logger.info(f"Saved result for strategy {result.strategy_id}: {result.ticker}")


async def get_results(
    session: AsyncSession,
    strategy_id: str,
    limit: int = 100,
) -> List[StrategyResult]:
    result = await session.execute(
        select(StrategyResultRow)
        .where(StrategyResultRow.strategy_id == strategy_id)
        .order_by(desc(StrategyResultRow.matched_at))
        .limit(limit)
    )
    return [_result_row_to_model(r) for r in result.scalars().all()]


async def get_recent_results(session: AsyncSession, limit: int = 50) -> List[StrategyResult]:
    result = await session.execute(
        select(StrategyResultRow)
        .order_by(desc(StrategyResultRow.matched_at))
        .limit(limit)
    )
    return [_result_row_to_model(r) for r in result.scalars().all()]


async def increment_strategy_hits(
    session: AsyncSession,
    strategy_id: str,
    count: int = 1,
) -> None:
    row = await session.get(StrategyRow, strategy_id)
    if row:
        row.hits_today = (row.hits_today or 0) + count
        row.total_hits = (row.total_hits or 0) + count
        row.last_run = datetime.now(timezone.utc)
        await session.commit()


async def reset_daily_hits(session: AsyncSession) -> None:
    await session.execute(update(StrategyRow).values(hits_today=0))
    await session.commit()
    logger.info("Reset daily hits for all strategies")
