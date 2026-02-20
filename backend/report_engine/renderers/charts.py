"""Plotly chart renderers — return inline HTML divs (not full pages)."""
import plotly.graph_objects as go
import plotly.express as px
from plotly.io import to_html
import pandas as pd
from typing import List, Optional


def _to_div(fig: go.Figure) -> str:
    """Convert Plotly figure to inline div (no JS embed — CDN handles it)."""
    return to_html(fig, full_html=False, include_plotlyjs=False, div_id=None)


def _dark_layout(title: str = "", height: int = 400) -> dict:
    return dict(
        title=dict(text=title, font=dict(color="#e2e8f0", size=14)),
        paper_bgcolor="#0f172a",
        plot_bgcolor="#1e293b",
        font=dict(color="#94a3b8", family="monospace"),
        height=height,
        margin=dict(l=50, r=20, t=40, b=40),
        xaxis=dict(gridcolor="#334155", linecolor="#475569"),
        yaxis=dict(gridcolor="#334155", linecolor="#475569"),
        legend=dict(bgcolor="#1e293b", bordercolor="#334155"),
    )


def candlestick_with_mas(
    dates: List[str],
    opens: List[float],
    highs: List[float],
    lows: List[float],
    closes: List[float],
    ma_20: List[Optional[float]],
    ma_50: List[Optional[float]],
    ma_200: List[Optional[float]],
    ticker: str = "",
    support_levels: List[float] = [],
    resistance_levels: List[float] = [],
) -> str:
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=dates,
        open=opens,
        high=highs,
        low=lows,
        close=closes,
        name=ticker,
        increasing=dict(line=dict(color="#22c55e"), fillcolor="#166534"),
        decreasing=dict(line=dict(color="#ef4444"), fillcolor="#7f1d1d"),
    ))

    for ma, color, name in [
        (ma_20, "#facc15", "MA20"),
        (ma_50, "#60a5fa", "MA50"),
        (ma_200, "#f97316", "MA200"),
    ]:
        if ma:
            fig.add_trace(go.Scatter(x=dates, y=ma, name=name,
                                     line=dict(color=color, width=1.5), mode="lines"))

    for s in support_levels[-3:]:
        fig.add_hline(y=s, line=dict(color="#22c55e", width=1, dash="dot"),
                      annotation_text=f"S {s:.2f}", annotation_font=dict(color="#22c55e", size=10))

    for r in resistance_levels[:3]:
        fig.add_hline(y=r, line=dict(color="#ef4444", width=1, dash="dot"),
                      annotation_text=f"R {r:.2f}", annotation_font=dict(color="#ef4444", size=10))

    layout = _dark_layout(f"{ticker} Price", height=450)
    layout["xaxis"]["rangeslider"] = dict(visible=False)
    fig.update_layout(**layout)
    return _to_div(fig)


def rsi_chart(dates: List[str], rsi: List[Optional[float]], ticker: str = "") -> str:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=rsi, name="RSI",
                             line=dict(color="#a78bfa", width=2), mode="lines"))
    fig.add_hline(y=70, line=dict(color="#ef4444", dash="dash", width=1))
    fig.add_hline(y=30, line=dict(color="#22c55e", dash="dash", width=1))
    fig.add_hrect(y0=70, y1=100, fillcolor="#ef4444", opacity=0.05)
    fig.add_hrect(y0=0, y1=30, fillcolor="#22c55e", opacity=0.05)
    fig.update_layout(**_dark_layout(f"{ticker} RSI (14)", height=200))
    fig.update_yaxes(range=[0, 100])
    return _to_div(fig)


def macd_chart(
    dates: List[str],
    macd_line: List[Optional[float]],
    macd_signal: List[Optional[float]],
    macd_histogram: List[Optional[float]],
    ticker: str = "",
) -> str:
    colors = ["#22c55e" if (v or 0) >= 0 else "#ef4444" for v in macd_histogram]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=macd_histogram, name="Histogram",
                         marker_color=colors, opacity=0.7))
    fig.add_trace(go.Scatter(x=dates, y=macd_line, name="MACD",
                             line=dict(color="#60a5fa", width=2)))
    fig.add_trace(go.Scatter(x=dates, y=macd_signal, name="Signal",
                             line=dict(color="#f97316", width=1.5, dash="dash")))
    fig.update_layout(**_dark_layout(f"{ticker} MACD", height=200))
    return _to_div(fig)


def sector_heatmap(sector_data: List[dict]) -> str:
    """Sector performance heatmap."""
    names = [s["name"] for s in sector_data]
    values_1d = [s["change_1d"] for s in sector_data]
    values_5d = [s["change_5d"] for s in sector_data]
    values_1m = [s["change_1m"] for s in sector_data]

    fig = go.Figure(data=go.Heatmap(
        z=[values_1d, values_5d, values_1m],
        x=names,
        y=["1D", "5D", "1M"],
        colorscale=[
            [0, "#7f1d1d"],
            [0.5, "#1e293b"],
            [1, "#166534"],
        ],
        zmid=0,
        text=[[f"{v:+.1f}%" for v in row] for row in [values_1d, values_5d, values_1m]],
        texttemplate="%{text}",
        showscale=True,
    ))
    fig.update_layout(**_dark_layout("Sector Performance Heatmap", height=300))
    return _to_div(fig)


def vix_gauge(vix: float) -> str:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=vix,
        title=dict(text="VIX", font=dict(color="#e2e8f0")),
        gauge=dict(
            axis=dict(range=[0, 80], tickcolor="#94a3b8"),
            bar=dict(color="#a78bfa"),
            bgcolor="#1e293b",
            bordercolor="#475569",
            steps=[
                dict(range=[0, 15], color="#166534"),
                dict(range=[15, 25], color="#854d0e"),
                dict(range=[25, 35], color="#7f1d1d"),
                dict(range=[35, 80], color="#450a0a"),
            ],
            threshold=dict(
                line=dict(color="#ef4444", width=4),
                thickness=0.75,
                value=vix,
            ),
        ),
        number=dict(font=dict(color="#e2e8f0")),
    ))
    fig.update_layout(
        paper_bgcolor="#0f172a",
        font=dict(color="#94a3b8"),
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return _to_div(fig)


def correlation_heatmap(tickers: List[str], matrix: dict) -> str:
    z = [[matrix.get(r, {}).get(c, 0) for c in tickers] for r in tickers]
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=tickers,
        y=tickers,
        colorscale="RdBu",
        zmid=0,
        zmin=-1,
        zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in z],
        texttemplate="%{text}",
        showscale=True,
    ))
    fig.update_layout(**_dark_layout("Correlation Matrix (90D)", height=400))
    return _to_div(fig)
