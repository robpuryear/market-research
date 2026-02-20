import math
import logging
from datetime import datetime, timezone

import numpy as np
import yfinance as yf

from models.market import IVAnalytics
from core import cache, rate_limiter

logger = logging.getLogger(__name__)


def _zero_result(ticker: str) -> IVAnalytics:
    return IVAnalytics(
        ticker=ticker,
        atm_iv=0.0,
        iv_rank=0.0,
        expected_move_1w=0.0,
        expected_move_1m=0.0,
        put_call_skew=0.0,
        term_structure=[],
        timestamp=datetime.now(timezone.utc),
    )


async def compute(ticker: str) -> IVAnalytics:
    cache_key = f"iv_{ticker}"
    cached = cache.get(cache_key, "options")
    if cached:
        return IVAnalytics(**cached)

    rate_limiter.acquire("yfinance")

    try:
        tk = yf.Ticker(ticker)

        expiries = tk.options
        if not expiries:
            return _zero_result(ticker)

        info = tk.info or {}
        spot = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0)
        if spot == 0:
            return _zero_result(ticker)

        # Realized 30-day vol for IV rank denominator
        hist = tk.history(period="40d", interval="1d", auto_adjust=True)
        realized_30d_vol = 0.0
        if hist is not None and len(hist) >= 2:
            returns = hist["Close"].pct_change().dropna()
            if len(returns) >= 2:
                realized_30d_vol = float(returns.std() * math.sqrt(252))

        # Take nearest 4 expiries
        nearest_expiries = list(expiries[:4])

        atm_iv_values = []
        term_structure = []
        otm_put_ivs = []
        otm_call_ivs = []

        for expiry in nearest_expiries:
            try:
                chain = tk.option_chain(expiry)
                calls = chain.calls
                puts = chain.puts

                if calls.empty or puts.empty:
                    continue

                # ATM strike: closest to spot
                call_strikes = calls["strike"].values
                atm_idx = int(np.argmin(np.abs(call_strikes - spot)))
                atm_strike = call_strikes[atm_idx]

                call_row = calls[calls["strike"] == atm_strike]
                put_row = puts[puts["strike"] == atm_strike]

                call_iv = float(call_row["impliedVolatility"].iloc[0]) if not call_row.empty else None
                put_iv = float(put_row["impliedVolatility"].iloc[0]) if not put_row.empty else None

                if call_iv is not None and put_iv is not None:
                    atm_iv_val = (call_iv + put_iv) / 2
                    atm_iv_values.append(atm_iv_val)
                    term_structure.append(round(atm_iv_val, 4))

                # OTM skew: ~5% away from spot
                otm_put_strike = spot * 0.95
                otm_call_strike = spot * 1.05

                put_strikes = puts["strike"].values
                call_strikes_all = calls["strike"].values

                put_otm_idx = int(np.argmin(np.abs(put_strikes - otm_put_strike)))
                call_otm_idx = int(np.argmin(np.abs(call_strikes_all - otm_call_strike)))

                put_otm_row = puts.iloc[put_otm_idx]
                call_otm_row = calls.iloc[call_otm_idx]

                otm_put_ivs.append(float(put_otm_row["impliedVolatility"]))
                otm_call_ivs.append(float(call_otm_row["impliedVolatility"]))

            except Exception as e:
                logger.debug(f"IV chain error for {ticker} expiry {expiry}: {e}")
                continue

        if not atm_iv_values:
            return _zero_result(ticker)

        atm_iv = float(np.mean(atm_iv_values))

        iv_rank = 0.0
        if realized_30d_vol > 0:
            iv_rank = min(100.0, atm_iv / realized_30d_vol * 50)

        expected_move_1w = spot * atm_iv * math.sqrt(7 / 365)
        expected_move_1m = spot * atm_iv * math.sqrt(30 / 365)

        put_call_skew = 0.0
        if otm_put_ivs and otm_call_ivs:
            put_call_skew = float(np.mean(otm_put_ivs) - np.mean(otm_call_ivs))

        if len(term_structure) < 2:
            term_structure = []

        result = IVAnalytics(
            ticker=ticker,
            atm_iv=round(atm_iv, 4),
            iv_rank=round(iv_rank, 2),
            expected_move_1w=round(expected_move_1w, 2),
            expected_move_1m=round(expected_move_1m, 2),
            put_call_skew=round(put_call_skew, 4),
            term_structure=[round(v, 4) for v in term_structure],
            timestamp=datetime.now(timezone.utc),
        )

        cache.set(cache_key, result.model_dump())
        return result

    except Exception as e:
        logger.error(f"IV analytics error for {ticker}: {e}")
        return _zero_result(ticker)
