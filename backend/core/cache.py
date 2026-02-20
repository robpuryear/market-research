import json
import time
import os
import hashlib
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"

# TTLs in seconds
TTL = {
    "snapshot": 300,        # 5 min
    "technicals": 900,      # 15 min
    "sectors": 600,         # 10 min
    "breadth": 600,         # 10 min
    "options": 600,         # 10 min
    "fundamentals": 3600,   # 1 hr
    "earnings": 86400,      # 24 hr
    "sentiment": 1800,      # 30 min
    "flow": 300,            # 5 min
    "watchlist": 300,       # 5 min
    "market_scan": 3600,    # 1 hr (market scanning is expensive)
}

AFTER_HOURS_MULTIPLIER = 6


def _is_market_hours() -> bool:
    """Return True if NYSE is currently open (simplified: 9:30–16:00 ET, Mon–Fri)."""
    now = datetime.now(timezone.utc)
    # ET = UTC-5 (EST) or UTC-4 (EDT); approximate with UTC-5
    et_hour = (now.hour - 5) % 24
    et_minute = now.minute
    weekday = now.weekday()  # 0=Mon, 6=Sun

    if weekday >= 5:  # weekend
        return False
    et_time = et_hour * 60 + et_minute
    return 570 <= et_time <= 960  # 9:30 = 570, 16:00 = 960


def _cache_path(key: str) -> Path:
    safe = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{safe}.json"


def get(key: str, ttl_category: str = "snapshot") -> Optional[Any]:
    """Return cached value if valid, else None."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            record = json.load(f)
        ttl = TTL.get(ttl_category, 300)
        if not _is_market_hours():
            ttl *= AFTER_HOURS_MULTIPLIER
        if time.time() - record["timestamp"] < ttl:
            return record["data"]
    except Exception as e:
        logger.debug(f"Cache miss for {key}: {e}")
    return None


def set(key: str, data: Any) -> None:
    """Write data to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(key)
    record = {"timestamp": time.time(), "data": data}
    with open(path, "w") as f:
        json.dump(record, f, default=str)


def get_stale(key: str) -> Optional[Any]:
    """Return cached value regardless of TTL (stale-on-error fallback)."""
    path = _cache_path(key)
    if not path.exists():
        return None
    try:
        with open(path) as f:
            record = json.load(f)
        return record["data"]
    except Exception:
        return None


def invalidate(key: str) -> bool:
    """Delete a specific cache entry."""
    path = _cache_path(key)
    if path.exists():
        path.unlink()
        return True
    return False


def invalidate_all() -> int:
    """Delete all cache files. Returns count deleted."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in CACHE_DIR.glob("*.json"):
        f.unlink()
        count += 1
    return count
