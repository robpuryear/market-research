"""Daily market scanner report renderer."""
import logging
from datetime import datetime
from typing import List
from backend.models.analytics import ScanCandidate
from backend.engines.analytics import market_scanner

logger = logging.getLogger(__name__)


def _render_signal_badges(candidate: ScanCandidate) -> str:
    """Render ML signal badges HTML."""
    if not candidate.ml_signals:
        return '<span class="badge neutral">No signals</span>'

    badges = []
    for sig in candidate.ml_signals[:5]:  # Limit to 5 signals
        badge_class = "bullish" if sig.direction == "bullish" else "bearish" if sig.direction == "bearish" else "neutral"
        badges.append(f'<span class="badge {badge_class}">{sig.signal_type}</span>')

    return " ".join(badges)


def _render_score_bar(score: float, label: str) -> str:
    """Render a horizontal score bar."""
    color = "#22c55e" if score >= 70 else "#eab308" if score >= 40 else "#ef4444"
    return f'''
    <div class="score-item">
        <div class="score-label">{label}</div>
        <div class="score-bar-bg">
            <div class="score-bar-fill" style="width: {score}%; background-color: {color};"></div>
        </div>
        <div class="score-value">{score:.1f}</div>
    </div>
    '''


def _render_candidate_card(candidate: ScanCandidate, rank: int) -> str:
    """Render a single candidate card."""
    return f'''
    <div class="candidate-card">
        <div class="candidate-header">
            <div class="rank-badge">#{rank}</div>
            <div class="candidate-title">
                <h2>{candidate.ticker}</h2>
                <div class="company-name">{candidate.company_name}</div>
            </div>
            <div class="composite-score">{candidate.composite_score:.1f}</div>
        </div>

        <div class="candidate-body">
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Price:</span>
                    <span class="info-value">${candidate.price:.2f}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Volume Ratio:</span>
                    <span class="info-value">{candidate.volume_ratio:.1f}x</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Market Cap:</span>
                    <span class="info-value">${candidate.market_cap / 1e9:.1f}B</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Sector:</span>
                    <span class="info-value">{candidate.sector or "—"}</span>
                </div>
            </div>

            <div class="scores-section">
                <h3>Opportunity Scores</h3>
                {_render_score_bar(candidate.squeeze_score, "Squeeze Potential")}
                {_render_score_bar(min(candidate.bullish_signal_count * 25, 100), "Technical Signals")}
                {_render_score_bar(min(candidate.unusual_options_count * 20, 100), "Options Activity")}
                {_render_score_bar(candidate.iv_rank, "IV Rank")}
            </div>

            <div class="signals-section">
                <h3>ML Signals ({candidate.bullish_signal_count} Bullish, {candidate.bearish_signal_count} Bearish)</h3>
                <div class="signal-badges">
                    {_render_signal_badges(candidate)}
                </div>
            </div>

            <div class="highlights">
                {'<span class="highlight">🔥 High Squeeze Score</span>' if candidate.squeeze_score > 70 else ''}
                {'<span class="highlight">📈 Unusual Options</span>' if candidate.unusual_options_count > 0 else ''}
                {'<span class="highlight">⚡ High IV</span>' if candidate.iv_rank > 80 else ''}
                {'<span class="highlight">📊 High Volume</span>' if candidate.volume_ratio > 2 else ''}
            </div>
        </div>
    </div>
    '''


