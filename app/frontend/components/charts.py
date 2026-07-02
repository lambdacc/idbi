"""Plotly visualizations for the Health Card and Explainability pages.

Palette matches custom.css; charts are deliberately clean (no gridline clutter)
to read as a banking analytics product rather than a notebook.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import plotly.graph_objects as go

NAVY, BLUE, GREEN, AMBER, RED, GRID = "#0b3d75", "#1466b8", "#178a54", "#b7791f", "#c0392b", "#dbe2ec"
_BASE = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
             font=dict(family="Inter, Segoe UI, sans-serif", color="#1b2733"),
             margin=dict(l=10, r=10, t=30, b=10))

_CLUSTER_COLORS = [NAVY, GREEN, BLUE, AMBER, RED]


def radar(labels: List[str], values: List[float]) -> go.Figure:
    """5-dimension Health Card radar (0-100)."""
    lab = labels + labels[:1]
    val = values + values[:1]
    fig = go.Figure(go.Scatterpolar(
        r=val, theta=lab, fill="toself", mode="lines+markers",
        line=dict(color=BLUE, width=2), marker=dict(color=NAVY, size=7),
        fillcolor="rgba(20,102,184,0.20)", hovertemplate="%{theta}: %{r:.0f}/100<extra></extra>"))
    fig.update_layout(
        **_BASE, height=360, showlegend=False,
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(range=[0, 100], showline=False, gridcolor=GRID,
                                   tickfont=dict(size=9, color="#647587")),
                   angularaxis=dict(gridcolor=GRID, tickfont=dict(size=11, color=NAVY))))
    return fig


def pillar_bars(labels: List[str], values: List[float]) -> go.Figure:
    """Horizontal per-pillar bars, colored by score band."""
    colors = [GREEN if v >= 74 else (AMBER if v >= 58 else RED) for v in values]
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h", marker=dict(color=colors),
        text=[f"{v:.0f}" for v in values], textposition="outside",
        hovertemplate="%{y}: %{x:.1f}/100<extra></extra>"))
    fig.update_layout(**_BASE, height=300, xaxis=dict(range=[0, 105], showgrid=True,
                      gridcolor=GRID, zeroline=False), yaxis=dict(autorange="reversed"))
    return fig


def cluster_scatter(scatter: List[dict], entity_point: Dict[str, float],
                    entity_name: str) -> go.Figure:
    """Cohort peer groups (colored by tier) with this MSME highlighted."""
    fig = go.Figure()
    by_tier: Dict[str, List[dict]] = {}
    for p in scatter:
        by_tier.setdefault(p["tier"], []).append(p)
    for i, (tier, pts) in enumerate(sorted(by_tier.items())):
        fig.add_trace(go.Scatter(
            x=[p["x"] for p in pts], y=[p["y"] for p in pts], mode="markers",
            name=tier, marker=dict(size=7, color=_CLUSTER_COLORS[i % len(_CLUSTER_COLORS)],
                                   opacity=0.5, line=dict(width=0)),
            hovertext=[p["name"] for p in pts], hoverinfo="text+name"))
    fig.add_trace(go.Scatter(
        x=[entity_point["x"]], y=[entity_point["y"]], mode="markers+text",
        name=entity_name, text=[f"  {entity_name}"], textposition="middle right",
        textfont=dict(color=NAVY, size=12, family="Inter"),
        marker=dict(size=20, color=NAVY, symbol="star", line=dict(width=2, color="#fff")),
        hovertext=[entity_name], hoverinfo="text"))
    fig.update_layout(**_BASE, height=420,
                      xaxis=dict(title="Peer-space component 1", showgrid=True, gridcolor=GRID, zeroline=False),
                      yaxis=dict(title="Peer-space component 2", showgrid=True, gridcolor=GRID, zeroline=False),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=10)))
    return fig


def shap_waterfall(shap_top: List[dict], labeler=None) -> go.Figure:
    """Top SHAP contributors to P(default): red pushes toward default, green away."""
    items = list(reversed(shap_top))  # largest at top
    names = [(labeler(i["feature"]) if labeler else i["feature"]) for i in items]
    vals = [i["shap"] for i in items]
    colors = [RED if v > 0 else GREEN for v in vals]
    fig = go.Figure(go.Bar(
        x=vals, y=names, orientation="h", marker=dict(color=colors),
        hovertemplate="%{y}: %{x:+.3f} to PD<extra></extra>"))
    fig.update_layout(**_BASE, height=max(240, 42 * len(items)),
                      xaxis=dict(title="SHAP contribution to P(default)", showgrid=True,
                                 gridcolor=GRID, zeroline=True, zerolinecolor="#9fb0c3"),
                      yaxis=dict(automargin=True))
    return fig


def gauge(value: float, title: str, vmax: float = 100.0,
          good: float = 74, warn: float = 58) -> go.Figure:
    """Simple score gauge for the dashboard hero."""
    color = GREEN if value >= good else (AMBER if value >= warn else RED)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value, title={"text": title, "font": {"size": 14}},
        gauge=dict(axis=dict(range=[0, vmax], tickcolor="#647587"), bar=dict(color=color),
                   bgcolor="#eef2f8", borderwidth=0)))
    fig.update_layout(**_BASE, height=220)
    return fig
