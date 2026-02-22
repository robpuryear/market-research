"""
Portfolio Metrics Calculator

Computes portfolio performance, risk metrics, and allocation.
"""

from typing import List
from models.portfolio import PortfolioMetrics
from engines.portfolio.positions import get_all_positions, _load_transactions
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def calculate_portfolio_metrics(cash: float = 0.0) -> PortfolioMetrics:
    """Calculate comprehensive portfolio metrics"""
    positions = get_all_positions(include_closed=False)

    # Basic metrics
    total_cost_basis = sum(p.avg_cost_basis * p.quantity for p in positions)
    invested_value = sum(p.current_value or 0 for p in positions)
    total_value = invested_value + cash

    unrealized_pnl = sum(p.unrealized_pnl or 0 for p in positions)
    unrealized_pnl_pct = (unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0

    # Realized P&L (from closed positions)
    realized_pnl = calculate_realized_pnl()

    total_pnl = realized_pnl + unrealized_pnl

    # Total return calculation
    # Total invested = original cost basis + any realized losses (money lost)
    total_invested = total_cost_basis + abs(min(realized_pnl, 0))
    total_return_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    # Day change (TODO: requires historical snapshots)
    # For now, calculate from positions' daily change
    day_change = 0.0
    day_change_pct = 0.0

    # Position stats
    winning = [p for p in positions if (p.unrealized_pnl or 0) > 0]
    losing = [p for p in positions if (p.unrealized_pnl or 0) < 0]
    win_rate = len(winning) / len(positions) * 100 if positions else 0

    # Allocation
    if positions and invested_value > 0:
        largest_position_pct = max((p.current_value or 0) / invested_value * 100 for p in positions)
    else:
        largest_position_pct = 0.0

    sorted_positions = sorted(positions, key=lambda p: p.current_value or 0, reverse=True)
    top_3_value = sum((p.current_value or 0) for p in sorted_positions[:3])
    top_3_concentration = (top_3_value / invested_value * 100) if invested_value > 0 else 0

    # Sector allocation (TODO: would need to fetch sector data for each ticker)
    sectors = {}

    # Risk metrics (TODO: requires historical performance data)
    sharpe_ratio = None
    max_drawdown = None
    volatility = None
    beta = None

    return PortfolioMetrics(
        total_value=total_value,
        cash=cash,
        invested_value=invested_value,
        total_cost_basis=total_cost_basis,
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_pct=unrealized_pnl_pct,
        realized_pnl=realized_pnl,
        total_pnl=total_pnl,
        total_return_pct=total_return_pct,
        day_change=day_change,
        day_change_pct=day_change_pct,
        positions_count=len(positions),
        open_positions_count=len(positions),
        winning_positions_count=len(winning),
        losing_positions_count=len(losing),
        win_rate=win_rate,
        sharpe_ratio=sharpe_ratio,
        max_drawdown=max_drawdown,
        volatility=volatility,
        beta=beta,
        largest_position_pct=largest_position_pct,
        top_3_concentration=top_3_concentration,
        sectors=sectors,
        timestamp=datetime.now(timezone.utc)
    )


def calculate_realized_pnl() -> float:
    """
    Calculate realized P&L from closed positions.

    Uses FIFO (First In, First Out) accounting.
    """
    transactions = _load_transactions()

    # Group by ticker (not position_id, since we want to track across all positions)
    ticker_txns = {}
    for txn in transactions:
        ticker = txn["ticker"]
        if ticker not in ticker_txns:
            ticker_txns[ticker] = []
        ticker_txns[ticker].append(txn)

    total_realized = 0.0

    for ticker, txns in ticker_txns.items():
        # Sort by date
        sorted_txns = sorted(txns, key=lambda t: t["date"])

        buys = []
        sells = []

        for txn in sorted_txns:
            if txn["transaction_type"] == "buy":
                buys.append(txn)
            elif txn["transaction_type"] == "sell":
                sells.append(txn)

        if not sells:
            continue

        # Match sells to buys using FIFO
        buy_queue = buys.copy()

        for sell in sells:
            shares_to_sell = sell["quantity"]
            sell_price = sell["price"]
            sell_proceeds = 0.0
            sell_cost_basis = 0.0

            while shares_to_sell > 0 and buy_queue:
                buy = buy_queue[0]
                buy_shares = buy["quantity"]
                buy_price = buy["price"]

                if buy_shares <= shares_to_sell:
                    # Fully consume this buy
                    sell_proceeds += buy_shares * sell_price
                    sell_cost_basis += buy_shares * buy_price
                    shares_to_sell -= buy_shares
                    buy_queue.pop(0)
                else:
                    # Partially consume this buy
                    sell_proceeds += shares_to_sell * sell_price
                    sell_cost_basis += shares_to_sell * buy_price
                    buy["quantity"] -= shares_to_sell
                    shares_to_sell = 0

            realized_gain = sell_proceeds - sell_cost_basis - sell.get("commission", 0)
            total_realized += realized_gain

    logger.info(f"Calculated realized P&L: ${total_realized:.2f}")
    return total_realized
