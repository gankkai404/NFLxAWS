"""Couleurs et noms des 32 équipes NFL (saison 2021, abréviations du Big Data Bowl)."""
from __future__ import annotations

# abbr: (nom complet, texte end zone, couleur principale, couleur secondaire, casque)
_TEAMS = {
    "ARI": ("Arizona Cardinals", "CARDINALS", "#97233F", "#FFB612", "#F5F5F5"),
    "ATL": ("Atlanta Falcons", "FALCONS", "#A71930", "#101820", "#101820"),
    "BAL": ("Baltimore Ravens", "RAVENS", "#241773", "#9E7C0C", "#101820"),
    "BUF": ("Buffalo Bills", "BILLS", "#00338D", "#C60C30", "#F5F5F5"),
    "CAR": ("Carolina Panthers", "PANTHERS", "#0085CA", "#101820", "#BFC0BF"),
    "CHI": ("Chicago Bears", "BEARS", "#0B162A", "#C83803", "#0B162A"),
    "CIN": ("Cincinnati Bengals", "BENGALS", "#FB4F14", "#101820", "#FB4F14"),
    "CLE": ("Cleveland Browns", "BROWNS", "#311D00", "#FF3C00", "#FF3C00"),
    "DAL": ("Dallas Cowboys", "COWBOYS", "#003594", "#869397", "#B0B7BC"),
    "DEN": ("Denver Broncos", "BRONCOS", "#FB4F14", "#002244", "#002244"),
    "DET": ("Detroit Lions", "LIONS", "#0076B6", "#B0B7BC", "#B0B7BC"),
    "GB": ("Green Bay Packers", "PACKERS", "#203731", "#FFB612", "#FFB612"),
    "HOU": ("Houston Texans", "TEXANS", "#03202F", "#A71930", "#03202F"),
    "IND": ("Indianapolis Colts", "COLTS", "#002C5F", "#A2AAAD", "#F5F5F5"),
    "JAX": ("Jacksonville Jaguars", "JAGUARS", "#006778", "#D7A22A", "#101820"),
    "KC": ("Kansas City Chiefs", "CHIEFS", "#E31837", "#FFB81C", "#E31837"),
    "LA": ("Los Angeles Rams", "RAMS", "#003594", "#FFA300", "#003594"),
    "LAC": ("Los Angeles Chargers", "CHARGERS", "#0080C6", "#FFC20E", "#F5F5F5"),
    "LV": ("Las Vegas Raiders", "RAIDERS", "#101010", "#A5ACAF", "#A5ACAF"),
    "MIA": ("Miami Dolphins", "DOLPHINS", "#008E97", "#FC4C02", "#F5F5F5"),
    "MIN": ("Minnesota Vikings", "VIKINGS", "#4F2683", "#FFC62F", "#4F2683"),
    "NE": ("New England Patriots", "PATRIOTS", "#002244", "#C60C30", "#B0B7BC"),
    "NO": ("New Orleans Saints", "SAINTS", "#D3BC8D", "#101820", "#D3BC8D"),
    "NYG": ("New York Giants", "GIANTS", "#0B2265", "#A71930", "#0B2265"),
    "NYJ": ("New York Jets", "JETS", "#125740", "#F5F5F5", "#125740"),
    "PHI": ("Philadelphia Eagles", "EAGLES", "#004C54", "#A5ACAF", "#004C54"),
    "PIT": ("Pittsburgh Steelers", "STEELERS", "#FFB612", "#101820", "#101820"),
    "SEA": ("Seattle Seahawks", "SEAHAWKS", "#002244", "#69BE28", "#002244"),
    "SF": ("San Francisco 49ers", "49ERS", "#AA0000", "#B3995D", "#B3995D"),
    "TB": ("Tampa Bay Buccaneers", "BUCCANEERS", "#D50A0A", "#34302B", "#34302B"),
    "TEN": ("Tennessee Titans", "TITANS", "#0C2340", "#4B92DB", "#0C2340"),
    "WAS": ("Washington Football Team", "WASHINGTON", "#5A1414", "#FFB612", "#5A1414"),
}

_FALLBACK = ("Équipe", "NFL", "#334155", "#94A3B8", "#334155")


def _is_light(hex_color: str) -> bool:
    """Vrai si la couleur est claire (pour choisir des numéros noirs ou blancs)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) > 160


def team_style(abbr: str, is_home: bool) -> dict:
    """
    Style visuel d'une équipe pour le replay.

    Convention NFL : l'équipe à domicile porte son maillot couleur,
    l'équipe visiteuse porte le maillot blanc (le contraste est garanti).
    """
    name, endzone, primary, secondary, helmet = _TEAMS.get(abbr, _FALLBACK)
    if is_home:
        jersey = primary
        number = "#101820" if _is_light(primary) else "#FFFFFF"
        pants = "#E5E7EB" if not _is_light(primary) else secondary
    else:
        jersey = "#F4F4F5"
        number = primary if not _is_light(primary) else secondary
        pants = primary if not _is_light(primary) else "#E5E7EB"
    return {
        "abbr": abbr,
        "name": name,
        "endzone": endzone,
        "primary": primary,
        "secondary": secondary,
        "helmet": helmet,
        "jersey": jersey,
        "number": number,
        "pants": pants,
        "isHome": bool(is_home),
    }
