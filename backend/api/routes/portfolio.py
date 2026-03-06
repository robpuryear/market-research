"""
Portfolio API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from models.portfolio import Position, Transaction, PortfolioMetrics
from engines.portfolio import positions, metrics
from db.session import get_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class AddPositionRequest(BaseModel):
    ticker: str
    quantity: float
    price: float
    date: str
    notes: Optional[str] = None


class SellPositionRequest(BaseModel):
    quantity: float
    price: float
    date: str
    notes: Optional[str] = None


class UpdatePositionRequest(BaseModel):
    notes: Optional[str] = None


@router.get("/positions", response_model=List[Position])
async def get_positions(
    include_closed: bool = False,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await positions.get_all_positions(session, include_closed)
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions/{position_id}", response_model=Position)
async def get_position(
    position_id: str,
    session: AsyncSession = Depends(get_session),
):
    position = await positions.get_position(session, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.post("/positions", response_model=Position)
async def add_position(
    req: AddPositionRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await positions.add_position(
            session,
            ticker=req.ticker.upper(),
            quantity=req.quantity,
            price=req.price,
            date=req.date,
            notes=req.notes,
        )
    except Exception as e:
        logger.error(f"Failed to add position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/positions/{position_id}/sell", response_model=Position)
async def sell_position(
    position_id: str,
    req: SellPositionRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await positions.sell_position(
            session,
            position_id=position_id,
            quantity=req.quantity,
            price=req.price,
            date=req.date,
            notes=req.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to sell position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/positions/{position_id}", response_model=Position)
async def update_position(
    position_id: str,
    req: UpdatePositionRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        updates = {}
        if req.notes is not None:
            updates["notes"] = req.notes
        position = await positions.update_position(session, position_id, updates)
        if not position:
            raise HTTPException(status_code=404, detail="Position not found")
        return position
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/positions/{position_id}")
async def delete_position(
    position_id: str,
    session: AsyncSession = Depends(get_session),
):
    try:
        success = await positions.delete_position(session, position_id)
        if not success:
            raise HTTPException(status_code=404, detail="Position not found")
        return {"status": "deleted", "position_id": position_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=PortfolioMetrics)
async def get_portfolio_metrics(
    cash: float = 0.0,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await metrics.calculate_portfolio_metrics(session, cash)
    except Exception as e:
        logger.error(f"Failed to calculate metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_model=List[Transaction])
async def get_transactions(
    position_id: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await positions.get_transactions(session, position_id)
    except Exception as e:
        logger.error(f"Failed to get transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
