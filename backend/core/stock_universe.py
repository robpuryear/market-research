"""Stock universe definitions for market scanning."""
import logging
from typing import List
import yfinance as yf

logger = logging.getLogger(__name__)

# S&P 500 top holdings (curated list of most liquid stocks)
SP500_TOP_100 = [
    # Mega Cap Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL", "ADBE",
    # Large Cap Tech
    "CRM", "CSCO", "INTC", "AMD", "QCOM", "TXN", "AMAT", "MU", "LRCX", "KLAC",
    # Financials
    "BRK.B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "C", "SCHW",
    # Healthcare
    "UNH", "JNJ", "LLY", "ABBV", "MRK", "TMO", "ABT", "DHR", "PFE", "BMY",
    # Consumer
    "WMT", "HD", "PG", "KO", "PEP", "COST", "MCD", "NKE", "SBUX", "TGT",
    # Communication
    "DIS", "CMCSA", "NFLX", "VZ", "T", "TMUS", "CHTR", "EA", "TTWO", "SPOT",
    # Industrial
    "BA", "UPS", "CAT", "GE", "HON", "UNP", "RTX", "LMT", "MMM", "DE",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL",
    # Materials
    "LIN", "APD", "ECL", "SHW", "NEM", "FCX", "NUE", "DOW", "DD", "ALB",
    # Real Estate & Utilities
    "AMT", "PLD", "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL",
]

# High momentum / meme stocks (often have squeeze potential)
HIGH_MOMENTUM_STOCKS = [
    "GME", "AMC", "BBBY", "PLTR", "RIVN", "LCID", "SOFI", "HOOD", "COIN",
    "RBLX", "U", "DKNG", "MARA", "RIOT", "ABNB", "DASH", "UBER", "LYFT",
    "SNAP", "PINS", "TWLO", "ZM", "DOCU", "SHOP", "SQ", "PYPL", "ROKU",
]

# Small/Mid cap with options activity
SMALL_MID_CAP = [
    "CVNA", "UPST", "AFRM", "FUBO", "SKLZ", "APPS", "PTON", "W", "CHWY",
    "FVRR", "ETSY", "CRWD", "ZS", "DDOG", "NET", "SNOW", "MDB", "TEAM",
]


def get_universe(universe_type: str = "top100", limit: int = None) -> List[str]:
    """
    Get a list of tickers for market scanning.

    Args:
        universe_type: "top100" (S&P 500 top 100), "momentum" (meme/high momentum),
                      "small_mid" (small/mid cap), "all" (combined)
        limit: Optional limit on number of tickers returned

    Returns:
        List of ticker symbols
    """
    if universe_type == "top100":
        tickers = SP500_TOP_100
    elif universe_type == "momentum":
        tickers = HIGH_MOMENTUM_STOCKS
    elif universe_type == "small_mid":
        tickers = SMALL_MID_CAP
    elif universe_type == "all":
        tickers = list(set(SP500_TOP_100 + HIGH_MOMENTUM_STOCKS + SMALL_MID_CAP))
    else:
        logger.warning(f"Unknown universe type: {universe_type}, defaulting to top100")
        tickers = SP500_TOP_100

    if limit:
        tickers = tickers[:limit]

    logger.info(f"Loaded {len(tickers)} tickers from universe '{universe_type}'")
    return tickers


def validate_ticker(ticker: str) -> bool:
    """Quick validation that a ticker exists and is tradeable."""
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        # Check if it has a valid price
        if info and (info.get("regularMarketPrice") or info.get("currentPrice")):
            return True
    except Exception:
        pass
    return False
