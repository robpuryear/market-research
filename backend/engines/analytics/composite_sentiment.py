"""
Composite Sentiment Engine

Combines multiple sentiment signals into a unified score:
- News sentiment (Alpha Vantage)
- Analyst ratings & price targets
- Insider trading activity
- Options flow & unusual activity
- Technical momentum (RSI, MACD, MA positioning)
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from models.analytics import CompositeSentiment, SentimentComponent
from engines.sentiment import finnhub_news
from engines.market_data import options
from engines.watchlist import fundamentals
from core import cache

logger = logging.getLogger(__name__)


# Component weights (must sum to 1.0)
WEIGHTS = {
    "news": 0.30,
    "analyst": 0.20,
    "insider": 0.15,
    "options": 0.20,
    "technical": 0.15,
}


async def compute_composite_sentiment(ticker: str) -> CompositeSentiment:
    """
    Compute composite sentiment score from multiple factors.
    Score range: -100 (very bearish) to +100 (very bullish)
    """
    cache_key = f"composite_sentiment_{ticker}"
    cached = cache.get(cache_key, "sentiment")
    if cached:
        return CompositeSentiment(**cached)

    components: List[SentimentComponent] = []

    # 1. News Sentiment (30%)
    news_component = await _compute_news_sentiment(ticker)
    if news_component:
        components.append(news_component)

    # 2. Analyst Sentiment (20%)
    analyst_component = await _compute_analyst_sentiment(ticker)
    if analyst_component:
        components.append(analyst_component)

    # 3. Insider Activity (15%)
    insider_component = await _compute_insider_sentiment(ticker)
    if insider_component:
        components.append(insider_component)

    # 4. Options Flow (20%)
    options_component = await _compute_options_sentiment(ticker)
    if options_component:
        components.append(options_component)

    # 5. Technical Momentum (15%)
    technical_component = await _compute_technical_sentiment(ticker)
    if technical_component:
        components.append(technical_component)

    # Calculate weighted composite score
    if not components:
        # No data available
        return _empty_result(ticker)

    total_weight = sum(c.weight for c in components)
    weighted_score = sum(c.score * c.weight for c in components) / total_weight
    avg_confidence = sum(c.confidence for c in components) / len(components)

    # Scale to -100 to +100
    composite_score = round(weighted_score * 100, 2)

    # Assign label
    if composite_score >= 60:
        label = "Very Bullish"
    elif composite_score >= 20:
        label = "Bullish"
    elif composite_score <= -60:
        label = "Very Bearish"
    elif composite_score <= -20:
        label = "Bearish"
    else:
        label = "Neutral"

    result = CompositeSentiment(
        ticker=ticker,
        composite_score=composite_score,
        composite_label=label,
        confidence=round(avg_confidence, 3),
        components=components,
        timestamp=datetime.now(timezone.utc),
    )

    cache.set(cache_key, result.model_dump())
    return result


async def _compute_news_sentiment(ticker: str) -> Optional[SentimentComponent]:
    """News sentiment from Finnhub (-1 to +1)"""
    try:
        news_data = await finnhub_news.fetch_news_sentiment(ticker)
        if not news_data:
            return None

        # Finnhub score is already -1 to +1
        score = news_data.avg_sentiment_score
        confidence = min(1.0, news_data.article_count / 10)  # More articles = higher confidence

        return SentimentComponent(
            name="News Sentiment",
            score=score,
            weight=WEIGHTS["news"],
            confidence=confidence,
            description=f"{news_data.sentiment_label} ({news_data.article_count} articles)"
        )
    except Exception as e:
        logger.warning(f"News sentiment failed for {ticker}: {e}")
        return None


async def _compute_analyst_sentiment(ticker: str) -> Optional[SentimentComponent]:
    """Analyst rating and price target positioning (-1 to +1)"""
    try:
        stock_data = await fundamentals.fetch_fundamentals(ticker)
        if not stock_data:
            return None

        score = 0.0
        factors = []

        # Factor 1: Price vs analyst target
        if stock_data.price_target and stock_data.price:
            pct_to_target = ((stock_data.price_target - stock_data.price) / stock_data.price) * 100
            # +20% upside = bullish (+0.5), -20% downside = bearish (-0.5)
            target_score = max(-1.0, min(1.0, pct_to_target / 40))
            score += target_score * 0.6
            factors.append(f"{pct_to_target:+.1f}% to target")

        # Factor 2: Analyst rating (assuming 1=Strong Buy, 5=Sell)
        if stock_data.analyst_rating:
            rating_map = {
                "Strong Buy": 1.0,
                "Buy": 0.5,
                "Hold": 0.0,
                "Sell": -0.5,
                "Strong Sell": -1.0,
            }
            rating_score = rating_map.get(stock_data.analyst_rating, 0.0)
            score += rating_score * 0.4
            factors.append(stock_data.analyst_rating)

        if not factors:
            return None

        confidence = 0.7 if stock_data.price_target else 0.4

        return SentimentComponent(
            name="Analyst Sentiment",
            score=score,
            weight=WEIGHTS["analyst"],
            confidence=confidence,
            description=", ".join(factors)
        )
    except Exception as e:
        logger.warning(f"Analyst sentiment failed for {ticker}: {e}")
        return None


async def _compute_insider_sentiment(ticker: str) -> Optional[SentimentComponent]:
    """Insider trading activity (-1 to +1)"""
    try:
        stock_data = await fundamentals.fetch_fundamentals(ticker)
        if not stock_data or not stock_data.insider_transactions:
            return None

        # Calculate net insider buying/selling (last 90 days)
        buy_value = 0.0
        sell_value = 0.0

        for txn in stock_data.insider_transactions[:20]:  # Last 20 transactions
            if "buy" in txn.transaction.lower() or "purchase" in txn.transaction.lower():
                buy_value += txn.value
            elif "sell" in txn.transaction.lower() or "sale" in txn.transaction.lower():
                sell_value += txn.value

        total_value = buy_value + sell_value
        if total_value == 0:
            return None

        # Net buying ratio: +1 = all buying, -1 = all selling
        net_ratio = (buy_value - sell_value) / total_value

        # Confidence based on total transaction value (more = higher confidence)
        confidence = min(1.0, total_value / 10_000_000)  # $10M+ = full confidence

        description = f"${buy_value/1e6:.1f}M buy, ${sell_value/1e6:.1f}M sell"

        return SentimentComponent(
            name="Insider Activity",
            score=net_ratio,
            weight=WEIGHTS["insider"],
            confidence=confidence,
            description=description
        )
    except Exception as e:
        logger.warning(f"Insider sentiment failed for {ticker}: {e}")
        return None


async def _compute_options_sentiment(ticker: str) -> Optional[SentimentComponent]:
    """Options flow and unusual activity (-1 to +1)"""
    try:
        from engines.sentiment import flow_toxicity

        # Get flow toxicity
        toxicity = await flow_toxicity.fetch_flow_toxicity(ticker)

        score = 0.0
        factors = []

        if toxicity:
            # PIN score: <0.2 = bullish, >0.3 = bearish
            if toxicity.pin_score < 0.2:
                pin_sentiment = 0.5
                factors.append("Low toxicity (bullish)")
            elif toxicity.pin_score > 0.3:
                pin_sentiment = -0.5
                factors.append("High toxicity (bearish)")
            else:
                pin_sentiment = 0.0
                factors.append("Neutral toxicity")

            score += pin_sentiment * 0.5

            # Buy/sell volume ratio
            total_volume = toxicity.buy_volume + toxicity.sell_volume
            if total_volume > 0:
                buy_ratio = toxicity.buy_volume / total_volume
                volume_sentiment = (buy_ratio - 0.5) * 2  # Convert 0-1 to -1 to +1
                score += volume_sentiment * 0.5
                factors.append(f"{buy_ratio*100:.0f}% buy volume")

        # Get unusual options activity
        stock_data = await fundamentals.fetch_fundamentals(ticker)
        if stock_data and stock_data.unusual_options:
            call_volume = sum(opt.volume for opt in stock_data.unusual_options if opt.option_type == "call")
            put_volume = sum(opt.volume for opt in stock_data.unusual_options if opt.option_type == "put")

            if call_volume + put_volume > 0:
                # More unusual calls = bullish, more unusual puts = bearish
                unusual_ratio = (call_volume - put_volume) / (call_volume + put_volume)
                factors.append(f"{len(stock_data.unusual_options)} unusual")

                # Blend with existing score
                if score == 0:
                    score = unusual_ratio
                else:
                    score = (score + unusual_ratio) / 2

        if not factors:
            return None

        return SentimentComponent(
            name="Options Flow",
            score=score,
            weight=WEIGHTS["options"],
            confidence=0.6,
            description=", ".join(factors)
        )
    except Exception as e:
        logger.warning(f"Options sentiment failed for {ticker}: {e}")
        return None


async def _compute_technical_sentiment(ticker: str) -> Optional[SentimentComponent]:
    """Technical momentum signals (-1 to +1)"""
    try:
        from engines.market_data import technicals

        tech_data = await technicals.compute(ticker)
        if not tech_data:
            return None

        score = 0.0
        factors = []

        # RSI: >70 = overbought (caution), <30 = oversold (opportunity)
        if tech_data.rsi and len(tech_data.rsi) > 0:
            latest_rsi = tech_data.rsi[-1]
            if latest_rsi:
                if latest_rsi > 70:
                    rsi_score = -0.3  # Overbought = slight bearish
                    factors.append(f"RSI {latest_rsi:.0f} (overbought)")
                elif latest_rsi < 30:
                    rsi_score = 0.5  # Oversold = bullish opportunity
                    factors.append(f"RSI {latest_rsi:.0f} (oversold)")
                elif latest_rsi > 50:
                    rsi_score = 0.2
                    factors.append(f"RSI {latest_rsi:.0f}")
                else:
                    rsi_score = -0.2
                    factors.append(f"RSI {latest_rsi:.0f}")
                score += rsi_score * 0.4

        # MACD: positive histogram = bullish, negative = bearish
        if tech_data.macd_histogram and len(tech_data.macd_histogram) > 0:
            latest_hist = tech_data.macd_histogram[-1]
            if latest_hist:
                # Normalize histogram to -1 to +1 (rough estimate)
                macd_score = max(-1.0, min(1.0, latest_hist * 10))
                score += macd_score * 0.3
                factors.append(f"MACD {'bullish' if latest_hist > 0 else 'bearish'}")

        # Moving averages: price above MAs = bullish
        if tech_data.closes and len(tech_data.closes) > 0:
            current_price = tech_data.closes[-1]
            if current_price and tech_data.ma_20 and tech_data.ma_50:
                ma_20_val = tech_data.ma_20[-1]
                ma_50_val = tech_data.ma_50[-1]

                if ma_20_val and ma_50_val:
                    above_20 = current_price > ma_20_val
                    above_50 = current_price > ma_50_val

                    if above_20 and above_50:
                        ma_score = 0.5
                        factors.append("Above MAs")
                    elif not above_20 and not above_50:
                        ma_score = -0.5
                        factors.append("Below MAs")
                    else:
                        ma_score = 0.0
                        factors.append("Mixed MAs")

                    score += ma_score * 0.3

        if not factors:
            return None

        return SentimentComponent(
            name="Technical Momentum",
            score=score,
            weight=WEIGHTS["technical"],
            confidence=0.7,
            description=", ".join(factors)
        )
    except Exception as e:
        logger.warning(f"Technical sentiment failed for {ticker}: {e}")
        return None


def _empty_result(ticker: str) -> CompositeSentiment:
    """Return neutral result when no data available"""
    return CompositeSentiment(
        ticker=ticker,
        composite_score=0.0,
        composite_label="Neutral",
        confidence=0.0,
        components=[],
        timestamp=datetime.now(timezone.utc),
    )
