# Requirements Document

## Introduction

Document d'exigences — Weak Link · Partie 1 : Données & métrique.

« Weak Link » est un outil pour coachs NFL développé en hackathon de 3 heures par une équipe de 3 développeurs. Il montre en un écran quel bloqueur de la ligne offensive adverse craque, dans quelles situations, avec un replay animé comme preuve.

Les données proviennent du NFL Big Data Bowl : tracking Next Gen Stats (10 Hz) et scouting PFF, 122 matchs, semaines 1 à 8 de la saison 2021, uniquement des jeux de passe.

Le projet est découpé en trois parties :
1. Données & métrique (objet de ce document) : `src/metrics.py` produit `data/processed/blocks.csv`.
2. Replay animé (coéquipier) : `src/replay.py`, `make_replay(game_id, play_id, focus_blocker_id=None) -> plotly.graph_objects.Figure`.
3. App & pitch (coéquipier) : `app.py` Streamlit qui lit `blocks.csv` et appelle `make_replay()`.

Contrainte de temps : une première version fonctionnelle sur 2-3 matchs en ~45 minutes, au plus simple qui marche, puis consolidation.

**Écart observé dans le workspace (point ouvert)** : le plan suppose les données brutes dans `data/raw/`. Dans le workspace actuel (`/home/thibault/cyber/NFLxAWS`), les fichiers se trouvent dans `data/` : `data/games.csv`, `data/plays.csv`, `data/players.csv`, `data/pffScoutingData.csv` et `data/tracking/tracking_*.csv` (122 fichiers). Les fichiers de données ne doivent pas être modifiés par l'agent. Deux options restent ouvertes et seront tranchées par l'option la plus simple qui fonctionne (voir Exigence 2) : (a) l'utilisateur déplace lui-même les données dans `data/raw/`, ou (b) la CLI est lancée avec `--raw data` et la découverte des fichiers gère cet emplacement. Un `README.md` minimal existe déjà à la racine (contenu : `# NFWxAWS`) ; il sera remplacé par le README complet du projet (Exigence 25).

## Glossary

