"""Rendering: static HTML blocks (st.html) and clickable custom components (v2)."""

from __future__ import annotations

import hashlib
from html import escape

import numpy as np
import streamlit as st

from . import theme
from .labels import (
    FORMATIONS, NNBSP, PASS_RESULTS, dec, down_label, num, pct, pts, sec, short_name, split_name, team_name,
)
from .stats import GROUP_LABELS

LOGO = f"""<svg viewBox="0 0 46 26" role="img" aria-label="Weak Link">
<rect x="2" y="5" width="24" height="16" rx="8" fill="none" stroke="{theme.INK}" stroke-width="3.4"/>
<rect x="19" y="5" width="24" height="16" rx="8" fill="none" stroke="{theme.RED}" stroke-width="3.4"
 pathLength="100" stroke-dasharray="74 26" stroke-dashoffset="-6"/></svg>"""


def _esc(value) -> str:
    return escape("" if value is None else str(value))


def _jersey(value) -> str:
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return "—"


def html(block: str) -> None:
    st.html(block)


# ---------------------------------------------------------------- page blocks

def masthead(ds, n_plays: int, n_games: int) -> None:
    if ds.is_demo:
        status = '<span class="wl-status demo"><i></i>Démo · timing simulé</span>'
    else:
        status = f'<span class="wl-status"><i></i>Tracking · blocks.csv {ds.updated or ""}</span>'
    html(
        f"""
<header class="wl-page">
  <div class="wl-mast">
    <div class="wl-brand">{LOGO}<span class="wl-word">Weak Link</span></div>
    <div class="wl-tagline"><b>Le bloqueur qui craque</b>, la situation où il craque, et le replay qui le prouve.</div>
    {status}
  </div>
  <div class="wl-meta">
    <span>Scouting de protection de passe</span><span>NFL <b>2021</b> · semaines <b>1–8</b></span>
    <span><b>{num(n_games)}</b> matchs</span><span><b>{num(n_plays)}</b> jeux de passe</span>
    <span><b>{num(len(ds.blocks))}</b> duels de bloc</span><span>NGS tracking + PFF</span>
  </div>
</header>"""
    )


def demo_banner(warnings: list[str]) -> None:
    extra = "".join(f"<br>{_esc(w)}" for w in warnings)
    html(
        f"""<div class="wl-banner wl-page"><b>Mode démo</b><span>Duels, pressions et sacks PFF réels ; le <i>temps tenu</i>
est simulé en attendant la métrique tracking. L'app bascule seule sur <code>data/processed/blocks.csv</code> dès qu'il existe.{extra}</span></div>"""
    )


def section(num_label: str, title: str, aside: str = "") -> None:
    html(
        f"""<div class="wl-sec wl-page"><span class="n">{_esc(num_label)}</span><h2>{_esc(title)}</h2>
<span class="aside">{_esc(aside)}</span></div>"""
    )


def sub(text_html: str) -> None:
    html(f'<p class="wl-sub wl-page">{text_html}</p>')


def verdict(team: str, label: str, w, bio: dict, league: dict, team_rate: float, team_rank: int, n_teams: int, worst) -> None:
    first, last = split_name(w["name"])
    group = GROUP_LABELS.get(w["group"], "bloqueurs")
    ratio = w["rate"] / w["pos_rate"] if w["pos_rate"] else np.nan
    chips = [
        f'<span class="wl-chip solid">{_esc(w["slot"])}</span>',
        f'<span class="wl-chip">#{_jersey(w["jersey"])}</span>',
        f'<span class="wl-chip">{num(w["duels"])} duels</span>',
    ]
    if bio.get("age"):
        chips.append(f'<span class="wl-chip soft">{bio["age"]} ans</span>')
    if bio.get("college"):
        chips.append(f'<span class="wl-chip soft">{_esc(bio["college"])}</span>')

    if ratio == ratio and ratio >= 1.05:
        compare = f'<b>{dec(ratio)}×</b> la moyenne des {group} NFL'
    elif ratio == ratio and ratio <= 0.95:
        compare = f"pourtant sous la moyenne des {group} NFL ({pct(w['pos_rate'])})"
    else:
        compare = f"dans la moyenne des {group} NFL"
    rupture = (
        f" Quand il cède, son défenseur est sur le QB en <b>{sec(w['rupture'])}</b>."
        if w["rupture"] == w["rupture"] else ""
    )
    lede = f'Perd <b class="hot">{pct(w["rate"])}</b> de ses duels, {compare}.{rupture}'

    if worst:
        attack = (
            f'<div class="wl-attack"><span class="k">À attaquer</span><span><b>{_esc(worst["label"])}</b> : '
            f'{pct(worst["rate"], 0)} de duels perdus ({worst["losses"]} sur {worst["n"]}), '
            f'{pts(worst["delta"])} par rapport à son niveau habituel.</span></div>'
        )
    else:
        attack = ""
    rank_txt = (
        f"{team_rank}<sup>e</sup> ligne la plus fragile sur {n_teams}" if team_rank else ""
    )
    html(
        f"""
<div class="wl-verdict wl-page">
  <div class="wl-eyebrow">Maillon faible · {_esc(team_name(team))}</div>
  <div class="wl-first">{_esc(first)}</div>
  <div class="wl-last">{_esc(last)}</div>
  <div class="wl-idline">{''.join(chips)}</div>
  <p class="wl-lede">{lede}</p>
  {attack}
  <div class="wl-teamline">Ligne {_esc(team)} : <b>{pct(team_rate)}</b> de duels perdus · {rank_txt} · {_esc(label)}</div>
</div>"""
    )


