"""Persistent watchlist management."""
import json
import logging
from pathlib import Path
from typing import List
import threading

logger = logging.getLogger(__name__)

WATCHLIST_FILE = Path(__file__).parent.parent / "data" / "watchlist.json"
_lock = threading.RLock()  # Use RLock for reentrant locking


def _ensure_file_exists():
    """Ensure watchlist file exists, create with defaults if not."""
    if not WATCHLIST_FILE.exists():
        WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Default tickers
        default_tickers = ["IBM", "CVNA", "NVDA", "TSLA", "AAPL", "SPY", "QQQ", "IWM"]
        _save_tickers(default_tickers)
        logger.info(f"Created watchlist file with {len(default_tickers)} default tickers")


def get_tickers() -> List[str]:
    """Get current watchlist tickers."""
    _ensure_file_exists()
    with _lock:
        try:
            with open(WATCHLIST_FILE, "r") as f:
                data = json.load(f)
                return data.get("tickers", [])
        except Exception as e:
            logger.error(f"Error reading watchlist: {e}")
            return ["AAPL", "SPY", "QQQ"]  # Fallback


def _save_tickers(tickers: List[str]):
    """Save tickers to file (internal, assumes lock is held)."""
    with open(WATCHLIST_FILE, "w") as f:
        json.dump({"tickers": tickers}, f, indent=2)


def add_ticker(ticker: str) -> bool:
    """Add a ticker to the watchlist. Returns True if added, False if already exists."""
    ticker = ticker.strip().upper()
    if not ticker:
        return False

    with _lock:
        tickers = get_tickers()
        if ticker in tickers:
            return False
        tickers.append(ticker)
        _save_tickers(tickers)
        logger.info(f"Added {ticker} to watchlist")
        return True


def remove_ticker(ticker: str) -> bool:
    """Remove a ticker from the watchlist. Returns True if removed, False if not found."""
    ticker = ticker.strip().upper()

    with _lock:
        tickers = get_tickers()
        if ticker not in tickers:
            return False
        tickers.remove(ticker)
        _save_tickers(tickers)
        logger.info(f"Removed {ticker} from watchlist")
        return True


def ticker_exists(ticker: str) -> bool:
    """Check if ticker is in the watchlist."""
    ticker = ticker.strip().upper()
    return ticker in get_tickers()
