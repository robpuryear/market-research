import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select, desc, delete

from models.reports import ReportMeta
from engines.market_data import macro, sectors
from engines.watchlist import price_data, fundamentals, options_flow
from engines.analytics import ml_signals, correlation, short_squeeze
from engines.sentiment import flow_toxicity
from report_engine.renderers import charts, tables, scanner_report
from engines.market_data import technicals

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


async def _load_index_db(session) -> list:
    """Load report index from DB (for route handlers)."""
    from db.base import ReportRow
    result = await session.execute(
        select(ReportRow).order_by(desc(ReportRow.generated_at)).limit(50)
    )
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "type": r.type,
            "ticker": r.ticker,
            "generated_at": r.generated_at.isoformat(),
            "path": r.path,
            "file_size_kb": r.file_size_kb,
            "title": r.title,
        }
        for r in rows
    ]


async def _delete_report_db(session, report_id: str) -> None:
    """Delete a report row from DB."""
    from db.base import ReportRow
    row = await session.get(ReportRow, report_id)
    if row:
        await session.delete(row)
        await session.commit()


async def _register_report(meta: ReportMeta) -> None:
    """Persist report metadata to DB. Creates its own session."""
    from db.session import AsyncSessionLocal
    from db.base import ReportRow
    async with AsyncSessionLocal() as session:
        # Remove duplicate
        from sqlalchemy import delete as sa_delete
        await session.execute(sa_delete(ReportRow).where(ReportRow.id == meta.id))
        session.add(ReportRow(
            id=meta.id,
            type=meta.type,
            ticker=meta.ticker,
            generated_at=meta.generated_at,
            path=meta.path,
            file_size_kb=meta.file_size_kb,
            title=meta.title,
        ))
        await session.commit()


async def generate_report_a(standalone: bool = False) -> ReportMeta:
    """Daily Market Report."""
    logger.info("Generating Report A (Daily Market Report)")

    snapshot, sector_list, stock_list = await asyncio.gather(
        macro.fetch_snapshot(),
        sectors.fetch_rotation(),
        price_data.bulk_fetch(),
    )

    vix_html = charts.vix_gauge(snapshot.vix)
    sector_heat_html = charts.sector_heatmap([s.model_dump() for s in sector_list])
    sector_tbl_html = tables.sector_table([s.model_dump() for s in sector_list])
    watchlist_tbl_html = tables.watchlist_table([s.model_dump() for s in stock_list])

    template = jinja_env.get_template("report_a.html")
    html = template.render(
        title="Daily Market Report",
        report_type="Daily Market Report",
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        standalone=standalone,
        snapshot=snapshot,
        vix_gauge_html=vix_html,
        sector_heatmap_html=sector_heat_html,
        sector_table_html=sector_tbl_html,
        watchlist_table_html=watchlist_tbl_html,
        breadth=None,
    )

    report_id = str(uuid.uuid4())[:8]
    filename = f"report_a_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{report_id}.html"
    path = REPORTS_DIR / filename
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(html)

    size_kb = round(os.path.getsize(path) / 1024, 1)
    meta = ReportMeta(
        id=report_id,
        type="daily",
        generated_at=datetime.now(timezone.utc),
        path=str(path),
        file_size_kb=size_kb,
        title=f"Daily Market Report — {datetime.now(timezone.utc).strftime('%b %d, %Y')}",
    )
    _register_report(meta)
    logger.info(f"Report A generated: {filename} ({size_kb}KB)")
    return meta


