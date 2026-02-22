from fastapi import APIRouter, HTTPException, Query
from engines.analytics import ml_signals, correlation, short_squeeze, market_scanner, composite_sentiment
from models.analytics import MLSignalsData, MLSignal, SqueezeScore, CorrelationMatrix, ScanCandidate, CompositeSentiment
from datetime import datetime, timezone
from typing import List

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _classify_signal(signal_str: str) -> tuple[str, str]:
    """Return (signal_type, direction) from a raw signal string."""
    s = signal_str.lower()
    if "bullish divergence" in s or "rsi bullish" in s:
        return signal_str, "bullish"
    if "bearish divergence" in s or "rsi bearish" in s:
        return signal_str, "bearish"
    if "bullish crossover" in s or "golden cross" in s:
        return signal_str, "bullish"
    if "bearish crossover" in s or "death cross" in s:
        return signal_str, "bearish"
    if "oversold" in s:
        return signal_str, "bullish"
    if "overbought" in s:
        return signal_str, "bearish"
    if "squeeze" in s:
        return signal_str, "neutral"
    return signal_str, "neutral"


@router.get("/squeeze", response_model=List[SqueezeScore])
async def get_squeeze():
    try:
        raw = await short_squeeze.score_all()
        results = []
        for item in raw:
            results.append(SqueezeScore(
                ticker=item["ticker"],
                squeeze_score=item["squeeze_score"],
                short_interest_pct=item.get("short_interest_pct"),
                short_ratio=item.get("days_to_cover"),
                volume_ratio=item.get("volume_ratio", 1.0),
                options_unusual=item.get("options_unusual", False),
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correlation", response_model=CorrelationMatrix)
async def get_correlation():
    try:
        raw = await correlation.compute_matrix()
        tickers = raw.get("tickers", [])
        matrix_dict = raw.get("matrix", {})

        # Convert dict-of-dicts to 2D list ordered by tickers
        matrix_2d: List[List[float]] = []
        for t1 in tickers:
            row = []
            for t2 in tickers:
                val = matrix_dict.get(t1, {}).get(t2, 0.0) if isinstance(matrix_dict, dict) else 0.0
                row.append(val)
            matrix_2d.append(row)

        return CorrelationMatrix(
            tickers=tickers,
            matrix=matrix_2d,
            timestamp=datetime.fromisoformat(raw.get("timestamp", datetime.now(timezone.utc).isoformat())),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signals/{ticker}", response_model=MLSignalsData)
async def get_signals(ticker: str):
    try:
        raw = await ml_signals.run_all(ticker.upper())
        raw_signals: List[str] = raw.get("signals", [])

        parsed_signals = []
        for s in raw_signals:
            signal_type, direction = _classify_signal(s)
            parsed_signals.append(MLSignal(
                signal_type=signal_type,
                direction=direction,
                description=s,
            ))

        ts_str = raw.get("timestamp", datetime.now(timezone.utc).isoformat())
        return MLSignalsData(
            ticker=raw.get("ticker", ticker.upper()),
            signals=parsed_signals,
            rsi=raw.get("rsi_current", 50.0),
            signal_count=raw.get("signal_count", len(parsed_signals)),
            timestamp=datetime.fromisoformat(ts_str),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-scan", response_model=List[ScanCandidate])
async def scan_market(
    universe: str = Query("top100", description="Stock universe: top100, momentum, small_mid, or all"),
    limit: int = Query(100, description="Max tickers to scan", ge=10, le=200),
    min_price: float = Query(5.0, description="Minimum stock price", ge=0.01),
    max_price: float = Query(1000.0, description="Maximum stock price"),
    min_composite: float = Query(50.0, description="Minimum composite score", ge=0, le=100),
    top_n: int = Query(10, description="Number of top results", ge=1, le=50),
):
    """
    Scan the market for top stock opportunities.

    Scans a universe of stocks and returns top candidates based on:
    - Short squeeze potential
    - ML technical signals
    - Unusual options activity
    - IV rank (volatility opportunity)
    - Volume ratio

    Returns top N candidates ranked by composite score.
    """
    try:
        candidates = await market_scanner.scan_market(
            universe=universe,
            limit=limit,
            min_price=min_price,
            max_price=max_price,
            min_composite=min_composite,
            top_n=top_n,
        )
        return candidates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/composite-sentiment/{ticker}", response_model=CompositeSentiment)
async def get_composite_sentiment(ticker: str):
    """
    Get composite sentiment score for a stock.

    Combines multiple sentiment signals:
    - News sentiment (30%)
    - Analyst ratings & price targets (20%)
    - Insider trading activity (15%)
    - Options flow & unusual activity (20%)
    - Technical momentum (15%)

    Returns score from -100 (very bearish) to +100 (very bullish).
    """
    try:
        return await composite_sentiment.compute_composite_sentiment(ticker.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
