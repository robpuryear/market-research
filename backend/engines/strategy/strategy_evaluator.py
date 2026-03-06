"""
Strategy Evaluator - Execute strategies and evaluate conditions.
"""

import asyncio
import logging
from typing import List, Optional, Tuple, Union
from datetime import datetime, timezone
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from models.strategy import (
    Strategy, StrategyResult,
    IndicatorCondition, PricePatternCondition, ConditionGroup,
)
from models.market import TechnicalData
from engines.market_data import technicals
from engines.strategy import strategy_manager

logger = logging.getLogger(__name__)

_semaphore = asyncio.Semaphore(10)


async def evaluate_strategy(
    strategy: Strategy,
    ticker: str,
) -> Optional[StrategyResult]:
    try:
        tech_data = await technicals.compute(ticker)

        entry_met, entry_matches = await _evaluate_condition_group(
            strategy.entry_conditions, tech_data
        )

        exit_met = False
        if strategy.exit_conditions:
            exit_met, _ = await _evaluate_condition_group(
                strategy.exit_conditions, tech_data
            )

        if not entry_met:
            return None

        signal_strength = _calculate_signal_strength(
            strategy.entry_conditions, entry_matches, tech_data
        )
        current_price = tech_data.closes[-1] if tech_data.closes else 0.0

        indicator_values = {
            "rsi": tech_data.rsi[-1] if tech_data.rsi and tech_data.rsi[-1] is not None else None,
            "macd_line": tech_data.macd_line[-1] if tech_data.macd_line and tech_data.macd_line[-1] is not None else None,
            "macd_signal": tech_data.macd_signal[-1] if tech_data.macd_signal and tech_data.macd_signal[-1] is not None else None,
            "ma_20": tech_data.ma_20[-1] if tech_data.ma_20 and tech_data.ma_20[-1] is not None else None,
            "ma_50": tech_data.ma_50[-1] if tech_data.ma_50 and tech_data.ma_50[-1] is not None else None,
            "ma_200": tech_data.ma_200[-1] if tech_data.ma_200 and tech_data.ma_200[-1] is not None else None,
            "bb_upper": tech_data.bb_upper[-1] if tech_data.bb_upper and tech_data.bb_upper[-1] is not None else None,
            "bb_lower": tech_data.bb_lower[-1] if tech_data.bb_lower and tech_data.bb_lower[-1] is not None else None,
            "volume": tech_data.volumes[-1] if tech_data.volumes else None,
            "current_signal": tech_data.current_signal,
        }
        indicator_values = {k: v for k, v in indicator_values.items() if v is not None}

        return StrategyResult(
            id=str(uuid.uuid4()),
            strategy_id=strategy.id,
            ticker=ticker,
            matched_at=datetime.now(timezone.utc),
            entry_conditions_met=entry_met,
            exit_conditions_met=exit_met,
            current_price=current_price,
            indicator_values=indicator_values,
            signal_strength=signal_strength,
        )
    except Exception as e:
        logger.error(f"Error evaluating strategy {strategy.id} for {ticker}: {e}")
        return None


