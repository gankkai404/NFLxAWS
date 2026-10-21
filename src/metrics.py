"""Weak Link · Partie 1 : calcul des duels de protection de passe.

Pour chaque action de passe, on associe chaque bloqueur de la ligne offensive
au défenseur qu'il bloque (scouting PFF), puis on suit la distance entre ce
défenseur et le QB dans le tracking (10 Hz). Le duel est « perdu » dès que le
défenseur passe sous un seuil de distance du QB entre le snap et la fin de
l'action.

Usage CLI :
    python -m src.metrics --raw data/raw --out data/processed/blocks.csv --seuil 2.0 --max-games 3

API Python :
    from src.metrics import load_blocks, summarize_blockers
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

FPS = 10  # le tracking est à 10 Hz : 1 frame = 0,1 s
SEUIL_PRESSION = 2.0  # yards

# Valeurs d'event observées à l'étape 0 sur les 122 matchs (comparées en minuscules).
SNAP_EVENTS = ("ball_snap", "autoevent_ballsnap")
# « pass_shovel » n'apparaît jamais dans les données : il n'est donc pas retenu.
END_EVENTS = ("pass_forward", "autoevent_passforward", "qb_sack", "qb_strip_sack", "run")

# Facteur utilisé par le bloc de validation pour « nettement plus élevé ».
FACTEUR_ANOMALIE = 1.5

# Valeur de remplacement des chaînes manquantes (le contrat n'autorise des NA que sur frame_perdu).
VALEUR_INCONNUE = "UNKNOWN"

CLES_ACTION = ["gameId", "playId"]
CLES_DUEL = ["gameId", "playId", "blockerId", "defenderId"]

CONTRACT_COLUMNS = [
    # Colonnes obligatoires (contrat d'équipe)
    "gameId", "playId", "blockerId", "blockerName", "blockerPos", "team",
    "defenderId", "defenderName", "temps_tenu", "perdu", "pressure_allowed",
    "sack_allowed", "down", "yardsToGo", "nb_rushers", "stunt", "pff_playAction",
    "offenseFormation", "passResult", "playDescription",
    # Colonnes additionnelles
    "week", "quarter", "defenseTeam", "defenderPos", "blockType",
    "beaten_by_defender", "frame_snap", "frame_fin", "frame_perdu",
    "duree_action", "dist_min", "dropBackType", "pff_passCoverage",
]

COLONNES_INT = [
    "gameId", "playId", "week", "quarter", "down", "yardsToGo", "nb_rushers",
    "blockerId", "defenderId", "frame_snap", "frame_fin",
]
COLONNES_INT_NULLABLE = ["frame_perdu"]
COLONNES_FLOAT = ["temps_tenu", "duree_action", "dist_min"]
COLONNES_BOOL = [
    "perdu", "pressure_allowed", "sack_allowed", "beaten_by_defender", "stunt",
    "pff_playAction",
]
COLONNES_STR = [
    c for c in CONTRACT_COLUMNS
    if c not in COLONNES_INT + COLONNES_INT_NULLABLE + COLONNES_FLOAT + COLONNES_BOOL
]

COLONNES_SUMMARY = [
    "team", "blockerId", "blockerName", "blockerPos", "n_duels", "n_perdus",
    "taux_perdu", "temps_tenu_moyen", "temps_avant_defaite_median",
    "pressions_accordees", "taux_pression", "sacks_accordes",
]

# Colonnes lues dans chaque fichier (on ne lit que l'utile).
USECOLS = {
    "games": ["gameId", "week", "homeTeamAbbr", "visitorTeamAbbr"],
    "plays": [
        "gameId", "playId", "quarter", "down", "yardsToGo", "possessionTeam",
        "defensiveTeam", "passResult", "offenseFormation", "dropBackType",
        "pff_playAction", "pff_passCoverage", "playDescription",
    ],
    "players": ["nflId", "displayName", "officialPosition"],
    "pffScoutingData": [
        "gameId", "playId", "nflId", "pff_role", "pff_positionLinedUp",
        "pff_nflIdBlockedPlayer", "pff_blockType", "pff_hitAllowed",
        "pff_hurryAllowed", "pff_sackAllowed", "pff_beatenByDefender",
        "pff_hit", "pff_hurry", "pff_sack",
    ],
}
TRACKING_USECOLS = ["gameId", "playId", "nflId", "frameId", "x", "y", "event"]
INDICATEURS_PFF = [
    "pff_hitAllowed", "pff_hurryAllowed", "pff_sackAllowed",
    "pff_beatenByDefender", "pff_hit", "pff_hurry", "pff_sack",
]


# ---------------------------------------------------------------------------
# Chargement
# ---------------------------------------------------------------------------

def _normaliser_scouting(scouting: pd.DataFrame) -> pd.DataFrame:
    """Normalise le scouting PFF (casse de pff_role, Int64, indicateurs 0/1).

    Idempotente : peut être appliquée à un scouting déjà normalisé.
    """
    sc = scouting.copy()
    sc["pff_role"] = sc["pff_role"].str.strip().str.lower()
    sc["pff_nflIdBlockedPlayer"] = pd.to_numeric(
        sc["pff_nflIdBlockedPlayer"], errors="coerce"
    ).astype("Int64")
    for col in INDICATEURS_PFF:
        if col in sc.columns:
            sc[col] = pd.to_numeric(sc[col], errors="coerce").fillna(0).astype(int)
    return sc


def load_static(raw_dir: Path) -> dict[str, pd.DataFrame]:
    """Charge games, plays, players et pffScoutingData depuis `raw_dir`.

    Lève FileNotFoundError (avec la liste des fichiers manquants) si un des
    quatre CSV est absent.
    """
    raw_dir = Path(raw_dir)
    manquants = [f"{nom}.csv" for nom in USECOLS if not (raw_dir / f"{nom}.csv").is_file()]
    if manquants:
        raise FileNotFoundError(
            f"Fichiers manquants dans {raw_dir} : {', '.join(manquants)}"
        )
    tables = {
        nom: pd.read_csv(raw_dir / f"{nom}.csv", usecols=cols)
        for nom, cols in USECOLS.items()
    }
    tables["pffScoutingData"] = _normaliser_scouting(tables["pffScoutingData"])
    return tables


def find_tracking_files(raw_dir: Path) -> list[Path]:
    """Retourne la liste triée des fichiers `tracking_*.csv` sous `raw_dir` (récursif)."""
    raw_dir = Path(raw_dir)
    fichiers = sorted(raw_dir.glob("**/tracking_*.csv"))
    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier tracking_*.csv trouvé sous {raw_dir}")
    return fichiers


def read_tracking(path: Path) -> pd.DataFrame:
    """Lit un fichier de tracking (colonnes utiles uniquement, event en minuscules)."""
    tracking = pd.read_csv(path, usecols=TRACKING_USECOLS)
    tracking["event"] = tracking["event"].str.lower()
    return tracking


# ---------------------------------------------------------------------------
# Calcul
# ---------------------------------------------------------------------------

def play_frames(tracking: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par action : gameId, playId, frame_snap, frame_fin.

    - frame_snap : première frame dont l'event est dans SNAP_EVENTS ;
    - frame_fin : première frame > snap dont l'event est dans END_EVENTS,
      à défaut la dernière frame de l'action.
    Les actions sans snap sont exclues.
    """
    event = tracking["event"].str.lower()
    snap = (
        tracking.loc[event.isin(SNAP_EVENTS)]
        .groupby(CLES_ACTION, as_index=False)["frameId"].min()
        .rename(columns={"frameId": "frame_snap"})
    )
    derniere = (
        tracking.groupby(CLES_ACTION, as_index=False)["frameId"].max()
        .rename(columns={"frameId": "frame_derniere"})
    )
    fins = tracking.loc[event.isin(END_EVENTS), CLES_ACTION + ["frameId"]]
    fins = fins.merge(snap, on=CLES_ACTION)
    fins = (
        fins.loc[fins["frameId"] > fins["frame_snap"]]
        .groupby(CLES_ACTION, as_index=False)["frameId"].min()
        .rename(columns={"frameId": "frame_fin"})
    )
    pf = snap.merge(derniere, on=CLES_ACTION).merge(fins, on=CLES_ACTION, how="left")
    pf["frame_fin"] = pf["frame_fin"].fillna(pf["frame_derniere"]).astype("int64")
    pf["frame_snap"] = pf["frame_snap"].astype("int64")
    return pf[CLES_ACTION + ["frame_snap", "frame_fin"]]


