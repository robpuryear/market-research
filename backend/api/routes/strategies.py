"""
Strategies API Routes

Endpoints for creating and managing trading strategies.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from models.strategy import Strategy, StrategyResult, ConditionGroup
from engines.strategy import strategy_manager, strategy_evaluator
from engines.alerts import alert_manager
from core import watchlist as watchlist_module, stock_universe
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


class CreateStrategyRequest(BaseModel):
    """Request body for creating a strategy"""
    name: str
    description: Optional[str] = None
    entry_conditions: ConditionGroup
    exit_conditions: Optional[ConditionGroup] = None
    enabled: bool = True
    scope: str = "watchlist"  # "watchlist" | "market"
    generate_alerts: bool = False


@router.get("/", response_model=List[Strategy])
async def get_strategies():
    """
    Get all strategies.

    Returns list of all strategies (enabled and disabled).
    """
    try:
        return strategy_manager.get_all_strategies()
    except Exception as e:
        logger.error(f"Failed to get strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=Strategy)
async def create_strategy(req: CreateStrategyRequest):
    """
    Create a new strategy.

    Request body:
    - name: Strategy name
    - description: Optional description
    - entry_conditions: Condition group for entry signals
    - exit_conditions: Optional condition group for exit signals
    - enabled: Whether strategy is active (default: true)
    - scope: "watchlist" or "market" (default: "watchlist")
    - generate_alerts: Auto-create alerts when strategy matches (default: false)
    """
    try:
        return strategy_manager.create_strategy(req.model_dump())
    except Exception as e:
        logger.error(f"Failed to create strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}", response_model=Strategy)
async def get_strategy(strategy_id: str):
    """Get strategy by ID"""
    strategy = strategy_manager.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.patch("/{strategy_id}", response_model=Strategy)
async def update_strategy(strategy_id: str, updates: dict):
    """
    Update a strategy.

    Common updates:
    - {"enabled": false} - Disable strategy
    - {"enabled": true} - Re-enable strategy
    - {"entry_conditions": {...}} - Update entry conditions
    - {"generate_alerts": true} - Enable alert generation
    """
    strategy = strategy_manager.update_strategy(strategy_id, updates)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strategy


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """Delete a strategy"""
    success = strategy_manager.delete_strategy(strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {"status": "deleted", "strategy_id": strategy_id}


@router.post("/{strategy_id}/run", response_model=List[StrategyResult])
async def run_strategy(strategy_id: str):
    """
    Run a strategy now.

    Executes the strategy against tickers based on its scope:
    - "watchlist": Scans user's watchlist
    - "market": Scans full market (stock universe)

    Returns list of matching results.
    """
    try:
        strategy = strategy_manager.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        # Get tickers based on scope
        if strategy.scope == "watchlist":
            tickers = [item["ticker"] for item in watchlist_module.get_all()]
        else:  # market
            tickers = stock_universe.get_all_tickers()

        if not tickers:
            return []

        # Run strategy scan
        results = await strategy_evaluator.run_strategy_scan(strategy, tickers)

        # Generate alerts if configured
        if strategy.generate_alerts:
            for result in results:
                try:
                    # Create alert for each match
                    alert_data = {
                        "ticker": result.ticker,
                        "alert_type": "signal",
                        "condition": {
                            "signal_type": "strategy",
                            "operator": "fired",
                            "threshold": None,
                            "direction": None
                        },
                        "message": f"Strategy '{strategy.name}' matched (signal strength: {result.signal_strength})"
                    }
                    alert_manager.create_alert(alert_data)
                except Exception as e:
                    logger.error(f"Failed to create alert for {result.ticker}: {e}")

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to run strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{strategy_id}/results", response_model=List[StrategyResult])
async def get_strategy_results(strategy_id: str, limit: int = 100):
    """
    Get historical results for a strategy.

    Query params:
    - limit: Max number of results to return (default 100)
    """
    try:
        # Verify strategy exists
        strategy = strategy_manager.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")

        return strategy_manager.get_results(strategy_id, limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get results for strategy {strategy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/recent", response_model=List[StrategyResult])
async def get_recent_results(limit: int = 50):
    """
    Get recent results across all strategies.

    Query params:
    - limit: Max number of results to return (default 50)
    """
    try:
        return strategy_manager.get_recent_results(limit)
    except Exception as e:
        logger.error(f"Failed to get recent results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{strategy_id}/backtest")
async def backtest_strategy(strategy_id: str):
    """
    Backtest a strategy on historical data.

    TODO: Integration with backtest engine.
    This endpoint is a placeholder for future backtest functionality.
    """
    strategy = strategy_manager.get_strategy(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # TODO: Convert strategy to backtest config and run backtest
    raise HTTPException(status_code=501, detail="Backtest integration not yet implemented")
