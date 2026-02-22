"""
Options API Routes

Endpoints for options chain, Greeks, analytics, and spreads.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import logging

from models.options import (
    OptionsChain,
    OptionsAnalytics,
    ExpirationDate,
    SpreadLeg,
    SpreadAnalysis,
)
from engines.options import chain as options_engine
from engines.options import spreads as spreads_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/options", tags=["options"])


@router.get("/chain/{ticker}", response_model=OptionsChain)
async def get_options_chain(
    ticker: str,
    expiration: Optional[str] = Query(None, description="Expiration date (YYYY-MM-DD). If not provided, uses nearest expiration.")
):
    """
    Get options chain for a ticker and expiration.

    Returns calls and puts with full Greeks and pricing data.
    """
    try:
        ticker = ticker.upper()
        logger.info(f"Fetching options chain for {ticker}, expiration: {expiration or 'nearest'}")

        chain = await options_engine.fetch_options_chain(ticker, expiration)

        if not chain:
            raise HTTPException(
                status_code=404,
                detail=f"No options chain found for {ticker}"
            )

        return chain

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch options chain for {ticker}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch options chain: {str(e)}"
        )


@router.get("/expirations/{ticker}", response_model=list[ExpirationDate])
async def get_expirations(ticker: str):
    """
    Get available expiration dates for a ticker.

    Returns list of expiration dates with metadata (weekly, monthly, quarterly).
    """
    try:
        ticker = ticker.upper()
        logger.info(f"Fetching expirations for {ticker}")

        expirations = await options_engine.fetch_expirations(ticker)

        if not expirations:
            raise HTTPException(
                status_code=404,
                detail=f"No options expirations found for {ticker}"
            )

        return expirations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch expirations for {ticker}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch expirations: {str(e)}"
        )


@router.get("/analytics/{ticker}", response_model=OptionsAnalytics)
async def get_options_analytics(ticker: str):
    """
    Get options analytics for a ticker.

    Includes IV rank, max pain, put/call ratios, and volatility metrics.
    """
    try:
        ticker = ticker.upper()
        logger.info(f"Fetching options analytics for {ticker}")

        analytics = await options_engine.fetch_options_analytics(ticker)

        if not analytics:
            raise HTTPException(
                status_code=404,
                detail=f"No options analytics found for {ticker}"
            )

        return analytics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch options analytics for {ticker}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch options analytics: {str(e)}"
        )


class SpreadRequest(BaseModel):
    ticker: str
    spot_price: float
    legs: List[SpreadLeg]
    spread_type: Optional[str] = None


@router.post("/spread/analyze", response_model=SpreadAnalysis)
async def analyze_spread(request: SpreadRequest):
    """
    Analyze an options spread strategy.

    Calculates max profit/loss, breakeven points, P/L diagram, and Greeks.

    Supported spreads:
    - Vertical spreads (bull call, bear put, etc.)
    - Iron condor
    - Butterflies
    - Custom multi-leg strategies
    """
    try:
        logger.info(f"Analyzing {request.spread_type or 'custom'} spread for {request.ticker}")

        analysis = spreads_engine.analyze_spread(
            ticker=request.ticker,
            spot_price=request.spot_price,
            legs=request.legs,
            spread_type=request.spread_type
        )

        return analysis

    except ValueError as e:
        logger.error(f"Invalid spread configuration: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to analyze spread: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze spread: {str(e)}"
        )
