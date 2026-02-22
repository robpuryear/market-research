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
    - macd_cross: MACD crossover (buy on bullish cross, sell on bearish cross)
    - ma_cross: Moving Average crossover (Golden/Death cross)
    - bb_breakout: Bollinger Band breakout or mean reversion
    - momentum: Multi-indicator momentum (ROC + RSI + volume)
    - multi_factor: Combined signals with scoring system

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

    Returns strategy names with descriptions and configurable parameters.
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
            {
                "name": "macd_cross",
                "display_name": "MACD Crossover",
                "description": "Trend-following strategy using MACD crossovers. Buys on bullish cross, sells on bearish cross.",
                "parameters": []
            },
            {
                "name": "ma_cross",
                "display_name": "Moving Average Crossover",
                "description": "Golden/Death cross strategy using 50-day and 200-day moving averages.",
                "parameters": []
            },
            {
                "name": "bb_breakout",
                "display_name": "Bollinger Band Breakout",
                "description": "Volatility breakout or mean reversion using Bollinger Bands. Default is breakout mode.",
                "parameters": [
                    {"name": "bb_mode", "type": "string", "default": "breakout", "description": "Mode: 'breakout' or 'mean_reversion'"},
                ]
            },
            {
                "name": "momentum",
                "display_name": "Momentum Strategy",
                "description": "Multi-indicator momentum strategy combining ROC, RSI, and volume analysis.",
                "parameters": [
                    {"name": "roc_entry", "type": "float", "default": 5.0, "description": "ROC entry threshold (%)"},
                    {"name": "roc_exit", "type": "float", "default": 0.0, "description": "ROC exit threshold (%)"},
                    {"name": "roc_period", "type": "int", "default": 10, "description": "ROC calculation period"},
                ]
            },
            {
                "name": "multi_factor",
                "display_name": "Multi-Factor Strategy",
                "description": "Combined signals strategy using RSI, MACD, MA trends, Bollinger Bands, and volume with scoring system.",
                "parameters": [
                    {"name": "signal_entry_threshold", "type": "float", "default": 3.0, "description": "Signal score threshold to enter (max 5.0)"},
                    {"name": "signal_exit_threshold", "type": "float", "default": 0.0, "description": "Signal score threshold to exit"},
                ]
            },
        ]
    }