def empty_state(title: str, body: str) -> None:
    html(f'<div class="wl-empty wl-page"><b>{_esc(title)}</b>{body}</div>')


def dossier_header(row, bio: dict, team: str) -> None:
    bits = [b for b in [
        bio.get("position") and f"{bio['position']}",
        bio.get("height") and f"{bio['height'].replace('-', '′')}″",
        bio.get("weight") and f"{bio['weight']} lb",
        bio.get("age") and f"{bio['age']} ans",
        bio.get("college"),
    ] if b]
    html(
        f"""<div class="wl-page"><div class="wl-who"><span class="jn">{_jersey(row['jersey'])}</span>
<span class="nm">{_esc(row['name'])}</span><span class="ps">{_esc(row['slot'])} · {_esc(team)}</span></div>
<div class="wl-bio">{' · '.join(_esc(b) for b in bits)}</div></div>"""
    )


def kpis(row, league_rate_group: float) -> None:
    group = GROUP_LABELS.get(row["group"], "bloqueurs")
    hot = row["eligible"] and row["rate"] > row["pos_rate"] * 1.15
    idx = row["index"]
    items = [
        ("Duels", num(row["duels"]), "dans la situation"),
        ("Duels perdus", pct(row["rate"]), f"{group} NFL : {pct(league_rate_group)}", hot),
        ("Indice poste", "—" if idx != idx else f"{idx:.0f}", "100 = moyenne NFL", hot),
        ("Rupture moy.", "—" if row["rupture"] != row["rupture"] else dec(row["rupture"]) + f"<small>{NNBSP}s</small>", "quand il perd"),
        ("Pressions accordées", num(row["pressures"]), "hit, hurry ou sack · PFF"),
        ("Sacks accordés", num(row["sacks"]), "PFF"),
    ]
    cells = []
    for item in items:
        label, value, note = item[:3]
        is_hot = len(item) > 3 and item[3]
        value_html = value if "<small>" in value else _esc(value)
        cells.append(
            f'<div class="wl-kpi"><div class="l">{label}</div><div class="v{" hot" if is_hot else ""}">{value_html}</div>'
            f'<div class="s">{_esc(note)}</div></div>'
        )
    html(f'<div class="wl-kpis wl-page">{"".join(cells)}</div>')


def nemeses(rows: list[dict]) -> None:
    if not rows:
        items = '<li><span class="i">—</span><span>Aucun défenseur ne l’a battu ici.</span><span></span></li>'
    else:
        items = "".join(
            f'<li><span class="i">{i + 1:02d}</span><span>{_esc(r["defenderName"])}<span class="p">{_esc(r.get("pos") or "")}</span></span>'
            f'<span class="w"><b>{int(r["wins"])}</b> / {int(r["duels"])} duels</span></li>'
            for i, r in enumerate(rows)
        )
    html(f'<div class="wl-nem wl-page"><h4>Qui le bat</h4><ol>{items}</ol></div>')


def chart_head(title: str, insight_html: str, keys_html: str) -> None:
    html(
        f"""<div class="wl-page"><div class="wl-chart-head"><h4>{_esc(title)}</h4><div class="wl-keys">{keys_html}</div></div>
<p class="wl-insight">{insight_html}</p></div>"""
    )


