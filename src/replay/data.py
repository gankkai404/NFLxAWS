"""
Chargement des CSV et préparation d'une action pour le replay 2D.

Tout est calculé ici une seule fois par action, puis partagé :
- coordonnées normalisées (l'attaque va toujours vers la droite) ;
- frames du snap et de la fin d'action (passe, sack, scramble) ;
- duels bloqueur -> défenseur (pff_nflIdBlockedPlayer) avec la distance
  défenseur <-> QB à chaque frame et le « temps tenu ».

Le temps tenu suit la définition de l'équipe :
    (première frame après le snap où défenseur-QB < seuil - frame du snap) / 10,
    plafonné à la frame de fin si le seuil n'est jamais atteint (duel non perdu).
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .teams import team_style

FIELD_LENGTH = 120.0
FIELD_WIDTH = 53.3
FPS = 10
PRESSURE_THRESHOLD = 2.0  # yards

SNAP_EVENTS = ("ball_snap", "autoevent_ballsnap")
END_EVENTS = ("pass_forward", "autoevent_passforward", "qb_sack", "qb_strip_sack", "run")

EVENT_LABELS = {
    "ball_snap": "Snap",
    "autoevent_ballsnap": "Snap",
    "pass_forward": "Passe",
    "autoevent_passforward": "Passe",
    "qb_sack": "Sack",
    "qb_strip_sack": "Strip-sack",
    "run": "Scramble",
    "play_action": "Play action",
    "line_set": "Ligne en place",
    "man_in_motion": "Motion",
    "shift": "Shift",
    "pass_tipped": "Passe déviée",
    "pass_arrived": "Ballon arrivé",
    "autoevent_passinterrupted": "Passe interrompue",
    "pass_outcome_incomplete": "Incomplète",
    "pass_outcome_caught": "Attrapée",
    "fumble": "Fumble",
    "fumble_offense_recovered": "Fumble récupéré",
    "first_contact": "Contact",
}

PASS_RESULT_LABELS = {
    "C": "Passe complète",
    "I": "Passe incomplète",
    "S": "Sack",
    "IN": "Interception",
    "R": "Scramble",
}

REPO_ROOT = Path(__file__).resolve().parents[2]

_TRACKING_COLS = [
    "gameId", "playId", "nflId", "frameId", "jerseyNumber", "team",
    "playDirection", "x", "y", "s", "o", "event",
]


# --------------------------------------------------------------------------- #
# Chargement des fichiers                                                      #
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def data_dir() -> Path:
    """Dossier des CSV : $WEAKLINK_DATA_DIR, sinon data/raw/, sinon data/."""
    candidates = []
    if os.environ.get("WEAKLINK_DATA_DIR"):
        candidates.append(Path(os.environ["WEAKLINK_DATA_DIR"]))
    candidates += [REPO_ROOT / "data" / "raw", REPO_ROOT / "data"]
    for folder in candidates:
        if (folder / "plays.csv").exists():
            return folder
    raise FileNotFoundError(
        "plays.csv introuvable. Dossiers testés : " + ", ".join(str(c) for c in candidates)
    )


def _read_csv(path: Path, fast: bool = False, **kwargs) -> pd.DataFrame:
    """
    Lecture CSV. fast=True utilise pyarrow (gros fichiers, colonnes numériques) ;
    le moteur classique garde les horloges ('13:33') et dates en texte.
    """
    if fast:
        try:
            return pd.read_csv(path, engine="pyarrow", **kwargs)
        except (ImportError, ValueError):
            pass
    return pd.read_csv(path, **kwargs)


@lru_cache(maxsize=1)
def load_games() -> pd.DataFrame:
    return _read_csv(data_dir() / "games.csv", dtype={"gameDate": str, "gameTimeEastern": str})


@lru_cache(maxsize=1)
def load_plays() -> pd.DataFrame:
    return _read_csv(data_dir() / "plays.csv", dtype={"gameClock": str})


@lru_cache(maxsize=1)
def load_players() -> pd.DataFrame:
    return _read_csv(data_dir() / "players.csv")


@lru_cache(maxsize=1)
def load_pff() -> pd.DataFrame:
    return _read_csv(data_dir() / "pffScoutingData.csv", fast=True)


def _tracking_files(game_id: int) -> list[Path]:
    """Fichier tracking d'un match : tracking_<gameId>.csv ou, à défaut, le fichier de la semaine."""
    base = data_dir()
    folders = [base / "tracking", base, base.parent / "tracking"]
    for folder in folders:
        candidate = folder / f"tracking_{game_id}.csv"
        if candidate.exists():
            return [candidate]
    # Format Kaggle d'origine : week1.csv ... week8.csv (plusieurs matchs par fichier)
    games = load_games()
    week = games.loc[games["gameId"] == game_id, "week"]
    if not week.empty:
        w = int(week.iloc[0])
        for folder in folders:
            for name in (f"week{w}.csv", f"tracking_week_{w}.csv"):
                if (folder / name).exists():
                    return [folder / name]
    raise FileNotFoundError(f"Aucun fichier de tracking trouvé pour le match {game_id}")


