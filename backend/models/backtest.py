from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class BacktestConfig(BaseModel):
    """Configuration for a backtest run"""
    strategy_type: str  # "buy_hold", "rsi_reversal", "macd_cross", etc.
    ticker: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    initial_capital: float = 100000.0
    position_size: float = 1.0  # % of capital per trade (1.0 = 100% for buy-hold)
    commission: float = 0.001   # 0.1% per trade
    slippage: float = 0.001     # 0.1% slippage

    # Strategy-specific parameters
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0

    # Risk management
    stop_loss: Optional[float] = None  # % loss to exit (e.g., 0.05 = 5%)
    take_profit: Optional[float] = None  # % gain to exit (e.g., 0.10 = 10%)


class Trade(BaseModel):
    """Individual trade record"""
    entry_date: str
    exit_date: Optional[str] = None
    entry_price: float
    exit_price: Optional[float] = None
    shares: int
    pnl: float = 0.0
    return_pct: float = 0.0
    hold_days: int = 0
    entry_reason: str
    exit_reason: Optional[str] = None
    commission_paid: float = 0.0


class BacktestResult(BaseModel):
    """Complete backtest results with metrics"""
    config: BacktestConfig
    trades: List[Trade]

    # Portfolio metrics
    final_value: float
    total_return: float  # Total % return
    annual_return: float  # Annualized return (CAGR)

    # Risk metrics
    sharpe_ratio: float
    max_drawdown: float  # Worst peak-to-trough % loss
    volatility: float    # Annualized volatility

    # Trade metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    avg_win_loss_ratio: float
    profit_factor: float

    # Time series data for charts
    equity_curve: List[float]  # Portfolio value over time
    dates: List[str]
    drawdown_curve: List[float]

    # Benchmark comparison
    benchmark_return: float  # Buy-and-hold return
    alpha: float  # Strategy return - benchmark return

    # Execution metadata
    start_date: str
    end_date: str
    total_days: int
    timestamp: datetime


class BacktestSummary(BaseModel):
    """Lightweight summary for listing backtests"""
    id: str
    strategy_type: str
    ticker: str
    start_date: str
    end_date: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    timestamp: datetime
