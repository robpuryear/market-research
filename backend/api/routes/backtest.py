"""
Backtesting API Routes

Endpoints for running backtests and retrieving results.
"""

from fastapi import APIRouter, HTTPException
from models.backtest import BacktestConfig, BacktestResult
from engines.backtest import engine
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])


@router.post("/run", response_model=BacktestResult)
async def run_backtest(config: BacktestConfig):
    """
    Run a backtest with the given configuration.

    Supported strategies:
    - buy_hold: Simple buy-and-hold baseline
    - rsi_reversal: RSI mean reversion (buy oversold, sell overbought)

    Returns complete backtest results with trades and performance metrics.
    """
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


@router.get("/strategies")
async def list_strategies():
    """
    List available backtest strategies.

    Returns strategy names with descriptions.
    """
    return {
        "strategies": [
            {
                "name": "buy_hold",
                "display_name": "Buy and Hold",
                "description": "Simple buy-and-hold baseline strategy. Buys at start and holds until end.",
                "parameters": []
            },
            {
                "name": "rsi_reversal",
                "display_name": "RSI Reversal",
                "description": "Mean reversion strategy using RSI. Buys when oversold, sells when overbought.",
                "parameters": [
                    {"name": "rsi_period", "type": "int", "default": 14, "description": "RSI calculation period"},
                    {"name": "rsi_oversold", "type": "float", "default": 30.0, "description": "Oversold threshold (buy signal)"},
                    {"name": "rsi_overbought", "type": "float", "default": 70.0, "description": "Overbought threshold (sell signal)"},
                ]
            },
        ]
    }
