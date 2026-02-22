"""
Options API Routes

Endpoints for options chain, Greeks, analytics, and spreads.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from models.options import (
    OptionsChain,
    OptionsAnalytics,
    ExpirationDate,
)
from engines.options import chain as options_engine

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