def splits(rows: list[dict], group: str) -> None:
    peers = [r["peer"] for r in rows if r["peer"] == r["peer"]]
    rates = [r["rate"] for r in rows if r["rate"] == r["rate"]]
    scale = max([0.2] + peers + rates) * 1.08
    cells = []
    for r in rows:
        has = r["rate"] == r["rate"]
        hot = has and not r["is_base"] and r["n"] >= 15 and r["delta"] >= 0.05
        cls = "wl-split" + (" base" if r["is_base"] else "") + (" hot" if hot else "") + ("" if has else " na")
        fill = f'<span class="f" style="width:{min(100, 100 * r["rate"] / scale):.1f}%"></span>' if has else ""
        peer = f'<span class="pk" style="left:{min(100, 100 * r["peer"] / scale):.1f}%"></span>' if r["peer"] == r["peer"] else ""
        delta = "réf." if r["is_base"] else (pts(r["delta"]) if has else "")
        cells.append(
            f'<div class="{cls}"><span class="lb">{_esc(r["label"])}</span><span class="bar">{fill}{peer}</span>'
            f'<span class="v">{pct(r["rate"], 0) if has else "—"}</span><span class="d">{delta}</span>'
            f'<span class="nn">n={r["n"]}</span></div>'
        )
    half = (len(cells) + 1) // 2
    group_label = GROUP_LABELS.get(group, "bloqueurs")
    html(
        f"""<div class="wl-page"><div class="wl-split-legend"><span><i></i>son taux de duels perdus</span>
<span><i class="hot"></i>situation à cibler (+5 pts, n ≥ 15)</span><span><i class="pk"></i>moyenne des {group_label} NFL</span></div>
<div class="wl-splits"><div>{''.join(cells[:half])}</div><div>{''.join(cells[half:])}</div></div></div>"""
    )


def play_head(play, team: str) -> None:
    opp = play.get("defensiveTeam") or ""
    home = play.get("homeTeamAbbr")
    venue = f"{team} @ {opp}" if home == opp else f"{opp} @ {team}"
    chips = [
        f'<span class="wl-chip solid">S{int(play["week"])}</span>' if play.get("week") == play.get("week") else "",
        f'<span class="wl-chip">{_esc(venue)}</span>',
        f'<span class="wl-chip">Q{_esc(play.get("quarter", "—"))} · {_esc(play.get("gameClock", ""))}</span>',
        f'<span class="wl-chip">{_esc(down_label(play.get("down"), play.get("yardsToGo")))}</span>',
        f'<span class="wl-chip">{int(play["nb_rushers"])} rushers</span>',
    ]
    if play.get("stunt"):
        chips.append('<span class="wl-chip">Stunt</span>')
    if play.get("pff_playAction") == 1:
        chips.append('<span class="wl-chip">Play action</span>')
    if isinstance(play.get("pff_passCoverage"), str):
        chips.append(f'<span class="wl-chip soft">{_esc(play["pff_passCoverage"])}</span>')
    formation = FORMATIONS.get(play.get("offenseFormation"), play.get("offenseFormation"))
    if isinstance(formation, str):
        chips.append(f'<span class="wl-chip soft">{_esc(formation)}</span>')
    html(
        f"""<div class="wl-page"><div class="wl-play-head">{''.join(chips)}</div>
<div class="wl-play-desc">{_esc(play.get("playDescription", ""))}</div></div>"""
    )


def replay_legend(blocker: str, defender: str, threshold: float) -> None:
    html(
        f"""<div class="wl-legend wl-page"><span><i class="b"></i>{_esc(short_name(blocker))} (bloqueur)</span>
<span><i class="d"></i>{_esc(short_name(defender))} (défenseur bloqué)</span><span><i class="q">★</i>QB</span>
<span><i class="o"></i>attaque</span><span><i class="x"></i>défense</span>
<span><i class="l"></i>distance défenseur → QB</span><span><i class="l hot"></i>&lt; {dec(threshold)}{NNBSP}yd : pression</span></div>"""
    )


def note(text: str) -> None:
    html(f'<div class="wl-note wl-page">{_esc(text)}</div>')