def _positions(tracking: pd.DataFrame) -> pd.DataFrame:
    """Positions des joueurs (lignes du ballon exclues, nflId en entier)."""
    pos = tracking.loc[tracking["nflId"].notna(), CLES_ACTION + ["nflId", "frameId", "x", "y"]]
    return pos.astype({"nflId": "int64"})


def _dans_fenetre(df: pd.DataFrame) -> pd.Series:
    """Masque des frames comprises entre frame_snap et frame_fin (incluses)."""
    return (df["frameId"] >= df["frame_snap"]) & (df["frameId"] <= df["frame_fin"])


def _typer_contrat(df: pd.DataFrame) -> pd.DataFrame:
    """Applique l'ordre et les types du contrat de blocks.csv."""
    df = df.reindex(columns=CONTRACT_COLUMNS)
    for col in COLONNES_INT:
        df[col] = df[col].astype("int64")
    df["frame_perdu"] = df["frame_perdu"].astype("Int64")
    for col in COLONNES_FLOAT:
        df[col] = df[col].astype("float64").round(2)
    for col in COLONNES_BOOL:
        df[col] = df[col].astype(bool)
    for col in COLONNES_STR:
        df[col] = df[col].fillna(VALEUR_INCONNUE).astype("str")
    return df.reset_index(drop=True)


