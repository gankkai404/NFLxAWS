"""
Ligne de commande du replay 2D (pratique pour préparer les actions « waouh »).

    python -m src.replay --game 2021090900 --play 2279 --blocker 37082 --open
    python -m src.replay --game 2021090900 --play 2279 --duels   # liste des duels
"""
from __future__ import annotations

import argparse
import webbrowser
from pathlib import Path

from .data import PRESSURE_THRESHOLD, REPO_ROOT, play_duels


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m src.replay",
                                 description="Génère le replay 2D d'une action en HTML.")
    ap.add_argument("--game", type=int, required=True, help="gameId")
    ap.add_argument("--play", type=int, required=True, help="playId")
    ap.add_argument("--blocker", type=int, default=None, help="blockerId du bloqueur à suivre (optionnel)")
    ap.add_argument("--threshold", type=float, default=PRESSURE_THRESHOLD, help="seuil de pression en yards")
    ap.add_argument("--out", type=Path, default=None, help="fichier de sortie (défaut : replays/...)")
    ap.add_argument("--duels", action="store_true", help="affiche les duels de bloc de l'action et quitte")
    ap.add_argument("--open", action="store_true", help="ouvre le fichier dans le navigateur")
    args = ap.parse_args()

    if args.duels:
        duels = play_duels(args.game, args.play, args.threshold)
        print(duels.to_string(index=False) if not duels.empty else "Aucun duel de bloc sur cette action.")
        return

    from .plotly2d import make_replay

    suffix = f"_{args.blocker}" if args.blocker else ""
    out = args.out or REPO_ROOT / "replays" / f"replay_{args.game}_{args.play}{suffix}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    make_replay(args.game, args.play, args.blocker, args.threshold).write_html(out, include_plotlyjs=True)
    print(f"Replay écrit : {out}")
    if args.open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