def footer(ds, replay_source: str, threshold: float) -> None:
    source = "tracking (Partie 1)" if not ds.is_demo else "démo — temps simulé, duels PFF réels"
    html(
        f"""<footer class="wl-page"><div class="wl-foot">
<div><h5>Temps tenu</h5><p>Temps entre le snap et le moment où le défenseur bloqué passe à moins de <b>{dec(threshold)} yards</b> du QB,
plafonné à la passe ou au sack. Le défenseur vient de <b>pff_nflIdBlockedPlayer</b>.</p></div>
<div><h5>Lecture</h5><p>Chaque bloqueur est comparé aux joueurs de <b>son poste</b> : un tackle affronte les meilleurs edge rushers.
L’indice 100 = moyenne NFL du poste, dans la même situation.</p></div>
<div><h5>Prudence</h5><p>Un taux sur 30 duels reste fragile : la barre grise montre l’intervalle de confiance à 80 %.
La courbe de rupture (Kaplan–Meier) ne pénalise pas les passes rapides.</p></div>
<div><h5>Limites</h5><p>8 semaines, jeux de passe uniquement. Le seuil de {dec(threshold)} yards est une convention.
Sur un stunt, le premier défenseur bloqué n’est pas toujours celui qui arrive. Démo, pas un produit fini.</p></div>
</div><div class="wl-colophon">Données : NFL Next Gen Stats · Pro Football Focus · Big Data Bowl 2023 — Duels : {source} — Replay : {_esc(replay_source)}</div></footer>"""
    )


# ---------------------------------------------------------------- clickable components

_PICK_JS = """
export default function ({ parentElement, data, setTriggerValue }) {
  let root = parentElement.querySelector('.wl-mount');
  if (!root) {
    root = document.createElement('div');
    root.className = 'wl wl-mount';
    parentElement.appendChild(root);
  }
  if (root.dataset.sig !== data.sig) {
    root.innerHTML = data.html;
    root.dataset.sig = data.sig;
  }
  root.onclick = (event) => {
    const el = event.target.closest('[data-pick]');
    if (!el || !root.contains(el)) return;
    root.querySelectorAll('[data-pick].is-selected').forEach((n) => {
      n.classList.remove('is-selected');
      n.setAttribute('aria-pressed', 'false');
    });
    el.classList.add('is-selected');
    el.setAttribute('aria-pressed', 'true');
    setTriggerValue('pick', el.dataset.pick);
  };
}
"""

