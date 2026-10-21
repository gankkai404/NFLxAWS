"""Plotly charts in the Weak Link style."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from . import theme
from .labels import NNBSP, dec, short_name
from .stats import cumulative_loss

GRID = np.round(np.arange(0, 5.01, 0.1), 2)


def rupture_curve(player_df, peer_df, team_df, release: float, name: str, peer_label: str, team_label: str) -> tuple[go.Figure, dict]:
    """Cumulative share of duels lost after the snap (Kaplan–Meier)."""
    p = 100 * cumulative_loss(player_df["temps_tenu"], player_df["perdu"], GRID)
    q = 100 * cumulative_loss(peer_df["temps_tenu"], peer_df["perdu"], GRID)
    t = 100 * cumulative_loss(team_df["temps_tenu"], team_df["perdu"], GRID) if len(team_df) else None
    top = np.nanmax([np.nanmax(p), np.nanmax(q), 8.0])
    ymax = float(np.ceil(top * 1.18 / 5) * 5)

    fig = go.Figure()
    hover = "%{y:.0f}" + NNBSP + "% perdus à %{x:.1f}" + NNBSP + "s<extra>%{fullData.name}</extra>"
    fig.add_trace(go.Scatter(x=GRID, y=q, name=peer_label, mode="lines", line=dict(color=theme.INK_3, width=2, dash="dash", shape="hv"), hovertemplate=hover))
    if t is not None:
        fig.add_trace(go.Scatter(x=GRID, y=t, name=team_label, mode="lines", line=dict(color=theme.INK, width=1.5, shape="hv"), opacity=0.55, hovertemplate=hover))
    fill_ok = np.nanmean(p - q) > 0
    fig.add_trace(
        go.Scatter(
            x=GRID, y=p, name=short_name(name), mode="lines", line=dict(color=theme.RED, width=3.2, shape="hv"),
            fill="tonexty" if fill_ok and t is None else None, fillcolor="rgba(215,48,31,0.10)", hovertemplate=hover,
        )
    )

    at = None
    if release == release:
        i = int(np.clip(np.searchsorted(GRID, release), 0, len(GRID) - 1))
        at = {"t": release, "player": p[i] / 100, "peer": q[i] / 100, "team": (t[i] / 100) if t is not None else np.nan}
        fig.add_vline(x=release, line=dict(color=theme.INK, width=1, dash="dot"))
        fig.add_annotation(
            x=release, y=1, yref="paper", yanchor="bottom", xanchor="left", xshift=5, showarrow=False,
            text=f"PASSE MÉDIANE · {dec(release)}{NNBSP}s", font=dict(family=theme.MONO, size=10, color=theme.INK_2),
        )
        fig.add_trace(go.Scatter(x=[GRID[i]], y=[p[i]], mode="markers", marker=dict(size=9, color=theme.RED, line=dict(color=theme.PAPER, width=2)), hoverinfo="skip"))

    for series, color, label, weight in [(p, theme.RED_INK, short_name(name), 600), (q, theme.INK_2, peer_label, 500)]:
        fig.add_annotation(
            x=GRID[-1], y=series[-1], xanchor="left", xshift=8, showarrow=False, align="left",
            text=f"<b>{dec(series[-1], 0)}{NNBSP}%</b> {label}", font=dict(family=theme.MONO, size=11, color=color, weight=weight),
        )

    fig.update_layout(
        template="weaklink", height=340, margin=dict(l=46, r=150, t=26, b=36), hovermode="x unified",
        separators=", ",
        xaxis=dict(range=[0, 5.02], dtick=1, ticksuffix=f"{NNBSP}s", title=None, fixedrange=True),
        yaxis=dict(range=[0, ymax], ticksuffix=f"{NNBSP}%", dtick=5 if ymax <= 30 else 10, title=None, fixedrange=True),
    )
    return fig, at
