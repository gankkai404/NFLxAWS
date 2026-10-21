# Métrique « Weak Link » : duels de protection de passe

## 1. Objectif

Sur chaque jeu de passe, chaque bloqueur de l'attaque doit empêcher un défenseur précis d'atteindre le quarterback. La métrique dit, pour chaque bloqueur et chaque action, s'il a laissé son défenseur s'approcher dangereusement du quarterback et combien de temps il a tenu avant. En agrégeant ces duels, on repère le bloqueur adverse qui craque le plus souvent, et dans quelles situations.

## 2. Définitions

| Terme | Définition |
|---|---|
| **Duel** | Un bloqueur (`pff_role` = « pass block », casse ignorée) associé au défenseur qu'il bloque (`pff_nflIdBlockedPlayer` non vide), sur une action. |
| **QB** | Le joueur de l'action avec `pff_role` = « pass » (le premier s'il y en a plusieurs). Action ignorée s'il n'y en a pas. |
| **Snap** | Première frame dont l'`event` vaut `ball_snap` ou `autoevent_ballsnap`. Action ignorée sans snap. |
| **Fin** | Première frame après le snap dont l'`event` vaut `pass_forward`, `autoevent_passforward`, `qb_sack`, `qb_strip_sack` ou `run`. À défaut, dernière frame de l'action. |
| **Distance** | À chaque frame entre snap et fin (incluses) : `sqrt((x_def − x_qb)² + (y_def − y_qb)²)` en yards, sur les coordonnées brutes (pas de retournement de terrain). |
| **Seuil** | `SEUIL_PRESSION = 2.0` yards par défaut, modifiable avec `--seuil`. Comparaison stricte (`<`). |
| **Duel perdu** | La distance passe sous le seuil au moins une fois entre snap et fin. `frame_perdu` = première frame concernée. |
| **Temps tenu** | Perdu : `(frame_perdu − frame_snap) / 10`. Sinon : `(frame_fin − frame_snap) / 10` (en secondes, tracking à 10 Hz). |
| **Censure** | Un duel non perdu est « censuré » : le bloqueur a tenu jusqu'à la fin de l'action, on ne sait pas combien de temps il aurait tenu de plus. |

```
frames  ──┬──────────────────────┬──────────────────┬──────►
       frame_snap            frame_perdu         frame_fin
          │◄──── temps_tenu ────►│   (duel perdu)    │
          │◄──────────────── duree_action ──────────►│

Duel non perdu (censuré) : temps_tenu = duree_action
```

## 3. Dictionnaire de `data/processed/blocks.csv`

Une ligne par duel. Les noms de colonnes sont un contrat entre les parties : ne pas les renommer.

| Colonne | Type | Description |
|---|---|---|
| `gameId` | entier | Identifiant du match. |
| `playId` | entier | Identifiant de l'action dans le match. |
| `blockerId` | entier | `nflId` du bloqueur. |
| `blockerName` | chaîne | Nom du bloqueur (`players.displayName`). |
| `blockerPos` | chaîne | Position alignée du bloqueur sur l'action (`pff_positionLinedUp` : LT, LG, C, RG, RT, TE-L, HB-R…). |
| `team` | chaîne | Équipe du bloqueur = attaque (`possessionTeam`). Filtrer dessus pour analyser une O-line. |
| `defenderId` | entier | `nflId` du défenseur bloqué. |
| `defenderName` | chaîne | Nom du défenseur. |
| `temps_tenu` | float (2 déc.) | Secondes tenues avant la perte, ou jusqu'à la fin si non perdu. |
| `perdu` | booléen | True si le défenseur est passé sous le seuil de distance du QB. |
| `pressure_allowed` | booléen | PFF : hit, hurry ou sack accordé par le bloqueur. |
| `sack_allowed` | booléen | PFF : sack accordé par le bloqueur. |
| `down` | entier | Tentative (0 à 4, 0 sur quelques actions spéciales). |
| `yardsToGo` | entier | Yards à gagner pour le premier down. |
| `nb_rushers` | entier | Nombre de joueurs en `pass rush` sur l'action (≥ 5 ≈ blitz). |
| `stunt` | booléen | True si au moins un bloc de l'action est de type `SW` (switch). |
| `pff_playAction` | booléen | Action en play action. |
| `offenseFormation` | chaîne | Formation offensive (`UNKNOWN` si absente). |
| `passResult` | chaîne | Résultat de la passe (C, I, S, IN, R). |
| `playDescription` | chaîne | Description textuelle de l'action. |
| `week` | entier | Semaine de la saison (1 à 8). |
| `quarter` | entier | Quart-temps. |
| `defenseTeam` | chaîne | Équipe en défense (`defensiveTeam`). |
| `defenderPos` | chaîne | Position alignée du défenseur sur l'action. |
| `blockType` | chaîne | Type de bloc PFF du bloqueur (PP, SW, CH…). |
| `beaten_by_defender` | booléen | PFF : bloqueur battu par le défenseur. |
| `frame_snap` | entier | Frame du snap. |
| `frame_fin` | entier | Frame de fin de l'action. |
| `frame_perdu` | Int64 (vide si non perdu) | Première frame sous le seuil. Sert au replay : c'est le moment à mettre en évidence dans `make_replay(gameId, playId, focus_blocker_id=blockerId)`. |
| `duree_action` | float (2 déc.) | `(frame_fin − frame_snap) / 10`, en secondes. |
| `dist_min` | float (2 déc.) | Distance minimale défenseur↔QB entre snap et fin, en yards. |
| `dropBackType` | chaîne | Type de drop back du QB (`UNKNOWN` si absent). |
| `pff_passCoverage` | chaîne | Couverture défensive PFF (Cover-1, Cover-3…). |