LINE_CSS = theme.COMPONENT_BASE + """
.wl-mount { padding: 0.15rem 0 0.2rem; }
.scrim { display: flex; justify-content: space-between; align-items: center; font-family: var(--mono); font-size: 0.64rem;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-2); padding: 0 0 0.55rem; }
.scrim .ball { display: inline-flex; align-items: center; gap: 0.45rem; }
.scrim .ball svg { width: 18px; height: 11px; }
.slots { display: grid; grid-template-columns: 1fr 14px 1fr 14px 1fr 14px 1fr 14px 1fr; align-items: stretch; }
.link { align-self: start; margin-top: 4.1rem; height: 2px; background: var(--ink); }
.link.broken { background: repeating-linear-gradient(90deg, var(--red) 0 3px, transparent 3px 6px); }
.slot { position: relative; display: flex; flex-direction: column; min-height: 15.2rem; padding: 0.7rem 0.75rem 0.75rem;
  background: var(--card); border: 1px solid var(--ink); transition: transform .18s var(--ease), box-shadow .18s var(--ease); }
.slot:hover { transform: translateY(-2px); }
.slot .pos { font-family: var(--mono); font-size: 0.7rem; font-weight: 600; letter-spacing: 0.14em; }
.slot .tag { position: absolute; top: 0.7rem; right: 0.7rem; font-family: var(--mono); font-size: 0.56rem; font-weight: 600;
  letter-spacing: 0.1em; text-transform: uppercase; }
.slot .jn { font-family: var(--display); font-weight: 850; font-size: 3.7rem; line-height: 0.82; margin-top: 0.45rem;
  color: transparent; -webkit-text-stroke: 1.4px var(--ink); }
.slot .nm { font-family: var(--display); font-weight: 760; font-size: 1.2rem; line-height: 1; text-transform: uppercase;
  margin-top: 0.4rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.slot .fn { font-family: var(--mono); font-size: 0.62rem; color: var(--ink-2); letter-spacing: 0.06em; text-transform: uppercase;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 0.15rem; }
.slot .rt { font-family: var(--display); font-weight: 820; font-size: 2rem; line-height: 1; margin-top: auto; padding-top: 0.7rem; }
.slot .rt small { font-size: 1rem; }
.slot .ml { font-family: var(--mono); font-size: 0.58rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-2); margin-top: 0.15rem; }
.slot .mt { position: relative; height: 6px; background: var(--paper-2); margin-top: 0.55rem; }
.slot .mt i { position: absolute; inset: 0 auto 0 0; background: var(--ink); }
.slot .mt b { position: absolute; top: -4px; bottom: -4px; width: 0; border-left: 2px solid var(--red); }
.slot .ft { font-family: var(--mono); font-size: 0.62rem; color: var(--ink-2); margin-top: 0.5rem; letter-spacing: 0.02em; }
.slot.flag .rt { color: var(--red-ink); }
.slot.thin { opacity: 0.55; }
.slot.weak { background: var(--red); border-color: var(--red); color: var(--paper); }
.slot.weak .jn { color: var(--paper); -webkit-text-stroke: 0; }
.slot.weak .fn, .slot.weak .ft, .slot.weak .ml { color: rgba(250,248,243,0.82); }
.slot.weak .rt { color: var(--paper); }
.slot.weak .mt { background: rgba(250,248,243,0.28); }
.slot.weak .mt i { background: var(--paper); }
.slot.weak .mt b { border-color: var(--ink); }
.slot.is-selected { box-shadow: 0 0 0 3px var(--paper), 0 0 0 5px var(--ink); }
.slot.is-selected::after { content: "Dossier ↓"; position: absolute; left: 50%; bottom: -1.75rem; transform: translateX(-50%);
  font-family: var(--mono); font-size: 0.6rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--ink);
  background: var(--yellow); padding: 0.12rem 0.4rem; white-space: nowrap; }
.slot.empty { cursor: default; border-style: dashed; border-color: var(--ink-3); color: var(--ink-3); }
.legend { display: flex; justify-content: space-between; gap: 1rem; margin-top: 2.3rem; font-family: var(--mono); font-size: 0.64rem;
  color: var(--ink-2); letter-spacing: 0.04em; }
.legend span { display: inline-flex; align-items: center; gap: 0.4rem; }
.legend i { display: inline-block; width: 0; height: 0.8rem; border-left: 2px solid var(--red); }
.also { font-family: var(--mono); font-size: 0.64rem; color: var(--ink-2); margin-top: 0.4rem; }
.also button { text-decoration: underline; text-underline-offset: 2px; }
"""

RANK_CSS = theme.COMPONENT_BASE + """
table { width: 100%; border-collapse: collapse; }
thead th { font-family: var(--mono); font-size: 0.62rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--ink-2); text-align: left; padding: 0 0.6rem 0.5rem; border-bottom: 1px solid var(--ink); white-space: nowrap; }
thead th.num { text-align: right; }
tbody td { padding: 0.55rem 0.6rem; border-bottom: 1px solid var(--rule); vertical-align: middle; }
td.num { text-align: right; font-family: var(--mono); font-size: 0.86rem; white-space: nowrap; }
td.rk { font-family: var(--mono); font-size: 0.72rem; color: var(--ink-3); width: 2.4rem; }
tr.grp td { font-family: var(--mono); font-size: 0.62rem; font-weight: 600; letter-spacing: 0.14em; text-transform: uppercase;
  color: var(--ink); padding: 1.1rem 0.6rem 0.4rem; border-bottom: 1px solid var(--ink); }
tr.grp:first-child td { padding-top: 0.5rem; }
tr.cut td { font-family: var(--mono); font-size: 0.6rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-3);
  padding: 0.6rem 0.6rem 0.3rem; border-bottom: 1px dashed var(--rule); }
tr.row { cursor: pointer; transition: background .12s var(--ease); }
tr.row:hover { background: var(--paper-2); }
tr.row.is-selected { background: var(--yellow-wash); }
tr.row.is-selected td.rk { box-shadow: inset 4px 0 0 var(--ink); color: var(--ink); }
.who { display: flex; align-items: baseline; gap: 0.6rem; min-width: 12rem; }
.who button { font-family: var(--display); font-weight: 760; font-size: 1.16rem; text-transform: uppercase; line-height: 1.05; letter-spacing: 0.005em; }
.who .meta { font-family: var(--mono); font-size: 0.66rem; color: var(--ink-2); letter-spacing: 0.04em; white-space: nowrap; }
.who .weak { font-family: var(--mono); font-size: 0.56rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--paper); background: var(--red); padding: 0.1rem 0.32rem; white-space: nowrap; }
td.viz { width: 34%; min-width: 15rem; }
.vz { display: grid; grid-template-columns: 1fr 4.2rem; align-items: center; gap: 0.7rem; }
.track { position: relative; height: 18px; }
.track::before { content: ""; position: absolute; left: 0; right: 0; top: 8px; height: 2px; background: var(--rule-2); }
.track .ci { position: absolute; top: 7px; height: 4px; background: var(--ink-3); opacity: 0.55; }
.track .pk { position: absolute; top: 1px; height: 16px; width: 0; border-left: 2px solid var(--ink); }
.track .dt { position: absolute; top: 3px; width: 12px; height: 12px; margin-left: -6px; border-radius: 50%; background: var(--ink); }
.row.flag .track .dt { background: var(--red); }
.row.thin .track .dt { background: var(--card); border: 2px solid var(--ink-3); }
.vz .val { font-family: var(--mono); font-weight: 600; font-size: 0.88rem; text-align: right; }
.row.flag .vz .val, .row.flag td.idx { color: var(--red-ink); }
td.idx { font-weight: 600; }
.row.thin td, .row.thin button { color: var(--ink-3); }
.scale { display: flex; justify-content: space-between; font-family: var(--mono); font-size: 0.58rem; color: var(--ink-3); margin-top: 0.2rem; padding-right: 4.9rem; }
@media (max-width: 900px) { .hide-sm { display: none; } }
"""

