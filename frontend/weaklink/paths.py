"""Filesystem layout. Works with both `data/*.csv` and the planned `data/raw/*.csv`."""

from __future__ import annotations

from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = FRONTEND_DIR.parent
DATA_DIR = REPO_DIR / "data"

# The team plan moves the Big Data Bowl CSVs to data/raw/; accept both layouts.
RAW_DIR = DATA_DIR / "raw" if (DATA_DIR / "raw" / "plays.csv").exists() else DATA_DIR

# Part 1 deliverable. When this file exists the app switches from demo data to it.
PROCESSED_BLOCKS = DATA_DIR / "processed" / "blocks.csv"


def tracking_dirs() -> list[Path]:
    """Folders that may contain tracking_<gameId>.csv files, in priority order."""
    candidates = [RAW_DIR / "tracking", RAW_DIR, DATA_DIR / "tracking", DATA_DIR]
    seen: list[Path] = []
    for folder in candidates:
        if folder.is_dir() and folder not in seen:
            seen.append(folder)
    return seen


def tracking_file(game_id: int) -> Path | None:
    for folder in tracking_dirs():
        path = folder / f"tracking_{int(game_id)}.csv"
        if path.exists():
            return path
    return None


def all_tracking_files() -> list[Path]:
    for folder in tracking_dirs():
        files = sorted(folder.glob("tracking_*.csv"))
        if files:
            return files
    return []
