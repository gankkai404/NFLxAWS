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
data/                # données brutes Big Data Bowl (non versionnées) : games.csv, plays.csv, players.csv, pffScoutingData.csv, tracking/
data/processed/      # blocks.csv, une ligne par duel (non versionné, à régénérer)
src/metrics.py       # Partie 1 : calcul des duels et de la métrique (CLI + API)
src/replay/          # Partie 2 : replay animé 2D Plotly d'une action (module autonome)
frontend/            # Partie 3 : application Streamlit « Weak Link »
  ├── app.py         #   point d'entrée (streamlit run app.py)
  ├── .streamlit/    #   thème, polices auto-hébergées, static serving
  ├── static/fonts/  #   Archivo + IBM Plex Mono (licence OFL incluse)
  └── weaklink/      #   data, stats, charts, replay, ui, theme, labels, paths
docs/                # documentation de la métrique (metriques.md)
tests/               # tests unitaires pytest
```

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

Le projet se lance en deux temps : générer les duels, puis ouvrir l'application.

```bash
# 1. Générer la métrique à partir des données brutes (une seule fois, ~3-4 min pour les 122 matchs).
#    Écrit data/processed/blocks.csv. Ajouter --max-games 3 pour un essai rapide.
python -m src.metrics --raw data

# 2. Lancer l'application (depuis le dossier frontend/).
cd frontend
streamlit run app.py
```

L'application lit `data/processed/blocks.csv` dès qu'il existe. Tant qu'il n'a pas
été généré, elle démarre en **mode démo** sur les vrais duels PFF (le temps tenu est
alors simulé) et bascule seule sur les vraies données au rechargement suivant.

Tests : `pytest -q`

## Contrats entre les parties

- `data/processed/blocks.csv` : une ligne par duel. Colonnes clés : `gameId`, `playId`, `blockerId`, `blockerName`, `blockerPos`, `team`, `defenderId`, `defenderName`, `temps_tenu`, `perdu`, `pressure_allowed`, `sack_allowed`, `down`, `yardsToGo`, `nb_rushers`, `stunt`, `pff_playAction`, `offenseFormation`, `passResult`, `playDescription`, plus `frame_perdu` pour le replay. Dictionnaire complet : [docs/metriques.md](docs/metriques.md).
- Replay : `from src.replay import make_replay` ; `make_replay(game_id, play_id, focus_blocker_id=None) -> plotly.graph_objects.Figure`. `focus_blocker_id` est le `blockerId` d'une ligne de `blocks.csv` : le replay surligne ce bloqueur, son défenseur et la ligne défenseur → QB. Le replay recalcule les positions depuis les CSV bruts, avec le même temps tenu que `metrics.py` (vérifié).
- L'application (`frontend/`) lit directement `data/processed/blocks.csv` via sa propre couche de chargement (`frontend/weaklink/data.py`) et complète les colonnes de contexte depuis les CSV bruts. Elle dessine son propre replay (terrain clair, dans le style de l'app) à partir du tracking.

### Détails Partie 2 (module autonome)

Le replay 2D de la Partie 2 reste utilisable de façon autonome :

```bash
streamlit run src/replay/demo_app.py                                     # démo Streamlit
python -m src.replay --game 2021090900 --play 2279 --blocker 37082 --open  # export HTML d'une action
```

API : `from src.replay import make_replay` ; `make_replay(game_id, play_id, focus_blocker_id=None) -> plotly.graph_objects.Figure`.

## Équipe

- Partie 1 « Données & métrique » : Thibault
- Partie 2 « Replay animé » : Nicolas — replay 2D Plotly (`src/replay/`), branché sur `blocks.csv`
- Partie 3 « App & pitch » : Daniel

## Planning du hackathon

- 1:00 : synchro, chaque partie montre sa base
- 2:00 : intégration
- 2:30 : gel du code

## Limites connues

- Les passes rapides gonflent le temps tenu (censure) : comparer les bloqueurs sur `taux_perdu`.
- Le seuil de 2 yards est une convention, et un QB qui se déplace vers un défenseur peut faire « perdre » un duel.
- Un seul défenseur par duel (le premier bloqué selon PFF), sur 8 semaines : petit échantillon par joueur.
- Jeux de passe uniquement.
