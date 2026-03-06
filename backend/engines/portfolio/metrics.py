"""
Portfolio Metrics Calculator — async, DB-backed.
"""

from datetime import datetime, timezone
from typing import List
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from models.portfolio import PortfolioMetrics
from engines.portfolio.positions import get_all_positions, load_all_transactions

logger = logging.getLogger(__name__)


async def calculate_portfolio_metrics(
    session: AsyncSession,
    cash: float = 0.0,
) -> PortfolioMetrics:
    """Calculate comprehensive portfolio metrics."""
    pos_list = await get_all_positions(session, include_closed=False)

    total_cost_basis = sum(p.avg_cost_basis * p.quantity for p in pos_list)
    invested_value = sum(p.current_value or 0 for p in pos_list)
    total_value = invested_value + cash

    unrealized_pnl = sum(p.unrealized_pnl or 0 for p in pos_list)
    unrealized_pnl_pct = (unrealized_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0

    realized_pnl = await calculate_realized_pnl(session)
    total_pnl = realized_pnl + unrealized_pnl

    total_invested = total_cost_basis + abs(min(realized_pnl, 0))
    total_return_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    winning = [p for p in pos_list if (p.unrealized_pnl or 0) > 0]
    losing = [p for p in pos_list if (p.unrealized_pnl or 0) < 0]
    win_rate = len(winning) / len(pos_list) * 100 if pos_list else 0

    if pos_list and invested_value > 0:
        largest_position_pct = max(
            (p.current_value or 0) / invested_value * 100 for p in pos_list
        )
    else:
        largest_position_pct = 0.0

    sorted_positions = sorted(pos_list, key=lambda p: p.current_value or 0, reverse=True)
    top_3_value = sum((p.current_value or 0) for p in sorted_positions[:3])
    top_3_concentration = (top_3_value / invested_value * 100) if invested_value > 0 else 0

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
        day_change=0.0,
        day_change_pct=0.0,
        positions_count=len(pos_list),
        open_positions_count=len(pos_list),
        winning_positions_count=len(winning),
        losing_positions_count=len(losing),
        win_rate=win_rate,
        sharpe_ratio=None,
        max_drawdown=None,
        volatility=None,
        beta=None,
        largest_position_pct=largest_position_pct,
        top_3_concentration=top_3_concentration,
        sectors={},
        timestamp=datetime.now(timezone.utc),
    )


async def calculate_realized_pnl(session: AsyncSession) -> float:
    """Calculate realized P&L from closed positions using FIFO."""
    transactions = await load_all_transactions(session)

    ticker_txns: dict = {}
    for txn in transactions:
        ticker = txn["ticker"]
        ticker_txns.setdefault(ticker, []).append(txn)

    total_realized = 0.0

    for ticker, txns in ticker_txns.items():
        sorted_txns = sorted(txns, key=lambda t: t["date"])
        buys = [t for t in sorted_txns if t["transaction_type"] == "buy"]
        sells = [t for t in sorted_txns if t["transaction_type"] == "sell"]

        if not sells:
            continue

        buy_queue = list(buys)
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
                    sell_proceeds += buy_shares * sell_price
                    sell_cost_basis += buy_shares * buy_price
                    shares_to_sell -= buy_shares
                    buy_queue.pop(0)
                else:
                    sell_proceeds += shares_to_sell * sell_price
                    sell_cost_basis += shares_to_sell * buy_price
                    buy["quantity"] -= shares_to_sell
                    shares_to_sell = 0

            realized_gain = sell_proceeds - sell_cost_basis - sell.get("commission", 0)
            total_realized += realized_gain

    logger.info(f"Calculated realized P&L: ${total_realized:.2f}")
    return total_realized
