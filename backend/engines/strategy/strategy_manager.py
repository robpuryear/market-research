"""
Strategy Manager - CRUD operations for strategies

Stores strategies and results in JSON files at data/strategies.json and data/strategy_results.json
"""

import json
import os
from typing import List, Optional
from models.strategy import Strategy, StrategyResult
from datetime import datetime, timezone
import uuid
import logging
from threading import RLock

logger = logging.getLogger(__name__)

STRATEGIES_FILE = "data/strategies.json"
RESULTS_FILE = "data/strategy_results.json"

# Thread-safe file access
_strategies_lock = RLock()
_results_lock = RLock()


def create_strategy(strategy_data: dict) -> Strategy:
    """Create a new strategy"""
    with _strategies_lock:
        strategies = _load_strategies()
        strategy = Strategy(
            id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            **strategy_data
        )
        strategies.append(strategy.model_dump())
        _save_strategies(strategies)
        logger.info(f"Created strategy {strategy.id}: {strategy.name}")
        return strategy


def get_all_strategies() -> List[Strategy]:
    """Get all strategies"""
    with _strategies_lock:
        return [Strategy(**s) for s in _load_strategies()]


def get_strategy(strategy_id: str) -> Optional[Strategy]:
    """Get strategy by ID"""
    with _strategies_lock:
        strategies = _load_strategies()
        for s in strategies:
            if s["id"] == strategy_id:
                return Strategy(**s)
        return None


def update_strategy(strategy_id: str, updates: dict) -> Optional[Strategy]:
    """Update a strategy"""
    with _strategies_lock:
        strategies = _load_strategies()
        for i, s in enumerate(strategies):
            if s["id"] == strategy_id:
                strategies[i].update(updates)
                _save_strategies(strategies)
                logger.info(f"Updated strategy {strategy_id}")
                return Strategy(**strategies[i])
        return None


def delete_strategy(strategy_id: str) -> bool:
    """Delete a strategy"""
    with _strategies_lock:
        strategies = _load_strategies()
        filtered = [s for s in strategies if s["id"] != strategy_id]
        if len(filtered) < len(strategies):
            _save_strategies(filtered)
            logger.info(f"Deleted strategy {strategy_id}")
            return True
        return False


def save_result(result: StrategyResult) -> None:
    """Save a strategy result"""
    with _results_lock:
        results = _load_results()
        results.append(result.model_dump())
        _save_results(results)
        logger.info(f"Saved result for strategy {result.strategy_id}: {result.ticker}")


def get_results(strategy_id: str, limit: int = 100) -> List[StrategyResult]:
    """Get results for a strategy"""
    with _results_lock:
        results = _load_results()
        filtered = [r for r in results if r["strategy_id"] == strategy_id]
        filtered.sort(key=lambda x: x["matched_at"], reverse=True)
        return [StrategyResult(**r) for r in filtered[:limit]]


def get_recent_results(limit: int = 50) -> List[StrategyResult]:
    """Get recent results across all strategies"""
    with _results_lock:
        results = _load_results()
        results.sort(key=lambda x: x["matched_at"], reverse=True)
        return [StrategyResult(**r) for r in results[:limit]]


def increment_strategy_hits(strategy_id: str, count: int = 1) -> None:
    """Increment hit counters for a strategy"""
    with _strategies_lock:
        strategies = _load_strategies()
        for i, s in enumerate(strategies):
            if s["id"] == strategy_id:
                strategies[i]["hits_today"] = strategies[i].get("hits_today", 0) + count
                strategies[i]["total_hits"] = strategies[i].get("total_hits", 0) + count
                strategies[i]["last_run"] = datetime.now(timezone.utc).isoformat()
                _save_strategies(strategies)
                break


def reset_daily_hits() -> None:
    """Reset hits_today counter for all strategies (called daily by scheduler)"""
    with _strategies_lock:
        strategies = _load_strategies()
        for s in strategies:
            s["hits_today"] = 0
        _save_strategies(strategies)
        logger.info("Reset daily hits for all strategies")


def _load_strategies() -> list:
    """Load strategies from JSON file"""
    if not os.path.exists(STRATEGIES_FILE):
        return []
    try:
        with open(STRATEGIES_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading strategies: {e}")
        return []


def _save_strategies(strategies: list):
    """Save strategies to JSON file"""
    try:
        os.makedirs(os.path.dirname(STRATEGIES_FILE), exist_ok=True)
        with open(STRATEGIES_FILE, "w") as f:
            json.dump(strategies, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving strategies: {e}")


def _load_results() -> list:
    """Load results from JSON file"""
    if not os.path.exists(RESULTS_FILE):
        return []
    try:
        with open(RESULTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading results: {e}")
        return []


def _save_results(results: list):
    """Save results to JSON file"""
    try:
        os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
        with open(RESULTS_FILE, "w") as f:
            json.dump(results, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Error saving results: {e}")