DUELS_CSS = theme.COMPONENT_BASE + """
ol { list-style: none; margin: 0; padding: 0; max-height: 34rem; overflow-y: auto; border-top: 1px solid var(--ink); scrollbar-width: thin; }
li { border-bottom: 1px solid var(--rule); }
.duel { display: grid; grid-template-columns: 4.3rem 1fr; gap: 0.8rem; width: 100%; padding: 0.7rem 0.6rem 0.75rem 0.7rem;
  transition: background .12s var(--ease); }
.duel:hover { background: var(--paper-2); }
.duel.is-selected { background: var(--yellow-wash); box-shadow: inset 4px 0 0 var(--ink); }
.tt { font-family: var(--display); font-weight: 820; font-size: 1.9rem; line-height: 0.95; }
.tt small { font-size: 0.85rem; font-weight: 700; margin-left: 1px; }
.tt span { display: block; font-family: var(--mono); font-size: 0.56rem; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-2); margin-top: 0.2rem; }
.body { display: flex; flex-direction: column; gap: 0.18rem; min-width: 0; }
.top { font-family: var(--mono); font-size: 0.64rem; color: var(--ink-2); letter-spacing: 0.06em; text-transform: uppercase; }
.mid { display: flex; align-items: center; gap: 0.5rem; font-weight: 650; font-size: 0.98rem; }
.sev { font-family: var(--mono); font-size: 0.58rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; padding: 0.12rem 0.35rem; border: 1px solid var(--ink); }
.sev.s2 { background: var(--red); border-color: var(--red); color: var(--paper); }
.sev.s1 { border-color: var(--red-ink); color: var(--red-ink); }
.desc { font-size: 0.82rem; color: var(--ink-2); line-height: 1.35; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.more { font-family: var(--mono); font-size: 0.62rem; color: var(--ink-3); padding: 0.55rem 0.7rem; letter-spacing: 0.06em; }
"""

_line_component = st.components.v2.component("wl_line", css=LINE_CSS, js=_PICK_JS)
_rank_component = st.components.v2.component("wl_rank", css=RANK_CSS, js=_PICK_JS)
_duels_component = st.components.v2.component("wl_duels", css=DUELS_CSS, js=_PICK_JS)


def _mount(component, key: str, markup: str, on_pick) -> None:
    sig = hashlib.md5(markup.encode()).hexdigest()[:12]
    component(key=key, data={"html": markup, "sig": sig}, on_pick_change=on_pick)


BALL_SVG = f'<svg viewBox="0 0 18 11" aria-hidden="true"><ellipse cx="9" cy="5.5" rx="8.2" ry="4.8" fill="{theme.BALL}"/><path d="M6 5.5h6M7.5 4.3v2.4M9 4.3v2.4M10.5 4.3v2.4" stroke="{theme.CARD}" stroke-width=".9"/></svg>'


