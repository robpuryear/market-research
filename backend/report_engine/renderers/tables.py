"""DataFrame and dict → styled HTML tables for dark theme reports."""
import pandas as pd
from typing import List, Dict, Any


def _color_class(value: float) -> str:
    if value > 0:
        return "color:#22c55e"
    elif value < 0:
        return "color:#ef4444"
    return "color:#94a3b8"


def watchlist_table(stocks: List[Dict]) -> str:
    rows = ""
    for s in stocks:
        chg = s.get("change_pct", 0) or 0
        price_target = s.get("price_target")
        pt_str = f"${price_target:.2f}" if price_target else "—"
        si = s.get("short_interest_pct")
        si_str = f"{si*100:.1f}%" if si else "—"
        sq = s.get("squeeze_score")
        sq_str = f"{sq:.0f}" if sq else "—"

        rows += f"""
        <tr>
            <td style="font-weight:bold;color:#e2e8f0">{s.get('ticker','')}</td>
            <td>${s.get('price',0):.2f}</td>
            <td style="{_color_class(chg)}">{chg:+.2f}%</td>
            <td>{s.get('volume_ratio',1):.1f}x</td>
            <td>{s.get('analyst_rating','—') or '—'}</td>
            <td>{pt_str}</td>
            <td>{si_str}</td>
            <td>{sq_str}</td>
            <td style="color:{'#22c55e' if s.get('options_unusual') else '#64748b'}">
                {'● Unusual' if s.get('options_unusual') else '—'}
            </td>
        </tr>"""

    return f"""
    <table class="data-table">
        <thead>
            <tr>
                <th>Ticker</th><th>Price</th><th>Change</th><th>Vol Ratio</th>
                <th>Rating</th><th>PT</th><th>Short %</th><th>Squeeze</th><th>Options</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


def sector_table(sectors: List[Dict]) -> str:
    rows = ""
    for s in sectors:
        ch1d = s.get("change_1d", 0) or 0
        ch5d = s.get("change_5d", 0) or 0
        ch1m = s.get("change_1m", 0) or 0
        vs1d = s.get("vs_spy_1d", 0) or 0

        rows += f"""
        <tr>
            <td style="font-weight:bold;color:#e2e8f0">{s.get('ticker','')}</td>
            <td style="color:#94a3b8">{s.get('name','')}</td>
            <td style="{_color_class(ch1d)}">{ch1d:+.2f}%</td>
            <td style="{_color_class(ch5d)}">{ch5d:+.2f}%</td>
            <td style="{_color_class(ch1m)}">{ch1m:+.2f}%</td>
            <td style="{_color_class(vs1d)}">{vs1d:+.2f}%</td>
        </tr>"""

    return f"""
    <table class="data-table">
        <thead>
            <tr>
                <th>ETF</th><th>Sector</th><th>1D</th><th>5D</th><th>1M</th><th>vs SPY 1D</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


def options_flow_table(flows: List[Dict]) -> str:
    if not flows:
        return '<p style="color:#64748b">No unusual options flow detected.</p>'

    rows = ""
    for f in flows:
        otype = f.get("option_type", "")
        color = "#22c55e" if otype == "call" else "#ef4444"
        premium = f.get("premium_total", 0)
        premium_str = f"${premium/1000:.1f}K" if premium < 1e6 else f"${premium/1e6:.2f}M"

        rows += f"""
        <tr>
            <td style="color:{color};font-weight:bold">{otype.upper()}</td>
            <td>${f.get('strike',0):.2f}</td>
            <td>{f.get('expiry','')}</td>
            <td>{f.get('volume',0):,}</td>
            <td>{f.get('open_interest',0):,}</td>
            <td style="color:#facc15">{f.get('volume_oi_ratio',0):.1f}x</td>
            <td style="color:#22c55e">{premium_str}</td>
        </tr>"""

    return f"""
    <table class="data-table">
        <thead>
            <tr>
                <th>Type</th><th>Strike</th><th>Expiry</th>
                <th>Volume</th><th>OI</th><th>Vol/OI</th><th>Premium</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""


def insider_table(transactions: List[Dict]) -> str:
    if not transactions:
        return '<p style="color:#64748b">No recent insider transactions.</p>'

    rows = ""
    for t in transactions:
        txn = t.get("transaction", "")
        color = "#22c55e" if "buy" in txn.lower() or "purchase" in txn.lower() else "#ef4444"
        value = t.get("value", 0)
        val_str = f"${value/1000:.0f}K" if value < 1e6 else f"${value/1e6:.2f}M"

        rows += f"""
        <tr>
            <td style="color:#e2e8f0">{t.get('name','')}</td>
            <td style="color:{color}">{txn}</td>
            <td>{t.get('shares',0):,}</td>
            <td>{val_str}</td>
            <td style="color:#64748b">{t.get('date','')}</td>
        </tr>"""

    return f"""
    <table class="data-table">
        <thead>
            <tr>
                <th>Insider</th><th>Transaction</th><th>Shares</th><th>Value</th><th>Date</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>"""
