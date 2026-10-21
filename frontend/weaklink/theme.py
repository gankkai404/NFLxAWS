"""Design system: scouting-report paper, ink, grease-pencil red, highlighter yellow.

One family (Archivo, variable width) for display and text, IBM Plex Mono for data.
Every colour and size lives here so the Streamlit theme, the custom components and
the Plotly charts stay in sync.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from .labels import FORMATIONS


def FORMATIONS_LABEL(code: str) -> str:
    return FORMATIONS.get(code, str(code).title())


PAPER = "#F3F0E8"
PAPER_2 = "#EAE5D9"
CARD = "#FAF8F3"
INK = "#16140F"
INK_2 = "#59544A"
INK_3 = "#8C8577"
RULE = "#D6CFBF"
RULE_2 = "#E2DCCF"
RED = "#D7301F"
RED_INK = "#B3261A"
RED_WASH = "#F4D9CF"
YELLOW = "#F5CF3A"
YELLOW_WASH = "#FBEBA8"
TURF = "#2F5B3B"
TURF_LINE = "rgba(243,240,232,0.34)"
BALL = "#8A5A33"

DISPLAY = "'WL Condensed', 'Archivo Narrow', 'Arial Narrow', sans-serif"
TEXT = "'WL Archivo', 'Archivo', system-ui, sans-serif"
MONO = "'WL Mono', 'IBM Plex Mono', ui-monospace, monospace"

FONT_FACES = """
@font-face { font-family: 'WL Archivo'; src: url('app/static/fonts/Archivo-Variable-latin.woff2') format('woff2');
  font-weight: 100 900; font-stretch: 62% 125%; font-style: normal; font-display: swap; }
@font-face { font-family: 'WL Condensed'; src: url('app/static/fonts/Archivo-Variable-latin.woff2') format('woff2');
  font-weight: 100 900; font-stretch: 68%; font-style: normal; font-display: swap; }
@font-face { font-family: 'WL Mono'; src: url('app/static/fonts/IBMPlexMono-400-latin.woff2') format('woff2'); font-weight: 400; font-display: swap; }
@font-face { font-family: 'WL Mono'; src: url('app/static/fonts/IBMPlexMono-500-latin.woff2') format('woff2'); font-weight: 500; font-display: swap; }
@font-face { font-family: 'WL Mono'; src: url('app/static/fonts/IBMPlexMono-600-latin.woff2') format('woff2'); font-weight: 600 700; font-display: swap; }
"""

TOKENS = f"""
  --paper: {PAPER}; --paper-2: {PAPER_2}; --card: {CARD};
  --ink: {INK}; --ink-2: {INK_2}; --ink-3: {INK_3};
  --rule: {RULE}; --rule-2: {RULE_2};
  --red: {RED}; --red-ink: {RED_INK}; --red-wash: {RED_WASH};
  --yellow: {YELLOW}; --yellow-wash: {YELLOW_WASH};
  --display: {DISPLAY}; --text: {TEXT}; --mono: {MONO};
  --ease: cubic-bezier(.2,.7,.2,1);
"""

# Shared by the shadow-DOM components (they don't see the page stylesheet).
COMPONENT_BASE = f"""
:host, .wl {{ {TOKENS} }}
.wl {{ font-family: var(--text); color: var(--ink); -webkit-font-smoothing: antialiased; font-feature-settings: "tnum" 1, "lnum" 1; }}
.wl *, .wl *::before, .wl *::after {{ box-sizing: border-box; }}
.wl button {{ font: inherit; color: inherit; background: none; border: 0; padding: 0; margin: 0; text-align: inherit; cursor: pointer; }}
.wl button:focus-visible, .wl [tabindex]:focus-visible {{ outline: 2px solid var(--ink); outline-offset: 3px; }}
@media (prefers-reduced-motion: reduce) {{ .wl * {{ transition: none !important; animation: none !important; }} }}
"""

PAGE_CSS = f"""
{FONT_FACES}
:root {{ {TOKENS} }}

