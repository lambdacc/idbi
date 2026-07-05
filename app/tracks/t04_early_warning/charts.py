"""Track-04 plotly visualisations (in-track; not appended to the shared
`components/charts.py`, per the isolation rules).

`ews_timeline` is the money chart: the borrower's alt-data footprint (indexed) on
the left axis, DPD bars on the right, and three dashed vertical markers — the
alt-data model's first Red alert, the repayment-only baseline's first alert, and
the projected default month. The alt-data series visibly roll over BEFORE the
repayment/DPD line reacts. Palette: navy/teal series, RED/AMBER reserved for the
risk markers (matching the platform semantics).
"""
from __future__ import annotations

from typing import Dict, List, Optional

import plotly.graph_objects as go

# Platform palette (mirrors components/charts.py so the tracks read as one system).
NAVY, BLUE, TEAL, GREEN, AMBER, RED, GRID = (
    "#0b3d75", "#1466b8", "#0e7c66", "#147347", "#8f5c13", "#c0392b", "#dbe2ec")
INK, MUTED = "#1b2733", "#647587"
_SANS = "Schibsted Grotesk, system-ui, sans-serif"
_BASE = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
             font=dict(family=_SANS, color=INK),
             margin=dict(l=10, r=10, t=34, b=10))
CONFIG = {"displayModeBar": False, "responsive": True}


def _index(series: List[float]) -> List[Optional[float]]:
    """Index a level series to 100 at its first non-zero value (so series with
    wildly different scales share one axis)."""
    base = next((float(v) for v in series if v not in (0, None)), None)
    if not base:
        return [None for _ in series]
    return [(100.0 * float(v) / base) if v not in (None,) else None for v in series]


def band_bar(band_counts: Dict[str, int]) -> go.Figure:
    """Portfolio band distribution — Green / Amber / Red counts."""
    order = ["Green", "Amber", "Red"]
    colors = {"Green": GREEN, "Amber": AMBER, "Red": RED}
    vals = [int(band_counts.get(b, 0)) for b in order]
    fig = go.Figure(go.Bar(
        x=vals, y=order, orientation="h", marker=dict(color=[colors[b] for b in order]),
        text=[str(v) for v in vals], textposition="outside",
        hovertemplate="%{y}: %{x} loans<extra></extra>"))
    fig.update_layout(**_BASE, height=200, showlegend=False,
                      xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False,
                                 rangemode="tozero"),
                      yaxis=dict(autorange="reversed"))
    return fig


def ews_timeline(tl: Dict[str, object]) -> go.Figure:
    """The drilldown money chart (see module docstring)."""
    months = [int(m) for m in tl.get("months", [])]
    fig = go.Figure()

    # Indexed alt-data footprint (left axis). Navy/teal/blue — never the risk hues.
    series = [
        ("gst_turnover_declared", "GST declared turnover", NAVY),
        ("bank_inflows", "Bank inflows", BLUE),
        ("epfo_employee_count", "EPFO headcount", TEAL),
    ]
    for key, label, color in series:
        vals = tl.get(key) or []
        fig.add_trace(go.Scatter(
            x=months, y=_index([float(v) for v in vals]), name=label,
            mode="lines", line=dict(color=color, width=2.4),
            hovertemplate=f"{label}: %{{y:.0f}} (index)<extra></extra>"))

    # DPD bars on the right axis (the LAGGING repayment signal).
    dpd = tl.get("dpd") or []
    fig.add_trace(go.Bar(
        x=months, y=[float(d or 0) for d in dpd], name="Days past due",
        marker=dict(color="rgba(192,57,43,0.35)"), yaxis="y2",
        hovertemplate="DPD: %{y:.0f} days<extra></extra>"))

    # Three ordered markers. Extend the x-range to include a projected default
    # month that sits beyond the observed panel.
    xmax = max(months) if months else 0
    xmin = min(months) if months else -23
    ews = tl.get("ews_first_alert")
    base = tl.get("baseline_first_alert")
    dm = tl.get("default_month")

    def _vline(x, color, label, dash="dash"):
        fig.add_vline(x=x, line=dict(color=color, width=2, dash=dash))
        fig.add_annotation(x=x, y=1.06, yref="paper", showarrow=False,
                           text=label, font=dict(color=color, size=11),
                           bgcolor="rgba(255,255,255,0.6)")

    if ews is not None:
        _vline(ews, RED, "EWS first alert")
    if base is not None:
        _vline(base, AMBER, "Baseline alert")
    if dm is not None:
        _vline(dm, MUTED, "Projected default", dash="dot")
        xmax = max(xmax, int(dm))

    fig.update_layout(
        **_BASE, height=420, bargap=0.55,
        xaxis=dict(title="Month (0 = today)", showgrid=True, gridcolor=GRID,
                   zeroline=False, range=[xmin - 0.5, xmax + 1.0]),
        yaxis=dict(title="Alt-data footprint (indexed to 100)", showgrid=True,
                   gridcolor=GRID, zeroline=False),
        yaxis2=dict(title="Days past due", overlaying="y", side="right",
                    showgrid=False, zeroline=False, rangemode="tozero"),
        legend=dict(orientation="h", yanchor="bottom", y=1.12, x=0, font=dict(size=10)))
    return fig