async def generate_report_b(standalone: bool = False) -> ReportMeta:
    """Advanced Analytics Report."""
    logger.info("Generating Report B (Advanced Analytics)")

    from core.watchlist_manager import get_tickers
    tickers_from_config = get_tickers()

    signals_list, corr_data, squeeze_data, flow_data = await asyncio.gather(
        asyncio.gather(*[ml_signals.run_all(t) for t in tickers_from_config]),
        correlation.compute_matrix(),
        short_squeeze.score_all(),
        asyncio.gather(*[flow_toxicity.compute(t) for t in tickers_from_config[:5]]),
    )

    # Options flow per ticker
    all_options_flow = []
    for ticker in tickers_from_config:
        flows = await options_flow.detect_unusual(ticker)
        all_options_flow.append({
            "ticker": ticker,
            "flows": flows,
            "table_html": tables.options_flow_table([f.model_dump() for f in flows]),
        })

    corr_tickers = corr_data.get("tickers", [])
    corr_matrix = corr_data.get("matrix", {})
    corr_html = charts.correlation_heatmap(corr_tickers, corr_matrix) if corr_tickers else ""

    template = jinja_env.get_template("report_b.html")
    html = template.render(
        title="Advanced Analytics Report",
        report_type="Advanced Analytics",
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        standalone=standalone,
        all_signals=list(signals_list),
        correlation_html=corr_html,
        all_options_flow=all_options_flow,
        squeeze_scores=squeeze_data,
        flow_toxicity=[ft.model_dump() for ft in flow_data],
    )

    report_id = str(uuid.uuid4())[:8]
    filename = f"report_b_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{report_id}.html"
    path = REPORTS_DIR / filename
    with open(path, "w") as f:
        f.write(html)

    size_kb = round(os.path.getsize(path) / 1024, 1)
    meta = ReportMeta(
        id=report_id,
        type="analytics",
        generated_at=datetime.now(timezone.utc),
        path=str(path),
        file_size_kb=size_kb,
        title=f"Advanced Analytics — {datetime.now(timezone.utc).strftime('%b %d, %Y')}",
    )
    _register_report(meta)
    logger.info(f"Report B generated: {filename} ({size_kb}KB)")
    return meta


async def generate_report_c(ticker: str, standalone: bool = False) -> ReportMeta:
    """Deep Research Report for a specific ticker."""
    logger.info(f"Generating Report C (Deep Research) for {ticker}")

    tech, detail, flow, signals_data = await asyncio.gather(
        technicals.compute(ticker),
        fundamentals.deep_dive(ticker),
        options_flow.detect_unusual(ticker),
        ml_signals.run_all(ticker),
    )

    candle_html = charts.candlestick_with_mas(
        dates=tech.dates[-120:],
        opens=tech.opens[-120:],
        highs=tech.highs[-120:],
        lows=tech.lows[-120:],
        closes=tech.closes[-120:],
        ma_20=tech.ma_20[-120:],
        ma_50=tech.ma_50[-120:],
        ma_200=tech.ma_200[-120:],
        ticker=ticker,
        support_levels=tech.support_levels,
        resistance_levels=tech.resistance_levels,
    )
    rsi_html = charts.rsi_chart(tech.dates[-120:], tech.rsi[-120:], ticker)
    macd_html = charts.macd_chart(
        tech.dates[-120:],
        tech.macd_line[-120:],
        tech.macd_signal[-120:],
        tech.macd_histogram[-120:],
        ticker,
    )
    opts_html = tables.options_flow_table([f.model_dump() for f in flow])
    insider_html = tables.insider_table(detail.insider_transactions)

    template = jinja_env.get_template("report_c.html")
    html = template.render(
        title=f"Deep Research: {ticker}",
        report_type=f"Deep Research · {ticker}",
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        standalone=standalone,
        ticker=ticker,
        detail=detail,
        tech=tech,
        candlestick_html=candle_html,
        rsi_html=rsi_html,
        macd_html=macd_html,
        options_flow_html=opts_html,
        insider_table_html=insider_html,
        signals=signals_data.get("signals", []),
    )

    report_id = str(uuid.uuid4())[:8]
    filename = f"report_c_{ticker}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{report_id}.html"
    path = REPORTS_DIR / filename
    with open(path, "w") as f:
        f.write(html)

    size_kb = round(os.path.getsize(path) / 1024, 1)
    meta = ReportMeta(
        id=report_id,
        type="research",
        ticker=ticker,
        generated_at=datetime.now(timezone.utc),
        path=str(path),
        file_size_kb=size_kb,
        title=f"Deep Research: {ticker} — {datetime.now(timezone.utc).strftime('%b %d, %Y')}",
    )
    _register_report(meta)
    logger.info(f"Report C generated for {ticker}: {filename} ({size_kb}KB)")
    return meta


async def generate_scanner_report(standalone: bool = False) -> ReportMeta:
    """Daily Market Scanner Report."""
    logger.info("Generating Market Scanner Report")

    # Generate the scanner report
    report_data = await scanner_report.generate_scanner_report()

    report_id = str(uuid.uuid4())[:8]
    filename = f"scanner_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{report_id}.html"
    path = REPORTS_DIR / filename

    with open(path, "w") as f:
        f.write(report_data["html"])

    size_kb = round(os.path.getsize(path) / 1024, 1)
    meta = ReportMeta(
        id=report_id,
        type="scanner",
        generated_at=datetime.now(timezone.utc),
        path=str(path),
        file_size_kb=size_kb,
        title=report_data["title"],
    )
    _register_report(meta)
    logger.info(f"Scanner report generated: {filename} ({size_kb}KB)")
    return meta