/* ---------- Streamlit chrome ---------- */
[data-testid="stDecoration"] {{ display: none; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stAppDeployButton"], [data-testid="stToolbarActions"] {{ display: none; }}
[data-testid="stMainBlockContainer"] {{ max-width: 1320px; padding: 1.75rem 3rem 5rem; }}
[data-testid="stAppViewContainer"] {{ background: var(--paper); }}
.stApp {{ font-feature-settings: "tnum" 1, "lnum" 1; }}
[data-testid="stVerticalBlock"] {{ gap: 0.9rem; }}

/* Widget labels read like form fields on a printed report. */
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {{
  font-family: var(--mono) !important; font-size: 0.69rem !important; font-weight: 500 !important;
  letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-2) !important;
}}
[data-baseweb="select"] > div {{ background: var(--card); border-color: var(--ink) !important; min-height: 2.6rem; }}
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
[data-baseweb="select"] div[value] {{ font-weight: 600; }}
[data-testid="stNumberInputContainer"] {{ background: var(--card); border-color: var(--ink) !important; }}
[data-testid="stNumberInputField"] {{ font-family: var(--mono); font-weight: 500; }}

/* Situation pills: square tags, ink when on. */
[data-testid="stBaseButton-pills"], [data-testid="stBaseButton-pillsActive"] {{
  font-family: var(--mono); font-size: 0.78rem; font-weight: 500; letter-spacing: 0.02em;
  border-radius: 3px; min-height: 2.6rem; padding: 0 0.95rem; transition: background .15s var(--ease), color .15s var(--ease);
}}
[data-testid="stBaseButton-pills"] {{ background: var(--card); border: 1px solid var(--rule); color: var(--ink); }}
[data-testid="stBaseButton-pills"]:hover {{ border-color: var(--ink); color: var(--ink); background: var(--card); }}
[data-testid="stBaseButton-pillsActive"] {{ background: var(--ink) !important; border: 1px solid var(--ink) !important; color: var(--paper) !important; }}
[data-testid="stBaseButton-pillsActive"] p, [data-testid="stBaseButton-pills"] p {{ font-family: var(--mono); font-size: 0.78rem; }}

[data-testid="stPlotlyChart"] {{ background: transparent; }}
[data-testid="stAlert"] {{ border-radius: 3px; }}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {{ background: var(--card); border-right: 1px solid var(--ink); }}
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {{ padding: 1.4rem 1.3rem 2rem; }}
.wl-side-title {{ display: flex; align-items: center; gap: 0.55rem; padding-bottom: 0.7rem; margin-bottom: 1.1rem; border-bottom: 2px solid var(--ink); }}
.wl-side-title svg {{ width: 34px; height: 20px; flex: none; }}
.wl-side-title span {{ font-family: var(--display); font-weight: 820; font-size: 1.3rem; text-transform: uppercase; letter-spacing: 0.02em; }}
.wl-side-rule {{ border: 0; border-top: 1px solid var(--rule); margin: 1.4rem 0 1rem; }}
.wl-side-note {{ font-family: var(--mono); font-size: 0.72rem; line-height: 1.6; color: var(--ink-2); letter-spacing: 0.02em; }}
.wl-side-note b {{ color: var(--ink); font-weight: 600; }}

/* ---------- Page typography ---------- */
.wl-page {{ font-family: var(--text); color: var(--ink); }}
.wl-mono {{ font-family: var(--mono); }}

/* Masthead */
.wl-mast {{ display: grid; grid-template-columns: auto 1fr auto; align-items: end; gap: 2rem; padding-bottom: 0.9rem; border-bottom: 3px solid var(--ink); }}
.wl-brand {{ display: flex; align-items: center; gap: 0.7rem; }}
.wl-brand svg {{ width: 46px; height: 26px; flex: none; }}
.wl-word {{ font-family: var(--display); font-weight: 850; font-size: 2.35rem; line-height: 0.82; letter-spacing: 0.01em; text-transform: uppercase; }}
.wl-tagline {{ font-size: 1.02rem; color: var(--ink-2); line-height: 1.35; max-width: 34rem; padding-bottom: 0.1rem; }}
.wl-tagline b {{ color: var(--ink); font-weight: 650; }}
.wl-status {{ font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.42rem 0.7rem; border: 1px solid var(--ink); border-radius: 3px; white-space: nowrap; }}
.wl-status i {{ width: 0.5rem; height: 0.5rem; border-radius: 50%; background: var(--ink); display: inline-block; }}
.wl-status.demo {{ border-color: var(--red-ink); color: var(--red-ink); }}
.wl-status.demo i {{ background: transparent; border: 1.5px solid var(--red-ink); }}
.wl-meta {{ display: flex; flex-wrap: wrap; gap: 0.35rem 1.4rem; padding: 0.55rem 0 0; font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-2); }}
.wl-meta b {{ color: var(--ink); font-weight: 600; }}

