"""Track-05 (SentinelPulse) plotly charts — in-track per isolation §1a.

Two figures, both rendering ONLY pre-computed backend payloads (D6):

  * ``ring_network`` — the suspected-ring diagram, a plotly scatter built straight
    from the ``expand_ring`` layout coordinates (NO graph library — D5). Nodes are
    coloured by inferred role; RED is reserved for confirmed top-band (Alert) nodes.
  * ``typology_bar`` — the desk-wide distribution of fired behavioural patterns.

Palette matches the platform charts (``app/frontend/components/charts.py``); these
are read-only siblings, not edits to that shared module.
"""
from __future__ import annotations

from typing import Dict, List

import plotly.graph_objects as go

NAVY, BLUE, GREEN, AMBER, RED, GRID = "#0b3d75", "#1466b8", "#147347", "#8f5c13", "#c0392b", "#dbe2ec"
PURPLE, SLATE, INK, MUTED = "#6b4fa1", "#647587", "#1b2733", "#647587"
_SANS = "Schibsted Grotesk, system-ui, sans-serif"
_BASE = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
             font=dict(family=_SANS, color=INK), margin=dict(l=10, r=10, t=30, b=10))

# role -> (legend label, colour). RED is used only for confirmed Alert nodes and
# is applied by band, overriding the role colour (see below).
_ROLE_STYLE = {
    "this": ("This account", NAVY),
    "cashout": ("Cash-out endpoint", AMBER),
    "recruiter": ("Recruiter hub", PURPLE),
    "mule": ("Flagged account", RED),
    "linked": ("Linked account", SLATE),
}
_ROLE_STYLE_PLAIN = {
    "this": ("This account", NAVY),
    "cashout": ("Cash-out point", AMBER),
    "recruiter": ("Forwarding hub", PURPLE),
    "mule": ("Flagged account", RED),
    "linked": ("Linked account", SLATE),
}


def _category(member: str, seed: str, role: str, band: str) -> str:
    """Bucket a node for the legend. Confirmed Alert nodes (other than the seed)
    render RED regardless of role — the reserved risk colour."""
    if member == seed:
        return "this"
    if band == "Alert":
        return "mule"        # RED, reserved for confirmed top-band
    return role if role in ("cashout", "recruiter", "linked") else "linked"


def ring_network(ring: dict, roles: Dict[str, str], bands: Dict[str, str],
                 plain: bool = False) -> go.Figure:
    """Suspected-ring scatter from the deterministic ``expand_ring`` layout."""
    layout = ring["layout"]
    seed = ring["seed"]
    style = _ROLE_STYLE_PLAIN if plain else _ROLE_STYLE

    fig = go.Figure()

    # edges first (under the nodes): dashed = shared device, solid = money transfer
    for e in ring["edges"]:
        a, b = layout.get(e["source"]), layout.get(e["target"])
        if a is None or b is None:
            continue
        dash = "dot" if e["type"] == "device" else "solid"
        fig.add_trace(go.Scatter(
            x=[a["x"], b["x"]], y=[a["y"], b["y"]], mode="lines",
            line=dict(color="#b7c2d0", width=1.2, dash=dash),
            hoverinfo="skip", showlegend=False))

    # nodes grouped by category so the legend reads cleanly
    buckets: Dict[str, List[str]] = {}
    for m in ring["members"]:
        cat = _category(m, seed, roles.get(m, "linked"), bands.get(m, "Clear"))
        buckets.setdefault(cat, []).append(m)

    for cat in ("linked", "recruiter", "cashout", "mule", "this"):
        members = buckets.get(cat)
        if not members:
            continue
        label, colour = style[cat]
        is_seed = cat == "this"
        fig.add_trace(go.Scatter(
            x=[layout[m]["x"] for m in members],
            y=[layout[m]["y"] for m in members],
            mode="markers", name=label,
            marker=dict(size=26 if is_seed else 18, color=colour,
                        symbol="star" if is_seed else "circle",
                        line=dict(width=2 if is_seed else 1, color="#ffffff")),
            hovertext=[f"{m} · {bands.get(m, 'Clear')}" for m in members],
            hoverinfo="text"))

    fig.update_layout(
        **_BASE, height=420, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=10)),
        xaxis=dict(visible=False, range=[-1.4, 1.4]),
        yaxis=dict(visible=False, range=[-1.4, 1.4], scaleanchor="x", scaleratio=1))
    return fig


def typology_bar(dist: List[dict], plain: bool = False) -> go.Figure:
    """Horizontal bar of how often each behavioural pattern fires across the desk."""
    items = list(reversed(dist))  # largest at top
    key = "plain_label" if plain else "label"
    names = [d[key] for d in items]
    vals = [d["count"] for d in items]
    fig = go.Figure(go.Bar(
        x=vals, y=names, orientation="h", marker=dict(color=BLUE),
        text=[str(v) for v in vals], textposition="outside",
        hovertemplate="%{y}: %{x} account(s)<extra></extra>"))
    fig.update_layout(**_BASE, height=max(240, 40 * len(items)),
                      xaxis=dict(title="accounts on the desk", showgrid=True,
                                 gridcolor=GRID, zeroline=False,
                                 range=[0, max(vals) * 1.18 if vals else 1]),
                      yaxis=dict(automargin=True))
    return fig
