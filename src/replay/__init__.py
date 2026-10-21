"""
Weak Link · Partie 2 : replay animé d'une action (2D Plotly).

Contrat avec les parties 1 (metrics) et 3 (app) :

    from src.replay import make_replay
    fig = make_replay(game_id, play_id, focus_blocker_id=None)
    st.plotly_chart(fig, use_container_width=True)

`focus_blocker_id` est le `blockerId` d'une ligne de blocks.csv. Le replay
surligne alors ce bloqueur, son défenseur (pff_nflIdBlockedPlayer) et trace
la ligne défenseur → QB qui passe au rouge sous le seuil de pression.

Helpers :
    build_play_payload(game_id, play_id, focus_blocker_id)  # données brutes de l'action
    play_duels(game_id, play_id)                            # duels de bloc (DataFrame)
"""
from importlib import import_module

# Imports paresseux : Plotly n'est chargé que si make_replay est appelé.
_EXPORTS = {
    "PRESSURE_THRESHOLD": ".data",
    "build_play_payload": ".data",
    "play_duels": ".data",
    "make_replay": ".plotly2d",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name):
    if name in _EXPORTS:
        return getattr(import_module(_EXPORTS[name], __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return __all__