.wl-banner {{ display: flex; gap: 0.9rem; align-items: baseline; padding: 0.7rem 0.9rem; border: 1px dashed var(--red-ink); color: var(--ink); font-size: 0.9rem; line-height: 1.45; }}
.wl-banner b {{ font-family: var(--mono); font-size: 0.68rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--red-ink); white-space: nowrap; }}
.wl-banner code {{ font-family: var(--mono); font-size: 0.82rem; background: var(--paper-2); padding: 0.05rem 0.3rem; border-radius: 2px; }}

/* Section heads: numbered, ruled, like a printed game plan. */
.wl-sec {{ display: grid; grid-template-columns: auto 1fr auto; align-items: baseline; gap: 0.9rem; border-top: 2px solid var(--ink); padding-top: 0.6rem; margin-top: 2.2rem; }}
.wl-sec .n {{ font-family: var(--mono); font-size: 0.72rem; font-weight: 600; letter-spacing: 0.08em; }}
.wl-sec h2 {{ font-family: var(--display); font-weight: 800; font-size: 1.9rem; line-height: 1; text-transform: uppercase; letter-spacing: 0.005em; margin: 0; padding: 0; color: var(--ink); }}
.wl-sec .aside {{ font-family: var(--mono); font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-2); text-align: right; }}
.wl-sub {{ color: var(--ink-2); font-size: 0.95rem; line-height: 1.5; margin: 0.15rem 0 0.2rem; max-width: 48rem; }}
.wl-sub b {{ color: var(--ink); font-weight: 600; }}