def line(slots: list[dict], weak_id: int | None, selected: int | None, scale: float, key: str, on_pick) -> None:
    cards = []
    weak_index = next((i for i, s in enumerate(slots) if not s["empty"] and s["blockerId"] == weak_id), None)
    for i, s in enumerate(slots):
        if i:
            broken = weak_index is not None and (i == weak_index or i - 1 == weak_index)
            cards.append(f'<span class="link{" broken" if broken else ""}" aria-hidden="true"></span>')
        if s["empty"]:
            cards.append(f'<div class="slot empty"><span class="pos">{s["slot"]}</span><span class="ft" style="margin-top:auto">Aucun duel</span></div>')
            continue
        cls = ["slot"]
        is_weak = s["blockerId"] == weak_id
        if is_weak:
            cls.append("weak")
        elif s["flag"]:
            cls.append("flag")
        if not s["eligible"]:
            cls.append("thin")
        if s["blockerId"] == selected:
            cls.append("is-selected")
        first, last = split_name(s["name"])
        fill = min(100, 100 * s["rate"] / scale)
        peer = min(100, 100 * s["pos_rate"] / scale)
        tag = '<span class="tag">Maillon faible</span>' if is_weak else ('<span class="tag">Échantillon faible</span>' if not s["eligible"] else "")
        rate_txt = pct(s["rate"]).replace(NNBSP + "%", f"<small>{NNBSP}%</small>")
        idx = "—" if s["index"] != s["index"] else f"{s['index']:.0f}"
        cards.append(
            f'<button class="{" ".join(cls)}" data-pick="{s["blockerId"]}" aria-pressed="{str(s["blockerId"] == selected).lower()}"'
            f' aria-label="{_esc(s["slot"])} {_esc(s["name"])}, {pct(s["rate"])} de duels perdus">'
            f'<span class="pos">{s["slot"]}</span>{tag}<span class="jn">{_jersey(s["jersey"])}</span>'
            f'<span class="nm">{_esc(last)}</span><span class="fn">{_esc(first)}</span>'
            f'<span class="rt">{rate_txt}</span><span class="ml">duels perdus</span>'
            f'<span class="mt"><i style="width:{fill:.1f}%"></i><b style="left:{peer:.1f}%"></b></span>'
            f'<span class="ft">{num(s["duels"])} duels · indice {idx}</span></button>'
        )
    also = []
    for s in slots:
        if not s["empty"] and s["others"]:
            names = ", ".join(
                f'<button data-pick="{o["blockerId"]}">{_esc(short_name(o["name"]))}</button> ({o["duels"]})' for o in s["others"]
            )
            also.append(f'{s["slot"]} : {names}')
    also_html = f'<div class="also">Aussi aligné — {" · ".join(also)}</div>' if also else ""
    markup = f"""
<div class="scrim"><span>Ligne offensive · vue depuis le QB</span><span class="ball">{BALL_SVG}Ligne de mêlée</span></div>
<div class="slots">{''.join(cards)}</div>
<div class="legend"><span>Barre : part de duels perdus</span><span><i></i>moyenne NFL du poste</span><span>Cliquez un joueur pour ouvrir son dossier</span></div>
{also_html}"""
    _mount(_line_component, key, markup, on_pick)