## 4. Dictionnaire de `summarize_blockers(blocks, min_duels=20)`

Une ligne par bloqueur (`team`, `blockerId`, `blockerName`), filtrée sur `n_duels >= min_duels`, triée par `taux_perdu` puis `taux_pression` décroissants : le plus faible arrive en premier.

| Colonne | Type | Description |
|---|---|---|
| `team` | chaîne | Équipe du bloqueur. |
| `blockerId` | entier | `nflId` du bloqueur. |
| `blockerName` | chaîne | Nom du bloqueur. |
| `blockerPos` | chaîne | Position la plus fréquente (égalité : ordre alphabétique). |
| `n_duels` | entier | Nombre de duels. |
| `n_perdus` | entier | Nombre de duels perdus. |
| `taux_perdu` | float | `n_perdus / n_duels`. |
| `temps_tenu_moyen` | float | Moyenne de `temps_tenu` (duels perdus et censurés). |
| `temps_avant_defaite_median` | float | Médiane de `temps_tenu` sur les seuls duels perdus (NaN si aucun). |
| `pressions_accordees` | entier | Somme de `pressure_allowed`. |
| `taux_pression` | float | `pressions_accordees / n_duels`. |
| `sacks_accordes` | entier | Somme de `sack_allowed`. |

## 5. Utilisation

```bash
# Les données sont actuellement dans data/ : passer --raw data
python -m src.metrics --raw data --out data/processed/blocks.csv --seuil 2.0 --max-games 3
python -m src.metrics --raw data   # tous les matchs
```

```python
from src.metrics import load_blocks, summarize_blockers
blocks = load_blocks()
subset = blocks[(blocks.team == "KC") & (blocks.down == 3)]
ranking = summarize_blockers(subset, min_duels=10)
```

`summarize_blockers` accepte un `blocks` déjà filtré (3e down, `nb_rushers >= 5`, `stunt`, `pff_playAction`…). `frame_perdu` indique au replay à quel moment le duel est perdu.

## 6. Biais et limites

- **Censure :** les passes rapides s'arrêtent avant que le défenseur ait le temps d'arriver, ce qui gonfle le temps tenu. Pour comparer les bloqueurs, privilégier `taux_perdu` plutôt que `temps_tenu_moyen`.
- **Seuil :** 2 yards est une convention, pas une valeur calibrée.
- **Mouvement du QB :** un défenseur peut passer sous le seuil parce que le QB s'est déplacé vers lui (scramble, glissement dans la poche), sans faute du bloqueur.
- **Un seul défenseur par duel :** le défenseur retenu est le *premier* bloqué selon PFF. Les doubles équipes et les changements de cible ne sont pas modélisés.
- **Petit échantillon :** 8 semaines de matchs, donc quelques dizaines de duels par joueur. Les classements sur des sous-ensembles (3e down d'une équipe) sont fragiles.
- **Jeux de passe uniquement :** la protection sur les courses n'est pas couverte.
- **Running backs et tight ends :** ils bloquent moins souvent mais sur des situations difficiles (blitz), d'où des taux élevés. Filtrer sur `blockerPos` (LT, LG, C, RG, RT) pour isoler la ligne offensive.
- **Bloc de validation :** l'alerte « anomalie probable » se déclenche si le taux de duels perdus avec pression PFF n'est pas au moins 1,5 fois le taux sans pression (`FACTEUR_ANOMALIE`, choix de convention).

## 7. Résultats de validation

Exécution complète : `python -m src.metrics --raw data` (122 matchs, seuil 2.0 yards), **16 s**.

| Indicateur | Valeur |
|---|---|
| Actions avec au moins un duel | 8 531 |
| Actions ignorées | 24 sans snap, 0 sans QB |
| Duels ignorés (défenseur ou QB absent du tracking) | 2 |
| Duels | 44 403 |
| Duels perdus | 9,8 % |
| Temps tenu médian | 2,80 s |
| Taille de `blocks.csv` | 11,9 Mo |

Tableau croisé `perdu × pressure_allowed` :

| | pressure_allowed = False | pressure_allowed = True |
|---|---|---|
| **perdu = False** | 38 851 | 1 214 |
| **perdu = True** | 2 603 | 1 735 |

Taux de duels perdus : **58,8 %** quand PFF crédite une pression, contre **6,3 %** sinon. La métrique est cohérente avec la référence PFF.
