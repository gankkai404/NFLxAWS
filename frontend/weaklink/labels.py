"""Display vocabulary (French UI, English football terms where coaches use them)."""

from __future__ import annotations

TEAM_NAMES = {
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB": "Green Bay Packers",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "KC": "Kansas City Chiefs",
    "LA": "Los Angeles Rams",
    "LAC": "Los Angeles Chargers",
    "LV": "Las Vegas Raiders",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE": "New England Patriots",
    "NO": "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks",
    "SF": "San Francisco 49ers",
    "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Football Team",
}

FORMATIONS = {
    "SHOTGUN": "Shotgun",
    "EMPTY": "Empty",
    "SINGLEBACK": "Singleback",
    "I_FORM": "I-Form",
    "PISTOL": "Pistol",
    "JUMBO": "Jumbo",
    "WILDCAT": "Wildcat",
}

PASS_RESULTS = {
    "C": "Complète",
    "I": "Incomplète",
    "S": "Sack",
    "IN": "Interception",
    "R": "Scramble",
}

OL_SLOTS = ["LT", "LG", "C", "RG", "RT"]

NNBSP = "\u202f"  # French typography: narrow no-break space before % and units.


def team_name(abbr: str) -> str:
    return TEAM_NAMES.get(abbr, abbr)


def pct(x: float, digits: int = 1) -> str:
    if x is None or x != x:  # NaN check without numpy
        return "—"
    return f"{x * 100:.{digits}f}".replace(".", ",") + NNBSP + "%"


def sec(x: float) -> str:
    if x is None or x != x:
        return "—"
    return f"{x:.1f}".replace(".", ",") + NNBSP + "s"


def num(n: float) -> str:
    if n is None or n != n:
        return "—"
    return f"{int(round(n)):,}".replace(",", NNBSP)


def dec(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pts(delta: float) -> str:
    """Signed percentage-point delta, e.g. +12 pts."""
    if delta is None or delta != delta:
        return "—"
    value = round(delta * 100)
    sign = "+" if value > 0 else ("−" if value < 0 else "±")
    return f"{sign}{abs(value)}{NNBSP}pts"


def down_label(down, to_go) -> str:
    try:
        d, t = int(down), int(to_go)
    except (TypeError, ValueError):
        return "—"
    if d == 0:
        return "Conversion à 2 pts"
    ordinal = {1: "1er", 2: "2e", 3: "3e", 4: "4e"}.get(d, f"{d}e")
    return f"{ordinal} & {t}"


def split_name(full: str) -> tuple[str, str]:
    """'Alex Leatherwood' -> ('Alex', 'Leatherwood'); keeps suffixes with the last name."""
    parts = str(full).split()
    if len(parts) <= 1:
        return "", str(full)
    if parts[-1].rstrip(".").upper() in {"JR", "SR", "II", "III", "IV", "V"} and len(parts) > 2:
        return " ".join(parts[:-2]), " ".join(parts[-2:])
    return " ".join(parts[:-1]), parts[-1]


def short_name(full: str) -> str:
    """'Alex Leatherwood' -> 'A. Leatherwood'."""
    first, last = split_name(full)
    return f"{first[0]}. {last}" if first else last
