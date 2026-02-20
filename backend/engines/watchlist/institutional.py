"""Institutional ownership and insider data - fetched as part of fundamentals."""
import yfinance as yf
import logging

logger = logging.getLogger(__name__)


async def get_institutional_summary(ticker: str) -> dict:
    """Return institutional ownership summary."""
    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        return {
            "institutional_ownership_pct": info.get("heldPercentInstitutions"),
            "insider_ownership_pct": info.get("heldPercentInsiders"),
        }
    except Exception as e:
        logger.warning(f"Error fetching institutional data for {ticker}: {e}")
        return {}
