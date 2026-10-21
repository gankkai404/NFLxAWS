"""Tests unitaires de src/metrics.py sur données synthétiques minuscules."""

import numpy as np
import pandas as pd
import pytest

from src.metrics import (
    CONTRACT_COLUMNS,
    compute_duels_for_game,
    load_blocks,
    play_frames,
    summarize_blockers,
)

GAME, PLAY = 2021090900, 1
QB, BLOQUEUR, DEFENSEUR = 100, 200, 300
QB_X, QB_Y = 50.0, 26.0


def _tracking(distances: dict[int, float], events: dict[int, str]) -> pd.DataFrame:
    """Tracking d'une action : QB immobile en (50, 26), défenseur à `distances[frame]` yards."""
    lignes = []
    for frame, dist in distances.items():
        event = events.get(frame)
        lignes.append((GAME, PLAY, QB, frame, QB_X, QB_Y, event))
        lignes.append((GAME, PLAY, DEFENSEUR, frame, QB_X + dist, QB_Y, event))
        lignes.append((GAME, PLAY, BLOQUEUR, frame, QB_X + dist / 2, QB_Y, event))
        lignes.append((GAME, PLAY, np.nan, frame, QB_X, QB_Y, event))  # ballon
    return pd.DataFrame(lignes, columns=["gameId", "playId", "nflId", "frameId", "x", "y", "event"])


def _statiques(role_bloqueur: str = "Pass Block"):
    """plays, scouting, players et games pour l'action synthétique."""
    plays = pd.DataFrame([{
        "gameId": GAME, "playId": PLAY, "quarter": 1, "down": 3, "yardsToGo": 7,
        "possessionTeam": "KC", "defensiveTeam": "LV", "passResult": "C",
        "offenseFormation": "SHOTGUN", "dropBackType": "TRADITIONAL",
        "pff_playAction": 0, "pff_passCoverage": "Cover-3", "playDescription": "test",
    }])
    vide = {c: np.nan for c in ["pff_hitAllowed", "pff_hurryAllowed", "pff_sackAllowed",
                                "pff_beatenByDefender", "pff_hit", "pff_hurry", "pff_sack"]}
    base = {"gameId": GAME, "playId": PLAY, "pff_nflIdBlockedPlayer": np.nan, "pff_blockType": np.nan}
    scouting = pd.DataFrame([
        {**base, **vide, "nflId": QB, "pff_role": "Pass", "pff_positionLinedUp": "QB"},
        {**base, **vide, "nflId": BLOQUEUR, "pff_role": role_bloqueur, "pff_positionLinedUp": "LT",
         "pff_nflIdBlockedPlayer": float(DEFENSEUR), "pff_blockType": "PP",
         "pff_hitAllowed": 0.0, "pff_hurryAllowed": 1.0, "pff_sackAllowed": 0.0,
         "pff_beatenByDefender": 0.0},
        {**base, **vide, "nflId": DEFENSEUR, "pff_role": "Pass Rush", "pff_positionLinedUp": "REO"},
    ])
    players = pd.DataFrame({"nflId": [QB, BLOQUEUR, DEFENSEUR],
                            "displayName": ["Le QB", "Le Bloqueur", "Le Défenseur"],
                            "officialPosition": ["QB", "T", "DE"]})
    games = pd.DataFrame([{"gameId": GAME, "week": 1, "homeTeamAbbr": "KC", "visitorTeamAbbr": "LV"}])
    return plays, scouting, players, games


def _calcul(tracking: pd.DataFrame, role_bloqueur: str = "Pass Block") -> pd.DataFrame:
    plays, scouting, players, games = _statiques(role_bloqueur)
    return compute_duels_for_game(tracking, plays, scouting, players, games)