async def run_strategy_scan(
    strategy: Strategy,
    tickers: List[str],
    session: AsyncSession,
) -> List[StrategyResult]:
    logger.info(f"Running strategy '{strategy.name}' against {len(tickers)} tickers")

    async def scan_with_semaphore(ticker: str) -> Optional[StrategyResult]:
        async with _semaphore:
            return await evaluate_strategy(strategy, ticker)

    tasks = [scan_with_semaphore(t) for t in tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    valid_results = [r for r in results if isinstance(r, StrategyResult)]

    for result in valid_results:
        await strategy_manager.save_result(session, result)

    if valid_results:
        await strategy_manager.increment_strategy_hits(session, strategy.id, len(valid_results))

    logger.info(f"Strategy '{strategy.name}' found {len(valid_results)} matches")
    return valid_results


# ── Condition evaluation helpers (unchanged logic) ──────────────────────────

async def _evaluate_condition_group(
    group: ConditionGroup,
    tech_data: TechnicalData,
) -> Tuple[bool, dict]:
    matches = []
    match_details = {}
    for i, condition in enumerate(group.conditions):
        met, details = await _evaluate_condition(condition, tech_data)
        matches.append(met)
        match_details[f"condition_{i}"] = details
    overall_met = all(matches) if group.logic == "AND" else any(matches)
    return overall_met, match_details


async def _evaluate_condition(
    condition: Union[IndicatorCondition, PricePatternCondition],
    tech_data: TechnicalData,
) -> Tuple[bool, dict]:
    if isinstance(condition, IndicatorCondition):
        return await _evaluate_indicator_condition(condition, tech_data)
    return await _evaluate_pattern_condition(condition, tech_data)


async def _evaluate_indicator_condition(
    condition: IndicatorCondition,
    tech_data: TechnicalData,
) -> Tuple[bool, dict]:
    indicator = condition.indicator
    operator = condition.operator
    value = condition.value
    value_high = condition.value_high
    current_val = None
    prev_val = None

    if indicator == "rsi":
        if tech_data.rsi and tech_data.rsi[-1] is not None:
            current_val = tech_data.rsi[-1]
            prev_val = tech_data.rsi[-2] if len(tech_data.rsi) > 1 and tech_data.rsi[-2] is not None else None

    elif indicator == "macd":
        if tech_data.macd_line and tech_data.macd_signal:
            current_val = tech_data.macd_line[-1]
            current_signal = tech_data.macd_signal[-1]
            prev_val = tech_data.macd_line[-2] if len(tech_data.macd_line) > 1 else None
            prev_signal = tech_data.macd_signal[-2] if len(tech_data.macd_signal) > 1 else None
            if operator in ["crosses_above", "crosses_below"]:
                if all(v is not None for v in [current_val, current_signal, prev_val, prev_signal]):
                    met = (current_val > current_signal and prev_val <= prev_signal) if operator == "crosses_above" \
                        else (current_val < current_signal and prev_val >= prev_signal)
                    return met, {"indicator": "macd", "current": current_val, "signal": current_signal, "met": met}

    elif indicator == "ma":
        period = condition.period or 20
        ma_map = {20: tech_data.ma_20, 50: tech_data.ma_50, 200: tech_data.ma_200}
        ma_series = ma_map.get(period)
        if ma_series:
            current_val = ma_series[-1]
        price = tech_data.closes[-1] if tech_data.closes else None
        if current_val is not None and price is not None:
            met = price > current_val if operator == "above" else price < current_val if operator == "below" else False
            return met, {"indicator": f"ma_{period}", "price": price, "ma": current_val, "met": met}

    elif indicator == "volume":
        if tech_data.volumes and len(tech_data.volumes) >= 20:
            current_vol = tech_data.volumes[-1]
            avg_vol = sum(tech_data.volumes[-20:]) / 20
            volume_ratio = current_vol / avg_vol if avg_vol > 0 else 0
            if value is not None:
                met = volume_ratio > value if operator == "above" else volume_ratio < value if operator == "below" else False
                return met, {"indicator": "volume", "ratio": round(volume_ratio, 2), "threshold": value, "met": met}

    elif indicator == "price":
        current_val = tech_data.closes[-1] if tech_data.closes else None

    elif indicator == "bb":
        if tech_data.bb_upper and tech_data.bb_lower:
            bb_upper = tech_data.bb_upper[-1]
            bb_lower = tech_data.bb_lower[-1]
            price = tech_data.closes[-1] if tech_data.closes else None
            if operator == "above" and bb_upper is not None and price is not None:
                met = price > bb_upper
                return met, {"indicator": "bb", "price": price, "bb_upper": bb_upper, "met": met}
            elif operator == "below" and bb_lower is not None and price is not None:
                met = price < bb_lower
                return met, {"indicator": "bb", "price": price, "bb_lower": bb_lower, "met": met}

    if current_val is not None and value is not None:
        if operator == "above":
            met = current_val > value
        elif operator == "below":
            met = current_val < value
        elif operator == "between" and value_high is not None:
            met = value <= current_val <= value_high
        else:
            met = False
        return met, {"indicator": indicator, "value": current_val, "threshold": value, "met": met}

    return False, {"indicator": indicator, "error": "insufficient_data"}


async def _evaluate_pattern_condition(
    condition: PricePatternCondition,
    tech_data: TechnicalData,
) -> Tuple[bool, dict]:
    pattern = condition.pattern
    direction = condition.direction

    if pattern == "golden_cross":
        if tech_data.ma_50 and tech_data.ma_200 and len(tech_data.ma_50) > 1 and len(tech_data.ma_200) > 1:
            c50, c200, p50, p200 = tech_data.ma_50[-1], tech_data.ma_200[-1], tech_data.ma_50[-2], tech_data.ma_200[-2]
            if all(v is not None for v in [c50, c200, p50, p200]):
                met = c50 > c200 and p50 <= p200
                return met, {"pattern": "golden_cross", "met": met}

    elif pattern == "death_cross":
        if tech_data.ma_50 and tech_data.ma_200 and len(tech_data.ma_50) > 1 and len(tech_data.ma_200) > 1:
            c50, c200, p50, p200 = tech_data.ma_50[-1], tech_data.ma_200[-1], tech_data.ma_50[-2], tech_data.ma_200[-2]
            if all(v is not None for v in [c50, c200, p50, p200]):
                met = c50 < c200 and p50 >= p200
                return met, {"pattern": "death_cross", "met": met}

    elif pattern == "macd_cross":
        if tech_data.macd_line and tech_data.macd_signal and len(tech_data.macd_line) > 1:
            cm, cs, pm, ps = tech_data.macd_line[-1], tech_data.macd_signal[-1], tech_data.macd_line[-2], tech_data.macd_signal[-2]
            if all(v is not None for v in [cm, cs, pm, ps]):
                if direction == "bullish":
                    met = cm > cs and pm <= ps
                elif direction == "bearish":
                    met = cm < cs and pm >= ps
                else:
                    met = (cm > cs and pm <= ps) or (cm < cs and pm >= ps)
                return met, {"pattern": "macd_cross", "direction": direction, "met": met}

    elif pattern == "bb_squeeze":
        if tech_data.bb_upper and tech_data.bb_lower and tech_data.closes:
            bb_upper = tech_data.bb_upper[-1]
            bb_lower = tech_data.bb_lower[-1]
            price = tech_data.closes[-1]
            if all(v is not None for v in [bb_upper, bb_lower, price]):
                bb_width = (bb_upper - bb_lower) / price if price > 0 else 0
                met = bb_width < 0.05
                return met, {"pattern": "bb_squeeze", "width_pct": round(bb_width * 100, 2), "met": met}

    return False, {"pattern": pattern, "error": "pattern_not_detected"}


def _calculate_signal_strength(
    entry_conditions: ConditionGroup,
    matches: dict,
    tech_data: TechnicalData,
) -> float:
    total_conditions = len(entry_conditions.conditions)
    met_conditions = sum(1 for v in matches.values() if v.get("met", False))
    base_score = (met_conditions / total_conditions * 70) if total_conditions > 0 else 0
    bonus = 0
    if tech_data.rsi and tech_data.rsi[-1] is not None:
        rsi = tech_data.rsi[-1]
        if rsi < 30 or rsi > 70:
            bonus += 10
    if tech_data.ma_200 and tech_data.closes:
        ma200 = tech_data.ma_200[-1]
        price = tech_data.closes[-1]
        if ma200 is not None and price is not None and price > ma200:
            bonus += 10
    if tech_data.current_signal in ["bullish", "bearish"]:
        bonus += 10
    return round(min(100, base_score + bonus), 1)
