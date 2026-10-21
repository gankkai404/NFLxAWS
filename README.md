# Weak Link — trouver le maillon faible de la ligne offensive adverse

Un écran pour savoir quel bloqueur adverse craque, dans quelles situations, avec le replay animé qui le prouve.

## Problème et positionnement

Des outils pros comme Teamworks Coaching ou Catapult Thunder analysent les tendances adverses de façon générique (formations, appels, vidéo). Weak Link se concentre sur un seul sujet : la protection de passe, duel par duel. Grâce au tracking des joueurs, on mesure pour chaque bloqueur s'il laisse son défenseur atteindre le quarterback, et à quel moment.

## Fonctionnalités du MVP

- Classement des bloqueurs d'une équipe, du plus faible au plus solide.
- Filtres de situation : 3e down, blitz, stunt, play action.
- Replay animé des duels perdus.

## Données

NFL Big Data Bowl : tracking Next Gen Stats (10 Hz) et scouting PFF, 122 matchs des semaines 1 à 8 de la saison 2021, jeux de passe uniquement. Les placer dans `data/raw/` (pour l'instant elles sont dans `data/` : lancer les commandes avec `--raw data`). Les données brutes ne sont pas versionnées (`data/raw/` est dans le `.gitignore`).

## Structure du repo

```
data/raw/            # données brutes Big Data Bowl (non versionnées)
data/processed/      # blocks.csv, une ligne par duel (non versionné, à régénérer)
src/metrics.py       # Partie 1 : calcul des duels et de la métrique (CLI + API)
src/replay/          # Partie 2 : replay animé 2D Plotly d'une action
  ├── data.py        #   prépare une action (positions, duels, frames snap/pression/fin)
  ├── plotly2d.py    #   make_replay(...) -> go.Figure
  ├── teams.py       #   couleurs des 32 équipes NFL
  ├── demo_app.py    #   page Streamlit de démo (branchée sur blocks.csv)
  └── __main__.py    #   CLI : python -m src.replay --game ... --play ...
app.py               # Partie 3 : application Streamlit
docs/                # documentation de la métrique (metriques.md)
tests/               # tests unitaires pytest
```

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

```bash
python -m src.metrics     # génère data/processed/blocks.csv (ajouter --raw data tant que les données sont dans data/)
streamlit run app.py      # lance l'application
pytest -q                 # lance les tests
```

## Contrats entre les parties

- `data/processed/blocks.csv` : une ligne par duel. Colonnes clés : `gameId`, `playId`, `blockerId`, `blockerName`, `blockerPos`, `team`, `defenderId`, `defenderName`, `temps_tenu`, `perdu`, `pressure_allowed`, `sack_allowed`, `down`, `yardsToGo`, `nb_rushers`, `stunt`, `pff_playAction`, `offenseFormation`, `passResult`, `playDescription`, plus `frame_perdu` pour le replay. Dictionnaire complet : [docs/metriques.md](docs/metriques.md).
- Replay : `from src.replay import make_replay` ; `make_replay(game_id, play_id, focus_blocker_id=None) -> plotly.graph_objects.Figure`. `focus_blocker_id` est le `blockerId` d'une ligne de `blocks.csv` : le replay surligne ce bloqueur, son défenseur et la ligne défenseur → QB. Le replay recalcule les positions depuis les CSV bruts, avec le même temps tenu que `metrics.py` (vérifié).
- L'app importe `load_blocks` et `summarize_blockers` depuis `src.metrics`, et `make_replay` depuis `src.replay`.

### Brancher le replay dans l'app (Partie 3)

```python
from src.metrics import load_blocks, summarize_blockers
from src.replay import make_replay
import streamlit as st

blocks = load_blocks()
ranking = summarize_blockers(blocks[blocks.team == "DAL"], min_duels=10)   # maillon faible en tête
# ... l'utilisateur choisit un bloqueur puis une de ses actions perdues ...
st.plotly_chart(make_replay(game_id, play_id, focus_blocker_id=blocker_id), use_container_width=True)
```

Démo autonome du replay : `streamlit run src/replay/demo_app.py`
Export d'une action en HTML : `python -m src.replay --game 2021090900 --play 2279 --blocker 37082 --open`

## Équipe

- Partie 1 « Données & métrique » : Thibault
- Partie 2 « Replay animé » : Nicolas — replay 2D Plotly (`src/replay/`), branché sur `blocks.csv`
- Partie 3 « App & pitch » : *à compléter*

## Planning du hackathon

- 1:00 : synchro, chaque partie montre sa base
- 2:00 : intégration
- 2:30 : gel du code

## Limites connues

- Les passes rapides gonflent le temps tenu (censure) : comparer les bloqueurs sur `taux_perdu`.
- Le seuil de 2 yards est une convention, et un QB qui se déplace vers un défenseur peut faire « perdre » un duel.
- Un seul défenseur par duel (le premier bloqué selon PFF), sur 8 semaines : petit échantillon par joueur.
- Jeux de passe uniquement.
