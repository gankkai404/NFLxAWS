"""Demo `blocks.csv` built from the real PFF duels, with the exact Part 1 contract.

Everything is real except the timing:
- duels, blockers, defenders, situations and PFF pressure/sack flags come from the data;
- `perdu` uses PFF (beaten / hit / hurry / sack allowed) as a stand-in for the
  "< 2 yards from the QB" tracking rule;
- `temps_tenu` is simulated. It is replaced as soon as data/processed/blocks.csv exists.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CONTRACT_COLUMNS = [
    "gameId", "playId", "blockerId", "blockerName", "blockerPos", "team",
    "defenderId", "defenderName", "temps_tenu", "perdu", "pressure_allowed",
    "sack_allowed", "down", "yardsToGo", "nb_rushers", "stunt", "pff_playAction",
    "offenseFormation", "passResult", "playDescription",
]

KEY = ["gameId", "playId"]


def _flag(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).astype(int).astype(bool)


def play_context(scouting: pd.DataFrame) -> pd.DataFrame:
    """nb_rushers and stunt per play, as defined in the team plan."""
    rushers = scouting.loc[scouting["pff_role"].eq("Pass Rush")].groupby(KEY).size()
    stunts = scouting.loc[scouting["pff_blockType"].eq("SW")].groupby(KEY).size()
    ctx = pd.DataFrame({"nb_rushers": rushers}).join(pd.DataFrame({"stunt": stunts}), how="outer")
    ctx["nb_rushers"] = ctx["nb_rushers"].fillna(0).astype(int)
    ctx["stunt"] = ctx["stunt"].fillna(0).gt(0)
    return ctx.reset_index()


def build_mock_blocks(plays: pd.DataFrame, scouting: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    blocks = scouting.loc[
        scouting["pff_role"].eq("Pass Block") & scouting["pff_nflIdBlockedPlayer"].notna()
    ].copy()

    sack = _flag(blocks["pff_sackAllowed"])
    pressure = _flag(blocks["pff_hitAllowed"]) | _flag(blocks["pff_hurryAllowed"]) | sack
    blocks["pressure_allowed"] = pressure
    blocks["sack_allowed"] = sack
    blocks["perdu"] = pressure | _flag(blocks["pff_beatenByDefender"])

    blocks = blocks.merge(play_context(scouting), on=KEY, how="left")
    play_cols = KEY + [
        "possessionTeam", "down", "yardsToGo", "pff_playAction",
        "offenseFormation", "passResult", "playDescription",
    ]
    blocks = blocks.merge(plays[play_cols], on=KEY, how="left")

    names = players.set_index("nflId")["displayName"]
    blocks["blockerId"] = blocks["nflId"].astype(int)
    blocks["defenderId"] = blocks["pff_nflIdBlockedPlayer"].astype(int)
    blocks["blockerName"] = blocks["blockerId"].map(names)
    blocks["defenderName"] = blocks["defenderId"].map(names)
    blocks["blockerPos"] = blocks["pff_positionLinedUp"]
    blocks["team"] = blocks["possessionTeam"]

    # Simulated timing. One end-of-play time per play (pass thrown, sack or scramble),
    # shared by every duel of that play. Lost duels break before the end.
    rng = np.random.default_rng(2021)
    ends = plays[KEY + ["passResult"]].copy()
    median = np.select(
        [ends["passResult"].eq("S"), ends["passResult"].eq("R")], [3.4, 3.6], default=2.6
    )
    ends["play_end"] = np.clip(median * np.exp(rng.normal(0.0, 0.28, len(ends))), 1.2, 7.0)
    blocks = blocks.merge(ends[KEY + ["play_end"]], on=KEY, how="left")

    n = len(blocks)
    share = np.where(blocks["sack_allowed"], rng.uniform(0.82, 1.0, n), rng.uniform(0.42, 0.97, n))
    lost_at = np.maximum(0.7, blocks["play_end"].to_numpy() * share)
    blocks["temps_tenu"] = np.where(blocks["perdu"], lost_at, blocks["play_end"]).round(1)

    return blocks[CONTRACT_COLUMNS].reset_index(drop=True)
