"""Weak Link — pass-protection scouting for a coach, in one screen.

Part 3 of the hackathon plan (app + pitch). Run from the `frontend/` folder:

    streamlit run app.py

The app reads `data/processed/blocks.csv` (Part 1 deliverable) the moment it exists,
and otherwise runs on a contract-compatible demo built from the real PFF duels.
The replay is our own field, drawn in the Weak Link scouting-report style.
"""

from __future__ import annotations

import numpy as np
import streamlit as st

from weaklink import charts, data, replay, stats, theme, ui
from weaklink.labels import NNBSP, dec, pct, short_name, team_name

st.set_page_config(
    page_title="Weak Link · Scouting de protection",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)
theme.inject()

MIN_DUELS_DEFAULT = 40


# --------------------------------------------------------------------------- state

def _state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def _pick_player(pid) -> None:
    try:
        st.session_state.selected_player = int(pid)
    except (TypeError, ValueError):
        return
    st.session_state.selected_duel = None


def _pick_duel(value) -> None:
    st.session_state.selected_duel = str(value)


# --------------------------------------------------------------------------- load

ds = data.load_dataset()
blocks = stats.with_groups(ds.blocks)
n_games = int(blocks["gameId"].nunique())
n_plays = int(blocks.groupby(["gameId", "playId"]).ngroups)
teams = data.team_list(blocks)

ui.masthead(ds, n_plays, n_games)
if ds.is_demo:
    ui.demo_banner(ds.warnings)


# --------------------------------------------------------------------------- sidebar

with st.sidebar:
    st.html(f'<div class="wl-side-title wl-page">{ui.LOGO}<span>Plan de match</span></div>')

    default_team = teams.index("LV") if "LV" in teams else 0
    team = st.selectbox(
        "Ligne offensive adverse", teams, index=default_team,
        format_func=lambda t: f"{t} · {team_name(t)}",
        help="L'équipe dont vous préparez la défense. On analyse SA protection de passe.",
    )

    situations = st.pills(
        "Situation", list(stats.SITUATIONS), default=[], selection_mode="multi",
        format_func=lambda s: stats.SITUATIONS[s],
        help="Croisez les filtres : 3e down + blitz isole les passages où la protection casse.",
    )

    formations = ["(toutes)"] + sorted(
        blocks.loc[blocks["team"].eq(team), "offenseFormation"].dropna().unique().tolist()
    )
    formation = st.selectbox(
        "Formation", formations,
        format_func=lambda f: "Toutes formations" if f == "(toutes)" else theme.FORMATIONS_LABEL(f),
    )

    min_duels = st.slider(
        "Seuil de duels pour le classement", 10, 120, MIN_DUELS_DEFAULT, step=5,
        help="En dessous, un taux de duels perdus n'est pas fiable. Les joueurs sous le seuil sont montrés mais non classés.",
    )

    st.html('<hr class="wl-side-rule"/>')
    st.html(
        f'<div class="wl-side-note wl-page">Données <b>{"réelles" if not ds.is_demo else "démo"}</b> · '
        f'{data.as_int(n_games)} matchs · seuil pression <b>{dec(replay.PRESSURE_YD)}{NNBSP}yd</b>.<br>'
        f'Replay : <b>{replay.replay_source()}</b>.</div>'
    )

flt = stats.Filters(tuple(situations), None if formation == "(toutes)" else formation)


# --------------------------------------------------------------------------- compute

league_all = stats.league_rates(stats.apply_filters(blocks, flt))
team_blocks = stats.apply_filters(blocks[blocks["team"].eq(team)], flt)
table = stats.ranking(team_blocks, league_all, min_duels)
weak = stats.weakest(table)
weak_id = int(weak["blockerId"]) if weak is not None else None

selected = _state("selected_player", weak_id)
if table.empty:
    selected = None
elif selected not in set(table["blockerId"]):
    selected = weak_id
    st.session_state.selected_player = weak_id


# --------------------------------------------------------------------------- 01 · verdict

ui.section("01", "Le maillon faible", flt.label())

if weak is None:
    ui.empty_state(
        "Pas assez de duels",
        f"<span>Aucun bloqueur de {team_name(team)} n'atteint {min_duels} duels dans cette situation. "
        "Baissez le seuil ou retirez un filtre.</span>",
    )
else:
    bio = data.player_bio(ds.players, weak_id)
    team_rate, team_rank, n_teams = stats.team_line_rank(stats.apply_filters(blocks, flt), team)
    worst = stats.worst_split(stats.splits(team_blocks[team_blocks["blockerId"].eq(weak_id)], blocks, weak["group"]))
    ui.verdict(team, flt.label(), weak, bio, league_all, team_rate, team_rank, n_teams, worst)


# --------------------------------------------------------------------------- 02 · O-line

ui.section("02", "La ligne, poste par poste", "Vue depuis le quarterback")
ui.sub(
    "Chaque case est le joueur qui a le plus souvent tenu ce poste. "
    "La barre montre sa <b>part de duels perdus</b>, le repère la <b>moyenne NFL du poste</b>. "
    "Le lien rompu marque le maillon faible."
)
line_slots = stats.line_slots(team_blocks, table)
line_scale = max(0.2, float(np.nanmax(table["pos_rate"])) if len(table) else 0.2,
                 float(np.nanmax(table.loc[table["is_ol"], "rate"])) if (table["is_ol"]).any() else 0.2) * 1.15
