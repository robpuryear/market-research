import asyncio
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yfinance as yf

from engines.watchlist import price_data, fundamentals, options_flow, earnings_calendar
from models.analytics import EarningsCalendarEntry
from core import watchlist_manager, cache

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


class AddTickerRequest(BaseModel):
    ticker: str


class RemoveTickerRequest(BaseModel):
    ticker: str


@router.get("/")
async def get_watchlist():
    try:
        return await price_data.bulk_fetch()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/earnings-calendar", response_model=List[EarningsCalendarEntry])
async def get_earnings_calendar():
    try:
        return await earnings_calendar.get_earnings_calendar()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticker}")
async def get_stock_detail(ticker: str):
    try:
        detail, flow = await asyncio.gather(
            fundamentals.deep_dive(ticker.upper()),
            options_flow.detect_unusual(ticker.upper()),
        )
        result = detail.model_dump()
        result["unusual_options"] = [f.model_dump() for f in flow]
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_to_watchlist(request: AddTickerRequest):
    """Add a ticker to the watchlist after validating it exists."""
    ticker = request.ticker.strip().upper()

    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker cannot be empty")

    # Validate ticker exists using yfinance
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        if not info or info.get("regularMarketPrice") is None:
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or invalid")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Unable to validate ticker '{ticker}': {str(e)}")

    # Add to watchlist
    if watchlist_manager.add_ticker(ticker):
        # Invalidate watchlist cache so it refreshes
        cache.invalidate("watchlist_bulk")
        return {"status": "added", "ticker": ticker}
    else:
        raise HTTPException(status_code=409, detail=f"Ticker '{ticker}' already in watchlist")


@router.delete("/remove/{ticker}")
async def remove_from_watchlist(ticker: str):
    """Remove a ticker from the watchlist."""
    ticker = ticker.strip().upper()

    if watchlist_manager.remove_ticker(ticker):
        # Invalidate watchlist cache so it refreshes
        cache.invalidate("watchlist_bulk")
        return {"status": "removed", "ticker": ticker}
    else:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not in watchlist")