def test_duel_perdu_a_la_frame_15():
    # Défenseur à 5 yards jusqu'à la frame 14, puis sous 2 yards à partir de la frame 15.
    distances = {f: (5.0 if f < 15 else 1.5) for f in range(5, 31)}
    duels = _calcul(_tracking(distances, {10: "ball_snap", 30: "pass_forward"}))
    assert len(duels) == 1
    duel = duels.iloc[0]
    assert bool(duel["perdu"])
    assert duel["frame_perdu"] == 15
    assert duel["temps_tenu"] == pytest.approx(0.5)
    assert list(duels.columns) == CONTRACT_COLUMNS


def test_duel_tenu_jusqu_a_la_fin():
    distances = {f: 5.0 for f in range(5, 36)}
    duels = _calcul(_tracking(distances, {10: "ball_snap", 30: "pass_forward"}))
    assert len(duels) == 1
    duel = duels.iloc[0]
    assert not duel["perdu"]
    assert pd.isna(duel["frame_perdu"])
    assert duel["temps_tenu"] == pytest.approx(2.0)
    assert duel["duree_action"] == pytest.approx(2.0)
    assert duel["dist_min"] == pytest.approx(5.0)


def test_action_sans_snap_ignoree():
    distances = {f: 1.0 for f in range(1, 31)}
    duels = _calcul(_tracking(distances, {30: "pass_forward"}))
    assert len(duels) == 0
    assert duels.attrs["stats"]["actions_sans_snap"] == 1


def test_fin_par_defaut_derniere_frame():
    distances = {f: 5.0 for f in range(1, 43)}
    tracking = _tracking(distances, {10: "ball_snap"})
    frames = play_frames(tracking)
    assert len(frames) == 1
    assert frames.iloc[0]["frame_snap"] == 10
    assert frames.iloc[0]["frame_fin"] == 42


def test_casse_pff_role_detectee():
    distances = {f: 5.0 for f in range(5, 31)}
    duels = _calcul(_tracking(distances, {10: "ball_snap", 30: "pass_forward"}), role_bloqueur="  PASS BLOCK ")
    assert len(duels) == 1
    assert duels.iloc[0]["blockerId"] == BLOQUEUR
    assert duels.iloc[0]["defenderId"] == DEFENSEUR
    assert bool(duels.iloc[0]["pressure_allowed"])  # hurry PFF crédité


def _blocks_synthetiques() -> pd.DataFrame:
    """Trois bloqueurs : A (10 duels, 50 % perdus), B (10 duels, 50 % perdus, plus de pressions), C (3 duels)."""
    def bloqueur(bid, n, n_perdus, n_pressions):
        return pd.DataFrame({
            "team": "KC", "blockerId": bid, "blockerName": f"J{bid}", "blockerPos": "LT",
            "perdu": [i < n_perdus for i in range(n)],
            "pressure_allowed": [i < n_pressions for i in range(n)],
            "sack_allowed": False, "temps_tenu": 2.0,
        })
    return pd.concat([bloqueur(1, 10, 5, 1), bloqueur(2, 10, 5, 4), bloqueur(3, 3, 3, 3)], ignore_index=True)


def test_summarize_blockers_filtre_et_tri():
    resume = summarize_blockers(_blocks_synthetiques(), min_duels=5)
    assert list(resume["blockerId"]) == [2, 1]  # C exclu (3 duels), B devant A (taux_pression)
    assert resume.iloc[0]["taux_perdu"] == pytest.approx(0.5)
    assert resume.iloc[0]["taux_pression"] == pytest.approx(0.4)
    # Sur un sous-ensemble déjà filtré, le seuil min_duels s'applique au sous-ensemble.
    assert summarize_blockers(_blocks_synthetiques().query("blockerId == 3"), min_duels=3)["n_duels"].tolist() == [3]


def test_aller_retour_csv(tmp_path):
    distances = {f: (5.0 if f < 15 else 1.5) for f in range(5, 31)}
    duels = _calcul(_tracking(distances, {10: "ball_snap", 30: "pass_forward"}))
    chemin = tmp_path / "blocks.csv"
    duels.to_csv(chemin, index=False)
    relu = load_blocks(chemin)
    pd.testing.assert_frame_equal(relu, duels, check_dtype=True)
