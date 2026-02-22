"""
Options Spread Analyzer

Analyzes options spreads and generates P/L diagrams.
Supports vertical spreads, iron condors, butterflies, etc.
"""

import logging
from typing import List, Tuple, Optional
import numpy as np
from datetime import datetime, timezone

from models.options import SpreadLeg, SpreadAnalysis

logger = logging.getLogger(__name__)


def analyze_spread(
    ticker: str,
    spot_price: float,
    legs: List[SpreadLeg],
    spread_type: Optional[str] = None
) -> SpreadAnalysis:
    """
    Analyze an options spread strategy.

    Args:
        ticker: Stock ticker
        spot_price: Current stock price
        legs: List of spread legs (contracts)
        spread_type: Optional spread type (auto-detected if not provided)

    Returns:
        SpreadAnalysis with P/L diagram and metrics
    """
    if not legs:
        raise ValueError("At least one leg is required")

    # Auto-detect spread type if not provided
    if not spread_type:
        spread_type = _detect_spread_type(legs)

    # Calculate net debit/credit
    net_debit_credit = sum(
        leg.price * leg.quantity * (100 if leg.action == "sell" else -100)
        for leg in legs
    )

    # Calculate spread Greeks
    net_delta = sum(leg.delta * leg.quantity * (1 if leg.action == "buy" else -1) for leg in legs if leg.delta)
    net_gamma = 0.0  # TODO: Sum gammas from all legs
    net_theta = 0.0  # TODO: Sum thetas from all legs
    net_vega = 0.0   # TODO: Sum vegas from all legs

    # Generate P/L diagram data
    price_points, pnl_at_expiration = _calculate_pnl_diagram(legs, spot_price)

    # Calculate max profit, max loss, breakevens
    max_profit = float(np.max(pnl_at_expiration))
    max_loss = float(np.min(pnl_at_expiration))
    breakeven_points = _find_breakeven_points(price_points, pnl_at_expiration)

    # Calculate risk/reward
    risk_reward_ratio = abs(max_profit / max_loss) if max_loss != 0 else 0.0

    # Estimate probability of profit (simplified)
    # Percentage of price points with positive P/L
    prob_profit = float(np.sum(np.array(pnl_at_expiration) > 0) / len(pnl_at_expiration))

    analysis = SpreadAnalysis(
        spread_type=spread_type,
        ticker=ticker,
        spot_price=spot_price,
        legs=legs,
        max_profit=max_profit,
        max_loss=max_loss,
        breakeven_points=breakeven_points,
        net_debit_credit=net_debit_credit,
        net_delta=net_delta,
        net_gamma=net_gamma,
        net_theta=net_theta,
        net_vega=net_vega,
        risk_reward_ratio=risk_reward_ratio,
        probability_of_profit=prob_profit,
        price_points=price_points,
        pnl_at_expiration=pnl_at_expiration,
        timestamp=datetime.now(timezone.utc),
    )

    logger.info(f"Analyzed {spread_type} spread: Max P/L: ${max_profit:.2f}/${max_loss:.2f}")
    return analysis


def _detect_spread_type(legs: List[SpreadLeg]) -> str:
    """Auto-detect spread type based on leg configuration"""
    if len(legs) == 1:
        leg = legs[0]
        if leg.action == "buy":
            return f"long_{leg.contract_type}"
        else:
            return f"short_{leg.contract_type}"

    if len(legs) == 2:
        # Vertical spread
        sorted_legs = sorted(legs, key=lambda x: x.strike)
        if sorted_legs[0].contract_type == sorted_legs[1].contract_type == "call":
            if sorted_legs[0].action == "buy" and sorted_legs[1].action == "sell":
                return "bull_call_spread"
            else:
                return "bear_call_spread"
        elif sorted_legs[0].contract_type == sorted_legs[1].contract_type == "put":
            if sorted_legs[0].action == "sell" and sorted_legs[1].action == "buy":
                return "bull_put_spread"
            else:
                return "bear_put_spread"

    if len(legs) == 4:
        # Could be iron condor, iron butterfly, etc.
        calls = [l for l in legs if l.contract_type == "call"]
        puts = [l for l in legs if l.contract_type == "put"]
        if len(calls) == 2 and len(puts) == 2:
            return "iron_condor"

    return "custom_spread"


