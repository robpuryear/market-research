from fastapi import APIRouter, HTTPException
from engines.market_data import macro, technicals, sectors, options, iv_analytics, breadth

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/snapshot")
async def get_snapshot():
    try:
        return await macro.fetch_snapshot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/technicals/{ticker}")
async def get_technicals(ticker: str):
    try:
        return await technicals.compute(ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors")
async def get_sectors():
    try:
        return await sectors.fetch_rotation()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/options/{ticker}")
async def get_options(ticker: str):
    try:
        return await options.get_options_data(ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breadth")
async def get_breadth():
    try:
        return await breadth.fetch_breadth()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/iv/{ticker}")
async def get_iv(ticker: str):
    try:
        return await iv_analytics.compute(ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh")
async def refresh_cache():
    """Invalidate all cache entries and return count deleted."""
    from core.cache import invalidate_all
    count = invalidate_all()
    return {"message": f"Cache cleared: {count} entries deleted"}
