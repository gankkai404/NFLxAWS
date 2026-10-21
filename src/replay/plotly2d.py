"""
Replay 2D Plotly : le contrat de l'équipe, make_replay(...) -> go.Figure.

Données préparées par src/replay/data.py : terrain orienté attaque vers la
droite, QB en étoile, bloqueur / défenseur suivis, ligne défenseur -> QB qui
passe au rouge sous le seuil, slider + Play / Pause. Léger (Plotly seul).
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import plotly.graph_objects as go

from .data import FIELD_LENGTH, FIELD_WIDTH, PRESSURE_THRESHOLD, build_play_payload

C_BLOCKER = "#22d3ee"
C_DEFENDER = "#fb7185"
C_QB = "#facc15"
C_SAFE = "#22c55e"
C_WARN = "#f59e0b"
C_DANGER = "#ef4444"
C_LOS = "#3b82f6"
C_FIRST_DOWN = "#facc15"
C_BALL = "#8b4513"
HASH_Y = 23.58
_CIRCLE = np.linspace(0, 2 * np.pi, 41)


def _arr(values) -> np.ndarray:
    return np.array([np.nan if v is None else v for v in values], dtype=float)


def _level_color(d: float, threshold: float) -> str:
    if not np.isfinite(d) or d > threshold + 3:
        return C_SAFE
    return C_DANGER if d <= threshold else C_WARN


def _field(fig: go.Figure, p: dict) -> None:
    """Terrain : bandes de gazon, end zones aux couleurs des équipes, lignes, numéros."""
    shapes, notes = [], []
    for i in range(20):
        shapes.append(dict(type="rect", x0=10 + 5 * i, x1=15 + 5 * i, y0=0, y1=FIELD_WIDTH, line_width=0,
                           fillcolor="#2a6d36" if i % 2 else "#2e7a3c", layer="below"))
    for x0, team in ((0, p["teams"]["off"]), (110, p["teams"]["def"])):
        shapes.append(dict(type="rect", x0=x0, x1=x0 + 10, y0=0, y1=FIELD_WIDTH, line_width=0,
                           fillcolor=team["primary"], opacity=0.85, layer="below"))
        notes.append(dict(x=x0 + 5, y=FIELD_WIDTH / 2, text=f"<b>{team['endzone']}</b>", showarrow=False,
                          textangle=-90 if x0 == 0 else 90, font=dict(size=22, color="white")))
    for x in range(10, 111, 5):
        shapes.append(dict(type="line", x0=x, x1=x, y0=0, y1=FIELD_WIDTH, layer="below",
                           line=dict(color="rgba(255,255,255,0.9)", width=3 if x in (10, 110) else 1.4)))
    shapes.append(dict(type="rect", x0=0, x1=FIELD_LENGTH, y0=0, y1=FIELD_WIDTH, layer="below",
                       line=dict(color="white", width=3)))
    for x in range(20, 101, 10):
        label = str(x - 10 if x <= 60 else 110 - x)
        for y, angle in ((8, 0), (FIELD_WIDTH - 8, 180)):
            notes.append(dict(x=x, y=y, text=label, showarrow=False, textangle=angle,
                              font=dict(size=17, color="rgba(255,255,255,0.85)", family="Arial Black")))
    los, first_down = p["field"]["los"], p["field"]["firstDown"]
    if los is not None:
        shapes.append(dict(type="line", x0=los, x1=los, y0=0, y1=FIELD_WIDTH, layer="below",
                           line=dict(color=C_LOS, width=3)))
    if first_down is not None and first_down < 110:
        shapes.append(dict(type="line", x0=first_down, x1=first_down, y0=0, y1=FIELD_WIDTH, layer="below",
                           line=dict(color=C_FIRST_DOWN, width=3)))
    fig.update_layout(shapes=shapes, annotations=notes)

    # hash marks : une seule trace statique (rapide à dessiner)
    hx, hy = [], []
    for x in range(11, 110):
        if x % 5 == 0:
            continue
        for y0, y1 in ((0.3, 1.0), (HASH_Y - 0.67, HASH_Y), (FIELD_WIDTH - HASH_Y, FIELD_WIDTH - HASH_Y + 0.67),
                       (FIELD_WIDTH - 1.0, FIELD_WIDTH - 0.3)):
            hx += [x, x, None]
            hy += [y0, y1, None]
    fig.add_trace(go.Scatter(x=hx, y=hy, mode="lines", line=dict(color="rgba(255,255,255,0.7)", width=1),
                             hoverinfo="skip", showlegend=False))


def make_replay(game_id: int, play_id: int, focus_blocker_id: Optional[int] = None,
                threshold: float = PRESSURE_THRESHOLD) -> go.Figure:
    """
    Replay 2D animé d'une action (contrat partie 2 -> partie 3).

    focus_blocker_id : nflId du bloqueur à suivre ; surligne aussi son défenseur
    (pff_nflIdBlockedPlayer) et trace la ligne défenseur -> QB.
    """
    p = build_play_payload(game_id, play_id, focus_blocker_id, threshold)
    meta, players, n = p["meta"], p["players"], len(p["frames"])
    xs = np.vstack([_arr(pl["x"]) for pl in players])
    ys = np.vstack([_arr(pl["y"]) for pl in players])
    speeds = np.vstack([_arr(pl["s"]) for pl in players])
    off_idx = [i for i, pl in enumerate(players) if pl["side"] == "off"]
    def_idx = [i for i, pl in enumerate(players) if pl["side"] == "def"]
    qb = p["qb"]
    duel = p["duels"][p["focus"]] if p["focus"] is not None else None
    bx, by = _arr(p["ball"]["x"]), _arr(p["ball"]["y"])
    snap, fps = p["snap"], p["fps"]
    pressure = duel["pressure"] if duel else (p["nearest"]["pressure"] if p["nearest"] else None)

    fig = go.Figure()
    _field(fig, p)
    n_static = len(fig.data)

    def team_trace(idx, team, i, name):
        return go.Scatter(
            x=xs[idx, i], y=ys[idx, i], mode="markers+text", name=name,
            text=[str(players[k]["jersey"] or "") for k in idx], textfont=dict(size=9, color=team["number"]),
            marker=dict(size=17, color=team["jersey"], line=dict(width=2, color=team["primary"])),
            customdata=[[players[k]["name"], players[k]["pos"], speeds[k, i]] for k in idx],
            hovertemplate="<b>%{customdata[0]}</b> · %{customdata[1]}<br>%{customdata[2]:.1f} yd/s<extra></extra>",
        )

    def ring(k, i, color, name):
        if k is None:
            return go.Scatter(x=[None], y=[None], name=name, showlegend=False)
        return go.Scatter(x=[xs[k, i]], y=[ys[k, i]], mode="markers", name=name, hoverinfo="skip",
                          marker=dict(size=27, color="rgba(0,0,0,0)", line=dict(width=3, color=color)))

    def trail(k, i, color, name):
        if k is None:
            return go.Scatter(x=[None], y=[None], name=name, showlegend=False)
        lo = max(snap - 3, i - 20, 0)
        return go.Scatter(x=xs[k, lo:i + 1], y=ys[k, lo:i + 1], mode="lines", name=name, hoverinfo="skip",
                          line=dict(color=color, width=2), opacity=0.7, showlegend=False)

    def frame_traces(i):
        threat = duel["defender"] if duel else (p["nearest"]["who"][i] if p["nearest"] else None)
        traces = [
            team_trace(off_idx, p["teams"]["off"], i, f"{meta['offense']} (attaque)"),
            team_trace(def_idx, p["teams"]["def"], i, f"{meta['defense']} (défense)"),
            go.Scatter(x=[bx[i]], y=[by[i]], mode="markers", name="Ballon", hoverinfo="skip",
                       marker=dict(size=10, color=C_BALL, symbol="diamond", line=dict(width=1, color="white"))),
        ]
        if qb is not None and threat is not None:
            d = float(np.hypot(xs[threat, i] - xs[qb, i], ys[threat, i] - ys[qb, i]))
            color = _level_color(d, threshold)
            traces.append(go.Scatter(
                x=[xs[threat, i], xs[qb, i]], y=[ys[threat, i], ys[qb, i]], mode="lines", name="Menace",
                line=dict(color=color, width=5 if d <= threshold else 3, dash="solid" if d <= threshold + 3 else "dash"),
                hovertemplate=f"Défenseur → QB : {d:.1f} yd<extra></extra>", showlegend=False))
            traces.append(go.Scatter(
                x=xs[qb, i] + threshold * np.cos(_CIRCLE), y=ys[qb, i] + threshold * np.sin(_CIRCLE),
                mode="lines", line=dict(color=C_DANGER if d <= threshold else "rgba(255,255,255,0.7)", width=2),
                fill="toself", fillcolor="rgba(239,68,68,0.25)" if d <= threshold else "rgba(255,255,255,0.06)",
                hoverinfo="skip", showlegend=False, name="Bulle QB"))
        else:
            traces += [go.Scatter(x=[None], y=[None], showlegend=False) for _ in range(2)]
        traces += [
            ring(duel["blocker"] if duel else None, i, C_BLOCKER, "Bloqueur suivi"),
            ring(threat, i, C_DEFENDER, "Défenseur"),
            trail(duel["blocker"] if duel else None, i, C_BLOCKER, "trace bloqueur"),
            trail(duel["defender"] if duel else None, i, C_DEFENDER, "trace défenseur"),
            go.Scatter(x=[xs[qb, i]] if qb is not None else [None], y=[ys[qb, i]] if qb is not None else [None],
                       mode="markers", name="QB", hoverinfo="skip",
                       marker=dict(size=21, color=C_QB, symbol="star", line=dict(width=1.5, color="#7c2d12"))),
        ]
        return traces

    start = p["start"]
    for trace in frame_traces(start):
        fig.add_trace(trace)
    anim_idx = list(range(n_static, len(fig.data)))

    def label(i):
        rel = (p["frames"][i] - p["frames"][snap]) / fps
        tag = {snap: " · snap", p["end"]: f" · {p['endLabel'].lower()}"}.get(i, "")
        if pressure is not None and i == pressure:
            tag = " · PRESSION"
        return f"{rel:+.1f} s{tag}"

    fig.frames = [go.Frame(data=frame_traces(i), traces=anim_idx, name=str(i)) for i in range(n)]
    anim = dict(frame=dict(duration=1000 // fps, redraw=True), mode="immediate", transition=dict(duration=0))
    fig.update_layout(
        updatemenus=[dict(
            type="buttons", direction="left", x=0.0, y=-0.02, xanchor="left", yanchor="top",
            pad=dict(r=8, t=8), showactive=False,
            buttons=[
                dict(label="▶ Play", method="animate", args=[None, dict(anim, fromcurrent=True)]),
                dict(label="⏸ Pause", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
            ],
        )],
        sliders=[dict(
            active=start, x=0.16, y=-0.02, len=0.84, xanchor="left", yanchor="top", pad=dict(t=8),
            currentvalue=dict(prefix="t = ", font=dict(size=13, color="#e2e8f0")),
            font=dict(size=1, color="rgba(0,0,0,0)"),  # étiquettes de pas masquées, valeur courante affichée
            steps=[dict(method="animate", label=label(i), args=[[str(i)], anim]) for i in range(n)],
        )],
    )

    title = f"<b>{meta['away']} @ {meta['home']}</b> · Q{meta['quarter']} {meta['gameClock']} · {meta['downLabel']}"
    if duel:
        b, v = players[duel["blocker"]], players[duel["defender"]]
        verdict = "perdu" if duel["perdu"] else "tenu"
        title += (f"<br><sup><span style='color:{C_BLOCKER}'>#{b['jersey']} {b['short']} ({b['pos']})</span> vs "
                  f"<span style='color:{C_DEFENDER}'>#{v['jersey']} {v['short']} ({v['pos']})</span> · "
                  f"temps tenu {duel['tempsTenu']:.1f} s ({verdict})</sup>")
    elif meta.get("focusWarning"):
        title += f"<br><sup>{meta['focusWarning']}</sup>"
    else:
        title += f"<br><sup>{str(meta['description'])[:110]}</sup>"

    center = p["field"]["los"] if p["field"]["los"] is not None else FIELD_LENGTH / 2
    if qb is not None:
        center = 0.6 * center + 0.4 * float(np.nanmean(xs[qb]))
    fig.update_layout(
        title=dict(text=title, x=0.01, font=dict(size=15)),
        xaxis=dict(range=[max(-2, center - 24), min(FIELD_LENGTH + 2, center + 26)], showgrid=False,
                   zeroline=False, showticklabels=False, constrain="range"),
        yaxis=dict(range=[-1, FIELD_WIDTH + 1], showgrid=False, zeroline=False, showticklabels=False,
                   scaleanchor="x", scaleratio=1),
        plot_bgcolor="#1d4d2a", paper_bgcolor="#0b1220", font=dict(color="#e2e8f0"),
        height=640, margin=dict(l=10, r=10, t=70, b=90), hovermode="closest",
        legend=dict(orientation="h", x=0.99, xanchor="right", y=1.02, yanchor="bottom", font=dict(size=11)),
        uirevision=f"{game_id}-{play_id}",
    )
    for k in anim_idx:  # légende : seulement les équipes, le ballon et le QB
        if fig.data[k].name not in (f"{meta['offense']} (attaque)", f"{meta['defense']} (défense)", "Ballon", "QB"):
            fig.data[k].showlegend = False
    return fig
