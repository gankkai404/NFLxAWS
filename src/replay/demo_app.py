"""
Page de démonstration du replay (partie 2), branchée sur blocks.csv (partie 1).

    streamlit run src/replay/demo_app.py

Deux onglets :
- « Maillon faible » : classement des bloqueurs d'une équipe (summarize_blockers),
  clic sur un bloqueur → ses duels perdus → replay 2D de l'action.
- « Explorer une action » : choisit n'importe quelle action et son bloqueur à suivre.

Si blocks.csv n'existe pas encore, seul l'onglet « Explorer » est actif.
Pour le générer : python -m src.metrics --raw data
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # racine du repo

import streamlit as st  # noqa: E402

from src.replay import make_replay, play_duels  # noqa: E402
from src.replay.data import PASS_RESULT_LABELS, down_label, load_games, load_plays  # noqa: E402

st.set_page_config(page_title="Weak Link · Replay", page_icon="🏈", layout="wide")
st.title("🏈 Weak Link · replay")


@st.cache_data(show_spinner=False)
def _load_blocks():
    """Charge blocks.csv (partie 1) s'il existe, sinon None."""
    try:
        from src.metrics import load_blocks

        return load_blocks()
    except (ImportError, FileNotFoundError):
        return None


def _replay(game_id: int, play_id: int, focus):
    """Affiche le replay 2D + le tableau des duels de l'action."""
    st.plotly_chart(make_replay(int(game_id), int(play_id), focus), use_container_width=True)
    with st.expander("Duels de bloc de cette action"):
        st.dataframe(play_duels(int(game_id), int(play_id)), hide_index=True, use_container_width=True)


def onglet_maillon_faible(blocks):
    """Classement des bloqueurs d'une O-line + replay de leurs duels perdus."""
    from src.metrics import summarize_blockers

    st.sidebar.header("Maillon faible")
    equipes = sorted(blocks["team"].unique())
    team = st.sidebar.selectbox("Ligne offensive (équipe)", equipes)

    st.sidebar.caption("Situations")
    only_third = st.sidebar.checkbox("3e tentative")
    only_blitz = st.sidebar.checkbox("Blitz (≥ 5 rushers)")
    only_stunt = st.sidebar.checkbox("Stunt")
    only_pa = st.sidebar.checkbox("Play action")
    oline_only = st.sidebar.checkbox("Ligne offensive seule (LT, LG, C, RG, RT)", value=True)
    min_duels = st.sidebar.slider("Minimum de duels", 1, 40, 10)

    sub = blocks[blocks["team"] == team]
    if only_third:
        sub = sub[sub["down"] == 3]
    if only_blitz:
        sub = sub[sub["nb_rushers"] >= 5]
    if only_stunt:
        sub = sub[sub["stunt"]]
    if only_pa:
        sub = sub[sub["pff_playAction"]]
    if oline_only:
        sub = sub[sub["blockerPos"].isin(["LT", "LG", "C", "RG", "RT"])]

    ranking = summarize_blockers(sub, min_duels=min_duels)
    st.subheader(f"Classement des bloqueurs · {team}")
    if ranking.empty:
        st.info("Aucun bloqueur n'atteint le minimum de duels avec ces filtres. Baisse le seuil.")
        return

    st.caption("Du plus faible (taux de duels perdus le plus élevé) au plus solide.")
    st.bar_chart(ranking.set_index("blockerName")["taux_perdu"], height=260)
    st.dataframe(ranking, hide_index=True, use_container_width=True)

    choix = st.selectbox(
        "Bloqueur à inspecter",
        ranking["blockerId"].tolist(),
        format_func=lambda b: (lambda r: f"{r.blockerPos} · {r.blockerName} · "
                                         f"{r.taux_perdu:.0%} perdus ({r.n_perdus}/{r.n_duels})")(
            ranking[ranking["blockerId"] == b].iloc[0]),
    )
    perdus = sub[(sub["blockerId"] == choix) & (sub["perdu"])].sort_values("temps_tenu")
    st.subheader(f"Duels perdus · {ranking[ranking['blockerId'] == choix].iloc[0]['blockerName']}")
    if perdus.empty:
        st.info("Ce bloqueur n'a aucun duel perdu avec ces filtres.")
        return

    labels = {
        int(r.playId): (f"Q{r.quarter} · {down_label(r.down, r.yardsToGo)} · tenu {r.temps_tenu:.1f} s"
                        f" · {PASS_RESULT_LABELS.get(r.passResult, r.passResult)} — {str(r.playDescription)[:60]}")
        for r in perdus.itertuples()
    }
    play_id = st.selectbox("Action perdue", list(labels), format_func=lambda p: labels[p])
    game_id = int(perdus[perdus["playId"] == play_id].iloc[0]["gameId"])
    _replay(game_id, play_id, int(choix))


def onglet_explorer():
    """Choisit librement une action et son bloqueur à suivre (sans blocks.csv)."""
    games = load_games().sort_values(["week", "gameId"])
    plays = load_plays()

    st.sidebar.header("Explorer une action")
    game_id = st.sidebar.selectbox(
        "Match", games["gameId"].tolist(),
        format_func=lambda g: (lambda r: f"S{r.week} · {r.visitorTeamAbbr} @ {r.homeTeamAbbr}")(
            games[games["gameId"] == g].iloc[0]),
    )
    only_sacks = st.sidebar.checkbox("Seulement les sacks")
    gp = plays[plays["gameId"] == game_id].sort_values("playId")
    if only_sacks:
        gp = gp[gp["passResult"] == "S"]
    if gp.empty:
        st.warning("Aucune action avec ce filtre.")
        return
    rows = {int(r.playId): r for r in gp.itertuples()}
    play_id = st.sidebar.selectbox(
        "Action", list(rows),
        format_func=lambda p: f"Q{rows[p].quarter} {rows[p].gameClock} · {down_label(rows[p].down, rows[p].yardsToGo)}",
    )
    duels = play_duels(game_id, play_id)
    options = [None] + duels["blockerId"].tolist()
    labels = {None: "Aucun (rusher le plus proche)"}
    for d in duels.itertuples():
        labels[d.blockerId] = f"{d.blockerPos} {d.blockerName} vs {d.defenderName} · {d.temps_tenu:.1f} s {'✗' if d.perdu else '✓'}"
    lost = [d.blockerId for d in duels.itertuples() if d.perdu]
    focus = st.sidebar.selectbox("Bloqueur suivi", options,
                                 index=options.index(lost[0]) if lost else 0,
                                 format_func=lambda b: labels[b])
    st.subheader(f"{rows[play_id].quarter}e QT · {down_label(rows[play_id].down, rows[play_id].yardsToGo)}")
    st.caption(str(rows[play_id].playDescription))
    _replay(game_id, play_id, focus)


blocks = _load_blocks()
if blocks is not None:
    tab1, tab2 = st.tabs(["Maillon faible", "Explorer une action"])
    with tab1:
        onglet_maillon_faible(blocks)
    with tab2:
        onglet_explorer()
else:
    st.warning("blocks.csv introuvable. Génère-le avec `python -m src.metrics --raw data`. "
               "En attendant, tu peux explorer n'importe quelle action ci-dessous.")
    onglet_explorer()