def _distances_duels(duels: pd.DataFrame, tracking: pd.DataFrame, seuil: float) -> pd.DataFrame:
    """Calcule dist_min et frame_perdu par duel (fusion défenseur × QB par frame)."""
    pos = _positions(tracking)
    fenetres = duels[CLES_ACTION + ["qbId", "frame_snap", "frame_fin"]].drop_duplicates(CLES_ACTION)

    qb_pos = pos.merge(fenetres, left_on=CLES_ACTION + ["nflId"], right_on=CLES_ACTION + ["qbId"])
    qb_pos = qb_pos.loc[_dans_fenetre(qb_pos), CLES_ACTION + ["frameId", "x", "y"]]
    qb_pos = qb_pos.rename(columns={"x": "qb_x", "y": "qb_y"})

    def_pos = duels[CLES_DUEL + ["frame_snap", "frame_fin"]].merge(
        pos.rename(columns={"nflId": "defenderId"}), on=CLES_ACTION + ["defenderId"]
    )
    def_pos = def_pos.loc[_dans_fenetre(def_pos)]
    def_pos = def_pos.merge(qb_pos, on=CLES_ACTION + ["frameId"])
    def_pos["dist"] = np.hypot(def_pos["x"] - def_pos["qb_x"], def_pos["y"] - def_pos["qb_y"])

    dist_min = def_pos.groupby(CLES_DUEL, as_index=False)["dist"].min().rename(columns={"dist": "dist_min"})
    frame_perdu = (
        def_pos.loc[def_pos["dist"] < seuil]
        .groupby(CLES_DUEL, as_index=False)["frameId"].min()
        .rename(columns={"frameId": "frame_perdu"})
    )
    return dist_min.merge(frame_perdu, on=CLES_DUEL, how="left")


def _contexte_actions(scouting: pd.DataFrame) -> pd.DataFrame:
    """nb_rushers et stunt par action, à partir du scouting."""
    actions = scouting[CLES_ACTION].drop_duplicates()
    rushers = (
        scouting.loc[scouting["pff_role"] == "pass rush"]
        .groupby(CLES_ACTION).size().rename("nb_rushers").reset_index()
    )
    stunts = scouting.loc[scouting["pff_blockType"] == "SW", CLES_ACTION].drop_duplicates()
    stunts["stunt"] = True
    ctx = actions.merge(rushers, on=CLES_ACTION, how="left").merge(stunts, on=CLES_ACTION, how="left")
    ctx["nb_rushers"] = ctx["nb_rushers"].fillna(0).astype("int64")
    ctx["stunt"] = ctx["stunt"].fillna(False).astype(bool)
    return ctx


