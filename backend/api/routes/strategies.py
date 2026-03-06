"""
Strategies API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from models.strategy import Strategy, StrategyResult, ConditionGroup
from engines.strategy import strategy_manager, strategy_evaluator
from engines.alerts import alert_manager
from core import watchlist_manager, stock_universe
from db.session import get_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


class CreateStrategyRequest(BaseModel):
    name: str
    description: Optional[str] = None
    entry_conditions: ConditionGroup
    exit_conditions: Optional[ConditionGroup] = None
    enabled: bool = True
    scope: str = "watchlist"
    generate_alerts: bool = False


@router.get("/", response_model=List[Strategy])
async def get_strategies(session: AsyncSession = Depends(get_session)):
    try:
        return await strategy_manager.get_all_strategies(session)
    except Exception as e:
        logger.error(f"Failed to get strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Strategy)
async def create_strategy(
    req: CreateStrategyRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await strategy_manager.create_strategy(session, req.model_dump())
    except Exception as e:
        logger.error(f"Failed to create strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}", response_model=Strategy)
async def get_strategy(strategy_id: str, session: AsyncSession = Depends(get_session)):
    strategy = await strategy_manager.get_strategy(session, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.patch("/{strategy_id}", response_model=Strategy)
async def update_strategy(
    strategy_id: str,
    updates: dict,
    session: AsyncSession = Depends(get_session),
):
    strategy = await strategy_manager.update_strategy(session, strategy_id, updates)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: str, session: AsyncSession = Depends(get_session)):
    success = await strategy_manager.delete_strategy(session, strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {"status": "deleted", "strategy_id": strategy_id}


@router.post("/{strategy_id}/run", response_model=List[StrategyResult])
async def run_strategy(
    strategy_id: str,
    session: AsyncSession = Depends(get_session),
):
    try:
        strategy = await strategy_manager.get_strategy(session, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        if strategy.scope == "watchlist":
            tickers = watchlist_manager.get_tickers()
        else:
            tickers = stock_universe.get_all_tickers()

        if not tickers:
            return []

        results = await strategy_evaluator.run_strategy_scan(strategy, tickers, session)

        if strategy.generate_alerts:
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

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/recent", response_model=List[StrategyResult])
async def get_recent_results(
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    try:
        return await strategy_manager.get_recent_results(session, limit)
    except Exception as e:
        logger.error(f"Failed to get recent results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}/results", response_model=List[StrategyResult])
async def get_strategy_results(
    strategy_id: str,
    limit: int = 100,
    session: AsyncSession = Depends(get_session),
):
    try:
        strategy = await strategy_manager.get_strategy(session, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return await strategy_manager.get_results(session, strategy_id, limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results for strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/backtest")
async def backtest_strategy(strategy_id: str, session: AsyncSession = Depends(get_session)):
    strategy = await strategy_manager.get_strategy(session, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    raise HTTPException(status_code=501, detail="Backtest integration not yet implemented")
