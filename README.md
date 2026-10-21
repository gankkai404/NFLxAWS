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
src/replay.py        # Partie 2 : replay animé Plotly d'une action
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
- Replay : `make_replay(game_id, play_id, focus_blocker_id=None) -> plotly.graph_objects.Figure` dans `src/replay.py`.
- L'app importe `load_blocks` et `summarize_blockers` depuis `src.metrics`.

## Équipe

- Partie 1 « Données & métrique » : Thibault
- Partie 2 « Replay animé » : *à compléter*
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
