import yfinance as yf
import pandas as pd
from datetime import datetime, timezone
from typing import List
import logging

from models.watchlist import OptionsFlowData
from core import cache, rate_limiter

logger = logging.getLogger(__name__)

UNUSUAL_VOLUME_RATIO = 3.0
UNUSUAL_PREMIUM_THRESHOLD = 50_000


async def detect_unusual(ticker: str) -> List[OptionsFlowData]:
    cache_key = f"options_flow_{ticker}"
    cached = cache.get(cache_key, "options")
    if cached:
        return [OptionsFlowData(**f) for f in cached]

    rate_limiter.acquire("yfinance")

    try:
        tk = yf.Ticker(ticker)
        expirations = tk.options
        if not expirations:
            return []

        unusual = []
        # Check first 2 expirations for unusual flow
        for expiry in expirations[:2]:
            chain = tk.option_chain(expiry)
            for opt_type, df in [("call", chain.calls), ("put", chain.puts)]:
                if df.empty:
                    continue
                # Fill NaN values with 0 before iteration
                df = df.fillna(0)
                for _, row in df.iterrows():
                    volume = int(row.get("volume", 0))
                    oi = int(row.get("openInterest", 0))
                    strike = float(row.get("strike", 0))
                    last_price = float(row.get("lastPrice", 0))
                    premium = volume * last_price * 100  # total premium in $

                    if oi == 0:
                        continue
                    ratio = round(volume / oi, 2)
                    is_unusual = ratio >= UNUSUAL_VOLUME_RATIO or premium >= UNUSUAL_PREMIUM_THRESHOLD

                    if is_unusual and volume > 10:
                        unusual.append(OptionsFlowData(
                            ticker=ticker,
                            expiry=expiry,
                            strike=strike,
                            option_type=opt_type,
                            volume=volume,
                            open_interest=oi,
                            volume_oi_ratio=ratio,
                            premium_total=round(premium, 2),
                            is_unusual=True,
                            timestamp=datetime.now(timezone.utc),
                        ))

        unusual.sort(key=lambda x: x.premium_total, reverse=True)
        result = unusual[:10]

        cache.set(cache_key, [f.model_dump() for f in result])
        return result

    except Exception as e:
        logger.warning(f"Error detecting unusual options for {ticker}: {e}")
        return []