def _enrichir(res: pd.DataFrame, scouting: pd.DataFrame, plays: pd.DataFrame,
              players: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """Ajoute noms, positions, contexte de l'action et semaine."""
    noms = players[["nflId", "displayName"]]
    res = res.merge(noms.rename(columns={"nflId": "blockerId", "displayName": "blockerName"}),
                    on="blockerId", how="left")
    res = res.merge(noms.rename(columns={"nflId": "defenderId", "displayName": "defenderName"}),
                    on="defenderId", how="left")
    pos_def = scouting[CLES_ACTION + ["nflId", "pff_positionLinedUp"]].drop_duplicates(CLES_ACTION + ["nflId"])
    res = res.merge(pos_def.rename(columns={"nflId": "defenderId", "pff_positionLinedUp": "defenderPos"}),
                    on=CLES_ACTION + ["defenderId"], how="left")
    res = res.merge(_contexte_actions(scouting), on=CLES_ACTION, how="left")
    contexte = plays.rename(columns={"possessionTeam": "team", "defensiveTeam": "defenseTeam"})
    contexte = contexte.drop(columns=[c for c in ("homeTeamAbbr", "visitorTeamAbbr") if c in contexte])
    res = res.merge(contexte, on=CLES_ACTION, how="left")
    res = res.merge(games[["gameId", "week"]], on="gameId", how="left")
    res["pff_playAction"] = res["pff_playAction"].fillna(0).astype(int) == 1
    return res


def compute_duels_for_game(tracking: pd.DataFrame, plays: pd.DataFrame, scouting: pd.DataFrame,
                           players: pd.DataFrame, games: pd.DataFrame,
                           seuil: float = SEUIL_PRESSION) -> pd.DataFrame:
    """Calcule la table des duels (contrat blocks.csv) pour le tracking d'un match.

    Calcul entièrement vectorisé (merges + groupby). Les compteurs d'éléments
    ignorés sont exposés dans `resultat.attrs["stats"]` :
    actions, actions_sans_snap, actions_sans_qb, duels_ignores.
    """
    tracking = tracking.copy()
    tracking["event"] = tracking["event"].str.lower()
    matchs = tracking["gameId"].unique()
    sc = _normaliser_scouting(scouting.loc[scouting["gameId"].isin(matchs)])

    actions = sc[CLES_ACTION].drop_duplicates()
    pf = play_frames(tracking)
    qb = (
        sc.loc[sc["pff_role"] == "pass", CLES_ACTION + ["nflId"]]
        .drop_duplicates(CLES_ACTION, keep="first")
        .rename(columns={"nflId": "qbId"})
    )
    valides = pf.merge(qb, on=CLES_ACTION)

    duels = sc.loc[(sc["pff_role"] == "pass block") & sc["pff_nflIdBlockedPlayer"].notna()]
    duels = duels.rename(columns={
        "nflId": "blockerId", "pff_nflIdBlockedPlayer": "defenderId",
        "pff_positionLinedUp": "blockerPos", "pff_blockType": "blockType",
    })
    duels = duels.astype({"defenderId": "int64", "blockerId": "int64"})
    duels = duels.merge(valides, on=CLES_ACTION)

    res = duels.merge(_distances_duels(duels, tracking, seuil), on=CLES_DUEL)

    res["perdu"] = res["frame_perdu"].notna()
    fin_tenue = res["frame_perdu"].where(res["perdu"], res["frame_fin"])
    res["temps_tenu"] = (fin_tenue - res["frame_snap"]) / FPS
    res["duree_action"] = (res["frame_fin"] - res["frame_snap"]) / FPS
    res["pressure_allowed"] = (res[["pff_hitAllowed", "pff_hurryAllowed", "pff_sackAllowed"]] == 1).any(axis=1)
    res["sack_allowed"] = res["pff_sackAllowed"] == 1
    res["beaten_by_defender"] = res["pff_beatenByDefender"] == 1

    res = _typer_contrat(_enrichir(res, sc, plays, players, games))
    res.attrs["stats"] = {
        "actions": len(actions),
        "actions_sans_snap": len(actions.merge(pf, on=CLES_ACTION, how="left", indicator=True)
                                 .query("_merge == 'left_only'")),
        "actions_sans_qb": len(pf.merge(actions, on=CLES_ACTION)) - len(valides.merge(actions, on=CLES_ACTION)),
        "duels_ignores": len(duels) - len(res),
    }
    return res


def build_blocks(raw_dir: Path, seuil: float = SEUIL_PRESSION,
                 max_games: int | None = None) -> pd.DataFrame:
    """Construit la table des duels pour tous les matchs (ou les `max_games` premiers).

    Affiche une ligne de progression par match. Les compteurs cumulés sont
    exposés dans `resultat.attrs["stats"]`.
    """
    fichiers = find_tracking_files(raw_dir)
    static = load_static(raw_dir)
    if max_games is not None:
        fichiers = fichiers[:max_games]

    morceaux: list[pd.DataFrame] = []
    totaux = {"actions": 0, "actions_sans_snap": 0, "actions_sans_qb": 0, "duels_ignores": 0}
    for i, fichier in enumerate(fichiers, start=1):
        duels = compute_duels_for_game(
            read_tracking(fichier), static["plays"], static["pffScoutingData"],
            static["players"], static["games"], seuil=seuil,
        )
        stats = duels.attrs["stats"]
        for cle in totaux:
            totaux[cle] += stats[cle]
        ignorees = stats["actions_sans_snap"] + stats["actions_sans_qb"]
        game_id = fichier.stem.removeprefix("tracking_")
        print(f"[{i}/{len(fichiers)}] game {game_id} : {len(duels)} duels ({ignorees} actions ignorées)",
              flush=True)
        morceaux.append(duels)

    blocks = _typer_contrat(pd.concat(morceaux, ignore_index=True)) if morceaux else _typer_contrat(pd.DataFrame())
    blocks.attrs["stats"] = totaux
    return blocks


def load_blocks(path: str | Path = "data/processed/blocks.csv") -> pd.DataFrame:
    """Relit blocks.csv avec les types du contrat (booléens, Int64 pour frame_perdu…)."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    dtypes = {c: "int64" for c in COLONNES_INT}
    dtypes.update({c: "Int64" for c in COLONNES_INT_NULLABLE})
    dtypes.update({c: "float64" for c in COLONNES_FLOAT})
    dtypes.update({c: "bool" for c in COLONNES_BOOL})
    dtypes.update({c: "str" for c in COLONNES_STR})
    blocks = pd.read_csv(path, dtype=dtypes, keep_default_na=False, na_values={"frame_perdu": [""]})
    return blocks[CONTRACT_COLUMNS]


def summarize_blockers(blocks: pd.DataFrame, min_duels: int = 20) -> pd.DataFrame:
    """Classement des bloqueurs, du plus faible au plus solide.

    Groupé par team, blockerId, blockerName ; filtré sur n_duels >= min_duels ;
    trié par taux_perdu puis taux_pression décroissants. Fonctionne sur un
    `blocks` déjà filtré (situation de jeu, équipe…).
    """
    cles = ["team", "blockerId", "blockerName"]
    if blocks.empty:
        return pd.DataFrame(columns=COLONNES_SUMMARY)

    groupes = blocks.groupby(cles, as_index=False, observed=True)
    resume = groupes.agg(
        n_duels=("perdu", "size"),
        n_perdus=("perdu", "sum"),
        temps_tenu_moyen=("temps_tenu", "mean"),
        pressions_accordees=("pressure_allowed", "sum"),
        sacks_accordes=("sack_allowed", "sum"),
    )
    # Mode de blockerPos (égalité départagée par ordre alphabétique).
    modes = (
        blocks.groupby(cles + ["blockerPos"], observed=True).size().rename("n").reset_index()
        .sort_values(["n", "blockerPos"], ascending=[False, True])
        .drop_duplicates(cles)[cles + ["blockerPos"]]
    )
    medianes = (
        blocks.loc[blocks["perdu"]].groupby(cles, as_index=False, observed=True)["temps_tenu"].median()
        .rename(columns={"temps_tenu": "temps_avant_defaite_median"})
    )
    resume = resume.merge(modes, on=cles, how="left").merge(medianes, on=cles, how="left")
    resume["taux_perdu"] = resume["n_perdus"] / resume["n_duels"]
    resume["taux_pression"] = resume["pressions_accordees"] / resume["n_duels"]

    resume = resume.loc[resume["n_duels"] >= min_duels]
    resume = resume.sort_values(["taux_perdu", "taux_pression"], ascending=[False, False], kind="stable")
    return resume[COLONNES_SUMMARY].reset_index(drop=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _float_positif(valeur: str) -> float:
    """Type argparse : nombre décimal strictement positif."""
    try:
        nombre = float(valeur)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"--seuil doit être un nombre : {valeur!r}") from exc
    if not nombre > 0:
        raise argparse.ArgumentTypeError(f"--seuil doit être strictement positif : {valeur!r}")
    return nombre


def _entier_positif(valeur: str) -> int:
    """Type argparse : entier >= 1."""
    try:
        nombre = int(valeur)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"--max-games doit être un entier : {valeur!r}") from exc
    if nombre < 1:
        raise argparse.ArgumentTypeError(f"--max-games doit être >= 1 : {valeur!r}")
    return nombre


def _bloc_validation(blocks: pd.DataFrame, duree: float) -> None:
    """Affiche les contrôles de cohérence de fin d'exécution."""
    print("\n" + "=" * 70 + "\nBLOC DE VALIDATION\n" + "=" * 70)
    stats = blocks.attrs.get("stats", {})
    n_duels = len(blocks)
    print(f"Actions avec au moins un duel : {blocks[CLES_ACTION].drop_duplicates().shape[0]}")
    if stats:
        print(f"Actions ignorées : {stats['actions_sans_snap']} sans snap, {stats['actions_sans_qb']} sans QB"
              f" | duels ignorés (défenseur/QB absent du tracking) : {stats['duels_ignores']}")
    print(f"Duels : {n_duels}")
    if n_duels:
        print(f"Duels perdus : {100 * blocks['perdu'].mean():.1f} %")
        print(f"Temps tenu médian : {blocks['temps_tenu'].median():.2f} s")
    else:
        print("Duels perdus : n/d\nTemps tenu médian : n/d")
    print(f"Temps d'exécution : {duree:.0f} s")

    print("\nTableau croisé perdu × pressure_allowed :")
    croise = pd.crosstab(blocks["perdu"], blocks["pressure_allowed"]).reindex(
        index=[False, True], columns=[False, True], fill_value=0)
    print(croise.to_string())
    avec = blocks.loc[blocks["pressure_allowed"], "perdu"]
    sans = blocks.loc[~blocks["pressure_allowed"], "perdu"]
    if avec.empty or sans.empty:
        print("⚠ ANOMALIE PROBABLE : comparaison impossible (un des deux groupes est vide).")
    else:
        print(f"Taux perdu avec pression PFF : {avec.mean():.1%} | sans : {sans.mean():.1%}")
        if not avec.mean() > FACTEUR_ANOMALIE * sans.mean():
            print(f"⚠ ANOMALIE PROBABLE : le taux avec pression n'est pas > {FACTEUR_ANOMALIE} × le taux sans.")

    print("\nTop 10 summarize_blockers(min_duels=20) :")
    top = summarize_blockers(blocks, min_duels=20).head(10)
    print(top.to_string(index=False) if not top.empty else "Aucun bloqueur n'atteint 20 duels.")

    print("\nValeurs manquantes par colonne du contrat :")
    manquants = blocks[CONTRACT_COLUMNS].isna().sum()
    print(manquants.to_string())
    for col, n in manquants.items():
        if col != "frame_perdu" and n > 0:
            print(f"⚠ La colonne {col} contient {n} valeurs manquantes.")


def main(argv: list[str] | None = None) -> None:
    """Point d'entrée CLI : calcule blocks.csv et affiche le bloc de validation."""
    parser = argparse.ArgumentParser(description="Weak Link : calcul des duels de protection de passe.")
    parser.add_argument("--raw", type=Path, default=Path("data/raw"), help="dossier des données brutes")
    parser.add_argument("--out", type=Path, default=Path("data/processed/blocks.csv"), help="fichier de sortie")
    parser.add_argument("--seuil", type=_float_positif, default=SEUIL_PRESSION, help="seuil de pression (yards)")
    parser.add_argument("--max-games", type=_entier_positif, default=None, help="nombre max de matchs")
    args = parser.parse_args(argv)

    debut = time.perf_counter()
    try:
        blocks = build_blocks(args.raw, seuil=args.seuil, max_games=args.max_games)
    except FileNotFoundError as exc:
        print(f"Erreur : {exc}\nIndique le dossier des données avec --raw (exemple : --raw data).",
              file=sys.stderr)
        sys.exit(1)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    blocks.to_csv(args.out, index=False)
    print(f"\nÉcrit : {args.out} ({len(blocks)} duels, {args.out.stat().st_size / 1e6:.1f} Mo)")
    _bloc_validation(blocks, time.perf_counter() - debut)


if __name__ == "__main__":
    main()