/* Verdict */
.wl-verdict {{ padding-top: 0.6rem; }}
.wl-eyebrow {{ font-family: var(--mono); font-size: 0.72rem; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; color: var(--red-ink); display: flex; gap: 0.6rem; align-items: center; }}
.wl-eyebrow::before {{ content: ""; width: 1.6rem; height: 2px; background: var(--red); display: inline-block; }}
.wl-first {{ font-family: var(--mono); font-size: 0.95rem; font-weight: 500; letter-spacing: 0.22em; text-transform: uppercase; margin-top: 1.1rem; color: var(--ink-2); }}
.wl-last {{ font-family: var(--display); font-weight: 850; font-size: clamp(3.4rem, 6.4vw, 5.6rem); line-height: 0.84; text-transform: uppercase; letter-spacing: -0.005em; margin: 0.1rem 0 0.7rem; overflow-wrap: anywhere; }}
.wl-idline {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 1.1rem; }}
.wl-chip {{ font-family: var(--mono); font-size: 0.72rem; font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase; padding: 0.22rem 0.5rem; border: 1px solid var(--ink); border-radius: 2px; }}
.wl-chip.solid {{ background: var(--ink); color: var(--paper); }}
.wl-chip.soft {{ border-color: var(--rule); color: var(--ink-2); }}
.wl-lede {{ font-size: 1.32rem; line-height: 1.36; font-weight: 400; margin: 0 0 0.9rem; max-width: 33rem; text-wrap: pretty; }}
.wl-lede b {{ font-weight: 700; }}
.wl-lede .hot {{ color: var(--red-ink); }}
.wl-attack {{ display: grid; grid-template-columns: auto 1fr; gap: 0.75rem; align-items: baseline; border-top: 1px solid var(--rule); padding-top: 0.75rem; font-size: 1rem; line-height: 1.45; max-width: 33rem; }}
.wl-attack .k {{ font-family: var(--mono); font-size: 0.68rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; background: var(--yellow); padding: 0.18rem 0.42rem; border-radius: 2px; white-space: nowrap; }}
.wl-attack b {{ font-weight: 650; }}
.wl-teamline {{ font-family: var(--mono); font-size: 0.72rem; letter-spacing: 0.06em; color: var(--ink-2); margin-top: 0.9rem; text-transform: uppercase; }}
.wl-teamline b {{ color: var(--ink); font-weight: 600; }}
.wl-empty {{ border: 1px dashed var(--ink-3); padding: 1.4rem 1.5rem; font-size: 1.05rem; line-height: 1.5; color: var(--ink-2); }}
.wl-empty b {{ color: var(--ink); display: block; font-family: var(--display); font-weight: 800; text-transform: uppercase; font-size: 1.6rem; line-height: 1; margin-bottom: 0.5rem; }}

/* Dossier */
.wl-who {{ display: flex; align-items: baseline; gap: 0.8rem; flex-wrap: wrap; padding-top: 0.3rem; }}
.wl-who .jn {{ font-family: var(--display); font-weight: 850; font-size: 3.1rem; line-height: 0.85; -webkit-text-stroke: 1.5px var(--ink); color: transparent; }}
.wl-who .nm {{ font-family: var(--display); font-weight: 800; font-size: 2.35rem; line-height: 0.9; text-transform: uppercase; }}
.wl-who .ps {{ font-family: var(--mono); font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-2); }}
.wl-bio {{ font-family: var(--mono); font-size: 0.72rem; letter-spacing: 0.04em; color: var(--ink-2); margin: 0.35rem 0 1rem; }}
.wl-kpis {{ display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid var(--ink); }}
.wl-kpi {{ padding: 0.7rem 0.9rem 0.8rem 0; border-bottom: 1px solid var(--rule); }}
.wl-kpi + .wl-kpi {{ padding-left: 0.9rem; border-left: 1px solid var(--rule); }}
.wl-kpi:nth-child(3n+1) {{ padding-left: 0; border-left: 0; }}
.wl-kpi .l {{ font-family: var(--mono); font-size: 0.64rem; font-weight: 500; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink-2); }}
.wl-kpi .v {{ font-family: var(--display); font-weight: 800; font-size: 2.2rem; line-height: 1; margin-top: 0.3rem; }}
.wl-kpi .v small {{ font-size: 1.1rem; font-weight: 700; margin-left: 0.1rem; }}
.wl-kpi .v.hot {{ color: var(--red-ink); }}
.wl-kpi .s {{ font-family: var(--mono); font-size: 0.68rem; color: var(--ink-2); margin-top: 0.25rem; }}
.wl-nem {{ margin-top: 1.2rem; }}
.wl-nem h4, .wl-chart-head h4 {{ font-family: var(--mono); font-size: 0.68rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; margin: 0 0 0.45rem; color: var(--ink); }}
.wl-nem ol {{ list-style: none; margin: 0; padding: 0; }}
.wl-nem li {{ display: grid; grid-template-columns: 1.4rem 1fr auto; gap: 0.5rem; align-items: baseline; padding: 0.42rem 0; border-top: 1px solid var(--rule); font-size: 0.95rem; }}
.wl-nem li .i {{ font-family: var(--mono); font-size: 0.7rem; color: var(--ink-3); }}
.wl-nem li .p {{ font-family: var(--mono); font-size: 0.68rem; color: var(--ink-2); margin-left: 0.35rem; }}
.wl-nem li .w {{ font-family: var(--mono); font-size: 0.8rem; }}
.wl-nem li .w b {{ font-weight: 600; color: var(--red-ink); }}
.wl-chart-head {{ display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; }}
.wl-chart-head p {{ margin: 0; color: var(--ink-2); font-size: 0.92rem; }}
.wl-insight {{ font-size: 1.12rem; line-height: 1.4; margin: 0.35rem 0 0; max-width: 40rem; }}
.wl-insight b {{ font-weight: 700; }}
.wl-insight .hot {{ color: var(--red-ink); }}
.wl-keys {{ display: flex; gap: 1.2rem; flex-wrap: wrap; font-family: var(--mono); font-size: 0.68rem; color: var(--ink-2); letter-spacing: 0.04em; }}
.wl-keys span {{ display: inline-flex; align-items: center; gap: 0.4rem; }}
.wl-keys i {{ display: inline-block; width: 1.3rem; height: 0; border-top: 3px solid var(--red); }}
.wl-keys i.peer {{ border-top: 2px dashed var(--ink-3); }}
.wl-keys i.team {{ border-top: 2px solid var(--ink); }}
.wl-keys i.rel {{ width: 0; height: 0.9rem; border-top: 0; border-left: 1.5px dashed var(--ink); }}