- **Module_Metrics** : le module Python `src/metrics.py`, qui expose l'API Python et la CLI de la Partie 1.
- **CLI_Metrics** : le point d'entrée en ligne de commande `python -m src.metrics`, implémenté par la fonction `main()` du Module_Metrics.
- **Agent** : l'agent Kiro chargé de réaliser la Partie 1 (exploration, code, tests, documentation, exécution, rapport).
- **Suite_Tests** : le fichier `tests/test_metrics.py`, exécuté par `pytest -q`.
- **Doc_Metriques** : le fichier `docs/metriques.md`.
- **README_Projet** : le fichier `README.md` à la racine du dépôt.
- **Rapport_Final** : le compte rendu remis par l'Agent à la fin de la mission (section 9 du plan).
- **Dossier_Raw** : le dossier des données brutes passé via `--raw` (par défaut `data/raw` selon le plan ; `data` dans le workspace actuel).
- **Fichier_Tracking** : un fichier `tracking_[gameId].csv` (tracking 10 Hz, 1 frame = 0,1 s).
- **Fichier_Blocks** : le fichier de sortie `data/processed/blocks.csv`, une ligne par Duel.
- **Action** : un jeu identifié par le couple (gameId, playId).
- **Duel** : sur une Action, le couple formé par un bloqueur (pff_role = « pass block ») et le défenseur bloqué (pff_nflIdBlockedPlayer non vide).
- **QB** : sur une Action, le joueur avec pff_role = « pass » ; s'il y en a plusieurs, le premier.
- **Frame_Snap** : la première frameId d'une Action dont event appartient à SNAP_EVENTS.
- **Frame_Fin** : la première frameId après la Frame_Snap dont event appartient à END_EVENTS ; à défaut, la dernière frame de l'Action.
- **Fenetre_Duel** : l'ensemble des frames comprises entre la Frame_Snap et la Frame_Fin, bornes incluses.
- **Distance_Def_QB** : sqrt((x_def − x_qb)² + (y_def − y_qb)²), en yards, calculée à chaque frame de la Fenetre_Duel, sans retournement de terrain.
- **SEUIL_PRESSION** : constante seuil de distance, valeur par défaut 2.0 yards, paramétrable.
- **Duel_Perdu** : Duel pour lequel la Distance_Def_QB est strictement inférieure au seuil au moins une fois dans la Fenetre_Duel.
- **Frame_Perdu** : la première frameId de la Fenetre_Duel où la Distance_Def_QB est strictement inférieure au seuil.
- **Duel_Censure** : Duel non perdu ; son temps tenu est borné par la fin de l'Action.
- **SNAP_EVENTS** : constante listant les valeurs d'event considérées comme snap (candidats : ball_snap, autoevent_ballsnap, à confirmer à l'étape 0).
- **END_EVENTS** : constante listant les valeurs d'event considérées comme fin d'Action (candidats : pass_forward, autoevent_passforward, pass_shovel, qb_sack, qb_strip_sack, run…, à confirmer à l'étape 0).
- **CONTRACT_COLUMNS** : constante listant, dans l'ordre, les colonnes du contrat du Fichier_Blocks.
- **Bloc_Validation** : l'affichage de contrôle produit par la CLI_Metrics en fin d'exécution.

## Requirements

### Exigence 1 : Livrables et périmètre des fichiers

**User Story :** En tant que membre de l'équipe, je veux que la Partie 1 produise exactement les livrables prévus, afin que les parties 2 et 3 puissent s'y brancher sans conflit.

#### Critères d'acceptation

1. THE Agent SHALL créer le fichier `src/__init__.py` avec une taille de 0 octet.
2. THE Agent SHALL créer le fichier `src/metrics.py` (Module_Metrics) contenant, dans ce seul fichier, les constantes et fonctions de l'Exigence 5, le calcul des Duels et de la métrique (Exigences 8 à 17), l'API Python (`compute_duels_for_game`, `build_blocks`, `load_blocks`, `summarize_blockers`) et la CLI_Metrics (`main()`, Exigence 21).
3. THE Agent SHALL créer le fichier `tests/test_metrics.py` (Suite_Tests) contenant les tests unitaires de l'Exigence 23, construits sur des données synthétiques définies dans le fichier de test, sans lecture d'aucun fichier du Dossier_Raw.
4. THE Agent SHALL créer le fichier `docs/metriques.md` (Doc_Metriques) contenant toutes les sections exigées par l'Exigence 25.
5. THE Agent SHALL remplacer intégralement le contenu actuel du fichier `README.md` à la racine (`# NFWxAWS`) par le README_Projet décrit à l'Exigence 26, sans conserver l'ancien contenu.
6. THE Agent SHALL créer le fichier `requirements.txt` à la racine, contenant exactement les dépendances listées au critère 1 de l'Exigence 27.
7. THE Agent SHALL créer le fichier `.gitignore` à la racine, contenant les entrées listées au critère 3 de l'Exigence 27 et aucune entrée couvrant `data/processed/`.
8. WHEN la CLI_Metrics est exécutée sans argument `--out`, THE Module_Metrics SHALL générer le Fichier_Blocks au chemin `data/processed/blocks.csv`, en créant le dossier `data/processed/` s'il n'existe pas.
9. THE Agent SHALL limiter les créations et modifications de fichiers aux seuls livrables listés aux critères 1 à 8, à leurs dossiers parents (`src/`, `tests/`, `docs/`, `data/processed/`) et aux artefacts d'exécution correspondant aux entrées du `.gitignore` de l'Exigence 27 autres que `data/raw/` (`.venv/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, `.DS_Store`).
10. THE Agent SHALL laisser `src/replay.py` et `app.py` dans leur état initial en fin de mission : absents s'ils étaient absents au début de la mission, identiques octet pour octet s'ils existaient.
11. THE Agent SHALL laisser les fichiers de données existants sous `data/` au début de la mission (`data/games.csv`, `data/plays.csv`, `data/players.csv`, `data/pffScoutingData.csv` et les 122 Fichier_Tracking de `data/tracking/`) présents au même chemin et identiques octet pour octet en fin de mission, sans modification, déplacement, renommage ni suppression.

### Exigence 2 : Emplacement des données brutes (écart avec le plan)

**User Story :** En tant que développeur, je veux que l'outil trouve les données là où elles sont réellement, afin de pouvoir lancer le calcul sans manipulation fragile.

#### Critères d'acceptation

1. THE CLI_Metrics SHALL accepter l'argument optionnel `--raw` désignant le Dossier_Raw, sous la forme d'un chemin relatif au répertoire courant ou d'un chemin absolu, avec `data/raw` comme valeur par défaut lorsque l'argument est omis.
2. WHEN la CLI_Metrics est lancée depuis la racine du dépôt avec `--raw data`, THE Module_Metrics SHALL charger `games.csv`, `plays.csv`, `players.csv` et `pffScoutingData.csv` directement depuis `data/` et découvrir, via `find_tracking_files` et le motif `**/tracking_*.csv`, les 122 Fichiers_Tracking situés dans `data/tracking/`.
3. IF au moins un des quatre fichiers `games.csv`, `plays.csv`, `players.csv` et `pffScoutingData.csv` est absent du Dossier_Raw (y compris lorsque le Dossier_Raw par défaut `data/raw` n'existe pas), THEN THE CLI_Metrics SHALL afficher, avant tout traitement de match, un message d'erreur indiquant le chemin du Dossier_Raw recherché, le nom de chaque fichier manquant et l'usage de l'argument `--raw` (exemple : `--raw data`).
4. IF au moins un des quatre fichiers attendus est absent du Dossier_Raw, THEN THE CLI_Metrics SHALL se terminer avec un code de sortie non nul sans créer ni modifier le Fichier_Blocks.
5. WHEN l'Agent remet le Rapport_Final, THE Rapport_Final SHALL indiquer l'emplacement prévu (`data/raw/`), l'emplacement observé (`data/`), l'option retenue parmi exactement deux (lancement avec `--raw data`, ou déplacement des données par l'utilisateur dans `data/raw/`) et la commande CLI_Metrics effectivement utilisée pour générer le Fichier_Blocks.
6. THE Module_Metrics SHALL lire les fichiers du Dossier_Raw et les Fichiers_Tracking sans les modifier, les déplacer, les renommer ni les supprimer.

### Exigence 3 : Données d'entrée

**User Story :** En tant que développeur, je veux que les colonnes utilisées soient explicitement identifiées, afin de ne lire que l'utile et de ne jamais inventer de colonne.

#### Critères d'acceptation

1. THE Module_Metrics SHALL lire dans `games.csv` du Dossier_Raw uniquement la colonne gameId, utilisée comme clé de jointure, et les colonnes week, homeTeamAbbr et visitorTeamAbbr, sans lire aucune autre colonne.
2. THE Module_Metrics SHALL lire dans `plays.csv` du Dossier_Raw uniquement les colonnes gameId et playId, utilisées comme clé de jointure (gameId, playId), et les colonnes quarter, down, yardsToGo, possessionTeam, defensiveTeam, passResult, offenseFormation, dropBackType, pff_playAction, pff_passCoverage et playDescription, sans lire aucune autre colonne.
3. THE Module_Metrics SHALL lire dans `players.csv` du Dossier_Raw uniquement la colonne nflId, utilisée comme clé de jointure, et les colonnes displayName et officialPosition, sans lire aucune autre colonne.
4. THE Module_Metrics SHALL lire dans `pffScoutingData.csv` du Dossier_Raw uniquement les colonnes gameId, playId et nflId, utilisées comme clé de jointure (gameId, playId, nflId), et les colonnes pff_role, pff_positionLinedUp, pff_nflIdBlockedPlayer, pff_blockType, pff_hitAllowed, pff_hurryAllowed, pff_sackAllowed, pff_beatenByDefender, pff_hit, pff_hurry et pff_sack, sans lire aucune autre colonne.
5. THE Module_Metrics SHALL lire dans chaque Fichier_Tracking uniquement les 7 colonnes gameId, playId, nflId, frameId, x, y et event, sans lire aucune autre colonne.
6. THE Module_Metrics SHALL référencer, pour chaque fichier d'entrée, uniquement des noms de colonnes figurant dans l'en-tête de ce fichier, en respectant exactement la casse de l'en-tête.
7. IF une colonne listée aux critères 1 à 5 est absente de l'en-tête observé d'un fichier d'entrée lors de l'exploration (Étape 0), THEN THE Agent SHALL remplacer dans le Module_Metrics le nom de cette colonne par le nom de la colonne de l'en-tête observé qui porte la même information.
8. IF une colonne listée aux critères 1 à 5 est absente de l'en-tête observé d'un fichier d'entrée, THEN THE Agent SHALL indiquer dans le Rapport_Final, pour chaque écart, le nom du fichier, le nom de la colonne attendue et le nom de la colonne retenue, ou l'absence de colonne équivalente.

### Exigence 4 : Exploration des données (Étape 0)

**User Story :** En tant que développeur, je veux explorer les données avant de coder, afin de fonder les constantes et les jointures sur des valeurs observées.

#### Critères d'acceptation

1. THE Agent SHALL afficher la liste des noms de fichiers présents dans le Dossier_Raw et dans son sous-dossier `tracking/`, ainsi que le nombre de Fichiers_Tracking (fichiers dont le nom correspond au motif `tracking_*.csv`).
2. THE Agent SHALL afficher, pour chacun des 4 CSV statiques (`games.csv`, `plays.csv`, `players.csv`, `pffScoutingData.csv`), la forme (nombre de lignes, nombre de colonnes), la liste complète des noms de colonnes dans l'ordre du fichier et les 3 premières lignes.
3. THE Agent SHALL afficher, pour les colonnes pff_role et pff_blockType de `pffScoutingData.csv`, chaque valeur unique avec son effectif, valeurs manquantes comprises.
4. THE Agent SHALL afficher, pour la colonne event de 3 Fichiers_Tracking distincts, chaque valeur unique avec son effectif, valeurs manquantes comprises.
5. THE Agent SHALL afficher le nombre de couples (gameId, playId) distincts de `pffScoutingData.csv`, le nombre de ces couples absents de `plays.csv` et, pour les gameId des 3 Fichiers_Tracking explorés au critère 4, le nombre de ces couples absents de ces Fichiers_Tracking.
6. WHEN l'exploration est terminée et avant l'écriture du code de calcul de la métrique, THE Agent SHALL définir SNAP_EVENTS et END_EVENTS dans le Module_Metrics de sorte que chaque constante contienne uniquement les valeurs candidates du glossaire effectivement observées au critère 4.
7. THE Agent SHALL n'inclure dans SNAP_EVENTS et END_EVENTS aucune valeur d'event absente des effectifs affichés au critère 4.
8. IF aucune valeur candidate de SNAP_EVENTS ou aucune valeur candidate de END_EVENTS n'est observée dans les 3 Fichiers_Tracking explorés, THEN THE Agent SHALL signaler dans le Rapport_Final la constante concernée et les valeurs d'event observées.
9. THE Agent SHALL réaliser l'exploration au moyen d'un script jetable ou par exécution directe de code, sans ajouter de fichier d'exploration aux livrables du dépôt et sans modifier les fichiers du Dossier_Raw.

### Exigence 5 : Squelette du module et constantes (Étape 1)

**User Story :** En tant que développeur, je veux un module structuré en fonctions pures et testables, afin de pouvoir le tester et l'importer depuis l'app.

#### Critères d'acceptation

1. THE Module_Metrics SHALL être importable sans erreur sous Python 3.10 ou toute version supérieure, et chacune des 8 fonctions publiques citées aux critères 3 à 10 SHALL porter une annotation de type sur chacun de ses paramètres et sur sa valeur de retour, ainsi qu'une docstring non vide rédigée en français.
2. THE Module_Metrics SHALL définir au niveau du module les constantes `FPS = 10` (entier), `SEUIL_PRESSION = 2.0` (flottant, en yards), `SNAP_EVENTS` et `END_EVENTS` (chacune une collection non vide de chaînes de caractères correspondant à des valeurs de la colonne event), et `CONTRACT_COLUMNS` (liste ordonnée de noms de colonnes sous forme de chaînes, sans doublon).
3. THE Module_Metrics SHALL exposer la fonction `load_static(raw_dir: Path) -> dict[str, pd.DataFrame]`, avec exactement ce nom, ce paramètre et ce type de retour.
4. THE Module_Metrics SHALL exposer la fonction `find_tracking_files(raw_dir: Path) -> list[Path]`, avec exactement ce nom, ce paramètre et ce type de retour.
5. THE Module_Metrics SHALL exposer la fonction `play_frames(tracking: pd.DataFrame) -> pd.DataFrame`, avec exactement ce nom, ce paramètre et ce type de retour.
6. THE Module_Metrics SHALL exposer la fonction `compute_duels_for_game(tracking, plays, scouting, players, games, seuil=SEUIL_PRESSION) -> pd.DataFrame`, avec les paramètres dans cet ordre et la valeur par défaut de seuil égale à SEUIL_PRESSION.
7. THE Module_Metrics SHALL exposer la fonction `build_blocks(raw_dir, seuil=SEUIL_PRESSION, max_games=None) -> pd.DataFrame`, avec les paramètres dans cet ordre, la valeur par défaut de seuil égale à SEUIL_PRESSION et la valeur par défaut de max_games égale à None.
8. THE Module_Metrics SHALL exposer la fonction `load_blocks(path="data/processed/blocks.csv") -> pd.DataFrame`, avec la valeur par défaut de path égale à "data/processed/blocks.csv".
9. THE Module_Metrics SHALL exposer la fonction `summarize_blockers(blocks, min_duels=20) -> pd.DataFrame`, avec les paramètres dans cet ordre et la valeur par défaut de min_duels égale à 20.
10. THE Module_Metrics SHALL exposer la fonction `main()`, sans paramètre obligatoire, servant de point d'entrée à la CLI_Metrics et invoquée uniquement lorsque le module est exécuté via `python -m src.metrics`.
11. WHEN le Module_Metrics est importé (`import src.metrics`), THE Module_Metrics SHALL n'exécuter ni `main()`, ni lecture de fichier de données, ni écriture du Fichier_Blocks.
12. WHEN `play_frames`, `compute_duels_for_game` ou `summarize_blockers` est appelée, THE Module_Metrics SHALL laisser inchangés (mêmes colonnes, mêmes lignes, mêmes valeurs) les DataFrames reçus en argument et SHALL n'effectuer aucune lecture ni écriture de fichier.

### Exigence 6 : Chargement et normalisation des données statiques

**User Story :** En tant que développeur, je veux des données statiques chargées avec des types et une casse homogènes, afin d'éviter les pièges connus du jeu de données.

#### Critères d'acceptation

1. WHEN `load_static` est appelée avec un Dossier_Raw, THE Module_Metrics SHALL retourner un dictionnaire contenant exactement les 4 clés « games », « plays », « players » et « pffScoutingData », chacune associée au DataFrame lu depuis le fichier CSV de même nom (`games.csv`, `plays.csv`, `players.csv`, `pffScoutingData.csv`) du Dossier_Raw, avec les colonnes définies à l'Exigence 3.
2. WHEN `load_static` charge le scouting, THE Module_Metrics SHALL normaliser chaque valeur non vide de pff_role en supprimant d'abord les espaces de début et de fin, puis en la convertissant en minuscules (exemple : «  Pass Block » devient « pass block »), les valeurs absentes restant absentes.
3. WHEN `load_static` charge le scouting, THE Module_Metrics SHALL convertir pff_nflIdBlockedPlayer en type pandas Int64 nullable, chaque valeur non vide devenant l'entier égal à l'identifiant d'origine et chaque valeur vide devenant une valeur manquante (pd.NA).
4. WHEN `load_static` charge le scouting, THE Module_Metrics SHALL remplacer par 0 les valeurs NaN des 7 indicateurs PFF 0/1 pff_hitAllowed, pff_hurryAllowed, pff_sackAllowed, pff_beatenByDefender, pff_hit, pff_hurry et pff_sack, en conservant inchangées les valeurs 0 et 1 existantes, de sorte qu'aucune valeur NaN ne subsiste dans ces 7 colonnes.
5. WHEN un Fichier_Tracking est lu, THE Module_Metrics SHALL convertir chaque valeur non vide de la colonne event en minuscules (exemple : « BALL_SNAP » devient « ball_snap »), les valeurs absentes restant absentes, avant toute comparaison avec SNAP_EVENTS et END_EVENTS.
6. WHEN un Fichier_Tracking est lu, THE Module_Metrics SHALL exclure de toute jointure sur nflId les lignes du ballon, identifiées par une valeur nflId absente (lignes correspondant à team == "football" dans le fichier brut), de sorte qu'aucune ligne issue d'une jointure sur nflId ne comporte un nflId absent.

### Exigence 7 : Découverte des fichiers de tracking

**User Story :** En tant que développeur, je veux que les fichiers de tracking soient trouvés quel que soit le sous-dossier, afin de ne pas dépendre d'une arborescence précise.

#### Critères d'acceptation

1. WHEN `find_tracking_files(raw_dir)` est appelée, THE Module_Metrics SHALL retourner une `list[Path]` contenant tous les fichiers correspondant au motif `**/tracking_*.csv` sous le Dossier_Raw, à n'importe quelle profondeur de sous-dossier (y compris directement à la racine du Dossier_Raw), chaque fichier apparaissant exactement une fois et aucun fichier ne correspondant pas au motif (notamment `games.csv`, `plays.csv`, `players.csv`, `pffScoutingData.csv`) n'étant inclus.
2. WHEN `find_tracking_files` retourne sa liste, THE Module_Metrics SHALL ordonner les chemins par ordre lexicographique croissant, de sorte que deux appels successifs sur le même Dossier_Raw retournent la même liste dans le même ordre.
3. WHEN `find_tracking_files` est appelée avec le Dossier_Raw `data` du workspace actuel (Fichiers_Tracking situés dans `data/tracking/`), THE Module_Metrics SHALL retourner exactement 122 Fichiers_Tracking, le premier élément étant `data/tracking/tracking_2021090900.csv`.
4. IF aucun fichier correspondant au motif `**/tracking_*.csv` n'est trouvé sous le Dossier_Raw (y compris lorsque le Dossier_Raw n'existe pas), THEN THE Module_Metrics SHALL lever une exception dont le message contient le chemin du Dossier_Raw parcouru, au lieu de retourner une liste vide.

### Exigence 8 : Frames de snap et de fin

**User Story :** En tant qu'analyste, je veux une fenêtre temporelle précise pour chaque action, afin de mesurer le duel entre le snap et la fin de l'action.

#### Critères d'acceptation

1. WHEN `play_frames` est appelée avec un DataFrame de tracking, THE Module_Metrics SHALL retourner un DataFrame contenant exactement les colonnes gameId, playId, frame_snap et frame_fin, avec une et une seule ligne par Action du tracking contenant au moins un event de SNAP_EVENTS, quel que soit le nombre de lignes (joueurs et ballon) par frame.
2. WHEN `play_frames` détermine frame_snap, THE Module_Metrics SHALL définir frame_snap comme la Frame_Snap de l'Action, c'est-à-dire la plus petite frameId de l'Action dont l'event, converti en minuscules, appartient à SNAP_EVENTS.
3. WHEN une Action contient au moins un event de END_EVENTS sur une frameId strictement supérieure à la Frame_Snap, THE Module_Metrics SHALL définir frame_fin comme la plus petite de ces frameId, un event de END_EVENTS situé sur la Frame_Snap elle-même ou avant elle n'étant pas pris en compte.
4. IF une Action ne contient aucun event de END_EVENTS sur une frameId strictement supérieure à la Frame_Snap, THEN THE Module_Metrics SHALL définir frame_fin comme la plus grande frameId présente dans le tracking de l'Action.
5. IF une Action ne contient aucun event de SNAP_EVENTS, THEN THE Module_Metrics SHALL exclure l'Action du DataFrame retourné par `play_frames` et inclure dans les logs le nombre d'Actions ignorées pour absence de snap.
6. THE Module_Metrics SHALL produire, pour chaque ligne retournée par `play_frames`, des valeurs entières frame_snap et frame_fin vérifiant frame_snap ≤ frame_fin (invariant).
7. IF la valeur event d'une ligne du tracking est vide, THEN THE Module_Metrics SHALL considérer que cette ligne ne contient aucun event de SNAP_EVENTS ni de END_EVENTS.

### Exigence 9 : Identification du QB

**User Story :** En tant qu'analyste, je veux identifier le quarterback de chaque action, afin de mesurer la distance des défenseurs à la cible de la pression.

#### Critères d'acceptation

1. THE Module_Metrics SHALL identifier le QB d'une Action comme le nflId d'une ligne du scouting de cette Action (même couple gameId, playId) dont pff_role, normalisé selon l'Exigence 6 critère 2 (espaces de début et de fin supprimés, minuscules), est strictement égal à « pass ». Les valeurs « Pass » ou «  pass  » correspondent donc, et les valeurs « pass block » et « pass rush » ne correspondent pas.
2. WHEN au moins 2 lignes du scouting d'une Action ont pff_role normalisé égal à « pass », THE Module_Metrics SHALL retenir comme QB le nflId de la première de ces lignes dans l'ordre d'apparition du fichier `pffScoutingData.csv`, et un seul QB par Action.
3. IF aucune ligne du scouting d'une Action n'a pff_role normalisé égal à « pass », THEN THE Module_Metrics SHALL ignorer l'Action en ne produisant aucun Duel de cette Action dans le Fichier_Blocks, et SHALL continuer le traitement des autres Actions du même match.
4. IF une Action est ignorée faute de QB (critère 3), THEN THE Module_Metrics SHALL comptabiliser cette Action une seule fois dans les logs comme Action ignorée, et ce décompte SHALL être inclus dans le nombre d'actions ignorées de la ligne de progression du match (Exigence 21, critère 3).
5. WHEN le QB d'une Action est identifié, THE Module_Metrics SHALL utiliser les coordonnées x et y de ce seul QB pour calculer la Distance_Def_QB de tous les Duels de l'Action.

### Exigence 10 : Identification des duels

**User Story :** En tant qu'analyste, je veux la liste des duels bloqueur/défenseur, afin d'évaluer chaque bloqueur individuellement.

#### Critères d'acceptation

1. THE Module_Metrics SHALL constituer exactement un Duel par ligne du scouting dont pff_role normalisé (minuscules, espaces de début et de fin supprimés, cf. Exigence 6) vaut exactement « pass block » et dont pff_nflIdBlockedPlayer est non nul, en conservant les valeurs gameId et playId de cette ligne pour identifier l'Action du Duel.
2. WHEN les Duels sont constitués, THE Module_Metrics SHALL renommer nflId en blockerId et pff_nflIdBlockedPlayer en defenderId, en conservant leurs valeurs inchangées, de sorte qu'aucune colonne nommée nflId ni pff_nflIdBlockedPlayer ne subsiste dans la table des Duels.
3. WHEN pff_role vaut « Pass Block » dans le fichier source, ou toute variante de casse ou d'espaces de début et de fin de « pass block » (par exemple « PASS BLOCK », « pass block »), et que pff_nflIdBlockedPlayer est non nul, THE Module_Metrics SHALL détecter le Duel correspondant.
4. IF une ligne du scouting a un pff_role normalisé différent de « pass block » (y compris « pass », « pass rush » ou une valeur nulle), ou un pff_nflIdBlockedPlayer nul, THEN THE Module_Metrics SHALL exclure cette ligne de la table des Duels.

### Exigence 11 : Distance défenseur↔QB et perte du duel

**User Story :** En tant que coach, je veux savoir si et quand un bloqueur a laissé passer son défenseur près du QB, afin de repérer le maillon faible.

#### Critères d'acceptation

1. THE Module_Metrics SHALL extraire les positions du QB en sélectionnant, dans le Fichier_Tracking, les lignes dont nflId est égal au nflId du QB de l'Action et dont frameId appartient à la Fenetre_Duel (Frame_Snap et Frame_Fin incluses), avec exactement les colonnes gameId, playId, frameId, qb_x (= x du QB) et qb_y (= y du QB), à raison d'au plus une ligne par (gameId, playId, frameId).
2. THE Module_Metrics SHALL joindre les Duels au tracking sur (gameId, playId, defenderId = nflId), conserver uniquement les frames de la Fenetre_Duel (Frame_Snap et Frame_Fin incluses), puis joindre le résultat aux positions du QB sur (gameId, playId, frameId), seules les frames disposant à la fois d'une position du défenseur et d'une position du QB étant retenues pour le calcul de la Distance_Def_QB.
3. THE Module_Metrics SHALL calculer la Distance_Def_QB, en yards, à chaque frame retenue de la Fenetre_Duel avec `np.hypot(x_def − qb_x, y_def − qb_y)`, sans arrondi au niveau de la frame.
4. THE Module_Metrics SHALL calculer, pour chaque Duel, une seule valeur dist_min, en yards, égale au minimum de la Distance_Def_QB sur l'ensemble des frames retenues de la Fenetre_Duel de ce Duel.
5. IF la Distance_Def_QB non arrondie d'un Duel est strictement inférieure au seuil sur au moins une frame retenue de la Fenetre_Duel, THEN THE Module_Metrics SHALL marquer le Duel avec perdu = True et frame_perdu = la Frame_Perdu, frame_perdu étant une frameId entière comprise entre frame_snap et frame_fin, bornes incluses.
6. IF la Distance_Def_QB non arrondie d'un Duel est supérieure ou égale au seuil sur toutes les frames retenues de la Fenetre_Duel (y compris une distance exactement égale au seuil), THEN THE Module_Metrics SHALL marquer le Duel avec perdu = False et frame_perdu = valeur manquante, écrite comme cellule vide dans le Fichier_Blocks.
7. THE Module_Metrics SHALL utiliser comme seuil, exprimé en yards, la valeur du paramètre `seuil` de `compute_duels_for_game` (et de `build_blocks`), égale à SEUIL_PRESSION (2.0 yards) par défaut, et appliquer cette même valeur à tous les Duels traités par un même appel.
8. THE Module_Metrics SHALL calculer la Distance_Def_QB sur les colonnes x et y telles que lues dans le Fichier_Tracking, sans retournement de terrain ni autre transformation selon le sens du jeu.
9. FOR ALL Duels, THE Module_Metrics SHALL produire perdu = True si et seulement si dist_min, avant l'arrondi à 2 décimales de l'Exigence 12, est strictement inférieure au seuil (invariant).

### Exigence 12 : Temps tenu, durée de l'action et censure

**User Story :** En tant que coach, je veux savoir combien de temps chaque bloqueur a tenu, afin de comparer la solidité des bloqueurs.

#### Critères d'acceptation

1. IF un Duel est un Duel_Perdu (perdu = True), THEN THE Module_Metrics SHALL calculer temps_tenu, exprimé en secondes, comme (frame_perdu − frame_snap) / FPS, où frame_perdu est la Frame_Perdu et frame_snap la Frame_Snap de l'Action, avec FPS = 10 (exemple : frame_snap = 6 et frame_perdu = 31 donnent temps_tenu = 2.5).
2. IF un Duel n'est pas un Duel_Perdu (perdu = False), THEN THE Module_Metrics SHALL traiter le Duel comme Duel_Censure en calculant temps_tenu, exprimé en secondes, comme (frame_fin − frame_snap) / FPS, où frame_fin est la Frame_Fin de l'Action, de sorte que temps_tenu soit égal à duree_action pour ce Duel.
3. THE Module_Metrics SHALL calculer duree_action, exprimée en secondes, comme (frame_fin − frame_snap) / FPS pour chaque Duel, avec la même valeur pour tous les Duels d'une même Action.
4. THE Module_Metrics SHALL arrondir à 2 décimales les valeurs de temps_tenu, duree_action et dist_min écrites dans le Fichier_Blocks, l'arrondi s'appliquant uniquement aux valeurs restituées et non à la comparaison de la Distance_Def_QB au seuil qui détermine perdu et frame_perdu.
5. THE Module_Metrics SHALL produire, pour chaque Duel du Fichier_Blocks, des valeurs arrondies vérifiant 0 ≤ temps_tenu ≤ duree_action (invariant), l'égalité temps_tenu = 0 étant valide lorsque la Frame_Perdu est égale à la Frame_Snap et l'égalité duree_action = 0 étant valide lorsque la Frame_Fin est égale à la Frame_Snap.

### Exigence 13 : Enrichissement du contexte

**User Story :** En tant que coach, je veux le contexte de chaque duel, afin de filtrer par situation (down, stunt, play action, formation…).

#### Critères d'acceptation

1. THE Module_Metrics SHALL renseigner blockerName avec le displayName de la ligne de `players.csv` dont nflId est égal à blockerId, et defenderName avec le displayName de la ligne de `players.csv` dont nflId est égal à defenderId.
2. THE Module_Metrics SHALL renseigner blockerPos avec le pff_positionLinedUp de la ligne du scouting de clé (gameId, playId, nflId = blockerId) et defenderPos avec le pff_positionLinedUp de la ligne du scouting de clé (gameId, playId, nflId = defenderId).
3. THE Module_Metrics SHALL renseigner team avec possessionTeam et defenseTeam avec defensiveTeam de la ligne de `plays.csv` de même clé (gameId, playId) que le Duel.
4. THE Module_Metrics SHALL renseigner quarter, down, yardsToGo, passResult, offenseFormation, dropBackType, pff_playAction, pff_passCoverage et playDescription avec les valeurs, non transformées, de la ligne de `plays.csv` de même clé (gameId, playId) que le Duel.
5. THE Module_Metrics SHALL renseigner week avec la valeur de la ligne de `games.csv` de même gameId que le Duel.
6. THE Module_Metrics SHALL calculer nb_rushers comme le nombre entier (≥ 0) de lignes du scouting de l'Action (gameId, playId) dont pff_role normalisé vaut « pass rush », et attribuer cette même valeur à tous les Duels de l'Action.
7. THE Module_Metrics SHALL marquer stunt = True pour tous les Duels d'une Action dont au moins une ligne du scouting de l'Action a pff_blockType exactement égal à "SW", et stunt = False pour tous les Duels d'une Action dont aucune ligne du scouting n'a pff_blockType égal à "SW" (les valeurs pff_blockType vides ne comptant pas comme "SW").
8. THE Module_Metrics SHALL renseigner blockType avec le pff_blockType de la ligne du scouting de clé (gameId, playId, nflId = blockerId), laissé vide si cette valeur est absente.
9. WHEN l'enrichissement du contexte est appliqué, THE Module_Metrics SHALL conserver exactement le même nombre de Duels qu'avant l'enrichissement, sans en supprimer ni en dupliquer aucun.
10. IF aucune ligne correspondante n'existe dans `players.csv`, `plays.csv` ou `games.csv` pour la clé d'un Duel, THEN THE Module_Metrics SHALL conserver le Duel et laisser vides les colonnes de contexte issues de ce fichier.

### Exigence 14 : Indicateurs PFF

**User Story :** En tant qu'analyste, je veux les indicateurs PFF à côté de la métrique, afin de valider la métrique contre une référence externe.

#### Critères d'acceptation

1. THE Module_Metrics SHALL calculer, pour chaque Duel, pressure_allowed = True si au moins une des valeurs pff_hitAllowed, pff_hurryAllowed ou pff_sackAllowed de la ligne du scouting du bloqueur (clé gameId, playId, nflId = blockerId) est égale à 1, et pressure_allowed = False sinon, une valeur NaN étant traitée comme 0.
2. THE Module_Metrics SHALL calculer, pour chaque Duel, sack_allowed = True si pff_sackAllowed de la ligne du scouting du bloqueur (clé gameId, playId, nflId = blockerId) est égal à 1, et sack_allowed = False sinon, une valeur NaN étant traitée comme 0.
3. THE Module_Metrics SHALL calculer, pour chaque Duel, beaten_by_defender = True si pff_beatenByDefender de la ligne du scouting du bloqueur (clé gameId, playId, nflId = blockerId) est égal à 1, et beaten_by_defender = False sinon, une valeur NaN étant traitée comme 0.
4. THE Module_Metrics SHALL calculer pressure_allowed, sack_allowed et beaten_by_defender uniquement à partir des colonnes PFF du scouting, de sorte que leurs valeurs restent identiques quelle que soit la valeur du paramètre `seuil` et quelle que soit la valeur de perdu.

### Exigence 15 : Données manquantes dans le tracking

**User Story :** En tant que développeur, je veux que les duels incomplets soient écartés de façon traçable, afin que la sortie reste fiable sans masquer les pertes.

#### Critères d'acceptation

1. IF le tracking de l'Action ne contient, sur la Fenetre_Duel, aucune ligne dont nflId est égal au defenderId d'un Duel, THEN THE Module_Metrics SHALL exclure ce Duel du Fichier_Blocks, conserver les autres Duels de la même Action, poursuivre le traitement du match sans lever d'exception, et ajouter 1 au nombre de Duels ignorés comptabilisé dans les logs pour le gameId du match.
2. IF le tracking de l'Action ne contient, sur la Fenetre_Duel, aucune ligne dont nflId est égal au nflId du QB, THEN THE Module_Metrics SHALL exclure tous les Duels de cette Action du Fichier_Blocks, poursuivre le traitement des autres Actions du match sans lever d'exception, et ajouter le nombre de Duels de cette Action au nombre de Duels ignorés comptabilisé dans les logs pour le gameId du match.
3. IF le défenseur ou le QB d'un Duel n'est présent dans le tracking que sur une partie des frames de la Fenetre_Duel, THEN THE Module_Metrics SHALL conserver le Duel et calculer dist_min, perdu et frame_perdu sur les seules frames où le défenseur et le QB sont tous deux présents, frame_snap et frame_fin restant celles retournées par `play_frames`.
4. FOR ALL matchs traités, THE Module_Metrics SHALL produire dans le Fichier_Blocks un nombre de lignes pour ce gameId égal au nombre de Duels constitués (Exigence 10) sur les Actions non ignorées (Exigence 8 critère 5, Exigence 9 critère 3), moins le nombre de Duels ignorés aux critères 1 et 2 (invariant).

### Exigence 16 : Calcul vectorisé et performance

**User Story :** En tant que membre de l'équipe, je veux un calcul rapide, afin de pouvoir régénérer la sortie pendant le hackathon.

#### Critères d'acceptation

1. THE Module_Metrics SHALL implémenter `compute_duels_for_game` uniquement par merges et groupby (complétés d'opérations pandas vectorisées sur colonnes entières : filtres, colonnes calculées comme la Distance_Def_QB), sans aucune boucle `for`/`while`, compréhension, `iterrows`, `itertuples` ni `apply` ligne à ligne qui itère sur les frames ou sur les Duels ; la boucle sur les Fichiers_Tracking de `build_blocks` (Exigence 17) n'est pas concernée par cette restriction.
2. THE Module_Metrics SHALL sélectionner les colonnes au moment de la lecture de chaque fichier d'entrée (`games.csv`, `plays.csv`, `players.csv`, `pffScoutingData.csv`, chaque Fichier_Tracking), en ne lisant que les colonnes utilisées par au moins un calcul du Module_Metrics (jointures, Frame_Snap, Frame_Fin, Fenetre_Duel, Distance_Def_QB, Duel_Perdu, Frame_Perdu) ou recopiées dans une colonne de CONTRACT_COLUMNS.
3. WHEN la CLI_Metrics traite les 122 Fichiers_Tracking d'un Dossier_Raw valide sans `--max-games`, THE CLI_Metrics SHALL terminer en moins de 5 minutes (objectif), durée mesurée en temps écoulé entre le lancement de la commande et la fin de l'affichage du Bloc_Validation, écriture du Fichier_Blocks incluse.
4. IF l'exécution de la CLI_Metrics sur les 122 matchs dépasse 5 minutes, THEN THE Agent SHALL indiquer dans le Rapport_Final le temps mesuré et le dépassement de l'objectif, sans que ce dépassement bloque la génération du Fichier_Blocks.

### Exigence 17 : Construction de la table des duels

**User Story :** En tant que développeur, je veux une fonction unique qui construit tous les duels, afin de l'appeler depuis la CLI ou depuis Python.

#### Critères d'acceptation

1. WHEN `build_blocks(raw_dir, ...)` est appelée, THE Module_Metrics SHALL appeler `find_tracking_files(raw_dir)`, puis appeler `compute_duels_for_game` une fois par Fichier_Tracking retenu, dans l'ordre de la liste triée retournée par `find_tracking_files`, en lui passant le tracking lu depuis ce fichier et les DataFrames plays, pffScoutingData (scouting), players et games retournés par `load_static(raw_dir)`.
2. WHERE `max_games` est un entier supérieur ou égal à 1, THE Module_Metrics SHALL traiter uniquement les min(`max_games`, N) premiers Fichiers_Tracking de la liste triée retournée par `find_tracking_files`, N étant le nombre de Fichiers_Tracking trouvés sous le Dossier_Raw.
3. WHEN `build_blocks` est appelée, THE Module_Metrics SHALL transmettre à chaque appel de `compute_duels_for_game` la valeur du paramètre `seuil` reçue, ou SEUIL_PRESSION (2.0 yards) lorsque `seuil` n'est pas renseigné.
4. WHERE `max_games` vaut None (valeur par défaut), THE Module_Metrics SHALL traiter les N Fichiers_Tracking retournés par `find_tracking_files`.
5. WHEN tous les Fichiers_Tracking retenus ont été traités, THE Module_Metrics SHALL retourner un unique DataFrame égal à la concaténation, dans l'ordre de traitement des fichiers, des résultats de `compute_duels_for_game`, dont le nombre de lignes est égal à la somme des nombres de lignes de ces résultats et dont les colonnes suivent l'ordre de CONTRACT_COLUMNS, y compris lorsque ce nombre de lignes vaut 0.
6. IF `find_tracking_files` lève une erreur parce qu'aucun Fichier_Tracking n'est trouvé, THEN THE Module_Metrics SHALL propager cette erreur, qui indique le Dossier_Raw parcouru, sans retourner de DataFrame.

### Exigence 18 : Contrat de sortie data/processed/blocks.csv

**User Story :** En tant que coéquipier des parties 2 et 3, je veux un contrat de colonnes stable, afin de brancher l'app et le replay sans adaptation.

#### Critères d'acceptation

1. THE Fichier_Blocks SHALL contenir exactement une ligne par Duel retenu, c'est-à-dire par Duel non ignoré au titre des Exigences 8, 9 et 15, sans doublon sur le quadruplet (gameId, playId, blockerId, defenderId).
2. THE Fichier_Blocks SHALL contenir les 20 colonnes obligatoires gameId, playId, blockerId, blockerName, blockerPos, team, defenderId, defenderName, temps_tenu, perdu, pressure_allowed, sack_allowed, down, yardsToGo, nb_rushers, stunt, pff_playAction, offenseFormation, passResult et playDescription, avec ces noms exacts (casse comprise).
3. THE Fichier_Blocks SHALL contenir les 13 colonnes additionnelles week, quarter, defenseTeam, defenderPos, blockType, beaten_by_defender, frame_snap, frame_fin, frame_perdu, duree_action, dist_min, dropBackType et pff_passCoverage, avec ces noms exacts (casse comprise).
4. THE Module_Metrics SHALL typer en entiers non nullables les 11 colonnes gameId, playId, week, quarter, down, yardsToGo, nb_rushers, blockerId, defenderId, frame_snap et frame_fin, et les écrire dans le Fichier_Blocks sans partie décimale (par exemple 2021091200 et non 2021091200.0), y compris defenderId issu de pff_nflIdBlockedPlayer.
5. THE Module_Metrics SHALL typer frame_perdu en Int64 nullable et l'écrire dans le Fichier_Blocks sans partie décimale lorsqu'il est renseigné.
6. THE Module_Metrics SHALL typer en floats les 3 colonnes temps_tenu, duree_action et dist_min, chaque valeur étant égale à la valeur calculée arrondie à 2 décimales et écrite avec au plus 2 chiffres après le séparateur décimal.
7. THE Module_Metrics SHALL typer en booléens les 6 colonnes perdu, pressure_allowed, sack_allowed, beaten_by_defender, stunt et pff_playAction, écrites True ou False dans le Fichier_Blocks, pff_playAction valant True lorsque la valeur source de `plays.csv` vaut 1 et False lorsqu'elle vaut 0.
8. THE Module_Metrics SHALL typer en chaînes les 12 colonnes du contrat non citées aux critères 4 à 7 : blockerName, blockerPos, team, defenderName, offenseFormation, passResult, playDescription, defenseTeam, defenderPos, blockType, dropBackType et pff_passCoverage.
9. THE Module_Metrics SHALL renseigner team avec l'équipe du bloqueur, c'est-à-dire la valeur possessionTeam de l'Action dans `plays.csv`, identique pour tous les Duels d'une même Action (gameId, playId).
10. THE Module_Metrics SHALL écrire le Fichier_Blocks avec une ligne d'en-tête, sans colonne d'index, et avec exactement les colonnes de CONTRACT_COLUMNS dans l'ordre de CONTRACT_COLUMNS, CONTRACT_COLUMNS contenant les 33 colonnes des critères 2 et 3 et aucune autre.
11. THE Fichier_Blocks SHALL contenir zéro valeur manquante (cellule vide ou NaN) dans chacune des 32 colonnes du contrat autres que frame_perdu.
12. IF perdu = False pour un Duel, THEN THE Module_Metrics SHALL laisser frame_perdu vide pour ce Duel (cellule vide dans le Fichier_Blocks).
13. WHEN perdu = True pour un Duel, THE Module_Metrics SHALL renseigner frame_perdu avec la Frame_Perdu du Duel, valeur entière vérifiant frame_snap ≤ frame_perdu ≤ frame_fin.

### Exigence 19 : Relecture de la sortie (load_blocks)

**User Story :** En tant que coéquipier de la partie 3, je veux relire blocks.csv avec les bons types, afin de filtrer directement dans l'app.

#### Critères d'acceptation

1. WHEN `load_blocks` est appelée avec un argument `path`, THE Module_Metrics SHALL lire le Fichier_Blocks situé à ce chemin et retourner un `pd.DataFrame` ; WHEN `load_blocks` est appelée sans argument, THE Module_Metrics SHALL lire `data/processed/blocks.csv`, chemin résolu relativement au répertoire de travail courant.
2. WHEN `load_blocks` lit le Fichier_Blocks, THE Module_Metrics SHALL retourner un DataFrame dont les colonnes sont exactement celles de CONTRACT_COLUMNS, dans le même ordre, avec une ligne par ligne de données du Fichier_Blocks, dans l'ordre du fichier.
3. WHEN `load_blocks` lit le Fichier_Blocks, THE Module_Metrics SHALL restituer pour chaque colonne le type défini à l'Exigence 18 : type booléen (valeurs True/False, et non chaînes « True »/« False ») pour perdu, pressure_allowed, sack_allowed, beaten_by_defender, stunt et pff_playAction ; type entier non nullable pour gameId, playId, week, quarter, down, yardsToGo, nb_rushers, blockerId, defenderId, frame_snap et frame_fin ; type Int64 nullable pour frame_perdu ; type float pour temps_tenu, duree_action et dist_min ; type chaîne pour toutes les autres colonnes du contrat.
4. WHEN `load_blocks` lit une ligne dont frame_perdu est vide dans le Fichier_Blocks, THE Module_Metrics SHALL restituer frame_perdu comme valeur manquante du type Int64 (et non 0 ni chaîne vide), la colonne frame_perdu conservant le type Int64.
5. WHEN une table de Duels conforme à l'Exigence 18 (colonnes, ordre CONTRACT_COLUMNS, types, floats arrondis à 2 décimales, valeurs manquantes uniquement dans frame_perdu) est écrite dans le Fichier_Blocks puis relue avec `load_blocks`, THE Module_Metrics SHALL retourner une table identique à la table d'origine : mêmes noms de colonnes dans le même ordre, mêmes types par colonne, même nombre de lignes dans le même ordre, mêmes valeurs cellule par cellule (floats égaux à 2 décimales, valeurs manquantes de frame_perdu aux mêmes positions) (propriété aller-retour).
6. IF le Fichier_Blocks ne contient que la ligne d'en-tête (0 Duel), THEN THE Module_Metrics SHALL retourner un DataFrame de 0 ligne possédant les colonnes de CONTRACT_COLUMNS dans l'ordre et les types définis au critère 3.
7. IF aucun fichier n'existe au chemin passé à `load_blocks`, THEN THE Module_Metrics SHALL lever une erreur indiquant le chemin introuvable, sans retourner de DataFrame et sans créer de fichier.

### Exigence 20 : Classement des bloqueurs (summarize_blockers, Étape 4)

**User Story :** En tant que coach, je veux un classement des bloqueurs d'une équipe, afin de voir d'un coup d'œil qui craque le plus.

#### Critères d'acceptation

1. WHEN `summarize_blockers(blocks, min_duels=20)` est appelée, THE Module_Metrics SHALL regrouper les lignes de `blocks` (une ligne = un Duel) par le triplet (team, blockerId, blockerName) et retourner un DataFrame contenant une ligne par groupe, avec les colonnes team, blockerId et blockerName.
2. THE Module_Metrics SHALL produire pour chaque groupe les colonnes blockerPos, n_duels, n_perdus, taux_perdu, temps_tenu_moyen, temps_avant_defaite_median, pressions_accordees, taux_pression et sacks_accordes, où n_duels est le nombre de Duels du groupe, n_perdus le nombre de Duels du groupe avec perdu = True, taux_perdu = n_perdus / n_duels, temps_tenu_moyen la moyenne de temps_tenu sur tous les Duels du groupe (Duels perdus et Duel_Censure compris) et taux_pression = pressions_accordees / n_duels.
3. THE Module_Metrics SHALL calculer temps_avant_defaite_median comme la médiane de temps_tenu sur les seuls Duels du groupe avec perdu = True, les Duel_Censure étant exclus de ce calcul.
4. THE Module_Metrics SHALL calculer pressions_accordees comme le nombre de Duels du groupe avec pressure_allowed = True (somme de pressure_allowed) et sacks_accordes comme le nombre de Duels du groupe avec sack_allowed = True (somme de sack_allowed).
5. THE Module_Metrics SHALL conserver uniquement les groupes dont n_duels ≥ min_duels, un groupe avec n_duels exactement égal à min_duels étant conservé, avec min_duels = 20 par défaut.
6. THE Module_Metrics SHALL trier le résultat par taux_perdu décroissant puis, à taux_perdu égal, par taux_pression décroissant.
7. WHEN `summarize_blockers` reçoit une table de Duels déjà filtrée (par exemple sur team, down ou tout autre colonne du Fichier_Blocks), THE Module_Metrics SHALL calculer toutes les colonnes du classement et appliquer le filtre min_duels sur ce seul sous-ensemble de Duels.
8. FOR ALL groupes du résultat, THE Module_Metrics SHALL produire 0 ≤ n_perdus ≤ n_duels, 0 ≤ taux_perdu ≤ 1, 0 ≤ pressions_accordees ≤ n_duels et 0 ≤ taux_pression ≤ 1 (invariant).
9. IF un groupe conservé ne contient aucun Duel avec perdu = True, THEN THE Module_Metrics SHALL renseigner temps_avant_defaite_median avec une valeur manquante (NaN) pour ce groupe, conserver le groupe dans le résultat et renseigner n_perdus = 0 et taux_perdu = 0.
10. IF plusieurs valeurs de blockerPos sont à égalité de fréquence maximale dans un groupe, THEN THE Module_Metrics SHALL renseigner blockerPos avec la première de ces valeurs dans l'ordre alphabétique.
11. IF `blocks` est vide ou si aucun groupe n'atteint n_duels ≥ min_duels, THEN THE Module_Metrics SHALL retourner un DataFrame vide (0 ligne) comportant les colonnes team, blockerId, blockerName, blockerPos, n_duels, n_perdus, taux_perdu, temps_tenu_moyen, temps_avant_defaite_median, pressions_accordees, taux_pression et sacks_accordes, sans lever d'exception.

### Exigence 21 : Interface en ligne de commande (Étape 3)

**User Story :** En tant que développeur, je veux une commande unique pour générer la sortie, afin de relancer le calcul facilement.

#### Critères d'acceptation

1. THE CLI_Metrics SHALL accepter la commande `python -m src.metrics --raw data/raw --out data/processed/blocks.csv --seuil 2.0 --max-games 3`, les arguments `--raw`, `--out`, `--seuil` et `--max-games` pouvant être fournis dans n'importe quel ordre.
2. THE CLI_Metrics SHALL rendre optionnels les arguments `--raw`, `--out`, `--seuil` et `--max-games`, avec pour valeurs par défaut respectives `data/raw`, `data/processed/blocks.csv`, SEUIL_PRESSION (2.0 yards) et l'ensemble des Fichiers_Tracking retournés par `find_tracking_files` (aucune limite de nombre de matchs).
3. WHEN un Fichier_Tracking a été traité, THE CLI_Metrics SHALL afficher sur la sortie standard une ligne de progression au format `[i/N] game <gameId> : <d> duels (<a> actions ignorées)`, où i est le rang du match traité (à partir de 1), N le nombre total de Fichiers_Tracking à traiter après application de `--max-games`, d le nombre de Duels produits pour ce match et a le nombre d'Actions de ce match ignorées en application de l'Exigence 8 (critère 5) et de l'Exigence 9 (critère 3), par exemple `[12/122] game 2021091200 : 412 duels (3 actions ignorées)`.
4. IF le dossier parent du chemin `--out` n'existe pas, THEN THE CLI_Metrics SHALL créer ce dossier, y compris les dossiers intermédiaires manquants, avant d'écrire le Fichier_Blocks.
5. WHEN le traitement de tous les Fichiers_Tracking à traiter est terminé, THE CLI_Metrics SHALL écrire le Fichier_Blocks au chemin `--out`, en remplaçant tout fichier existant à ce chemin, avec une ligne d'en-tête contenant uniquement les colonnes de CONTRACT_COLUMNS dans cet ordre, sans colonne d'index, suivie d'une ligne par Duel.
6. WHEN l'argument `--seuil` est fourni, THE CLI_Metrics SHALL interpréter sa valeur comme un nombre décimal exprimé en yards et la transmettre comme paramètre `seuil` à `build_blocks`.
7. WHEN l'argument `--max-games` est fourni avec un entier n ≥ 1, THE CLI_Metrics SHALL traiter les n premiers Fichiers_Tracking de la liste triée retournée par `find_tracking_files`, ou la totalité de ces fichiers si la liste en contient moins de n.
8. IF la valeur de `--seuil` n'est pas un nombre décimal strictement positif ou si la valeur de `--max-games` n'est pas un entier supérieur ou égal à 1, THEN THE CLI_Metrics SHALL afficher un message d'erreur nommant l'argument invalide, se terminer avec un code de sortie non nul et ne pas écrire le Fichier_Blocks.

### Exigence 22 : Bloc de validation

**User Story :** En tant qu'analyste, je veux un contrôle de cohérence à chaque exécution, afin de détecter une métrique aberrante.

#### Critères d'acceptation

1. WHEN le calcul est terminé, THE CLI_Metrics SHALL afficher dans le Bloc_Validation : le nombre d'Actions (couples (gameId, playId) distincts du Fichier_Blocks), le nombre de Duels (lignes du Fichier_Blocks), le pourcentage de Duels perdus (100 × nombre de Duels avec perdu = True / nombre de Duels, arrondi à 1 décimale) et le temps tenu médian (médiane de temps_tenu sur l'ensemble des Duels, Duels perdus et Duel_Censure confondus, en secondes, arrondie à 2 décimales) ; si le nombre de Duels vaut 0, le pourcentage et la médiane sont affichés comme non disponibles.
2. WHEN le calcul est terminé, THE CLI_Metrics SHALL afficher le tableau croisé perdu × pressure_allowed sous forme d'effectifs de Duels pour les 4 combinaisons (perdu ∈ {True, False} × pressure_allowed ∈ {True, False}), une combinaison sans Duel étant affichée avec l'effectif 0.
3. IF le taux de Duels perdus parmi les Duels avec pressure_allowed = True (nombre de Duels avec perdu = True et pressure_allowed = True / nombre de Duels avec pressure_allowed = True) est inférieur ou égal à 1,5 fois le taux de Duels perdus parmi les Duels avec pressure_allowed = False, THEN THE CLI_Metrics SHALL afficher un avertissement d'anomalie probable indiquant les deux taux comparés. (Choix d'implémentation : « nettement supérieur » est interprété comme « strictement supérieur à 1,5 fois » ; ce facteur 1,5 est une valeur codée en dur, signalée en commentaire dans le code et dans Doc_Metriques.)
4. IF aucun Duel n'a pressure_allowed = True ou aucun Duel n'a pressure_allowed = False, THEN THE CLI_Metrics SHALL afficher, à la place de la comparaison du critère 3, un avertissement d'anomalie probable indiquant que la comparaison des taux est impossible faute de Duels dans l'un des deux groupes.
5. WHEN le calcul est terminé, THE CLI_Metrics SHALL afficher les 10 premières lignes, dans l'ordre de tri de `summarize_blockers`, du résultat de `summarize_blockers(min_duels=20)` appliquée à l'ensemble des Duels ; si ce résultat contient moins de 10 lignes, toutes ses lignes sont affichées, et s'il en contient 0, un message indiquant qu'aucun bloqueur n'atteint 20 Duels est affiché.
6. WHEN le calcul est terminé, THE CLI_Metrics SHALL afficher, pour chaque colonne de CONTRACT_COLUMNS et dans l'ordre de CONTRACT_COLUMNS, le nombre de valeurs manquantes de la colonne, y compris lorsque ce nombre vaut 0.
7. IF une colonne de CONTRACT_COLUMNS autre que frame_perdu contient au moins 1 valeur manquante, THEN THE CLI_Metrics SHALL afficher un avertissement par colonne concernée, nommant la colonne et indiquant son nombre de valeurs manquantes.
8. IF un avertissement des critères 3, 4 ou 7 est affiché, THEN THE CLI_Metrics SHALL poursuivre l'affichage du Bloc_Validation et conserver le Fichier_Blocks écrit au chemin `--out`, l'avertissement n'interrompant pas l'exécution.

### Exigence 23 : Tests unitaires (Étape 5)

**User Story :** En tant que développeur, je veux des tests sur données synthétiques, afin de garantir que la métrique calcule ce qu'elle prétend.

#### Critères d'acceptation

1. THE Suite_Tests SHALL contenir au moins les 6 tests décrits aux critères 2 à 7, chacun construisant en mémoire des DataFrames synthétiques sans lire aucun fichier de `data/` ni du Dossier_Raw ; pour les tests des critères 2 à 6, ces DataFrames décrivent 1 Action, un QB immobile en (x = 50, y = 26) sur toutes les frames, 1 bloqueur et 1 défenseur, avec un tracking à 10 Hz (1 frame = 0,1 s) et le seuil par défaut SEUIL_PRESSION = 2.0 yards.
2. WHEN le test « duel perdu » appelle `compute_duels_for_game` sur une Action dont la Frame_Snap vaut 10 et dont la Distance_Def_QB est supérieure ou égale à 2.0 yards sur les frames 10 à 14 puis strictement inférieure à 2.0 yards à la frame 15, THE Suite_Tests SHALL vérifier que la table retournée contient exactement 1 Duel avec perdu = True, frame_perdu = 15 et temps_tenu = 0.5.
3. WHEN le test « duel censuré » appelle `compute_duels_for_game` sur une Action dont la Frame_Snap vaut 10, la Frame_Fin vaut 30 et dont la Distance_Def_QB vaut 5.0 yards sur toutes les frames de la Fenetre_Duel, THE Suite_Tests SHALL vérifier que la table retournée contient exactement 1 Duel avec perdu = False, frame_perdu vide, temps_tenu = 2.0 et duree_action = 2.0.
4. WHEN le test « sans snap » appelle `compute_duels_for_game` sur une Action dont aucune valeur d'event n'appartient à SNAP_EVENTS, THE Suite_Tests SHALL vérifier que la table retournée contient 0 ligne et que l'appel ne lève aucune exception.
5. WHEN le test « sans fin » appelle `play_frames` sur une Action contenant une Frame_Snap et aucune valeur d'event appartenant à END_EVENTS après cette Frame_Snap, THE Suite_Tests SHALL vérifier que la table retournée contient 1 ligne dont frame_fin est égale à la plus grande frameId de l'Action.
6. WHEN le test « casse de pff_role » appelle `compute_duels_for_game` avec un scouting où pff_role du bloqueur vaut « Pass Block » (majuscules initiales) et pff_nflIdBlockedPlayer vaut le nflId du défenseur, THE Suite_Tests SHALL vérifier que la table retournée contient exactement 1 Duel associant ce blockerId à ce defenderId.
7. WHEN le test « classement » appelle `summarize_blockers` avec une valeur min_duels explicite sur une table de Duels synthétique contenant au moins un bloqueur avec n_duels < min_duels et au moins deux bloqueurs avec n_duels ≥ min_duels et un taux_perdu égal mais des taux_pression différents, THE Suite_Tests SHALL vérifier que les bloqueurs avec n_duels < min_duels sont absents du résultat, que les lignes sont triées par taux_perdu décroissant, et que les bloqueurs à taux_perdu égal sont ordonnés par taux_pression décroissant.
8. WHEN `pytest -q` est exécuté depuis la racine du dépôt, THE Suite_Tests SHALL terminer avec au moins 6 tests réussis, 0 échec, 0 erreur et un code de sortie égal à 0.

### Exigence 24 : Exécution et génération de la sortie (Étape 6)

**User Story :** En tant que membre de l'équipe, je veux une sortie validée sur l'ensemble des matchs, afin que l'app dispose de données complètes.

#### Critères d'acceptation

1. THE Agent SHALL exécuter la CLI_Metrics avec `--max-games 3` avant toute exécution sur tous les matchs, puis contrôler le Bloc_Validation affiché ; l'exécution sur 3 matchs est considérée comme validée si et seulement si la CLI_Metrics se termine sans erreur (code de sortie 0), affiche le Bloc_Validation complet (critères 1, 2, 5 et 6 de l'Exigence 22) et n'affiche ni l'avertissement d'anomalie probable (Exigence 22, critère 3) ni d'avertissement de valeurs manquantes (Exigence 22, critère 7) ; par exception, si l'avertissement d'anomalie probable persiste après analyse et correction éventuelle de sa cause, l'exécution sur 3 matchs est considérée comme validée et l'Agent poursuit en signalant cet avertissement dans le Rapport_Final.
2. WHEN l'exécution sur 3 matchs est validée, THE Agent SHALL exécuter la CLI_Metrics sans l'argument `--max-games`, avec le même Dossier_Raw que l'exécution sur 3 matchs, de sorte que tous les Fichiers_Tracking découverts dans le Dossier_Raw (122 dans le workspace actuel) soient traités et que le Fichier_Blocks soit écrit au chemin `data/processed/blocks.csv`.
3. IF l'exécution sur 3 matchs n'est pas validée selon le critère 1, THEN THE Agent SHALL ne pas lancer l'exécution sur tous les matchs, corriger la cause, puis relancer la CLI_Metrics avec `--max-games 3` jusqu'à obtenir une exécution validée.
4. WHEN l'exécution sur tous les matchs se termine, THE Agent SHALL relever le temps total d'exécution, mesuré en temps réel écoulé entre le lancement de la commande et la fin du processus, exprimé en secondes (arrondi à la seconde), et l'indiquer dans le Rapport_Final.
5. IF la taille sur disque du Fichier_Blocks est strictement supérieure à 50 Mo (50 × 1024 × 1024 octets), THEN THE Agent SHALL le signaler dans le Rapport_Final en indiquant la taille relevée en Mo avec une décimale.

### Exigence 25 : Documentation de la métrique (Étape 7)

**User Story :** En tant que coéquipier ou coach, je veux une documentation claire de la métrique, afin de comprendre et d'exploiter blocks.csv.

#### Critères d'acceptation

1. THE Doc_Metriques SHALL contenir une section « Objectif » de 2 à 3 phrases, sans formule mathématique ni nom de colonne, indiquant que la métrique identifie, pour chaque bloqueur de la ligne offensive, les Duels perdus et le temps tenu face à son défenseur sur les jeux de passe.
2. THE Doc_Metriques SHALL contenir les définitions de Duel, QB, snap, fin, distance, seuil, Duel_Perdu, temps tenu et censure, chacune conforme au glossaire et aux formules implémentées dans le Module_Metrics : Duel (pff_role « pass block » et pff_nflIdBlockedPlayer non vide), QB (pff_role « pass », le premier s'il y en a plusieurs), snap (Frame_Snap, avec les valeurs de SNAP_EVENTS retenues), fin (Frame_Fin, avec les valeurs de END_EVENTS retenues et le repli sur la dernière frame de l'Action), distance (formule de la Distance_Def_QB en yards, coordonnées brutes sans retournement de terrain), seuil (SEUIL_PRESSION = 2.0 yards par défaut, modifiable via `--seuil`, comparaison strictement inférieure), Duel_Perdu, temps tenu ((frame_perdu − frame_snap) / FPS si perdu, (frame_fin − frame_snap) / FPS sinon, avec FPS = 10) et censure (Duel_Censure).
3. THE Doc_Metriques SHALL contenir, dans le dictionnaire des colonnes de blocks.csv, une ligne par colonne de CONTRACT_COLUMNS (33 colonnes : les 20 colonnes obligatoires et les 13 colonnes additionnelles de l'Exigence 18), dans l'ordre de CONTRACT_COLUMNS, avec le nom exact de la colonne, un type parmi entier, Int64 nullable, float arrondi à 2 décimales, booléen ou chaîne conforme à l'Exigence 18, et une description non vide indiquant l'unité (secondes pour temps_tenu et duree_action, yards pour dist_min).
4. THE Doc_Metriques SHALL contenir le dictionnaire des 12 colonnes produites par `summarize_blockers` (team, blockerId, blockerName, blockerPos, n_duels, n_perdus, taux_perdu, temps_tenu_moyen, temps_avant_defaite_median, pressions_accordees, taux_pression, sacks_accordes), chacune avec une description incluant sa formule de calcul conforme à l'Exigence 20, ainsi que la valeur par défaut min_duels = 20 et l'ordre de tri (taux_perdu décroissant puis taux_pression décroissant).
5. THE Doc_Metriques SHALL contenir une section « Utilisation » avec la commande `python -m src.metrics --raw data/raw --out data/processed/blocks.csv --seuil 2.0 --max-games 3` et un exemple Python qui appelle `load_blocks`, filtre les Duels sur team == "KC" et down == 3, puis appelle `summarize_blockers` avec min_duels=10, cet exemple s'exécutant sans erreur une fois le Fichier_Blocks généré.
6. THE Doc_Metriques SHALL préciser, dans la description de la colonne frame_perdu, que frame_perdu sert au replay en indiquant la frame de la perte pour l'appel `make_replay(gameId, playId, focus_blocker_id=blockerId)`, et que frame_perdu est vide lorsque perdu = False.
7. THE Doc_Metriques SHALL contenir une section « Biais et limites » couvrant, chacun comme un point distinct : la censure des passes rapides qui gonfle le temps tenu (avec la recommandation explicite de privilégier taux_perdu à temps_tenu_moyen pour comparer les bloqueurs), le seuil de 2 yards comme convention non calibrée, le défenseur proche parce que le QB s'est déplacé vers lui, le défenseur bloqué limité au premier bloqué selon PFF, le petit échantillon par joueur (8 semaines) et la restriction aux jeux de passe.
8. THE Doc_Metriques SHALL contenir une section « Résultats de validation » reprenant, à l'identique des valeurs affichées par le Bloc_Validation lors de l'exécution de l'Étape 6 sur tous les matchs : le nombre de matchs traités, le seuil utilisé, le nombre d'Actions, le nombre de Duels, le pourcentage de Duels perdus, le temps tenu médian, le tableau croisé perdu × pressure_allowed, le top 10 de `summarize_blockers(min_duels=20)` et le temps total d'exécution.
9. THE Doc_Metriques SHALL contenir, avec les définitions, un mini-schéma ASCII placé dans un bloc de code montrant sur un axe temporel la Frame_Snap, la Frame_Perdu et la Frame_Fin, et annotant temps_tenu (snap → perte) et duree_action (snap → fin).
10. THE Doc_Metriques SHALL se limiter à 7 sections : « Objectif », les définitions, le dictionnaire des colonnes de blocks.csv, le dictionnaire des colonnes de `summarize_blockers`, « Utilisation », « Biais et limites » et « Résultats de validation ».

### Exigence 26 : README du projet (Étape 8)

**User Story :** En tant que membre de l'équipe ou jury, je veux un README complet, afin de comprendre, installer et lancer tout le projet.

#### Critères d'acceptation

1. THE README_Projet SHALL remplacer intégralement le contenu actuel du `README.md` racine (`# NFWxAWS`), de sorte que la ligne `# NFWxAWS` n'y figure plus et que la première ligne du fichier soit le titre défini au critère 2.
2. THE README_Projet SHALL contenir, comme unique titre de niveau 1, le texte exact « Weak Link — trouver le maillon faible de la ligne offensive adverse », suivi immédiatement d'une accroche d'une à deux phrases placée avant la première section.
3. THE README_Projet SHALL contenir une section intitulée « Problème et positionnement » qui nomme Teamworks Coaching et Catapult Thunder en les qualifiant d'outils génériques, et qui présente Weak Link comme l'analyse de la protection de passe duel par duel à partir des données de tracking.
4. THE README_Projet SHALL contenir une section listant les fonctionnalités MVP sous forme de trois éléments distincts : le classement des bloqueurs d'une équipe, les filtres de situation nommant explicitement les quatre filtres 3e down, blitz, stunt et play action, et le replay animé des Duels perdus.
5. THE README_Projet SHALL contenir une section décrivant les données avec les quatre mentions NFL Big Data Bowl, 122 matchs, semaines 1 à 8 de la saison 2021 et jeux de passe uniquement, l'emplacement `data/raw/`, et l'indication explicite que ces données ne sont pas versionnées dans le dépôt.
6. THE README_Projet SHALL contenir une section présentant la structure du dépôt avec les sept entrées data/raw, data/processed, src/metrics.py, src/replay.py, app.py, docs/ et tests/, chaque entrée étant accompagnée d'un commentaire d'une ligne décrivant son rôle.
7. THE README_Projet SHALL contenir une section d'installation présentant, dans un bloc de code et caractère pour caractère, les commandes `python -m venv .venv && source .venv/bin/activate` et `pip install -r requirements.txt`, dans cet ordre.
8. THE README_Projet SHALL contenir une section d'utilisation présentant, dans un bloc de code et caractère pour caractère, les trois commandes `python -m src.metrics`, `streamlit run app.py` et `pytest -q`, chacune accompagnée d'une ligne indiquant ce qu'elle produit ou lance.
9. THE README_Projet SHALL contenir une section décrivant les contrats, qui cite avec leurs noms exacts les colonnes obligatoires du Fichier_Blocks définies à l'Exigence 18 (critère 2) et contient un lien relatif vers `docs/metriques.md` pour le dictionnaire complet des colonnes.
10. THE README_Projet SHALL contenir une section intitulée « Équipe » comportant exactement trois entrées : Partie 1 attribuée à Thibault, Partie 2 portant la mention « à compléter », et Partie 3 portant la mention « à compléter ».
11. THE README_Projet SHALL contenir une section planning listant exactement trois jalons avec ces horaires : synchro à 1:00, intégration à 2:00 et gel du code à 2:30.
12. THE README_Projet SHALL contenir une section intitulée « Limites connues » composée de 3 ou 4 puces, chaque puce énonçant une limite distincte.
13. THE README_Projet SHALL contenir exactement les 11 parties décrites aux critères 2 à 12 (titre et accroche, problème et positionnement, fonctionnalités MVP, données, structure, installation, utilisation, contrats, équipe, planning, limites connues) et aucune autre section.
14. THE README_Projet SHALL reproduire, dans la section des contrats, la signature exacte `make_replay(game_id, play_id, focus_blocker_id=None) -> plotly.graph_objects.Figure` de `src/replay.py`.
15. THE README_Projet SHALL indiquer, dans la section des contrats, que `app.py` importe les fonctions `load_blocks` et `summarize_blockers` depuis le Module_Metrics (`src.metrics`).

### Exigence 27 : Dépendances et fichiers ignorés (Étape 9)

**User Story :** En tant que développeur, je veux un environnement reproductible et un dépôt propre, afin que chacun installe et versionne la même chose.

#### Critères d'acceptation

1. THE Agent SHALL lister dans `requirements.txt` exactement les 5 dépendances pandas, numpy, plotly, streamlit et pytest, à raison d'une dépendance par ligne, sans aucune autre dépendance (lignes vides et lignes de commentaire commençant par `#` mises à part).
2. THE Module_Metrics SHALL importer uniquement des modules de la bibliothèque standard Python ou des paquets listés dans `requirements.txt`, de sorte que chaque instruction `import` ou `from ... import` de `src/metrics.py` désigne un module de premier niveau appartenant à l'une de ces deux catégories.
3. THE Agent SHALL lister dans `.gitignore` exactement les 6 entrées `data/raw/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `*.pyc` et `.DS_Store`, chacune sur sa propre ligne, sans aucune autre entrée (lignes vides et lignes de commentaire commençant par `#` mises à part).
4. THE Agent SHALL laisser `data/processed/` versionnable, de sorte qu'aucune entrée du `.gitignore` ne fasse ignorer le Fichier_Blocks (vérifiable par `git check-ignore data/processed/blocks.csv`, qui ne doit rien renvoyer).
5. IF, à la fin de la mission, les données brutes se trouvent toujours dans `data/` (emplacement observé : `data/games.csv`, `data/plays.csv`, `data/players.csv`, `data/pffScoutingData.csv` et `data/tracking/`), THEN THE Rapport_Final SHALL signaler que l'entrée `data/raw/` du `.gitignore` ne couvre pas ces fichiers et que ceux-ci restent donc versionnables, sans que l'Agent ajoute d'entrée supplémentaire au `.gitignore`.
6. THE Suite_Tests SHALL importer uniquement des modules de la bibliothèque standard Python, des paquets listés dans `requirements.txt` et le Module_Metrics.

### Exigence 28 : Règles générales

**User Story :** En tant que membre de l'équipe, je veux un code lisible et des choix tracés, afin de pouvoir reprendre le travail rapidement en hackathon.

#### Critères d'acceptation

1. THE Module_Metrics SHALL être écrit avec des fonctions courtes et un nommage explicite, chaque fonction définie dans le Module_Metrics comportant une docstring rédigée en français.
2. THE Module_Metrics SHALL contenir des commentaires rédigés exclusivement en français.
3. IF un choix n'est pas couvert par le plan, THEN THE Agent SHALL retenir l'option la plus simple qui fonctionne et la consigner dans la liste des écarts et simplifications du Rapport_Final, en indiquant le choix concerné et l'option retenue.
4. IF un problème empêche l'étape en cours d'aboutir pendant 10 minutes ou plus, THEN THE Agent SHALL simplifier l'approche, consigner la simplification (problème rencontré et approche simplifiée retenue) dans la liste des écarts et simplifications du Rapport_Final, et poursuivre avec l'étape suivante du plan.
5. THE Agent SHALL produire une première version fonctionnelle, définie comme une exécution sans erreur de la CLI_Metrics sur 2 à 3 matchs (`--max-games 3` selon l'Exigence 24) qui génère le Fichier_Blocks et affiche le Bloc_Validation, avec un objectif d'environ 45 minutes, avant toute consolidation, y compris avant l'exécution sur tous les matchs.

### Exigence 29 : Critères de fin

**User Story :** En tant que membre de l'équipe, je veux des critères de fin vérifiables, afin de savoir quand la Partie 1 est terminée.

#### Critères d'acceptation

1. WHEN `python -m src.metrics --max-games 3` est exécutée depuis la racine du dépôt avec un Dossier_Raw valide (le Dossier_Raw par défaut `data/raw`, ou celui passé via `--raw`, p. ex. `--raw data` dans le workspace actuel ; valide = contient `games.csv`, `plays.csv`, `players.csv`, `pffScoutingData.csv` et au moins 3 Fichiers_Tracking découverts par `find_tracking_files`), THE CLI_Metrics SHALL traiter au plus 3 Fichiers_Tracking (une ligne de progression par match traité, Exigence 21 critère 3), se terminer avec un code de sortie 0 sans exception non gérée, et afficher le Bloc_Validation contenant les éléments des critères 1, 2, 5 et 6 de l'Exigence 22 ; les avertissements des critères 3, 4 et 7 de l'Exigence 22 ne constituent pas une erreur.
2. WHEN `python -m src.metrics` est exécutée depuis la racine du dépôt avec un Dossier_Raw valide (défini au critère 1), sans l'argument `--max-games`, THE CLI_Metrics SHALL traiter chacun des Fichiers_Tracking retournés par `find_tracking_files` (122 dans le workspace actuel, soit 122 lignes de progression), se terminer avec un code de sortie 0 et écrire `data/processed/blocks.csv`.
3. THE Fichier_Blocks SHALL contenir chacune des 33 colonnes du contrat (les 20 colonnes obligatoires du critère 2 et les 13 colonnes additionnelles du critère 3 de l'Exigence 18), avec ces noms exacts, et, après relecture par `load_blocks`, les types définis aux critères 4 à 8 de l'Exigence 18.
4. WHEN `pytest -q` est exécuté depuis la racine du dépôt, THE Suite_Tests SHALL se terminer avec un code de sortie 0, avec au moins 1 test collecté, 0 test en échec et 0 erreur.
5. THE Agent SHALL livrer `docs/metriques.md`, `README.md`, `requirements.txt` et `.gitignore`, chacun étant complet lorsque tous les critères qui le concernent sont satisfaits : critères 1 à 10 de l'Exigence 25 pour la Doc_Metriques, critères 1 à 15 de l'Exigence 26 pour le README_Projet, critères 1, 3 et 4 de l'Exigence 27 pour `requirements.txt` et `.gitignore`.

### Exigence 30 : Rapport final

**User Story :** En tant que coéquipier des parties 2 et 3, je veux un rapport final synthétique, afin de connaître l'état exact de la Partie 1 et ses points d'attention.

#### Critères d'acceptation

1. THE Rapport_Final SHALL lister, par leur chemin relatif à la racine du dépôt, les fichiers créés parmi les livrables des critères 1 à 8 de l'Exigence 1, en incluant `README.md` (remplacé) et `data/processed/blocks.csv`, et sans mentionner d'autre fichier comme créé.
2. THE Rapport_Final SHALL indiquer les valeurs d'event retenues pour SNAP_EVENTS et END_EVENTS, identiques, valeur par valeur, à celles des constantes définies dans `src/metrics.py`.
3. THE Rapport_Final SHALL indiquer les chiffres de validation issus de l'exécution de la CLI_Metrics sur tous les matchs (Exigence 24, critère 2) : nombre de Duels et pourcentage de Duels perdus identiques à ceux du Bloc_Validation de cette exécution, tableau croisé perdu × pressure_allowed avec ses 4 effectifs (perdu True/False × pressure_allowed True/False), et temps total d'exécution relevé à l'Exigence 24 critère 4, exprimé en secondes.
4. THE Rapport_Final SHALL lister les écarts et simplifications signalés au titre des Exigences 2 (critère 5), 3 (critère 8), 4 (critère 8), 16 (critère 4), 24 (critère 5), 27 (critère 5) et 28 (critères 3 et 4), chaque écart indiquant ce que prévoyait le plan et ce qui a été réellement fait, dont l'emplacement des données brutes avec l'option retenue et toute colonne manquante avec la colonne utilisée à la place ; IF aucun écart n'existe pour l'un de ces points, THEN THE Rapport_Final SHALL l'indiquer explicitement.
5. THE Rapport_Final SHALL lister les points d'attention pour les parties 2 et 3, chaque point étant explicitement rattaché à la Partie 2, à la Partie 3 ou aux deux ; IF aucun point d'attention n'existe pour une partie, THEN THE Rapport_Final SHALL l'indiquer explicitement pour cette partie.