@lru_cache(maxsize=12)
def load_tracking(game_id: int) -> pd.DataFrame:
    """Tracking d'un match (mis en cache : les 12 derniers matchs restent en mémoire)."""
    frames = []
    for path in _tracking_files(int(game_id)):
        df = _read_csv(path, fast=True, usecols=_TRACKING_COLS)
        frames.append(df[df["gameId"] == int(game_id)])
    df = pd.concat(frames, ignore_index=True)
    for col in ("x", "y", "s", "o", "nflId", "jerseyNumber"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    event = df["event"].astype("string")
    df["event"] = event.where(~event.isin(["None", "none", "", "nan", "NA"]))
    return df


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #
def _clean(value, default=None):
    """Convertit NaN/NA pandas en valeur JSON propre."""
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _rounded(values, digits: int = 2) -> list:
    arr = np.round(np.asarray(values, dtype=float), digits)
    return [None if np.isnan(v) else float(v) for v in arr]


def short_name(name: str) -> str:
    """'Tom Brady' -> 'T. Brady'."""
    parts = str(name).split()
    if len(parts) < 2:
        return str(name)
    return f"{parts[0][0]}. {' '.join(parts[1:])}"


def down_label(down, yards_to_go) -> str:
    down = _clean(down)
    ytg = _clean(yards_to_go)
    if not down:
        return ""
    suffix = "re" if int(down) == 1 else "e"
    return f"{int(down)}{suffix} & {int(ytg) if ytg is not None else '?'}"


def _first_event_index(events: list[tuple[int, str]], names, start: int = 0) -> Optional[int]:
    hits = [i for i, name in events if name in names and i >= start]
    return min(hits) if hits else None


def _first_below(dist: np.ndarray, threshold: float, lo: int, hi: int) -> Optional[int]:
    """Première frame (index) dans [lo, hi] où la distance passe sous le seuil."""
    window = dist[lo:hi + 1]
    hits = np.flatnonzero(window < threshold)  # les NaN comptent comme False
    return int(lo + hits[0]) if hits.size else None


# --------------------------------------------------------------------------- #
# Préparation d'une action                                                     #
# --------------------------------------------------------------------------- #
def _play_row(game_id: int, play_id: int) -> pd.Series:
    plays = load_plays()
    row = plays[(plays["gameId"] == game_id) & (plays["playId"] == play_id)]
    if row.empty:
        raise ValueError(f"Action introuvable dans plays.csv : game {game_id}, play {play_id}")
    return row.iloc[0]


@lru_cache(maxsize=64)
def _base_payload(game_id: int, play_id: int, threshold: float) -> dict:
    play = _play_row(game_id, play_id)
    games = load_games()
    game_rows = games[games["gameId"] == game_id]
    game = game_rows.iloc[0] if not game_rows.empty else None

    trk = load_tracking(game_id)
    trk = trk[trk["playId"] == play_id]
    if trk.empty:
        raise ValueError(f"Aucune donnée de tracking pour game {game_id}, play {play_id}")

    direction = str(trk["playDirection"].dropna().iloc[0]) if trk["playDirection"].notna().any() else "right"
    flipped = direction == "left"

    frames = np.sort(trk["frameId"].unique())
    n = len(frames)
    frame_pos = {int(f): i for i, f in enumerate(frames)}

    # Événements (première occurrence de chaque nom)
    ev = trk.loc[trk["event"].notna(), ["frameId", "event"]].drop_duplicates()
    events: list[tuple[int, str]] = sorted(
        {(frame_pos[int(f)], str(e)) for f, e in zip(ev["frameId"], ev["event"])}
    )
    snap_i = _first_event_index(events, SNAP_EVENTS)
    if snap_i is None:
        snap_i = 0
    end_i = _first_event_index(events, END_EVENTS, start=snap_i)
    end_event = next((name for i, name in events if i == end_i and name in END_EVENTS), None)
    if end_i is None:
        end_i = n - 1

    # Positions des joueurs : une colonne par nflId, une ligne par frame
    ppl = trk[trk["nflId"].notna()].copy()
    ppl["nflId"] = ppl["nflId"].astype("int64")

    def pivot(col: str) -> pd.DataFrame:
        table = ppl.pivot_table(index="frameId", columns="nflId", values=col, aggfunc="first")
        return table.reindex(frames).ffill().bfill()

    px, py, po, ps = pivot("x"), pivot("y"), pivot("o"), pivot("s")
    if flipped:
        px = FIELD_LENGTH - px
        py = FIELD_WIDTH - py
        po = (po + 180.0) % 360.0

    ball = trk[trk["team"] == "football"].set_index("frameId").sort_index()
    ball = ball[~ball.index.duplicated()].reindex(frames)
    bx = ball["x"].ffill().bfill().to_numpy(dtype=float)
    by = ball["y"].ffill().bfill().to_numpy(dtype=float)
    if flipped:
        bx, by = FIELD_LENGTH - bx, FIELD_WIDTH - by

    offense = str(play.get("possessionTeam"))
    defense = str(play.get("defensiveTeam"))
    home = str(game["homeTeamAbbr"]) if game is not None else offense
    away = str(game["visitorTeamAbbr"]) if game is not None else defense

    pff = load_pff()
    pff_play = pff[(pff["gameId"] == game_id) & (pff["playId"] == play_id)].set_index("nflId")
    pff_play = pff_play[~pff_play.index.duplicated()]
    players_df = load_players().set_index("nflId")
    players_df = players_df[~players_df.index.duplicated()]

    meta_rows = (
        ppl.sort_values("frameId").groupby("nflId", sort=False)[["team", "jerseyNumber"]].first()
    )

    # Ordre stable : attaque puis défense, chaque camp trié de haut en bas au snap
    snap_y = py.iloc[snap_i]
    ids = list(px.columns)
    ids.sort(key=lambda pid: (meta_rows.loc[pid, "team"] != offense, -float(snap_y.get(pid, 0.0))))

    players, index_of = [], {}
    for pid in ids:
        info = players_df.loc[pid] if pid in players_df.index else None
        scout = pff_play.loc[pid] if pid in pff_play.index else None
        name = str(info["displayName"]) if info is not None else f"Joueur {pid}"
        jersey = _clean(meta_rows.loc[pid, "jerseyNumber"])
        pos = _clean(scout["pff_positionLinedUp"]) if scout is not None else None
        if not pos and info is not None:
            pos = _clean(info["officialPosition"])
        index_of[pid] = len(players)
        players.append({
            "id": int(pid),
            "name": name,
            "short": short_name(name),
            "jersey": int(jersey) if jersey is not None else None,
            "team": str(meta_rows.loc[pid, "team"]),
            "side": "off" if meta_rows.loc[pid, "team"] == offense else "def",
            "role": _clean(scout["pff_role"]) if scout is not None else None,
            "pos": pos or "",
            "x": _rounded(px[pid]),
            "y": _rounded(py[pid]),
            "o": _rounded(po[pid], 0),
            "s": _rounded(ps[pid], 1),
        })

    def role_ids(role: str) -> list[int]:
        if "pff_role" not in pff_play.columns:
            return []
        return [int(i) for i in pff_play.index[pff_play["pff_role"] == role] if int(i) in index_of]

    qb_ids = role_ids("Pass")
    if not qb_ids:  # secours : poste officiel QB côté attaque
        qb_ids = [p["id"] for p in players if p["side"] == "off" and p["pos"] == "QB"]
    qb_i = index_of[qb_ids[0]] if qb_ids else None

    xs = px.to_numpy(dtype=float)
    ys = py.to_numpy(dtype=float)
    col_of = {pid: k for k, pid in enumerate(px.columns)}

    def dist_to_qb(pid: int) -> np.ndarray:
        q = col_of[qb_ids[0]]
        k = col_of[pid]
        return np.hypot(xs[:, k] - xs[:, q], ys[:, k] - ys[:, q])

    # Duels bloqueur -> défenseur
    duels = []
    if qb_i is not None:
        for pid in role_ids("Pass Block"):
            scout = pff_play.loc[pid]
            target = _clean(scout.get("pff_nflIdBlockedPlayer"))
            if target is None or int(target) not in index_of:
                continue
            target = int(target)
            dist = dist_to_qb(target)
            pressure_i = _first_below(dist, threshold, snap_i, end_i)
            stop_i = pressure_i if pressure_i is not None else end_i
            defender_scout = pff_play.loc[target] if target in pff_play.index else None
            duels.append({
                "blocker": index_of[pid],
                "defender": index_of[target],
                "dist": _rounded(dist),
                "pressure": pressure_i,
                "tempsTenu": round(float(frames[stop_i] - frames[snap_i]) / FPS, 2),
                "perdu": pressure_i is not None,
                "blockType": _clean(scout.get("pff_blockType")),
                "beaten": bool(_clean(scout.get("pff_beatenByDefender"), 0)),
                "hitAllowed": bool(_clean(scout.get("pff_hitAllowed"), 0)),
                "hurryAllowed": bool(_clean(scout.get("pff_hurryAllowed"), 0)),
                "sackAllowed": bool(_clean(scout.get("pff_sackAllowed"), 0)),
                "defSack": bool(_clean(defender_scout.get("pff_sack"), 0)) if defender_scout is not None else False,
            })
        duels.sort(key=lambda d: -float(snap_y.get(players[d["blocker"]]["id"], 0.0)))

    # Rusher le plus proche du QB à chaque frame (vue sans focus)
    rushers = role_ids("Pass Rush")
    nearest = None
    if qb_i is not None and rushers:
        mat = np.vstack([dist_to_qb(pid) for pid in rushers])  # (rushers, frames)
        safe = np.where(np.isnan(mat), np.inf, mat)
        who = safe.argmin(axis=0)
        best = safe.min(axis=0)
        best = np.where(np.isinf(best), np.nan, best)
        nearest = {
            "dist": _rounded(best),
            "who": [index_of[rushers[k]] for k in who],
            "pressure": _first_below(best, threshold, snap_i, end_i),
        }

    # Ligne de scrimmage et ligne du 1er down (attaque vers la droite)
    los = float(bx[snap_i]) if not np.isnan(bx[snap_i]) else None
    if los is None and _clean(play.get("absoluteYardlineNumber")) is not None:
        los = float(play["absoluteYardlineNumber"])
        los = FIELD_LENGTH - los if flipped else los
    ytg = _clean(play.get("yardsToGo"))
    first_down = min(los + float(ytg), 110.0) if (los is not None and ytg is not None) else None

    block_types = pff_play["pff_blockType"].dropna().astype(str).tolist() if "pff_blockType" in pff_play else []
    pass_result = _clean(play.get("passResult"))
    meta = {
        "gameId": game_id,
        "playId": play_id,
        "home": home,
        "away": away,
        "offense": offense,
        "defense": defense,
        "week": _clean(game["week"]) if game is not None else None,
        "gameDate": _clean(game["gameDate"]) if game is not None else None,
        "quarter": _clean(play.get("quarter")),
        "gameClock": _clean(play.get("gameClock"), ""),
        "down": _clean(play.get("down")),
        "yardsToGo": ytg,
        "downLabel": down_label(play.get("down"), ytg),
        "homeScore": _clean(play.get("preSnapHomeScore")),
        "awayScore": _clean(play.get("preSnapVisitorScore")),
        "description": _clean(play.get("playDescription"), ""),
        "passResult": pass_result,
        "passResultLabel": PASS_RESULT_LABELS.get(pass_result, pass_result or ""),
        "formation": _clean(play.get("offenseFormation"), ""),
        "dropBack": _clean(play.get("dropBackType"), ""),
        "coverage": _clean(play.get("pff_passCoverage"), ""),
        "playAction": bool(_clean(play.get("pff_playAction"), 0)),
        "nbRushers": len(rushers),
        "blitz": len(rushers) >= 5,
        "stunt": "SW" in block_types,
        "direction": direction,
        "flipped": flipped,
    }

    return {
        "v": 1,
        "fps": FPS,
        "threshold": float(threshold),
        "field": {"length": FIELD_LENGTH, "width": FIELD_WIDTH, "los": los, "firstDown": first_down},
        "meta": meta,
        "teams": {
            "off": team_style(offense, offense == home),
            "def": team_style(defense, defense == home),
        },
        "frames": [int(f) for f in frames],
        "events": [{"i": i, "name": name, "label": EVENT_LABELS.get(name, name)} for i, name in events],
        "snap": int(snap_i),
        "end": int(end_i),
        "endEvent": end_event,
        "endLabel": EVENT_LABELS.get(end_event, "Fin") if end_event else "Fin",
        "start": int(max(0, snap_i - 10)),
        "players": players,
        "ball": {"x": _rounded(bx), "y": _rounded(by)},
        "qb": qb_i,
        "duels": duels,
        "rushers": [index_of[r] for r in rushers],
        "nearest": nearest,
        "focus": None,
    }


def build_play_payload(game_id: int, play_id: int, focus_blocker_id: Optional[int] = None,
                       threshold: float = PRESSURE_THRESHOLD) -> dict:
    """
    Données complètes d'une action, prêtes pour le replay (JSON-sérialisables).

    focus_blocker_id : nflId du bloqueur à mettre en avant (optionnel).
    """
    base = _base_payload(int(game_id), int(play_id), float(threshold))
    payload = dict(base)  # copie superficielle : le cache reste intact
    payload["meta"] = dict(base["meta"])
    payload["focus"] = None
    if focus_blocker_id is not None and not pd.isna(focus_blocker_id):
        wanted = int(focus_blocker_id)
        for k, duel in enumerate(base["duels"]):
            if base["players"][duel["blocker"]]["id"] == wanted:
                payload["focus"] = k
                break
        else:
            payload["meta"]["focusWarning"] = (
                f"Le joueur {wanted} n'a pas de duel de bloc sur cette action."
            )
    return payload


def play_duels(game_id: int, play_id: int, threshold: float = PRESSURE_THRESHOLD) -> pd.DataFrame:
    """Résumé des duels de bloc d'une action (pratique pour choisir un focus)."""
    p = _base_payload(int(game_id), int(play_id), float(threshold))
    rows = []
    for d in p["duels"]:
        b, v = p["players"][d["blocker"]], p["players"][d["defender"]]
        rows.append({
            "blockerId": b["id"], "blockerName": b["name"], "blockerPos": b["pos"],
            "defenderId": v["id"], "defenderName": v["name"], "defenderPos": v["pos"],
            "temps_tenu": d["tempsTenu"], "perdu": d["perdu"],
            "pressure_allowed": d["hitAllowed"] or d["hurryAllowed"] or d["sackAllowed"],
            "sack_allowed": d["sackAllowed"], "blockType": d["blockType"],
        })
    return pd.DataFrame(rows)