/* Splits */
.wl-splits {{ display: grid; grid-template-columns: 1fr 1fr; column-gap: 3rem; }}
.wl-split {{ display: grid; grid-template-columns: 9.5rem 1fr 4rem 4.4rem 3rem; gap: 0.8rem; align-items: center; padding: 0.5rem 0; border-top: 1px solid var(--rule); font-size: 0.92rem; }}
.wl-split .lb {{ font-weight: 550; }}
.wl-split.base .lb {{ font-weight: 700; }}
.wl-split .bar {{ position: relative; height: 0.7rem; background: var(--paper-2); }}
.wl-split .bar .f {{ position: absolute; inset: 0 auto 0 0; background: var(--ink); }}
.wl-split.hot .bar .f {{ background: var(--red); }}
.wl-split .bar .pk {{ position: absolute; top: -0.25rem; bottom: -0.25rem; width: 0; border-left: 2px solid var(--ink); }}
.wl-split .bar .pk::after {{ content: ""; position: absolute; left: -4px; top: -3px; width: 6px; height: 2px; background: var(--ink); }}
.wl-split .v {{ font-family: var(--mono); font-weight: 600; text-align: right; }}
.wl-split.hot .v {{ color: var(--red-ink); }}
.wl-split .d {{ font-family: var(--mono); font-size: 0.78rem; text-align: right; color: var(--ink-2); }}
.wl-split.hot .d {{ color: var(--red-ink); font-weight: 600; }}
.wl-split .nn {{ font-family: var(--mono); font-size: 0.72rem; color: var(--ink-3); text-align: right; }}
.wl-split.na .lb, .wl-split.na .v {{ color: var(--ink-3); }}
.wl-split-legend {{ font-family: var(--mono); font-size: 0.68rem; color: var(--ink-2); display: flex; gap: 1.2rem; margin: 0.3rem 0 0.4rem; flex-wrap: wrap; }}
.wl-split-legend span {{ display: inline-flex; align-items: center; gap: 0.4rem; }}
.wl-split-legend i {{ display: inline-block; width: 1rem; height: 0.55rem; background: var(--ink); }}
.wl-split-legend i.hot {{ background: var(--red); }}
.wl-split-legend i.pk {{ width: 0; height: 0.9rem; background: none; border-left: 2px solid var(--ink); }}

