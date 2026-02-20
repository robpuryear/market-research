import asyncio
import yfinance as yf
from datetime import datetime, timezone
import logging
import math

from models.watchlist import StockDetailData, EarningsEntry
from core import cache, rate_limiter

logger = logging.getLogger(__name__)

RATING_MAP = {
    "Strong Buy": "Strong Buy",
    "Buy": "Buy",
    "Hold": "Hold",
    "Sell": "Sell",
    "Strong Sell": "Sell",
    "Overweight": "Buy",
    "Underweight": "Sell",
    "Neutral": "Hold",
    "Market Perform": "Hold",
    "Outperform": "Buy",
    "Underperform": "Sell",
}


def _normalize_rating(raw: str | None) -> str | None:
    if not raw:
        return None
    for k, v in RATING_MAP.items():
        if k.lower() in raw.lower():
            return v
    return "Hold"


def _sanitize_float(value) -> float | None:
    """Convert NaN and inf float values to None for JSON compatibility."""
    if value is None:
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None


async def deep_dive(ticker: str) -> StockDetailData:
    cache_key = f"fundamentals_{ticker}"
    cached = cache.get(cache_key, "fundamentals")
    if cached:
        return StockDetailData(**cached)

    rate_limiter.acquire("yfinance")

    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}

        # Insider transactions
        insiders = []
        try:
            insider_df = tk.insider_transactions
            if insider_df is not None and not insider_df.empty:
                # Fill NaN values before iteration
                insider_df = insider_df.fillna({"Shares": 0, "Value": 0, "Insider": "", "Transaction": "", "Start Date": ""})
                for _, row in insider_df.head(5).iterrows():
                    shares_val = _sanitize_float(row.get("Shares"))
                    value_val = _sanitize_float(row.get("Value"))
                    insiders.append({
                        "name": str(row.get("Insider", "")),
                        "transaction": str(row.get("Transaction", "")),
                        "shares": int(shares_val) if shares_val is not None else 0,
                        "value": value_val if value_val is not None else 0.0,
                        "date": str(row.get("Start Date", "")),
                    })
        except Exception:
            pass

        # Analyst recommendations
        analyst_rating = None
        price_target = None
        price_target_low = None
        price_target_high = None
        try:
            recs = tk.recommendations
            if recs is not None and not recs.empty:
                latest = recs.iloc[-1]
                analyst_rating = _normalize_rating(str(latest.get("To Grade", "")))
            price_target = info.get("targetMeanPrice")
            price_target_low = info.get("targetLowPrice")
            price_target_high = info.get("targetHighPrice")
        except Exception:
            pass

        # Earnings date
        earnings_date = None
        try:
            cal = tk.calendar
            if cal is not None and not cal.empty:
                earnings_col = "Earnings Date" if "Earnings Date" in cal.index else cal.index[0]
                earnings_date = str(cal.loc[earnings_col].iloc[0])
        except Exception:
            pass

        # Earnings history — try Alpha Vantage first, fall back to yfinance
        earnings_history = []
        earnings_surprise_pct = None
        try:
            from engines.market_data.alpha_vantage import fetch_earnings as av_fetch
            av_entries = await av_fetch(ticker)
            if av_entries:
                earnings_history = av_entries
                if av_entries:
                    earnings_surprise_pct = av_entries[0].surprise_pct
        except Exception:
            pass

        if not earnings_history:
            try:
                ed = tk.earnings_dates
                if ed is not None and not ed.empty:
                    for dt_idx, row in ed.head(8).iterrows():
                        est = row.get("EPS Estimate")
                        act = row.get("Reported EPS")
                        surp = row.get("Surprise(%)")

                        # Sanitize float values to handle NaN
                        eps_est = _sanitize_float(est)
                        eps_act = _sanitize_float(act)
                        surp_val = _sanitize_float(surp)
                        surp_pct = surp_val / 100 if surp_val is not None else None

                        earnings_history.append(EarningsEntry(
                            date=str(dt_idx)[:10] if dt_idx is not None else "",
                            eps_estimate=eps_est,
                            eps_actual=eps_act,
                            surprise_pct=surp_pct,
                        ))
                    if earnings_history and earnings_surprise_pct is None:
                        earnings_surprise_pct = earnings_history[0].surprise_pct
            except Exception:
                pass

        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
        prev_close = info.get("previousClose") or current_price
        change_pct = round((current_price - prev_close) / prev_close * 100, 2) if prev_close else 0.0

        volume = float(info.get("volume") or 0)
        avg_volume = float(info.get("averageVolume") or 1)

        result = StockDetailData(
            ticker=ticker,
            company_name=info.get("longName") or info.get("shortName") or ticker,
            sector=info.get("sector"),
            industry=info.get("industry"),
            price=round(float(current_price), 2),
            change_pct=change_pct,
            volume=volume,
            avg_volume=avg_volume,
            market_cap=_sanitize_float(info.get("marketCap")),
            pe_ratio=_sanitize_float(info.get("trailingPE")),
            forward_pe=_sanitize_float(info.get("forwardPE")),
            pb_ratio=_sanitize_float(info.get("priceToBook")),
            debt_to_equity=_sanitize_float(info.get("debtToEquity")),
            revenue_growth=_sanitize_float(info.get("revenueGrowth")),
            short_interest_pct=_sanitize_float(info.get("shortPercentOfFloat")),
            short_ratio=_sanitize_float(info.get("shortRatio")),
            analyst_rating=analyst_rating,
            price_target=_sanitize_float(price_target),
            price_target_low=_sanitize_float(price_target_low),
            price_target_high=_sanitize_float(price_target_high),
            earnings_date=earnings_date,
            earnings_surprise_pct=_sanitize_float(earnings_surprise_pct),
            profit_margin=_sanitize_float(info.get("profitMargins")),
            return_on_equity=_sanitize_float(info.get("returnOnEquity")),
            return_on_assets=_sanitize_float(info.get("returnOnAssets")),
            dividend_yield=_sanitize_float(info.get("dividendYield")),
            free_cash_flow=_sanitize_float(info.get("freeCashflow")),
            week_52_high=_sanitize_float(info.get("fiftyTwoWeekHigh")),
            week_52_low=_sanitize_float(info.get("fiftyTwoWeekLow")),
            earnings_history=earnings_history,
            institutional_ownership_pct=_sanitize_float(info.get("heldPercentInstitutions")),
            insider_transactions=insiders,
            unusual_options=[],  # Will be populated by route handler
            timestamp=datetime.now(timezone.utc),
        )

        cache.set(cache_key, result.model_dump())
        return result

    except Exception as e:
        logger.error(f"Error fetching fundamentals for {ticker}: {e}")
        stale = cache.get_stale(cache_key)
        if stale:
            logger.info(f"Returning stale fundamentals for {ticker}")
            return StockDetailData(**stale)
        raise
