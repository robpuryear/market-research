"""
Backtesting API Routes
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from models.backtest import BacktestConfig, BacktestResult, BacktestSummary
from engines.backtest import engine
from db.base import BacktestResultRow
from db.session import get_session
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.post("/run", response_model=BacktestResult)
async def run_backtest(config: BacktestConfig):
    try:
        logger.info(f"Running backtest: {config.strategy_type} on {config.ticker}")
        result = await engine.run_backtest(config)
        return result
    except ValueError as e:
        logger.error(f"Backtest validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.get("/results", response_model=List[BacktestSummary])
async def list_backtest_results(
    ticker: str = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
):
    """List saved backtest results (summary only, no full equity curves)."""
    q = select(BacktestResultRow).order_by(desc(BacktestResultRow.timestamp)).limit(limit)
    if ticker:
        q = q.where(BacktestResultRow.ticker == ticker.upper())
    result = await session.execute(q)
    rows = result.scalars().all()
    return [
        BacktestSummary(
            id=r.id,
            strategy_type=r.strategy_type,
            ticker=r.ticker,
            start_date=r.start_date,
            end_date=r.end_date,
            total_return=r.total_return,
            sharpe_ratio=r.sharpe_ratio,
            max_drawdown=r.max_drawdown,
            total_trades=r.total_trades,
            timestamp=r.timestamp,
        )
        for r in rows
    ]


@router.get("/results/{result_id}", response_model=BacktestResult)
async def get_backtest_result(
    result_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get full backtest result by ID."""
    row = await session.get(BacktestResultRow, result_id)
    if not row:
        raise HTTPException(status_code=404, detail="Backtest result not found")
    return BacktestResult(**row.result_json)


@router.get("/strategies")
async def list_strategies():
    return {
        "strategies": [
            {"name": "buy_hold", "display_name": "Buy and Hold", "description": "Simple buy-and-hold baseline strategy.", "parameters": []},
            {"name": "rsi_reversal", "display_name": "RSI Reversal", "description": "Mean reversion using RSI.", "parameters": [
                {"name": "rsi_period", "type": "int", "default": 14},
                {"name": "rsi_oversold", "type": "float", "default": 30.0},
                {"name": "rsi_overbought", "type": "float", "default": 70.0},
            ]},
            {"name": "macd_cross", "display_name": "MACD Crossover", "description": "Trend-following using MACD crossovers.", "parameters": []},
            {"name": "ma_cross", "display_name": "Moving Average Crossover", "description": "Golden/Death cross using 50 and 200-day MAs.", "parameters": []},
            {"name": "bb_breakout", "display_name": "Bollinger Band Breakout", "description": "Volatility breakout using Bollinger Bands.", "parameters": [
                {"name": "bb_mode", "type": "string", "default": "breakout"},
            ]},
            {"name": "momentum", "display_name": "Momentum Strategy", "description": "Multi-indicator momentum (ROC + RSI + volume).", "parameters": [
                {"name": "roc_entry", "type": "float", "default": 5.0},
                {"name": "roc_exit", "type": "float", "default": 0.0},
                {"name": "roc_period", "type": "int", "default": 10},
            ]},
            {"name": "multi_factor", "display_name": "Multi-Factor Strategy", "description": "Combined signals with scoring system.", "parameters": [
                {"name": "signal_entry_threshold", "type": "float", "default": 3.0},
                {"name": "signal_exit_threshold", "type": "float", "default": 0.0},
            ]},
        ]
    }