ui.line(line_slots, weak_id, selected, line_scale, "oline", lambda: _pick_player(st.session_state.oline.pick))


# --------------------------------------------------------------------------- 03 · ranking

ui.section("03", "Classement des bloqueurs", f"{team} · {flt.label()}")
ui.sub(
    "Trié par <b>indice de poste</b> (100 = moyenne NFL du poste). La barre d'incertitude à 80 % "
    "indique si l'écart tient sur l'échantillon. Cliquez un bloqueur pour ouvrir son dossier."
)
if table.empty:
    ui.empty_state("Aucun duel", "<span>Aucune donnée pour cette équipe dans cette situation.</span>")
else:
    ui.ranking(table, selected, weak_id, min_duels, "rank", lambda: _pick_player(st.session_state.rank.pick))


# --------------------------------------------------------------------------- 04 · dossier

if selected is not None:
    row = table.loc[table["blockerId"].eq(selected)].iloc[0]
    player_blocks = team_blocks[team_blocks["blockerId"].eq(selected)]
    bio = data.player_bio(ds.players, selected)

    ui.section("04", "Dossier du bloqueur", f"#{int(row['jersey']) if row['jersey'] == row['jersey'] else '—'}")
    ui.dossier_header(row, bio, team)
    ui.kpis(row, league_all.get(row["group"], league_all.get("ALL", np.nan)))

    left, right = st.columns([1.55, 1], gap="large")

    with left:
        peer = blocks.loc[blocks["group"].eq(row["group"])]
        peer = stats.apply_filters(peer, flt)
        release = stats.median_release(stats.apply_filters(blocks, flt))
        fig, at = charts.rupture_curve(
            player_blocks, peer, team_blocks, release, row["name"],
            f"moyenne {stats.GROUP_LABELS.get(row['group'], 'poste')}", f"ligne {team}",
        )
        if at is not None and at["player"] == at["player"]:
            gap = at["player"] - at["peer"]
            verb = "au-dessus de" if gap >= 0 else "sous"
            insight = (
                f"À la passe médiane (<b>{dec(at['t'])}{NNBSP}s</b>), il a déjà perdu "
                f"<b class='hot'>{pct(at['player'], 0)}</b> de ses duels, "
                f"{pct(abs(gap), 0)} {verb} ses pairs."
            )
        else:
            insight = "Part de duels perdus cumulée après le snap, corrigée des passes rapides."
        keys = (
            '<span><i></i>' + short_name(row["name"]) + '</span>'
            '<span><i class="peer"></i>moyenne du poste</span>'
            '<span><i class="team"></i>ligne ' + team + '</span>'
        )
        ui.chart_head("Quand la protection cède", insight, keys)
        st.plotly_chart(fig, config=theme.PLOTLY_CONFIG, key="rupture")

    with right:
        ui.nemeses(stats.nemeses(player_blocks))

    ui.chart_head(
        "Dans quelles situations il craque",
        "Taux de duels perdus par situation, comparé à son niveau habituel et à la moyenne du poste.",
        "",
    )
    ui.splits(stats.splits(player_blocks, blocks, row["group"]), row["group"])

    # ---------------------------------------------------------------- 05 · replay
    lost = stats.lost_duels(player_blocks)
    ui.section("05", "La preuve, au ralenti", f"{len(lost)} duels perdus")

    if lost.empty:
        ui.empty_state("Aucun duel perdu ici", "<span>Ce bloqueur n'a cédé aucun duel dans la situation filtrée.</span>")
    else:
        sel_duel = _state("selected_duel", None)
        keys = set(f'{int(d.gameId)}:{int(d.playId)}' for d in lost.itertuples())
        if sel_duel not in keys:
            top = lost.iloc[0]
            sel_duel = f"{int(top['gameId'])}:{int(top['playId'])}"
            st.session_state.selected_duel = sel_duel

        picker, stage = st.columns([1, 1.7], gap="large")
        with picker:
            ui.sub("Les duels perdus, du plus grave au plus rapide. Choisissez une action.")
            ui.duels(lost, sel_duel, "duels", lambda: _pick_duel(st.session_state.duels.pick))

        with stage:
            gid, pid = (int(x) for x in sel_duel.split(":"))
            play = lost.loc[(lost["gameId"].eq(gid)) & (lost["playId"].eq(pid))].iloc[0]
            ui.play_head(play, team)
            fig, source, err = replay.get_replay(gid, pid, selected)
            ui.replay_legend(row["name"], play.get("defenderName", "défenseur"), replay.PRESSURE_YD)
            st.plotly_chart(fig, config={**theme.PLOTLY_CONFIG, "displayModeBar": False}, key=f"replay-{sel_duel}")
            ui.note(f"Orienté attaque → droite · ligne rouge = défenseur à moins de {dec(replay.PRESSURE_YD)}{NNBSP}yd du QB.")


ui.footer(ds, replay.replay_source(), replay.PRESSURE_YD)
