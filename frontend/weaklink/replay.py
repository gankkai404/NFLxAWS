"""Animated replay — our own field, in the Weak Link scouting-report style.

Same signature as the Part 2 contract, `make_replay(game_id, play_id, focus_blocker_id=None)`,
so it reads the real tracking data, but it renders on a light field with our palette
(ink lines, red pressure, yellow QB) to match the rest of the app.

The field crops on the pocket: pass protection happens within ~15 yards of the ball,
and a full 120-yard field makes every player a 6-pixel dot.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import paths, theme
from .data import _mtime, load_raw
from .labels import NNBSP, dec, short_name

PRESSURE_YD = 2.0
FIELD_W = 160 / 3  # 53.33 yards
SNAP_EVENTS = {"ball_snap", "autoevent_ballsnap"}
END_EVENTS = {"pass_forward", "autoevent_passforward", "qb_sack", "qb_strip_sack", "run", "pass_shovel"}
EVENT_LABELS = {
    "ball_snap": "SNAP", "autoevent_ballsnap": "SNAP", "play_action": "PLAY ACTION", "pass_forward": "PASSE",
    "autoevent_passforward": "PASSE", "qb_sack": "SACK", "qb_strip_sack": "STRIP SACK", "run": "SCRAMBLE",
    "pass_arrived": "BALLON ARRIVÉ", "pass_outcome_caught": "RÉCEPTION", "pass_outcome_incomplete": "INCOMPLÈTE",
    "pass_outcome_interception": "INTERCEPTION", "fumble": "FUMBLE", "pass_shovel": "PASSE",
}


@st.cache_data(max_entries=6, show_spinner=False)
def _tracking(game_id: int, _stamp: float) -> pd.DataFrame:
    path = paths.tracking_file(game_id)
    if path is None:
        raise FileNotFoundError(f"tracking_{game_id}.csv introuvable")
    return pd.read_csv(path, na_values=["NA"])


def _roles(game_id: int, play_id: int, focus_blocker_id):
    raw = load_raw(_mtime(paths.RAW_DIR / "plays.csv"))
    sc = raw["scouting"]
    play_sc = sc.loc[sc["gameId"].eq(game_id) & sc["playId"].eq(play_id)]
    qb = play_sc.loc[play_sc["pff_role"].eq("Pass"), "nflId"]
    defender = None
    if focus_blocker_id is not None:
        row = play_sc.loc[play_sc["nflId"].eq(focus_blocker_id), "pff_nflIdBlockedPlayer"].dropna()
        defender = int(row.iloc[0]) if len(row) else None
    plays = raw["plays"]
    play = plays.loc[plays["gameId"].eq(game_id) & plays["playId"].eq(play_id)]
    players = raw["players"].set_index("nflId")["displayName"]
    return (int(qb.iloc[0]) if len(qb) else None), defender, (play.iloc[0] if len(play) else None), players


def _field(fig: go.Figure, x0: float, x1: float, y0: float, y1: float, los: float, first_down: float | None) -> None:
    shapes = []
    for ez in [(0, 10), (110, 120)]:
        if x0 < ez[1] and x1 > ez[0]:
            shapes.append(dict(type="rect", x0=ez[0], x1=ez[1], y0=0, y1=FIELD_W, fillcolor="#284F33", line_width=0, layer="below"))
    for x in range(int(np.ceil(x0 / 5) * 5), int(x1) + 1, 5):
        if 10 <= x <= 110:
            major = x % 10 == 0
            shapes.append(dict(type="line", x0=x, x1=x, y0=0, y1=FIELD_W, layer="below",
                               line=dict(color="rgba(243,240,232,0.55)" if major else theme.TURF_LINE, width=1.6 if major else 1)))
    shapes.append(dict(type="line", x0=los, x1=los, y0=0, y1=FIELD_W, layer="below", line=dict(color="rgba(243,240,232,0.95)", width=2.4)))
    if first_down is not None and x0 < first_down < x1 and first_down <= 110:
        shapes.append(dict(type="line", x0=first_down, x1=first_down, y0=0, y1=FIELD_W, layer="below", line=dict(color=theme.YELLOW, width=2.4)))
    fig.update_layout(shapes=shapes)

    hx, hy = [], []
    for x in range(int(np.ceil(x0)), int(x1) + 1):
        if 10 < x < 110 and x % 5:
            for y in (23.36667, 29.96667, 0.67, FIELD_W - 0.67):
                hx += [x, x, None]
                hy += [y - 0.33, y + 0.33, None]
    fig.add_trace(go.Scatter(x=hx, y=hy, mode="lines", line=dict(color=theme.TURF_LINE, width=1), hoverinfo="skip"))

    for x in range(int(np.ceil(x0 / 10) * 10), int(x1) + 1, 10):
        if 20 <= x <= 100:
            label = str(50 - abs(x - 60))
            fig.add_annotation(x=x, y=y1 - 1.1, text=label, showarrow=False, font=dict(family=theme.MONO, size=11, color="rgba(243,240,232,0.7)"))
    fig.add_annotation(x=los, y=y0 + 0.9, text="MÊLÉE", showarrow=False, xanchor="right", xshift=-4,
                       font=dict(family=theme.MONO, size=9, color="rgba(243,240,232,0.85)"))
    if first_down is not None and x0 < first_down < x1 and first_down <= 110:
        fig.add_annotation(x=first_down, y=y0 + 0.9, text="1ER DOWN", showarrow=False, xanchor="left", xshift=4,
                           font=dict(family=theme.MONO, size=9, color=theme.YELLOW))


def _make_replay(game_id: int, play_id: int, focus_blocker_id=None) -> go.Figure:
    game_id, play_id = int(game_id), int(play_id)
    focus = int(focus_blocker_id) if focus_blocker_id is not None else None
    trk = _tracking(game_id, _mtime(paths.tracking_file(game_id) or paths.DATA_DIR))
    trk = trk.loc[trk["playId"].eq(play_id)].copy()
    if trk.empty:
        raise ValueError(f"Action {game_id}/{play_id} absente du tracking")
    qb_id, defender_id, play, names = _roles(game_id, play_id, focus)

    if (trk["playDirection"] == "left").any():
        trk["x"] = 120 - trk["x"]
        trk["y"] = FIELD_W - trk["y"]

    events = trk.loc[trk["event"].notna() & trk["event"].ne("None")].groupby("frameId")["event"].first()
    snap_frames = [f for f, e in events.items() if e in SNAP_EVENTS]
    snap = int(min(snap_frames)) if snap_frames else int(trk["frameId"].min())
    end_frames = [f for f, e in events.items() if e in END_EVENTS and f > snap]
    last = int(trk["frameId"].max())
    end = int(min(end_frames)) if end_frames else last
    start, stop = max(int(trk["frameId"].min()), snap - 4), min(last, end + 8)
    trk = trk.loc[trk["frameId"].between(start, stop)]
    frames = sorted(trk["frameId"].unique())

    ball = trk.loc[trk["team"].eq("football")]
    at_snap = ball.loc[ball["frameId"].eq(snap)]
    los = float(at_snap["x"].iloc[0]) if len(at_snap) else float(trk["x"].median())
    ball_y = float(at_snap["y"].iloc[0]) if len(at_snap) else FIELD_W / 2
    first_down = None
    if play is not None and pd.notna(play.get("yardsToGo")) and int(play.get("down", 0) or 0) > 0:
        first_down = los + float(play["yardsToGo"])

    half_h = 13.5
    cy = float(np.clip(ball_y, half_h, FIELD_W - half_h))
    x0, x1 = los - 16, los + 24
    y0, y1 = cy - half_h, cy + half_h

    players = trk.loc[trk["team"].ne("football")]
    offense_team = None
    if qb_id is not None and (players["nflId"] == qb_id).any():
        offense_team = players.loc[players["nflId"].eq(qb_id), "team"].iloc[0]
    elif play is not None:
        offense_team = play.get("possessionTeam")

    fig = go.Figure()
    _field(fig, x0, x1, y0, y1, los, first_down)

    def path(pid):
        rows = players.loc[players["nflId"].eq(pid)].sort_values("frameId")
        return rows["x"].tolist(), rows["y"].tolist()

    dx, dy = path(defender_id) if defender_id else ([], [])
    bx, by = path(focus) if focus else ([], [])
    fig.add_trace(go.Scatter(x=dx, y=dy, mode="lines", line=dict(color=theme.RED, width=2.4, dash="dot"), opacity=0.75, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=bx, y=by, mode="lines", line=dict(color=theme.YELLOW, width=2.4), opacity=0.7, hoverinfo="skip"))
    static_count = len(fig.data)

    by_frame = {f: g for f, g in players.groupby("frameId")}
    ball_by_frame = {f: g for f, g in ball.groupby("frameId")}
    event_at = {int(f): EVENT_LABELS.get(e, "") for f, e in events.items()}

    def frame_traces(f):
        g = by_frame.get(f, players.iloc[0:0])
        qb = g.loc[g["nflId"].eq(qb_id)] if qb_id else g.iloc[0:0]
        blk = g.loc[g["nflId"].eq(focus)] if focus else g.iloc[0:0]
        dfd = g.loc[g["nflId"].eq(defender_id)] if defender_id else g.iloc[0:0]
        special = {qb_id, focus, defender_id}
        off = g.loc[g["team"].eq(offense_team) & ~g["nflId"].isin(special)]
        de = g.loc[g["team"].ne(offense_team) & ~g["nflId"].isin(special)]
        b = ball_by_frame.get(f, ball.iloc[0:0])

        near_x = near_y = far_x = far_y = []
        mid_text, mid_x, mid_y = [""], [None], [None]
        dist = None
        if len(qb) and len(dfd):
            qx, qy = float(qb["x"].iloc[0]), float(qb["y"].iloc[0])
            ddx, ddy = float(dfd["x"].iloc[0]), float(dfd["y"].iloc[0])
            dist = float(np.hypot(qx - ddx, qy - ddy))
            seg_x, seg_y = [ddx, qx], [ddy, qy]
            if dist < PRESSURE_YD:
                near_x, near_y = seg_x, seg_y
            else:
                far_x, far_y = seg_x, seg_y
            mid_x, mid_y = [(qx + ddx) / 2], [(qy + ddy) / 2 + 0.9]
            mid_text = [f"{dec(dist)}{NNBSP}yd" if dist >= PRESSURE_YD else "PRESSION"]

        def dots(df, fill, text_color, line_color, size=19, symbol="circle"):
            return go.Scatter(
                x=df["x"], y=df["y"], mode="markers+text", text=df["jerseyNumber"].map(lambda v: "" if pd.isna(v) else str(int(v))),
                textfont=dict(family=theme.MONO, size=9, color=text_color),
                marker=dict(size=size, color=fill, symbol=symbol, line=dict(color=line_color, width=1.5)),
                customdata=df["nflId"].map(lambda i: names.get(i, "")), hovertemplate="%{customdata}<extra></extra>",
            )

        t = (f - snap) / 10
        clock = f"{'+' if t >= 0 else '−'}{dec(abs(t))}{NNBSP}s"
        label = event_at.get(int(f), "")
        return [
            go.Scatter(x=far_x, y=far_y, mode="lines", line=dict(color="rgba(243,240,232,0.9)", width=2, dash="dash"), hoverinfo="skip"),
            go.Scatter(x=near_x, y=near_y, mode="lines", line=dict(color=theme.RED, width=4.5), hoverinfo="skip"),
            go.Scatter(x=mid_x, y=mid_y, mode="text", text=mid_text, hoverinfo="skip",
                       textfont=dict(family=theme.MONO, size=11, color=theme.RED if dist is not None and dist < PRESSURE_YD else theme.PAPER, weight=600)),
            dots(off, theme.PAPER, theme.INK, theme.INK),
            dots(de, theme.INK, theme.PAPER, theme.INK),
            dots(blk, theme.YELLOW, theme.INK, theme.INK, size=23),
            dots(dfd, theme.RED, theme.PAPER, theme.PAPER, size=23),
            go.Scatter(x=qb["x"], y=qb["y"], mode="markers", marker=dict(symbol="star", size=24, color=theme.PAPER, line=dict(color=theme.INK, width=1.6)),
                       customdata=qb["nflId"].map(lambda i: names.get(i, "")), hovertemplate="QB · %{customdata}<extra></extra>"),
            go.Scatter(x=b["x"], y=b["y"], mode="markers", marker=dict(symbol="circle", size=8, color=theme.BALL, line=dict(color=theme.PAPER, width=1)), hoverinfo="skip"),
            go.Scatter(x=[x0 + 0.8, x0 + 0.8], y=[y1 - 1.3, y1 - 3.1], mode="text", text=[clock, label], textposition="middle right", hoverinfo="skip",
                       textfont=dict(family=theme.MONO, size=[15, 11], color=[theme.PAPER, theme.YELLOW], weight=600)),
        ]

    for trace in frame_traces(frames[0]):
        fig.add_trace(trace)
    dynamic = list(range(static_count, len(fig.data)))
    fig.frames = [go.Frame(name=str(f), data=frame_traces(f), traces=dynamic) for f in frames]

    def anim(duration):
        return dict(frame=dict(duration=duration, redraw=False), transition=dict(duration=0), fromcurrent=True, mode="immediate")

    steps = [
        dict(method="animate", label=f"{dec((f - snap) / 10)}", args=[[str(f)], dict(mode="immediate", frame=dict(duration=0, redraw=False), transition=dict(duration=0))])
        for f in frames
    ]
    button_font = dict(family=theme.MONO, size=11, color=theme.INK)
    fig.update_layout(
        template="weaklink", height=620, margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor=theme.TURF,
        xaxis=dict(range=[x0, x1], visible=False, fixedrange=True, constrain="domain"),
        yaxis=dict(range=[y0, y1], visible=False, fixedrange=True, scaleanchor="x", scaleratio=1, constrain="domain", domain=[0.12, 1]),
        updatemenus=[dict(
            type="buttons", direction="right", x=0, y=0.065, xanchor="left", yanchor="middle", pad=dict(r=6, t=0, b=0, l=0),
            bgcolor=theme.CARD, bordercolor=theme.INK, borderwidth=1, font=button_font, showactive=False,
            buttons=[
                dict(label="▶  Lire", method="animate", args=[None, anim(100)]),
                dict(label="Ralenti ×0,5", method="animate", args=[None, anim(200)]),
                dict(label="❚❚  Pause", method="animate", args=[[None], dict(mode="immediate", frame=dict(duration=0, redraw=False), transition=dict(duration=0))]),
            ],
        )],
        sliders=[dict(
            active=0, steps=steps, x=0.36, len=0.64, y=0.065, yanchor="middle", pad=dict(t=0, b=0),
            bgcolor=theme.PAPER_2, bordercolor=theme.RULE, borderwidth=1, activebgcolor=theme.INK, tickcolor="rgba(0,0,0,0)", ticklen=0,
            font=dict(family=theme.MONO, size=1, color="rgba(0,0,0,0)"),
            currentvalue=dict(visible=True, prefix="t = ", suffix=f"{NNBSP}s après le snap", xanchor="right", offset=8,
                              font=dict(family=theme.MONO, size=11, color=theme.INK_2)),
        )],
    )
    fig._wl_meta = {"snap": snap, "end": end}
    return fig


# ---------------------------------------------------------------- app entry point

@st.cache_data(max_entries=48, show_spinner=False)
def _cached_replay(game_id: int, play_id: int, focus):
    return _make_replay(game_id, play_id, focus)


def replay_source() -> str:
    return "terrain intégré"


def get_replay(game_id: int, play_id: int, focus_blocker_id=None) -> tuple[go.Figure, str, str | None]:
    """Our own field replay — light scouting-report style, our palette. (game, play) cached."""
    return _cached_replay(int(game_id), int(play_id), focus_blocker_id), "terrain intégré", None


make_replay = _make_replay  # same signature as the Part 2 contract
