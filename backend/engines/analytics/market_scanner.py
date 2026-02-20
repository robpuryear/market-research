"""Market-wide scanner to find top stock opportunities."""
import asyncio
import logging
from typing import List, Optional
from datetime import datetime, timezone
import yfinance as yf

from core import stock_universe, cache, rate_limiter
from models.analytics import ScanCandidate
from engines.analytics import ml_signals
from engines.watchlist import options_flow
from engines.market_data import iv_analytics

logger = logging.getLogger(__name__)


async def scan_ticker(ticker: str) -> Optional[ScanCandidate]:
    """
    Scan a single ticker and return opportunity score.

    Returns None if ticker fails to load or doesn't meet minimum criteria.
    """
    try:
        rate_limiter.acquire("yfinance")

        # Get basic info
        tk = yf.Ticker(ticker)
        info = tk.info or {}

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if not price or price <= 0:
            return None

        volume = float(info.get("volume") or 0)
        avg_volume = float(info.get("averageVolume") or 1)
        if volume == 0 or avg_volume == 0:
            return None

        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0

        # Get short interest data
        short_pct = info.get("shortPercentOfFloat")
        short_ratio = info.get("shortRatio")

        # Calculate individual scores
        # Calculate squeeze score inline
        squeeze_score = 0.0
        if short_pct:
            squeeze_score += min(40, short_pct * 100 * 2)  # 20% SI = 40 pts
        if short_ratio:
            squeeze_score += min(30, short_ratio * 3)  # 10 days = 30 pts
        if volume_ratio > 1:
            squeeze_score += min(20, (volume_ratio - 1) * 10)  # 3x vol = 20 pts

        # Get ML signals
        ml_data = await ml_signals.run_all(ticker)
        raw_signals = ml_data.get("signals", [])

        # Parse signals into MLSignal objects
        from models.analytics import MLSignal
        signals = []
        for sig_str in raw_signals:
            # Simple classification
            direction = "bullish" if any(word in sig_str.lower() for word in ["bullish", "golden", "oversold"]) else \
                       "bearish" if any(word in sig_str.lower() for word in ["bearish", "death", "overbought"]) else \
                       "neutral"
            signals.append(MLSignal(
                signal_type=sig_str.split(":")[0] if ":" in sig_str else sig_str,
                direction=direction,
                description=sig_str
            ))
        unusual_opts = await options_flow.detect_unusual(ticker)

        # Add options bonus to squeeze score
        if len(unusual_opts) > 0:
            squeeze_score += 10

        squeeze_score = round(min(100, max(0, squeeze_score)), 1)

        # Get IV rank (simplified)
        try:
            iv_data = await iv_analytics.fetch_iv(ticker)
            iv_rank = iv_data.iv_rank if iv_data else 0.0
        except Exception:
            iv_rank = 0.0

        # Count bullish vs bearish signals
        bullish_signals = sum(1 for s in signals if s.direction == "bullish")
        bearish_signals = sum(1 for s in signals if s.direction == "bearish")
        signal_score = (bullish_signals - bearish_signals) * 10  # -40 to +40

        # Unusual options score
        options_score = min(len(unusual_opts) * 15, 30)  # 0-30

        # Volume score
        volume_score = min((volume_ratio - 1) * 10, 20) if volume_ratio > 1 else 0  # 0-20

        # Composite score (0-100)
        composite = (
            squeeze_score * 0.30 +  # 30% weight
            max(signal_score, 0) * 0.25 +  # 25% weight (0-10 range)
            options_score * 0.25 +  # 25% weight
            min(iv_rank, 100) * 0.10 +  # 10% weight
            volume_score * 0.10  # 10% weight
        )

        return ScanCandidate(
            ticker=ticker,
            company_name=info.get("longName") or info.get("shortName") or ticker,
            price=round(float(price), 2),
            volume_ratio=round(volume_ratio, 2),
            squeeze_score=round(squeeze_score, 1),
            ml_signals=signals,
            bullish_signal_count=bullish_signals,
            bearish_signal_count=bearish_signals,
            unusual_options_count=len(unusual_opts),
            iv_rank=round(iv_rank, 1),
            composite_score=round(composite, 1),
            short_interest_pct=info.get("shortPercentOfFloat"),
            market_cap=info.get("marketCap"),
            sector=info.get("sector"),
            timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.warning(f"Failed to scan {ticker}: {e}", exc_info=True)
        return None


async def scan_market(
    universe: str = "top100",
    limit: int = 100,
    min_price: float = 5.0,
    max_price: float = 1000.0,
    min_composite: float = 50.0,
    top_n: int = 10,
) -> List[ScanCandidate]:
    """
    Scan market universe and return top opportunities.

    Args:
        universe: "top100", "momentum", "small_mid", or "all"
        limit: Max tickers to scan from universe
        min_price: Minimum stock price filter
        max_price: Maximum stock price filter
        min_composite: Minimum composite score to include
        top_n: Number of top candidates to return

    Returns:
        List of top candidates sorted by composite score
    """
    cache_key = f"market_scan_{universe}_{limit}_{min_price}_{max_price}_{min_composite}_{top_n}"
    cached = cache.get(cache_key, "market_scan")
    if cached:
        return [ScanCandidate(**c) for c in cached]

    logger.info(f"Starting market scan: universe={universe}, limit={limit}")

    # Get tickers to scan
    tickers = stock_universe.get_universe(universe, limit=limit)

    # Scan all tickers concurrently (with semaphore to limit concurrency)
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent scans

    async def scan_with_semaphore(ticker):
        async with semaphore:
            return await scan_ticker(ticker)

    tasks = [scan_with_semaphore(t) for t in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter and process results
    candidates = []
    for result in results:
        if isinstance(result, ScanCandidate):
            # Apply price filters
            if result.price < min_price or result.price > max_price:
                continue
            # Apply minimum composite score filter
            if result.composite_score < min_composite:
                continue
            candidates.append(result)

    # Sort by composite score descending
    candidates.sort(key=lambda x: x.composite_score, reverse=True)

    # Take top N
    top_candidates = candidates[:top_n]

    # Cache for 1 hour
    cache.set(cache_key, [c.model_dump() for c in top_candidates])

    logger.info(f"Market scan complete: scanned {len(tickers)}, found {len(candidates)} candidates, returning top {len(top_candidates)}")

    return top_candidates
