import time
import threading
from typing import Dict
import logging

logger = logging.getLogger(__name__)


class TokenBucket:
    """Thread-safe token bucket rate limiter."""

    def __init__(self, capacity: int, refill_rate: float):
        """
        capacity: max tokens
        refill_rate: tokens per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def consume(self, tokens: int = 1, block: bool = True, timeout: float = 30.0) -> bool:
        """
        Attempt to consume tokens. If block=True, waits until available.
        Returns True if consumed, False if timed out.
        """
        deadline = time.monotonic() + timeout
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                wait = (tokens - self._tokens) / self.refill_rate

            if not block or time.monotonic() + wait > deadline:
                return False
            time.sleep(min(wait, 0.1))

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now


# Per-provider rate limiters
# Alpha Vantage: 25 calls/day = 25/(24*3600) = 0.000289 tokens/sec, capacity 5
# Polygon: 5 calls/min = 5/60 = 0.0833 tokens/sec, capacity 5
# yfinance: ~30 req/min practical limit; capacity=2 prevents burst, 0.5/sec = 1 req/2s
# StockTwits: ~200 req/hour unauthenticated = 200/3600 ~ 0.056/sec, capacity 5
_limiters: Dict[str, TokenBucket] = {
    "alpha_vantage": TokenBucket(capacity=5, refill_rate=25 / 86400),
    "polygon": TokenBucket(capacity=5, refill_rate=5 / 60),
    "yfinance": TokenBucket(capacity=2, refill_rate=0.5),
    "reddit": TokenBucket(capacity=10, refill_rate=1.0),
    "stocktwits": TokenBucket(capacity=5, refill_rate=200 / 3600),
}


def acquire(provider: str, block: bool = True) -> bool:
    """Acquire a rate limit token for the given provider."""
    limiter = _limiters.get(provider)
    if not limiter:
        logger.warning(f"No rate limiter for provider: {provider}")
        return True
    acquired = limiter.consume(block=block)
    if not acquired:
        logger.warning(f"Rate limit exceeded for provider: {provider}")
    return acquired
