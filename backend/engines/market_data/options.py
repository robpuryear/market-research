import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import logging

from models.market import OptionsGreeks
from core import cache, rate_limiter

logger = logging.getLogger(__name__)


def _compute_max_pain(chain) -> float | None:
    """Compute options max pain price."""
    try:
        calls = chain.calls[["strike", "openInterest"]].copy()
        puts = chain.puts[["strike", "openInterest"]].copy()
        strikes = sorted(set(calls["strike"].tolist() + puts["strike"].tolist()))

        pain = {}
        for s in strikes:
            call_pain = sum(
                max(0, s - k) * oi
                for k, oi in zip(calls["strike"], calls["openInterest"])
            )
            put_pain = sum(
                max(0, k - s) * oi
                for k, oi in zip(puts["strike"], puts["openInterest"])
            )
            pain[s] = call_pain + put_pain

        return min(pain, key=pain.get)
    except Exception:
        return None


async def get_options_data(ticker: str) -> OptionsGreeks:
    cache_key = f"options_{ticker}"
    cached = cache.get(cache_key, "options")
    if cached:
        return OptionsGreeks(**cached)

    rate_limiter.acquire("yfinance")

    try:
        tk = yf.Ticker(ticker)
        expirations = tk.options
        if not expirations:
            return OptionsGreeks(ticker=ticker, expiry="N/A")

        # Use nearest expiry
        expiry = expirations[0]
        chain = tk.option_chain(expiry)

        max_pain = _compute_max_pain(chain)
        total_call_oi = int(chain.calls["openInterest"].sum())
        total_put_oi = int(chain.puts["openInterest"].sum())
        pcr = round(total_put_oi / total_call_oi, 3) if total_call_oi > 0 else None

        # Gamma exposure approximation (simplified: sum of call OI * strike)
        gamma_exp = float((chain.calls["openInterest"] * chain.calls["strike"]).sum() -
                          (chain.puts["openInterest"] * chain.puts["strike"]).sum())

        result = OptionsGreeks(
            ticker=ticker,
            expiry=expiry,
            max_pain=round(max_pain, 2) if max_pain else None,
            gamma_exposure=round(gamma_exp / 1e6, 2),  # in millions
            put_call_ratio=pcr,
            total_call_oi=total_call_oi,
            total_put_oi=total_put_oi,
        )

        cache.set(cache_key, result.model_dump())
        return result

    except Exception as e:
        logger.error(f"Error fetching options data for {ticker}: {e}")
        return OptionsGreeks(ticker=ticker, expiry="N/A")
