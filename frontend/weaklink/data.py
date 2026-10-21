"""Data loading: raw Big Data Bowl tables + the duel table (real or demo)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from html import unescape

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import streamlit as st

from . import paths
from .mock import CONTRACT_COLUMNS, KEY, build_mock_blocks, play_context

REQUIRED = ["gameId", "playId", "blockerId", "temps_tenu", "perdu"]
BOOL_COLUMNS = ["perdu", "pressure_allowed", "sack_allowed", "stunt"]
PLAY_EXTRAS = [
    "quarter", "gameClock", "defensiveTeam", "possessionTeam", "pff_passCoverage",
    "pff_passCoverageType", "dropBackType",
]


@dataclass
class Dataset:
    blocks: pd.DataFrame
    players: pd.DataFrame
    mode: str  # "real" or "demo"
    path: str | None
    updated: str | None
    warnings: list[str] = field(default_factory=list)

    @property
    def is_demo(self) -> bool:
        return self.mode == "demo"


def _mtime(path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


@st.cache_data(show_spinner=False)
def load_raw(_stamp: float) -> dict[str, pd.DataFrame]:
    raw = paths.RAW_DIR
    return {
        "plays": pd.read_csv(raw / "plays.csv"),
        "games": pd.read_csv(raw / "games.csv"),
        "players": pd.read_csv(raw / "players.csv"),
        "scouting": pd.read_csv(raw / "pffScoutingData.csv"),
    }


@st.cache_data(show_spinner=False)
def jersey_map(_stamp: float) -> pd.DataFrame:
    """nflId + team -> jersey number, read from the first frame of every tracking file (~1 s)."""
    convert = pacsv.ConvertOptions(
        include_columns=["nflId", "jerseyNumber", "team", "frameId"],
        column_types={"nflId": pa.float64(), "jerseyNumber": pa.float64()},
        null_values=["NA", ""],
    )
    tables = []
    for file in paths.all_tracking_files():
        table = pacsv.read_csv(file, convert_options=convert)
        tables.append(table.filter(pc.equal(table["frameId"], 1)).select(["nflId", "jerseyNumber", "team"]))
    if not tables:
        return pd.DataFrame(columns=["nflId", "team", "jersey"])
    frame = pa.concat_tables(tables).to_pandas().dropna()
    frame = (
        frame.groupby(["nflId", "team"])["jerseyNumber"]
        .agg(lambda s: s.mode().iloc[0])
        .rename("jersey")
        .reset_index()
    )
    frame["nflId"] = frame["nflId"].astype(int)
    frame["jersey"] = frame["jersey"].astype(int)
    return frame


def _to_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    text = series.astype("string").str.strip().str.lower()
    return text.isin(["true", "1", "1.0", "yes", "oui", "t", "y"])


def _normalize(blocks: pd.DataFrame, raw: dict[str, pd.DataFrame], jerseys: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    plays, games, players, scouting = raw["plays"], raw["games"], raw["players"], raw["scouting"]
    df = blocks.copy()
    warnings: list[str] = []

    missing = [c for c in CONTRACT_COLUMNS if c not in df.columns]
    if missing:
        warnings.append("Colonnes absentes de blocks.csv, complétées depuis les données brutes : " + ", ".join(missing))

    for col in ["gameId", "playId", "blockerId"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["gameId", "playId", "blockerId"])
    df[["gameId", "playId", "blockerId"]] = df[["gameId", "playId", "blockerId"]].astype(int)
    if "defenderId" in df.columns:
        df["defenderId"] = pd.to_numeric(df["defenderId"], errors="coerce").astype("Int64")
    df["temps_tenu"] = pd.to_numeric(df["temps_tenu"], errors="coerce")
    for col in BOOL_COLUMNS:
        if col in df.columns:
            df[col] = _to_bool(df[col])

    # Play-level context: fill contract gaps, then add what the UI needs.
    play_cols = [c for c in ["down", "yardsToGo", "pff_playAction", "offenseFormation", "passResult", "playDescription"] if c not in df.columns]
    extras = [c for c in PLAY_EXTRAS if c not in df.columns]
    if play_cols or extras:
        df = df.merge(plays[KEY + play_cols + extras], on=KEY, how="left")
    if "team" not in df.columns:
        df["team"] = df["possessionTeam"]
    if "nb_rushers" not in df.columns or "stunt" not in df.columns:
        ctx = play_context(scouting)
        keep = [c for c in ["nb_rushers", "stunt"] if c not in df.columns]
        df = df.merge(ctx[KEY + keep], on=KEY, how="left")
    df["nb_rushers"] = pd.to_numeric(df["nb_rushers"], errors="coerce").fillna(0).astype(int)
    df["stunt"] = df["stunt"].fillna(False).astype(bool)
    df["pff_playAction"] = pd.to_numeric(df["pff_playAction"], errors="coerce").fillna(0).astype(int)
    for col in ["pressure_allowed", "sack_allowed"]:
        if col not in df.columns:
            df[col] = False

    # Only pull game columns the duel table doesn't already carry, so a real
    # blocks.csv (which includes `week`) doesn't collide into week_x / week_y.
    game_cols = [c for c in ["week", "homeTeamAbbr", "visitorTeamAbbr"] if c not in df.columns]
    if game_cols:
        df = df.merge(games[["gameId", *game_cols]], on="gameId", how="left")

    # Where each blocker lined up (LT, LG, C, RG, RT, TE-L, HB-R...) for the line diagram.
    # Prefer the alignment already in blocks.csv (blockerPos); otherwise read it from scouting.
    if "blockerPos" in df.columns:
        df["slot"] = df["blockerPos"]
    else:
        lined_up = scouting.loc[scouting["pff_role"].eq("Pass Block"), KEY + ["nflId", "pff_positionLinedUp"]]
        lined_up = lined_up.rename(columns={"nflId": "blockerId", "pff_positionLinedUp": "slot"})
        df = df.merge(lined_up, on=KEY + ["blockerId"], how="left")

    names = players.set_index("nflId")["displayName"]
    if "blockerName" not in df.columns:
        df["blockerName"] = df["blockerId"].map(names)
    if "defenderName" not in df.columns and "defenderId" in df.columns:
        df["defenderName"] = df["defenderId"].map(names)
    df["blockerName"] = df["blockerName"].fillna(df["blockerId"].map(names)).fillna("Inconnu")
    df["defenderName"] = df.get("defenderName", pd.Series(index=df.index, dtype="object")).fillna("Inconnu")
    if "defenderPos" not in df.columns:
        positions = players.set_index("nflId")["officialPosition"]
        df["defenderPos"] = df["defenderId"].map(positions) if "defenderId" in df.columns else None

    # Source CSVs store HTML-escaped text (e.g. "A&amp;T"); decode once so it
    # displays correctly and isn't double-escaped by the HTML renderer.
    for col in ["blockerName", "defenderName"]:
        if col in df.columns:
            df[col] = df[col].map(lambda v: unescape(v) if isinstance(v, str) else v)

    if "jersey" not in df.columns and not jerseys.empty:
        jm = jerseys.rename(columns={"nflId": "blockerId"})
        df = df.merge(jm, on=["blockerId", "team"], how="left")
    df["jersey"] = pd.to_numeric(df.get("jersey"), errors="coerce").astype("Int64")

    bad = df["temps_tenu"].isna().sum()
    if bad:
        warnings.append(f"{bad} duels sans temps_tenu ignorés.")
        df = df.dropna(subset=["temps_tenu"])
    return df.reset_index(drop=True), warnings


@st.cache_data(show_spinner="Chargement des duels…")
def _load(raw_stamp: float, processed_stamp: float) -> Dataset:
    raw = load_raw(raw_stamp)
    jerseys = jersey_map(raw_stamp)
    if processed_stamp:
        source = pd.read_csv(paths.PROCESSED_BLOCKS)
        absent = [c for c in REQUIRED if c not in source.columns]
        if absent:
            demo = build_mock_blocks(raw["plays"], raw["scouting"], raw["players"])
            blocks, warnings = _normalize(demo, raw, jerseys)
            warnings.insert(0, "blocks.csv ignoré, colonnes obligatoires absentes : " + ", ".join(absent))
            return Dataset(blocks, raw["players"], "demo", None, None, warnings)
        blocks, warnings = _normalize(source, raw, jerseys)
        updated = datetime.fromtimestamp(processed_stamp).strftime("%H:%M")
        return Dataset(blocks, raw["players"], "real", str(paths.PROCESSED_BLOCKS), updated, warnings)
    demo = build_mock_blocks(raw["plays"], raw["scouting"], raw["players"])
    blocks, warnings = _normalize(demo, raw, jerseys)
    return Dataset(blocks, raw["players"], "demo", None, None, warnings)


def load_dataset() -> Dataset:
    """Cached by file modification time, so a fresh blocks.csv shows up on the next rerun."""
    return _load(_mtime(paths.RAW_DIR / "plays.csv"), _mtime(paths.PROCESSED_BLOCKS))


def player_bio(players: pd.DataFrame, nfl_id: int) -> dict:
    row = players.loc[players["nflId"].eq(nfl_id)]
    if row.empty:
        return {}
    r = row.iloc[0]
    age = None
    birth = pd.to_datetime(r.get("birthDate"), errors="coerce", format="mixed")
    if pd.notna(birth):
        age = int((pd.Timestamp("2021-09-09") - birth).days // 365.25)
    weight = r.get("weight")
    college = r.get("collegeName")
    # players.csv stores HTML-escaped names, e.g. "North Carolina A&amp;T".
    college = unescape(college) if isinstance(college, str) else None
    return {
        "height": r.get("height") if isinstance(r.get("height"), str) else None,
        "weight": int(weight) if pd.notna(weight) else None,
        "college": college,
        "position": r.get("officialPosition"),
        "age": age,
    }


def team_list(blocks: pd.DataFrame) -> list[str]:
    return sorted(blocks["team"].dropna().unique().tolist())


def as_int(value) -> int | None:
    try:
        if value is None or (isinstance(value, float) and np.isnan(value)) or value is pd.NA:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
