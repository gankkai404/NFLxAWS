"""Aggregations behind every screen: filters, rankings, survival curves, splits."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .labels import FORMATIONS, OL_SLOTS

Z80 = 1.2816  # two-sided 80 % interval: honest about small samples without being alarmist

SITUATIONS = {
    "third": "3e down",
    "blitz": "Blitz 5+",
    "stunt": "Stunt",
    "pa": "Play action",
}


@dataclass(frozen=True)
class Filters:
    situations: tuple[str, ...] = ()
    formation: str | None = None

    @property
    def active(self) -> bool:
        return bool(self.situations or self.formation)

    def label(self) -> str:
        parts = [SITUATIONS[s] for s in self.situations]
        if self.formation:
            parts.append(FORMATIONS.get(self.formation, self.formation.title()))
        return " + ".join(parts) if parts else "Toutes situations"


def apply_filters(df: pd.DataFrame, f: Filters) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if "third" in f.situations:
        mask &= df["down"].eq(3)
    if "blitz" in f.situations:
        mask &= df["nb_rushers"].ge(5)
    if "stunt" in f.situations:
        mask &= df["stunt"]
    if "pa" in f.situations:
        mask &= df["pff_playAction"].eq(1)
    if f.formation:
        mask &= df["offenseFormation"].eq(f.formation)
    return df.loc[mask]


def position_group(slot: str | float) -> str:
    """Compare blockers with their peers: tackles face the best edge rushers."""
    s = str(slot)
    if s in ("LT", "RT", "T"):
        return "T"
    if s in ("LG", "RG", "G"):
        return "G"
    if s == "C":
        return "C"
    if s.startswith("TE"):
        return "TE"
    if s.startswith(("HB", "FB", "RB")):
        return "RB"
    return "WR"


GROUP_LABELS = {"T": "tackles", "G": "guards", "C": "centres", "TE": "tight ends", "RB": "running backs", "WR": "receveurs"}


def wilson(k: np.ndarray, n: np.ndarray, z: float = Z80) -> tuple[np.ndarray, np.ndarray]:
    k = np.asarray(k, dtype=float)
    n = np.asarray(n, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        p = np.where(n > 0, k / n, np.nan)
        denom = 1 + z**2 / n
        centre = (p + z**2 / (2 * n)) / denom
        half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return np.clip(centre - half, 0, 1), np.clip(centre + half, 0, 1)


def with_groups(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["group"] = out["slot"].map(position_group)
    return out


def league_rates(df: pd.DataFrame) -> dict[str, float]:
    """Loss rate per position group (plus 'ALL') for the given situation."""
    rates = df.groupby("group")["perdu"].mean().to_dict()
    rates["ALL"] = float(df["perdu"].mean()) if len(df) else np.nan
    return rates


def primary_slots(team_df: pd.DataFrame) -> pd.Series:
    """Most frequent alignment for each blocker."""
    return team_df.groupby("blockerId")["slot"].agg(lambda s: s.mode().iloc[0] if len(s.mode()) else "")


def ranking(team_df: pd.DataFrame, league: dict[str, float], min_duels: int) -> pd.DataFrame:
    if team_df.empty:
        return pd.DataFrame()
    g = team_df.groupby("blockerId")
    table = pd.DataFrame(
        {
            "name": g["blockerName"].first(),
            "jersey": g["jersey"].first(),
            "duels": g.size(),
            "losses": g["perdu"].sum(),
            "pressures": g["pressure_allowed"].sum(),
            "sacks": g["sack_allowed"].sum(),
            "tenu_moy": g["temps_tenu"].mean(),
        }
    )
    lost = team_df.loc[team_df["perdu"]]
    table["rupture"] = lost.groupby("blockerId")["temps_tenu"].mean()
    table["slot"] = primary_slots(team_df)
    table["group"] = table["slot"].map(position_group)
    table["is_ol"] = table["slot"].isin(OL_SLOTS)
    table["rate"] = table["losses"] / table["duels"]
    lo, hi = wilson(table["losses"].to_numpy(), table["duels"].to_numpy())
    table["ci_lo"], table["ci_hi"] = lo, hi
    table["pos_rate"] = table["group"].map(league).fillna(league.get("ALL", np.nan))
    with np.errstate(divide="ignore", invalid="ignore"):
        table["index"] = 100 * table["rate"] / table["pos_rate"]
    table["eligible"] = table["duels"].ge(min_duels)
    # Clearly above peers: the whole 80 % interval sits over the position average.
    table["flag"] = table["eligible"] & table["ci_lo"].gt(table["pos_rate"])
    table = table.reset_index().sort_values(
        ["is_ol", "eligible", "index", "duels"], ascending=[False, False, False, False]
    )
    return table.reset_index(drop=True)


def weakest(table: pd.DataFrame) -> pd.Series | None:
    if table.empty:
        return None
    pool = table.loc[table["eligible"] & table["is_ol"]]
    if pool.empty:
        pool = table.loc[table["eligible"]]
    if pool.empty:
        return None
    return pool.sort_values(["index", "duels"], ascending=[False, False]).iloc[0]


def line_slots(team_df: pd.DataFrame, table: pd.DataFrame) -> list[dict]:
    """The five O-line spots, each with the blocker who played it most."""
    slots = []
    by_id = table.set_index("blockerId") if not table.empty else pd.DataFrame()
    for slot in OL_SLOTS:
        at_slot = team_df.loc[team_df["slot"].eq(slot)]
        if at_slot.empty:
            slots.append({"slot": slot, "empty": True})
            continue
        counts = at_slot.groupby("blockerId").size().sort_values(ascending=False)
        bid = int(counts.index[0])
        others = [(int(i), int(c)) for i, c in counts.iloc[1:].items() if c >= 10]
        row = by_id.loc[bid]
        slots.append(
            {
                "slot": slot,
                "empty": False,
                "blockerId": bid,
                "snaps_here": int(counts.iloc[0]),
                "share_here": float(counts.iloc[0] / counts.sum()),
                "others": [{"blockerId": i, "name": by_id.loc[i, "name"], "duels": c} for i, c in others[:2]],
                **{k: row[k] for k in ["name", "jersey", "duels", "rate", "index", "pressures", "sacks", "eligible", "flag", "pos_rate"]},
            }
        )
    return slots


def team_line_rank(df_situation: pd.DataFrame, team: str) -> tuple[float, int, int]:
    """O-line loss rate for the team and its rank among teams (1 = most fragile)."""
    ol = df_situation.loc[df_situation["slot"].isin(OL_SLOTS)]
    rates = ol.groupby("team")["perdu"].mean().sort_values(ascending=False)
    if team not in rates.index:
        return np.nan, 0, len(rates)
    return float(rates[team]), int(list(rates.index).index(team)) + 1, len(rates)


def cumulative_loss(times: pd.Series, events: pd.Series, grid: np.ndarray) -> np.ndarray:
    """Kaplan–Meier: share of duels lost by time t, treating unfinished duels as censored.

    A plain average of `temps_tenu` mixes duels the blocker lost with plays where the
    ball was simply out early; the survival estimate keeps those apart.
    """
    t = np.round(np.asarray(times, dtype=float), 2)
    e = np.asarray(events, dtype=bool)
    if len(t) == 0:
        return np.full_like(grid, np.nan, dtype=float)
    event_times = np.unique(t[e])
    surv = np.ones(len(event_times))
    s = 1.0
    for i, tj in enumerate(event_times):
        at_risk = np.sum(t >= tj)
        deaths = np.sum((t == tj) & e)
        if at_risk > 0:
            s *= 1 - deaths / at_risk
        surv[i] = s
    idx = np.searchsorted(event_times, grid, side="right") - 1
    curve = np.where(idx >= 0, surv[np.clip(idx, 0, None)], 1.0)
    return 1 - curve


def median_release(df: pd.DataFrame) -> float:
    """Typical time the ball is out: duels that were never lost end with the play."""
    held = df.loc[~df["perdu"], "temps_tenu"]
    return float(held.median()) if len(held) else np.nan


SPLITS = [
    ("Toutes situations", lambda d: pd.Series(True, index=d.index)),
    ("1er & 2e down", lambda d: d["down"].isin([1, 2])),
    ("3e down", lambda d: d["down"].eq(3)),
    ("3e & long (7+)", lambda d: d["down"].eq(3) & d["yardsToGo"].ge(7)),
    ("Rush à 4 ou moins", lambda d: d["nb_rushers"].le(4)),
    ("Blitz 5+", lambda d: d["nb_rushers"].ge(5)),
    ("Stunt", lambda d: d["stunt"]),
    ("Play action", lambda d: d["pff_playAction"].eq(1)),
    ("Shotgun", lambda d: d["offenseFormation"].eq("SHOTGUN")),
    ("Empty", lambda d: d["offenseFormation"].eq("EMPTY")),
    ("Sous le centre", lambda d: d["offenseFormation"].isin(["SINGLEBACK", "I_FORM", "JUMBO"])),
]


def splits(player_df: pd.DataFrame, league_df: pd.DataFrame, group: str, min_n: int = 8) -> list[dict]:
    peers = league_df.loc[league_df["group"].eq(group)]
    rows = []
    base = player_df["perdu"].mean() if len(player_df) else np.nan
    for label, rule in SPLITS:
        sub = player_df.loc[rule(player_df)]
        peer = peers.loc[rule(peers)]
        n = len(sub)
        rate = sub["perdu"].mean() if n else np.nan
        rows.append(
            {
                "label": label,
                "n": n,
                "losses": int(sub["perdu"].sum()),
                "rate": rate if n >= min_n else np.nan,
                "peer": peer["perdu"].mean() if len(peer) else np.nan,
                "delta": (rate - base) if n >= min_n else np.nan,
                "is_base": label == "Toutes situations",
            }
        )
    return rows


def worst_split(rows: list[dict], min_n: int = 15) -> dict | None:
    pool = [r for r in rows if not r["is_base"] and r["n"] >= min_n and r["rate"] == r["rate"]]
    if not pool:
        return None
    top = max(pool, key=lambda r: r["rate"])
    return top if top["delta"] >= 0.04 else None


def nemeses(player_df: pd.DataFrame, top: int = 3) -> list[dict]:
    if player_df.empty or "defenderName" not in player_df:
        return []
    g = player_df.groupby(["defenderId", "defenderName"], dropna=True)
    table = pd.DataFrame({"wins": g["perdu"].sum(), "duels": g.size()}).reset_index()
    pos = player_df.drop_duplicates("defenderId").set_index("defenderId")["defenderPos"]
    table["pos"] = table["defenderId"].map(pos)
    table = table.loc[table["wins"].gt(0)].sort_values(["wins", "duels"], ascending=[False, True])
    return table.head(top).to_dict("records")


def lost_duels(player_df: pd.DataFrame) -> pd.DataFrame:
    lost = player_df.loc[player_df["perdu"]].copy()
    if lost.empty:
        return lost
    lost["severity"] = np.select([lost["sack_allowed"], lost["pressure_allowed"]], [2, 1], default=0)
    return lost.sort_values(["severity", "temps_tenu"], ascending=[False, True]).reset_index(drop=True)
