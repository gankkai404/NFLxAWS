"""
Weak Link · Partie 3 : application Streamlit (squelette de départ).

Cette base branche déjà la Partie 1 (métrique) et la Partie 2 (replay).
À l'équipe App de l'enrichir (mise en page, pitch, actions « waouh »).

    streamlit run app.py

Prérequis : data/processed/blocks.csv  (python -m src.metrics --raw data)

Une démo plus complète du replay existe déjà : streamlit run src/replay/demo_app.py
"""
import streamlit as st

from src.metrics import load_blocks, summarize_blockers
from src.replay import make_replay
from src.replay.data import PASS_RESULT_LABELS, down_label

st.set_page_config(page_title="Weak Link", page_icon="🏈", layout="wide")
st.title("🏈 Weak Link — le maillon faible de la protection adverse")


@st.cache_data(show_spinner="Chargement des duels…")
def get_blocks():
    return load_blocks()


try:
    blocks = get_blocks()
except FileNotFoundError:
    st.error("data/processed/blocks.csv introuvable. Génère-le : `python -m src.metrics --raw data`")
    st.stop()

# --- Sidebar : équipe adverse + filtres de situation ---
st.sidebar.header("Filtres")
team = st.sidebar.selectbox("Ligne offensive à analyser", sorted(blocks["team"].unique()))
third = st.sidebar.checkbox("3e tentative")
blitz = st.sidebar.checkbox("Blitz (≥ 5 rushers)")
stunt = st.sidebar.checkbox("Stunt")
play_action = st.sidebar.checkbox("Play action")
min_duels = st.sidebar.slider("Minimum de duels", 1, 40, 10)

sub = blocks[blocks["team"] == team]
if third:
    sub = sub[sub["down"] == 3]
if blitz:
    sub = sub[sub["nb_rushers"] >= 5]
if stunt:
    sub = sub[sub["stunt"]]
if play_action:
    sub = sub[sub["pff_playAction"]]
sub = sub[sub["blockerPos"].isin(["LT", "LG", "C", "RG", "RT"])]

# --- Classement des bloqueurs (le plus faible en haut) ---
ranking = summarize_blockers(sub, min_duels=min_duels)
st.subheader(f"Classement de la ligne de {team}")
if ranking.empty:
    st.info("Aucun bloqueur n'atteint le minimum de duels. Baisse le seuil ou enlève un filtre.")
    st.stop()
st.bar_chart(ranking.set_index("blockerName")["taux_perdu"], height=260)
st.dataframe(ranking, hide_index=True, use_container_width=True)

# --- Détail d'un bloqueur + replay d'un duel perdu ---
blocker = st.selectbox(
    "Inspecter un bloqueur",
    ranking["blockerId"].tolist(),
    format_func=lambda b: (lambda r: f"{r.blockerPos} · {r.blockerName} · {r.taux_perdu:.0%} perdus")(
        ranking[ranking["blockerId"] == b].iloc[0]),
)
perdus = sub[(sub["blockerId"] == blocker) & (sub["perdu"])].sort_values("temps_tenu")
if perdus.empty:
    st.info("Pas de duel perdu pour ce bloqueur avec ces filtres.")
    st.stop()

labels = {
    int(r.playId): f"Q{r.quarter} · {down_label(r.down, r.yardsToGo)} · tenu {r.temps_tenu:.1f} s · "
                   f"{PASS_RESULT_LABELS.get(r.passResult, r.passResult)}"
    for r in perdus.itertuples()
}
play_id = st.selectbox("Duel perdu à revoir", list(labels), format_func=lambda p: labels[p])
game_id = int(perdus[perdus["playId"] == play_id].iloc[0]["gameId"])
st.caption(str(perdus[perdus["playId"] == play_id].iloc[0]["playDescription"]))
st.plotly_chart(make_replay(game_id, play_id, int(blocker)), use_container_width=True)