async def generate_scanner_report() -> dict:
    """
    Generate daily market scanner report.

    Returns dict with 'title', 'html', 'metadata'
    """
    logger.info("Generating daily market scanner report")

    # Scan with broader parameters for daily report
    candidates = await market_scanner.scan_market(
        universe="all",  # Scan all universes
        limit=200,  # Scan more tickers
        min_price=3.0,
        max_price=2000.0,
        min_composite=55.0,  # Higher threshold
        top_n=10,
    )

    if not candidates:
        logger.warning("No candidates found in market scan")

    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p ET")

    # Render candidate cards
    cards_html = "\n".join(
        [_render_candidate_card(c, i + 1) for i, c in enumerate(candidates)]
    )

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Daily Market Scanner - {timestamp}</title>
        <style>
            {_get_styles()}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🚀 Daily Market Scanner</h1>
                <div class="subtitle">Top Stock Opportunities • {timestamp}</div>
            </header>

            <div class="summary">
                <div class="summary-stat">
                    <div class="stat-value">{len(candidates)}</div>
                    <div class="stat-label">Top Picks</div>
                </div>
                <div class="summary-stat">
                    <div class="stat-value">200</div>
                    <div class="stat-label">Stocks Scanned</div>
                </div>
                <div class="summary-stat">
                    <div class="stat-value">{candidates[0].composite_score:.0f}</div>
                    <div class="stat-label">Top Score</div>
                </div>
            </div>

            <div class="candidates">
                {cards_html if candidates else '<div class="no-data">No candidates found meeting criteria</div>'}
            </div>

            <footer>
                <p>Generated by Market Intelligence Platform • For informational purposes only</p>
            </footer>
        </div>
    </body>
    </html>
    '''

    return {
        "title": f"Market Scanner - {timestamp}",
        "html": html,
        "metadata": {
            "report_type": "scanner",
            "candidates_found": len(candidates),
            "top_score": candidates[0].composite_score if candidates else 0,
        },
    }


def _get_styles() -> str:
    """Return CSS styles for scanner report."""
    return '''
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f3f4f6; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }
        h1 { font-size: 32px; font-weight: 700; margin-bottom: 8px; }
        .subtitle { font-size: 16px; opacity: 0.9; }
        .summary { display: flex; gap: 20px; margin-bottom: 30px; }
        .summary-stat { background: white; border-radius: 8px; padding: 20px; flex: 1; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .stat-value { font-size: 36px; font-weight: 700; color: #667eea; }
        .stat-label { font-size: 14px; color: #6b7280; margin-top: 5px; }
        .candidates { display: flex; flex-direction: column; gap: 20px; }
        .candidate-card { background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }
        .candidate-header { background: linear-gradient(to right, #f9fafb, #f3f4f6); padding: 20px; display: flex; align-items: center; gap: 15px; border-bottom: 2px solid #e5e7eb; }
        .rank-badge { background: #667eea; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 18px; }
        .candidate-title { flex: 1; }
        .candidate-title h2 { font-size: 24px; color: #111827; margin-bottom: 4px; }
        .company-name { font-size: 14px; color: #6b7280; }
        .composite-score { background: #10b981; color: white; padding: 8px 16px; border-radius: 20px; font-size: 20px; font-weight: 700; }
        .candidate-body { padding: 20px; }
        .info-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .info-item { }
        .info-label { font-size: 12px; color: #6b7280; display: block; margin-bottom: 4px; }
        .info-value { font-size: 16px; font-weight: 600; color: #111827; }
        .scores-section { margin-bottom: 20px; }
        .scores-section h3 { font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 12px; }
        .score-item { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
        .score-label { width: 140px; font-size: 13px; color: #6b7280; }
        .score-bar-bg { flex: 1; height: 24px; background: #f3f4f6; border-radius: 4px; overflow: hidden; }
        .score-bar-fill { height: 100%; transition: width 0.3s; }
        .score-value { width: 40px; text-align: right; font-weight: 600; font-size: 14px; }
        .signals-section h3 { font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 10px; }
        .signal-badges { display: flex; flex-wrap: wrap; gap: 6px; }
        .badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
        .badge.bullish { background: #d1fae5; color: #065f46; }
        .badge.bearish { background: #fee2e2; color: #991b1b; }
        .badge.neutral { background: #f3f4f6; color: #6b7280; }
        .highlights { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 15px; padding-top: 15px; border-top: 1px solid #e5e7eb; }
        .highlight { background: #fef3c7; color: #92400e; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; }
        .no-data { text-align: center; padding: 40px; color: #6b7280; }
        footer { margin-top: 30px; padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }
    '''