def _calculate_pnl_diagram(
    legs: List[SpreadLeg],
    spot_price: float,
    num_points: int = 100
) -> Tuple[List[float], List[float]]:
    """
    Calculate P/L at expiration across a range of stock prices.

    Returns:
        (price_points, pnl_values)
    """
    # Determine price range (±50% from spot, or based on strikes)
    all_strikes = [leg.strike for leg in legs]
    min_strike = min(all_strikes)
    max_strike = max(all_strikes)

    # Expand range beyond strikes
    price_min = min(spot_price * 0.5, min_strike * 0.8)
    price_max = max(spot_price * 1.5, max_strike * 1.2)

    # Generate price points
    price_points = np.linspace(price_min, price_max, num_points)
    pnl_values = []

    for price in price_points:
        total_pnl = 0.0

        for leg in legs:
            # Calculate intrinsic value at expiration
            if leg.contract_type == "call":
                intrinsic = max(0, price - leg.strike)
            else:  # put
                intrinsic = max(0, leg.strike - price)

            # P&L for this leg
            # If we bought: P&L = (intrinsic - premium_paid) * quantity * 100
            # If we sold: P&L = (premium_received - intrinsic) * quantity * 100
            if leg.action == "buy":
                leg_pnl = (intrinsic - leg.price) * leg.quantity * 100
            else:  # sell
                leg_pnl = (leg.price - intrinsic) * leg.quantity * 100

            total_pnl += leg_pnl

        pnl_values.append(total_pnl)

    return price_points.tolist(), pnl_values


def _find_breakeven_points(
    price_points: List[float],
    pnl_values: List[float],
    tolerance: float = 0.1
) -> List[float]:
    """
    Find breakeven points where P/L crosses zero.

    Returns:
        List of stock prices where P/L ≈ 0
    """
    breakevens = []
    pnl_array = np.array(pnl_values)

    # Find sign changes
    for i in range(len(pnl_array) - 1):
        if pnl_array[i] * pnl_array[i + 1] < 0:  # Sign change
            # Linear interpolation to find exact breakeven
            x1, x2 = price_points[i], price_points[i + 1]
            y1, y2 = pnl_array[i], pnl_array[i + 1]

            # Breakeven = x1 - y1 * (x2 - x1) / (y2 - y1)
            breakeven = x1 - y1 * (x2 - x1) / (y2 - y1)
            breakevens.append(float(breakeven))

    return breakevens


# Pre-built spread templates for quick creation

def create_bull_call_spread(
    ticker: str,
    spot_price: float,
    long_strike: float,
    short_strike: float,
    expiration: str,
    long_price: float,
    short_price: float,
    quantity: int = 1
) -> SpreadAnalysis:
    """Create and analyze a bull call spread"""
    legs = [
        SpreadLeg(
            strike=long_strike,
            contract_type="call",
            action="buy",
            quantity=quantity,
            price=long_price,
            expiration=expiration,
        ),
        SpreadLeg(
            strike=short_strike,
            contract_type="call",
            action="sell",
            quantity=quantity,
            price=short_price,
            expiration=expiration,
        ),
    ]
    return analyze_spread(ticker, spot_price, legs, "bull_call_spread")


def create_iron_condor(
    ticker: str,
    spot_price: float,
    put_long_strike: float,
    put_short_strike: float,
    call_short_strike: float,
    call_long_strike: float,
    expiration: str,
    put_long_price: float,
    put_short_price: float,
    call_short_price: float,
    call_long_price: float,
    quantity: int = 1
) -> SpreadAnalysis:
    """Create and analyze an iron condor"""
    legs = [
        # Put spread (lower strikes)
        SpreadLeg(strike=put_long_strike, contract_type="put", action="buy", quantity=quantity, price=put_long_price, expiration=expiration),
        SpreadLeg(strike=put_short_strike, contract_type="put", action="sell", quantity=quantity, price=put_short_price, expiration=expiration),
        # Call spread (higher strikes)
        SpreadLeg(strike=call_short_strike, contract_type="call", action="sell", quantity=quantity, price=call_short_price, expiration=expiration),
        SpreadLeg(strike=call_long_strike, contract_type="call", action="buy", quantity=quantity, price=call_long_price, expiration=expiration),
    ]
    return analyze_spread(ticker, spot_price, legs, "iron_condor")
