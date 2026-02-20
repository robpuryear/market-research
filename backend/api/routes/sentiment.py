from fastapi import APIRouter, HTTPException
from engines.sentiment import reddit, flow_toxicity, dark_pool, stocktwits, av_news

router = APIRouter(prefix="/api/sentiment", tags=["sentiment"])


@router.get("/reddit")
async def get_reddit():
    try:
        return await reddit.fetch_trending()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flow-toxicity/{ticker}")
async def get_flow_toxicity(ticker: str):
    try:
        return await flow_toxicity.compute(ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dark-pool/{ticker}")
async def get_dark_pool(ticker: str):
    try:
        return await dark_pool.get_dark_pool(ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stocktwits/{ticker}")
async def get_stocktwits(ticker: str):
    try:
        return await stocktwits.fetch_stocktwits(ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news/{ticker}")
async def get_news_sentiment(ticker: str):
    """Returns Alpha Vantage news sentiment. Returns 204 if no API key configured."""
    try:
        result = await av_news.fetch_news_sentiment(ticker.upper())
        if result is None:
            from fastapi.responses import Response
            return Response(status_code=204)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
