"""
Portfolio API Routes

Endpoints for managing portfolio positions and viewing performance.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from models.portfolio import Position, Transaction, PortfolioMetrics
from engines.portfolio import positions, metrics
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class AddPositionRequest(BaseModel):
    """Request body for adding a position"""
    ticker: str
    quantity: float
    price: float
    date: str  # YYYY-MM-DD
    notes: Optional[str] = None


class SellPositionRequest(BaseModel):
    """Request body for selling a position"""
    quantity: float
    price: float
    date: str  # YYYY-MM-DD
    notes: Optional[str] = None


class UpdatePositionRequest(BaseModel):
    """Request body for updating a position"""
    notes: Optional[str] = None


@router.get("/positions", response_model=List[Position])
async def get_positions(include_closed: bool = False):
    """
    Get all portfolio positions.

    Query params:
    - include_closed: If true, include closed positions (default: false)

    Returns positions with current prices and unrealized P&L.
    """
    try:
        return positions.get_all_positions(include_closed)
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions/{position_id}", response_model=Position)
async def get_position(position_id: str):
    """Get a single position by ID"""
    position = positions.get_position(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.post("/positions", response_model=Position)
async def add_position(req: AddPositionRequest):
    """
    Add a new position or add to existing position.

    If a position for the ticker already exists, this will average up/down.

    Request body:
    - ticker: Stock symbol
    - quantity: Number of shares
    - price: Price per share
    - date: Transaction date (YYYY-MM-DD)
    - notes: Optional notes
    """
    try:
        return positions.add_position(
            ticker=req.ticker.upper(),
            quantity=req.quantity,
            price=req.price,
            date=req.date,
            notes=req.notes
        )
    except Exception as e:
        logger.error(f"Failed to add position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/positions/{position_id}/sell", response_model=Position)
async def sell_position(position_id: str, req: SellPositionRequest):
    """
    Sell part or all of a position.

    Request body:
    - quantity: Number of shares to sell
    - price: Sell price per share
    - date: Transaction date (YYYY-MM-DD)
    - notes: Optional notes

    If quantity equals total shares, position will be closed.
    """
    try:
        return positions.sell_position(
            position_id=position_id,
            quantity=req.quantity,
            price=req.price,
            date=req.date,
            notes=req.notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to sell position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/positions/{position_id}", response_model=Position)
async def update_position(position_id: str, req: UpdatePositionRequest):
    """Update position fields (notes, etc.)"""
    try:
        updates = {}
        if req.notes is not None:
            updates["notes"] = req.notes

        position = positions.update_position(position_id, updates)
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")

        return position
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/positions/{position_id}")
async def delete_position(position_id: str):
    """
    Delete a position.

    WARNING: This is for admin/cleanup only.
    To close a position, use the sell endpoint instead.
    """
    try:
        success = positions.delete_position(position_id)
        if not success:
            raise HTTPException(status_code=404, detail="Position not found")

        return {"status": "deleted", "position_id": position_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=PortfolioMetrics)
async def get_portfolio_metrics(cash: float = 0.0):
    """
    Get portfolio performance metrics.

    Query params:
    - cash: Cash balance (default: 0.0)

    Returns comprehensive metrics including P&L, win rate, and allocation.
    """
    try:
        return metrics.calculate_portfolio_metrics(cash)
    except Exception as e:
        logger.error(f"Failed to calculate metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_model=List[Transaction])
async def get_transactions(position_id: Optional[str] = None):
    """
    Get transaction history.

    Query params:
    - position_id: Filter by position ID (optional)

    Returns all buy/sell transactions.
    """
    try:
        return positions.get_transactions(position_id)
    except Exception as e:
        logger.error(f"Failed to get transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
