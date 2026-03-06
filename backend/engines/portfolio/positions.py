"""
Position Manager - PostgreSQL-backed CRUD for portfolio positions.
"""

from datetime import datetime, timezone
from typing import List, Optional
import uuid
import logging

import yfinance as yf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import PositionRow, TransactionRow
from models.portfolio import Position, Transaction

logger = logging.getLogger(__name__)


def _pos_row_to_model(row: PositionRow) -> Position:
    return Position(
        id=row.id,
        ticker=row.ticker,
        quantity=row.quantity,
        avg_cost_basis=row.avg_cost_basis,
        entry_date=row.entry_date,
        last_updated=row.last_updated,
        notes=row.notes,
        status=row.status,
    )


def _txn_row_to_model(row: TransactionRow) -> Transaction:
    return Transaction(
        id=row.id,
        position_id=row.position_id,
        ticker=row.ticker,
        transaction_type=row.transaction_type,
        quantity=row.quantity,
        price=row.price,
        total_value=row.total_value,
        commission=row.commission,
        date=row.date,
        timestamp=row.timestamp,
        notes=row.notes,
    )


async def add_position(
    session: AsyncSession,
    ticker: str,
    quantity: float,
    price: float,
    date: str,
    notes: Optional[str] = None,
) -> Position:
    """Add a new position or average up/down an existing one."""
    result = await session.execute(
        select(PositionRow)
        .where(PositionRow.ticker == ticker.upper())
        .where(PositionRow.status == "open")
    )
    existing = result.scalar_one_or_none()

    if existing:
        old_cost = existing.avg_cost_basis * existing.quantity
        new_cost = price * quantity
        total_qty = existing.quantity + quantity
        existing.avg_cost_basis = (old_cost + new_cost) / total_qty
        existing.quantity = total_qty
        existing.last_updated = datetime.now(timezone.utc)
        position_id = existing.id
    else:
        position_id = str(uuid.uuid4())
        session.add(PositionRow(
            id=position_id,
            ticker=ticker.upper(),
            quantity=quantity,
            avg_cost_basis=price,
            entry_date=date,
            last_updated=datetime.now(timezone.utc),
            notes=notes,
            status="open",
        ))

    await session.flush()

    await _record_transaction(
        session, position_id=position_id, ticker=ticker.upper(),
        transaction_type="buy", quantity=quantity, price=price,
        date=date, notes=notes,
    )
    await session.commit()

    updated = await session.get(PositionRow, position_id)
    pos = _pos_row_to_model(updated)
    logger.info(f"Added {quantity} shares of {ticker} at ${price}")
    return pos


async def sell_position(
    session: AsyncSession,
    position_id: str,
    quantity: float,
    price: float,
    date: str,
    notes: Optional[str] = None,
) -> Position:
    """Sell part or all of a position."""
    row = await session.get(PositionRow, position_id)
    if not row:
        raise ValueError(f"Position {position_id} not found")
    if quantity > row.quantity:
        raise ValueError(f"Cannot sell {quantity} shares — only {row.quantity} owned")

    row.quantity -= quantity
    row.last_updated = datetime.now(timezone.utc)
    if row.quantity == 0:
        row.status = "closed"

    await _record_transaction(
        session, position_id=position_id, ticker=row.ticker,
        transaction_type="sell", quantity=quantity, price=price,
        date=date, notes=notes,
    )
    await session.commit()

    updated = await session.get(PositionRow, position_id)
    logger.info(f"Sold {quantity} shares of {row.ticker} at ${price}")
    return _pos_row_to_model(updated)


async def update_position(
    session: AsyncSession,
    position_id: str,
    updates: dict,
) -> Optional[Position]:
    """Update position fields (notes, etc.)"""
    row = await session.get(PositionRow, position_id)
    if not row:
        return None
    if "notes" in updates:
        row.notes = updates["notes"]
    row.last_updated = datetime.now(timezone.utc)
    await session.commit()
    logger.info(f"Updated position {position_id}")
    return _pos_row_to_model(row)


async def delete_position(session: AsyncSession, position_id: str) -> bool:
    """Delete a position (admin only)."""
    row = await session.get(PositionRow, position_id)
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    logger.info(f"Deleted position {position_id}")
    return True


async def get_all_positions(
    session: AsyncSession,
    include_closed: bool = False,
) -> List[Position]:
    """Get all positions with current prices fetched from yfinance."""
    q = select(PositionRow)
    if not include_closed:
        q = q.where(PositionRow.status == "open")
    result = await session.execute(q)
    rows = result.scalars().all()

    enriched = []
    for row in rows:
        pos = _pos_row_to_model(row)
        if pos.status == "open":
            try:
                stock = yf.Ticker(pos.ticker)
                info = stock.info or {}
                current_price = info.get("currentPrice") or info.get("regularMarketPrice")
                if not current_price:
                    hist = stock.history(period="1d")
                    if not hist.empty:
                        current_price = float(hist["Close"].iloc[-1])
                if current_price:
                    pos.current_price = float(current_price)
                    pos.current_value = current_price * pos.quantity
                    cost_basis_total = pos.avg_cost_basis * pos.quantity
                    pos.unrealized_pnl = pos.current_value - cost_basis_total
                    pos.unrealized_pnl_pct = (
                        (pos.unrealized_pnl / cost_basis_total) * 100
                        if cost_basis_total > 0 else 0
                    )
                    entry = datetime.fromisoformat(pos.entry_date)
                    pos.days_held = (datetime.now(timezone.utc) - entry).days
            except Exception as e:
                logger.warning(f"Failed to fetch price for {pos.ticker}: {e}")
        enriched.append(pos)

    return enriched


async def get_position(session: AsyncSession, position_id: str) -> Optional[Position]:
    """Get a single position by ID (with live price)."""
    positions = await get_all_positions(session, include_closed=True)
    return next((p for p in positions if p.id == position_id), None)


async def _record_transaction(
    session: AsyncSession,
    position_id: str,
    ticker: str,
    transaction_type: str,
    quantity: float,
    price: float,
    date: str,
    commission: float = 0.0,
    notes: Optional[str] = None,
) -> Transaction:
    txn = TransactionRow(
        id=str(uuid.uuid4()),
        position_id=position_id,
        ticker=ticker.upper(),
        transaction_type=transaction_type,
        quantity=quantity,
        price=price,
        total_value=quantity * price,
        commission=commission,
        date=date,
        timestamp=datetime.now(timezone.utc),
        notes=notes,
    )
    session.add(txn)
    return txn


async def get_transactions(
    session: AsyncSession,
    position_id: Optional[str] = None,
) -> List[Transaction]:
    """Get transaction history, optionally filtered by position."""
    q = select(TransactionRow)
    if position_id:
        q = q.where(TransactionRow.position_id == position_id)
    result = await session.execute(q)
    return [_txn_row_to_model(r) for r in result.scalars().all()]


async def load_all_transactions(session: AsyncSession) -> List[dict]:
    """Load all transactions as dicts (used by metrics FIFO calculation)."""
    result = await session.execute(select(TransactionRow))
    return [
        {
            "ticker": r.ticker,
            "transaction_type": r.transaction_type,
            "quantity": r.quantity,
            "price": r.price,
            "commission": r.commission,
            "date": r.date,
        }
        for r in result.scalars().all()
    ]
