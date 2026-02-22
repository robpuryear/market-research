"""
Options Chain Fetcher

Fetches options chain data from yfinance with Greeks calculations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import yfinance as yf
import pandas as pd
import numpy as np

from models.options import (
    OptionContract,
    OptionsChain,
    OptionsAnalytics,
    ExpirationDate,
)
from core import cache

logger = logging.getLogger(__name__)


async def fetch_options_chain(
    ticker: str,
    expiration: Optional[str] = None
) -> Optional[OptionsChain]:
    """
    Fetch options chain for a ticker and expiration.

    Args:
        ticker: Stock ticker symbol
        expiration: Expiration date (YYYY-MM-DD). If None, uses nearest expiration.

    Returns:
        OptionsChain with calls and puts
    """
    cache_key = f"options_chain_{ticker}_{expiration or 'nearest'}"
    cached = cache.get(cache_key, "options")

    if cached:
        logger.info(f"Using cached options chain for {ticker}")
        return OptionsChain(**cached)

    try:
        logger.info(f"Fetching options chain for {ticker}, expiration: {expiration or 'nearest'}")

        stock = yf.Ticker(ticker)
        spot_price = stock.info.get('currentPrice') or stock.info.get('regularMarketPrice')

        if not spot_price:
            # Fallback to recent price
            hist = stock.history(period="1d")
            if not hist.empty:
                spot_price = hist['Close'].iloc[-1]
            else:
                logger.error(f"Could not get spot price for {ticker}")
                return None

        # Get available expirations
        expirations = stock.options
        if not expirations or len(expirations) == 0:
            logger.warning(f"No options available for {ticker}")
            return None

        # Use specified expiration or nearest
        if expiration:
            if expiration not in expirations:
                logger.warning(f"Expiration {expiration} not available for {ticker}")
                expiration = expirations[0]
        else:
            expiration = expirations[0]

        # Fetch options data
        opt = stock.option_chain(expiration)
        calls_df = opt.calls
        puts_df = opt.puts

        if calls_df.empty and puts_df.empty:
            logger.warning(f"Empty options chain for {ticker}")
            return None

        # Parse expiration date
        exp_date = pd.to_datetime(expiration)
        days_to_exp = (exp_date - pd.Timestamp.now()).days

        # Process calls
        calls = []
        for _, row in calls_df.iterrows():
            contract = _parse_contract(row, "call", spot_price, days_to_exp, expiration)
            if contract:
                calls.append(contract)

        # Process puts
        puts = []
        for _, row in puts_df.iterrows():
            contract = _parse_contract(row, "put", spot_price, days_to_exp, expiration)
            if contract:
                puts.append(contract)

        # Calculate summary stats
        total_call_volume = sum(c.volume or 0 for c in calls)
        total_put_volume = sum(p.volume or 0 for p in puts)
        total_call_oi = sum(c.open_interest or 0 for c in calls)
        total_put_oi = sum(p.open_interest or 0 for p in puts)

        pc_volume_ratio = total_put_volume / total_call_volume if total_call_volume > 0 else None
        pc_oi_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else None

        chain = OptionsChain(
            ticker=ticker,
            spot_price=float(spot_price),
            expiration=expiration,
            calls=calls,
            puts=puts,
            total_call_volume=total_call_volume,
            total_put_volume=total_put_volume,
            total_call_oi=total_call_oi,
            total_put_oi=total_put_oi,
            put_call_volume_ratio=pc_volume_ratio,
            put_call_oi_ratio=pc_oi_ratio,
            timestamp=datetime.now(timezone.utc),
        )

        # Cache for 5 minutes (options data changes frequently)
        cache.set(cache_key, chain.model_dump(), ttl=300)

        logger.info(f"Fetched options chain: {len(calls)} calls, {len(puts)} puts")
        return chain

    except Exception as e:
        logger.error(f"Failed to fetch options chain for {ticker}: {e}", exc_info=True)
        return None


def _parse_contract(
    row: pd.Series,
    contract_type: str,
    spot_price: float,
    days_to_exp: int,
    expiration: str
) -> Optional[OptionContract]:
    """Parse a single option contract from DataFrame row"""
    try:
        strike = float(row.get('strike', 0))

        # Pricing
        bid = _safe_float(row.get('bid'))
        ask = _safe_float(row.get('ask'))
        last = _safe_float(row.get('lastPrice'))

        mark = None
        if bid is not None and ask is not None:
            mark = (bid + ask) / 2
        elif last is not None:
            mark = last

        # Volume & OI
        volume = int(row.get('volume', 0)) if pd.notna(row.get('volume')) else 0
        oi = int(row.get('openInterest', 0)) if pd.notna(row.get('openInterest')) else 0

        # Greeks
        iv = _safe_float(row.get('impliedVolatility'))
        delta = _safe_float(row.get('delta'))
        gamma = _safe_float(row.get('gamma'))
        theta = _safe_float(row.get('theta'))
        vega = _safe_float(row.get('vega'))
        rho = _safe_float(row.get('rho'))

        # Calculate intrinsic and extrinsic value
        if contract_type == "call":
            intrinsic = max(0, spot_price - strike)
        else:  # put
            intrinsic = max(0, strike - spot_price)

        extrinsic = (mark or 0) - intrinsic if mark is not None else 0

        # Determine moneyness
        itm = intrinsic > 0
        atm_threshold = spot_price * 0.02  # Within 2% of spot

        if abs(spot_price - strike) <= atm_threshold:
            moneyness = "ATM"
        elif itm:
            moneyness = "ITM"
        else:
            moneyness = "OTM"

        # Percent change
        pct_change = _safe_float(row.get('percentChange'))

        contract = OptionContract(
            symbol=row.get('contractSymbol', f"{contract_type.upper()}_{strike}"),
            strike=strike,
            expiration=expiration,
            contract_type=contract_type,
            bid=bid,
            ask=ask,
            last=last,
            mark=mark,
            volume=volume,
            open_interest=oi,
            implied_volatility=iv,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho,
            in_the_money=itm,
            intrinsic_value=intrinsic,
            extrinsic_value=extrinsic,
            moneyness=moneyness,
            days_to_expiration=days_to_exp,
            percent_change=pct_change,
        )

        return contract

    except Exception as e:
        logger.warning(f"Failed to parse contract: {e}")
        return None


def _safe_float(value) -> Optional[float]:
    """Safely convert value to float, handling NaN"""
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


async def fetch_expirations(ticker: str) -> List[ExpirationDate]:
    """
    Fetch available expiration dates for a ticker.

    Returns:
        List of ExpirationDate objects with metadata
    """
    cache_key = f"options_expirations_{ticker}"
    cached = cache.get(cache_key, "options")

    if cached:
        return [ExpirationDate(**exp) for exp in cached]

    try:
        stock = yf.Ticker(ticker)
        expirations = stock.options

        if not expirations:
            return []

        result = []
        today = datetime.now().date()

        for exp_str in expirations:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            days_until = (exp_date - today).days

            # Determine expiration type
            # Weekly: typically Fridays, monthly: 3rd Friday
            is_monthly = exp_date.day >= 15 and exp_date.day <= 21
            is_quarterly = is_monthly and exp_date.month in [3, 6, 9, 12]
            is_weekly = not is_monthly and exp_date.weekday() == 4  # Friday

            exp_info = ExpirationDate(
                date=exp_str,
                days_until=days_until,
                is_weekly=is_weekly,
                is_monthly=is_monthly,
                is_quarterly=is_quarterly,
            )
            result.append(exp_info)

        # Cache for 1 hour (expirations don't change often)
        cache.set(cache_key, [e.model_dump() for e in result], ttl=3600)

        logger.info(f"Found {len(result)} expirations for {ticker}")
        return result

    except Exception as e:
        logger.error(f"Failed to fetch expirations for {ticker}: {e}")
        return []


async def fetch_options_analytics(ticker: str) -> Optional[OptionsAnalytics]:
    """
    Fetch advanced options analytics for a ticker.

    Includes IV rank, max pain, P/C ratios, etc.
    """
    cache_key = f"options_analytics_{ticker}"
    cached = cache.get(cache_key, "options")

    if cached:
        return OptionsAnalytics(**cached)

    try:
        # Fetch current chain for nearest expiration
        chain = await fetch_options_chain(ticker, None)
        if not chain:
            return None

        # Calculate ATM IV (average of ATM call and put IV)
        atm_strike = min(chain.calls + chain.puts,
                         key=lambda c: abs(c.strike - chain.spot_price),
                         default=None)

        current_iv = atm_strike.implied_volatility if atm_strike else None

        # TODO: Calculate IV rank (requires historical IV data)
        # For now, set to None - would need 52-week IV history
        iv_rank = None
        iv_percentile = None

        # Calculate 30-day historical volatility
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if not hist.empty:
            returns = np.log(hist['Close'] / hist['Close'].shift(1))
            hv_30 = returns.std() * np.sqrt(252)  # Annualized
        else:
            hv_30 = None

        analytics = OptionsAnalytics(
            ticker=ticker,
            spot_price=chain.spot_price,
            iv_rank=iv_rank,
            iv_percentile=iv_percentile,
            current_iv=current_iv,
            hv_30day=hv_30,
            put_call_ratio=chain.put_call_volume_ratio,
            max_pain=None,  # TODO: Implement max pain calculation
            gamma_exposure=None,  # TODO: Implement GEX calculation
            nearest_expiration=chain.expiration,
            days_to_expiration=chain.calls[0].days_to_expiration if chain.calls else None,
            timestamp=datetime.now(timezone.utc),
        )

        # Cache for 15 minutes
        cache.set(cache_key, analytics.model_dump(), ttl=900)

        return analytics

    except Exception as e:
        logger.error(f"Failed to fetch options analytics for {ticker}: {e}")
        return None