/* Replay */
.wl-play-head {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.1rem 0 0.4rem; }}
.wl-play-desc {{ font-size: 0.95rem; line-height: 1.5; color: var(--ink); border-left: 3px solid var(--yellow); padding: 0.1rem 0 0.1rem 0.8rem; margin: 0.2rem 0 0.4rem; }}
.wl-legend {{ display: flex; flex-wrap: wrap; gap: 0.6rem 1.3rem; font-family: var(--mono); font-size: 0.7rem; color: var(--ink-2); }}
.wl-legend span {{ display: inline-flex; align-items: center; gap: 0.45rem; }}
.wl-legend i {{ width: 0.8rem; height: 0.8rem; border-radius: 50%; display: inline-block; border: 1.5px solid var(--ink); }}
.wl-legend i.b {{ background: var(--yellow); }}
.wl-legend i.d {{ background: var(--red); border-color: var(--red); }}
.wl-legend i.o {{ background: var(--paper); }}
.wl-legend i.x {{ background: var(--ink); }}
.wl-legend i.l {{ width: 1.4rem; height: 0; border-radius: 0; border: 0; border-top: 2px dashed var(--ink); }}
.wl-legend i.l.hot {{ border-top: 3px solid var(--red); }}
.wl-legend i.q {{ border: 0; border-radius: 0; background: none; width: auto; height: auto; font-style: normal; color: var(--ink); font-size: 0.9rem; line-height: 1; }}
.wl-note {{ font-family: var(--mono); font-size: 0.68rem; color: var(--ink-3); letter-spacing: 0.04em; }}

/* Footer */
.wl-foot {{ margin-top: 3.5rem; border-top: 3px solid var(--ink); padding-top: 1rem; display: grid; grid-template-columns: repeat(4, 1fr); gap: 2rem; }}
.wl-foot h5 {{ font-family: var(--mono); font-size: 0.68rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; margin: 0 0 0.45rem; }}
.wl-foot p {{ font-size: 0.86rem; line-height: 1.5; color: var(--ink-2); margin: 0; }}
.wl-foot p b {{ color: var(--ink); font-weight: 600; }}
.wl-colophon {{ font-family: var(--mono); font-size: 0.66rem; color: var(--ink-3); letter-spacing: 0.06em; margin-top: 1.4rem; text-transform: uppercase; }}

@media (max-width: 1100px) {{
  [data-testid="stMainBlockContainer"] {{ padding: 1.2rem 1.4rem 4rem; }}
  .wl-mast {{ grid-template-columns: 1fr auto; }}
  .wl-tagline {{ display: none; }}
  .wl-splits {{ grid-template-columns: 1fr; }}
  .wl-foot {{ grid-template-columns: 1fr 1fr; }}
}}
"""


def inject() -> None:
    st.html(f"<style>{PAGE_CSS}</style>")


def _template() -> go.layout.Template:
    axis = dict(
        showgrid=False, zeroline=False, showline=True, linecolor=INK, linewidth=1,
        ticks="outside", tickcolor=INK, ticklen=4, tickwidth=1,
        tickfont=dict(family=MONO, size=11, color=INK_2),
        title=dict(font=dict(family=MONO, size=11, color=INK_2)),
    )
    return go.layout.Template(
        layout=dict(
            font=dict(family=TEXT, size=13, color=INK),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            colorway=[INK, RED, INK_3, YELLOW],
            xaxis=axis,
            yaxis={**axis, "showline": False, "ticks": "", "showgrid": True, "gridcolor": RULE_2, "gridwidth": 1},
            hoverlabel=dict(bgcolor=CARD, bordercolor=INK, font=dict(family=MONO, size=12, color=INK)),
            margin=dict(l=8, r=8, t=8, b=8),
            showlegend=False,
        )
    )


pio.templates["weaklink"] = _template()
PLOTLY_CONFIG = {"displayModeBar": False, "scrollZoom": False, "responsive": True}
