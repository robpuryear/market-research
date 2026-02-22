"""
Position Manager - CRUD for portfolio positions

Stores positions in data/positions.json and transactions in data/transactions.json
"""

import json
import os
from typing import List, Optional
from models.portfolio import Position, Transaction
from datetime import datetime, timezone
import uuid
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

POSITIONS_FILE = "data/positions.json"
TRANSACTIONS_FILE = "data/transactions.json"


def add_position(ticker: str, quantity: float, price: float, date: str, notes: Optional[str] = None) -> Position:
    """Add a new position or add to existing position"""
    positions = _load_positions()

    # Check if position already exists
    existing = next((p for p in positions if p["ticker"] == ticker and p["status"] == "open"), None)

    if existing:
        # Average up/down
        old_cost = existing["avg_cost_basis"] * existing["quantity"]
        new_cost = price * quantity
        total_quantity = existing["quantity"] + quantity
        new_avg = (old_cost + new_cost) / total_quantity

        existing["quantity"] = total_quantity
        existing["avg_cost_basis"] = new_avg
        existing["last_updated"] = datetime.now(timezone.utc).isoformat()

        position = Position(**existing)
        position_id = existing["id"]
    else:
        # New position
        position = Position(
            id=str(uuid.uuid4()),
            ticker=ticker.upper(),
            quantity=quantity,
            avg_cost_basis=price,
            entry_date=date,
            last_updated=datetime.now(timezone.utc),
            notes=notes,
            status="open"
        )
        positions.append(position.model_dump())
        position_id = position.id

    _save_positions(positions)

    # Record transaction
    record_transaction(
        position_id=position_id,
        ticker=ticker.upper(),
        transaction_type="buy",
        quantity=quantity,
        price=price,
        date=date,
        notes=notes
    )

    logger.info(f"Added {quantity} shares of {ticker} at ${price}")
    return position


def sell_position(position_id: str, quantity: float, price: float, date: str, notes: Optional[str] = None) -> Position:
    """Sell part or all of a position"""
    positions = _load_positions()

    for i, p in enumerate(positions):
        if p["id"] == position_id:
            if quantity > p["quantity"]:
                raise ValueError(f"Cannot sell {quantity} shares - only {p['quantity']} owned")

            p["quantity"] -= quantity
            p["last_updated"] = datetime.now(timezone.utc).isoformat()

            if p["quantity"] == 0:
                p["status"] = "closed"

            _save_positions(positions)

            # Record transaction
            record_transaction(
                position_id=position_id,
                ticker=p["ticker"],
                transaction_type="sell",
                quantity=quantity,
                price=price,
                date=date,
                notes=notes
            )

            logger.info(f"Sold {quantity} shares of {p['ticker']} at ${price}")
            return Position(**p)

    raise ValueError(f"Position {position_id} not found")


def update_position(position_id: str, updates: dict) -> Optional[Position]:
    """Update position fields (notes, etc.)"""
    positions = _load_positions()

    for i, p in enumerate(positions):
        if p["id"] == position_id:
            p.update(updates)
            p["last_updated"] = datetime.now(timezone.utc).isoformat()
            _save_positions(positions)
            logger.info(f"Updated position {position_id}")
            return Position(**p)

    return None


def delete_position(position_id: str) -> bool:
    """Delete a position (admin only - not for closing positions)"""
    positions = _load_positions()
    filtered = [p for p in positions if p["id"] != position_id]

    if len(filtered) < len(positions):
        _save_positions(filtered)
        logger.info(f"Deleted position {position_id}")
        return True

    return False


def get_all_positions(include_closed: bool = False) -> List[Position]:
    """Get all positions with current prices"""
    positions = _load_positions()

    if not include_closed:
        positions = [p for p in positions if p["status"] == "open"]

    # Enrich with current prices
    enriched = []
    for p in positions:
        pos = Position(**p)

        # Fetch current price
        if pos.status == "open":
            try:
                stock = yf.Ticker(pos.ticker)
                info = stock.info or {}
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')

                # Fallback to history
                if not current_price:
                    hist = stock.history(period="1d")
                    if not hist.empty:
                        current_price = float(hist['Close'].iloc[-1])

                if current_price:
                    pos.current_price = float(current_price)
                    pos.current_value = current_price * pos.quantity
                    cost_basis_total = pos.avg_cost_basis * pos.quantity
                    pos.unrealized_pnl = pos.current_value - cost_basis_total
                    pos.unrealized_pnl_pct = (pos.unrealized_pnl / cost_basis_total) * 100 if cost_basis_total > 0 else 0

                    # Days held
                    entry = datetime.fromisoformat(pos.entry_date)
                    pos.days_held = (datetime.now(timezone.utc) - entry).days

            except Exception as e:
                logger.warning(f"Failed to fetch price for {pos.ticker}: {e}")

        enriched.append(pos)

    return enriched


def get_position(position_id: str) -> Optional[Position]:
    """Get a single position by ID"""
    positions = get_all_positions(include_closed=True)
    return next((p for p in positions if p.id == position_id), None)


def record_transaction(position_id: str, ticker: str, transaction_type: str,
                       quantity: float, price: float, date: str,
                       commission: float = 0.0, notes: Optional[str] = None) -> Transaction:
    """Record a transaction"""
    transactions = _load_transactions()

    txn = Transaction(
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
        notes=notes
    )

    transactions.append(txn.model_dump())
    _save_transactions(transactions)

    return txn


def get_transactions(position_id: Optional[str] = None) -> List[Transaction]:
    """Get transaction history"""
    transactions = _load_transactions()

    if position_id:
        transactions = [t for t in transactions if t["position_id"] == position_id]

    return [Transaction(**t) for t in transactions]


def _load_positions() -> list:
    """Load positions from JSON file"""
    if not os.path.exists(POSITIONS_FILE):
        return []
    try:
        with open(POSITIONS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading positions: {e}")
        return []


def _save_positions(positions: list):
    """Save positions to JSON file"""
    try:
        os.makedirs(os.path.dirname(POSITIONS_FILE), exist_ok=True)
        with open(POSITIONS_FILE, "w") as f:
            json.dump(positions, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving positions: {e}")


def _load_transactions() -> list:
    """Load transactions from JSON file"""
    if not os.path.exists(TRANSACTIONS_FILE):
        return []
    try:
        with open(TRANSACTIONS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading transactions: {e}")
        return []


def _save_transactions(transactions: list):
    """Save transactions to JSON file"""
    try:
        os.makedirs(os.path.dirname(TRANSACTIONS_FILE), exist_ok=True)
        with open(TRANSACTIONS_FILE, "w") as f:
            json.dump(transactions, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving transactions: {e}")