def ranking(table, selected: int | None, weak_id: int | None, min_duels: int, key: str, on_pick) -> None:
    scale = max(0.3, float(np.nanmax(table["ci_hi"])) if len(table) else 0.3)
    scale = min(1.0, np.ceil(scale * 20) / 20)

    def row_html(r, rank: str) -> str:
        cls = ["row"]
        if r["flag"]:
            cls.append("flag")
        if not r["eligible"]:
            cls.append("thin")
        if r["blockerId"] == selected:
            cls.append("is-selected")
        lo, hi = 100 * r["ci_lo"] / scale, 100 * r["ci_hi"] / scale
        dot = 100 * r["rate"] / scale
        pk = 100 * r["pos_rate"] / scale if r["pos_rate"] == r["pos_rate"] else None
        weak = '<span class="weak">Maillon faible</span>' if r["blockerId"] == weak_id else ""
        idx = "—" if r["index"] != r["index"] else f"{r['index']:.0f}"
        return (
            f'<tr class="{" ".join(cls)}" data-pick="{int(r["blockerId"])}" aria-pressed="{str(r["blockerId"] == selected).lower()}">'
            f'<td class="rk">{rank}</td>'
            f'<td><div class="who"><button data-pick="{int(r["blockerId"])}">{_esc(short_name(r["name"]))}</button>'
            f'<span class="meta">{_esc(r["slot"])} · #{_jersey(r["jersey"])}</span>{weak}</div></td>'
            f'<td class="num">{num(r["duels"])}</td>'
            f'<td class="viz"><div class="vz"><div class="track"><span class="ci" style="left:{lo:.1f}%;width:{max(0.6, hi - lo):.1f}%"></span>'
            + (f'<span class="pk" style="left:{pk:.1f}%"></span>' if pk is not None else "")
            + f'<span class="dt" style="left:{dot:.1f}%"></span></div><span class="val">{pct(r["rate"])}</span></div></td>'
            f'<td class="num idx">{idx}</td>'
            f'<td class="num hide-sm">{sec(r["rupture"])}</td>'
            f'<td class="num">{num(r["pressures"])}</td>'
            f'<td class="num">{num(r["sacks"])}</td></tr>'
        )

    body = []
    for is_ol, title in [(True, "Ligne offensive"), (False, "TE, RB et autres bloqueurs")]:
        part = table.loc[table["is_ol"].eq(is_ol)]
        if part.empty:
            continue
        body.append(f'<tr class="grp"><td colspan="8">{title}</td></tr>')
        ok, thin = part.loc[part["eligible"]], part.loc[~part["eligible"]]
        for i, (_, r) in enumerate(ok.iterrows()):
            body.append(row_html(r, f"{i + 1:02d}"))
        if not thin.empty:
            body.append(f'<tr class="cut"><td colspan="8">Échantillon trop faible (moins de {min_duels} duels) — non classés</td></tr>')
            for _, r in thin.iterrows():
                body.append(row_html(r, "—"))
    ticks = "".join(f"<span>{int(round(t * 100))}{NNBSP}%</span>" for t in np.linspace(0, scale, 5))
    markup = f"""<table>
<thead><tr><th>#</th><th>Bloqueur</th><th class="num">Duels</th><th>Duels perdus · intervalle 80 % · moyenne du poste</th>
<th class="num">Indice</th><th class="num hide-sm">Rupture</th><th class="num">Pressions</th><th class="num">Sacks</th></tr></thead>
<tbody>{''.join(body)}</tbody></table><div class="scale">{ticks}</div>"""
    _mount(_rank_component, key, markup, on_pick)


def duels(lost, selected_key: str | None, key: str, on_pick, limit: int = 60) -> None:
    items = []
    for _, d in lost.head(limit).iterrows():
        pick = f'{int(d["gameId"])}:{int(d["playId"])}'
        if d["sack_allowed"]:
            sev = '<span class="sev s2">Sack accordé</span>'
        elif d["pressure_allowed"]:
            sev = '<span class="sev s1">Pression accordée</span>'
        else:
            sev = '<span class="sev">Battu</span>'
        opp = d.get("defensiveTeam") or ""
        week = f"S{int(d['week'])}" if d["week"] == d["week"] else ""
        result = PASS_RESULTS.get(d.get("passResult"), "")
        top = " · ".join(x for x in [week, f"Q{_esc(d.get('quarter', ''))} {_esc(d.get('gameClock', ''))}", f"vs {_esc(opp)}", _esc(result)] if x)
        cls = "duel is-selected" if pick == selected_key else "duel"
        items.append(
            f'<li><button class="{cls}" data-pick="{pick}" aria-pressed="{str(pick == selected_key).lower()}">'
            f'<span class="tt">{dec(d["temps_tenu"])}<small>{NNBSP}s</small><span>tenu</span></span>'
            f'<span class="body"><span class="top">{top}</span>'
            f'<span class="mid">{_esc(down_label(d.get("down"), d.get("yardsToGo")))} {sev}</span>'
            f'<span class="desc">{_esc(d.get("playDescription", ""))}</span></span></button></li>'
        )
    more = f'<div class="more">+ {len(lost) - limit} autres duels perdus</div>' if len(lost) > limit else ""
    _mount(_duels_component, key, f"<ol>{''.join(items)}</ol>{more}", on_pick)
