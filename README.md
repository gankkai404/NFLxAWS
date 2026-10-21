# 🏈 Weak Link - Hackathon NFL Big Data Bowl

**Trouver le maillon faible de la ligne offensive adverse**

## 🎯 Concept

Un outil qui montre à un coach, en un écran, quel bloqueur adverse craque, dans quelles situations, avec les replays animés comme preuve.

## 📁 Structure du Projet

```
NFLxAWS/
├── data/
│   ├── raw/              # CSV Big Data Bowl (tracking, plays, pff, players, games)
│   └── processed/        # Sorties de la partie 1 (blocks.csv)
├── src/
│   ├── metrics.py        # PARTIE 1 : Calcul du temps tenu
│   ├── replay.py         # PARTIE 2 : Replay animé ✅ FAIT
│   └── __init__.py
├── app.py                # PARTIE 3 : Application Streamlit
├── requirements.txt
└── README.md
```

## 🚀 Répartition des Tâches

### ✅ Partie 2 : Replay animé (COMPLÉTÉ)

**Fichier** : `src/replay.py`

**Fonction principale** :
```python
from src.replay import make_replay

# Replay simple
fig = make_replay(game_id=2021090900, play_id=97)

# Avec focus sur un bloqueur
fig = make_replay(game_id=2021090900, play_id=97, focus_blocker_id=12345)

# Afficher dans Streamlit
import streamlit as st
st.plotly_chart(fig, use_container_width=True)

# Ou sauvegarder en HTML
fig.write_html("replay.html")
```

**Fonctionnalités** :
- ✅ Terrain NFL 120×53.3 yards avec marquages
- ✅ Retournement automatique si `playDirection == "left"`
- ✅ Animation frame par frame avec contrôles Play/Pause
- ✅ QB surligné en étoile dorée
- ✅ Bloqueur et défenseur en focus si `focus_blocker_id` fourni
- ✅ Ligne défenseur→QB qui passe au rouge sous 2 yards
- ✅ Hover avec nom, numéro, vitesse

### ⏳ Partie 1 : Data & Métrique (À faire par vos coéquipiers)

**Fichier** : `src/metrics.py`

**Mission** : Calculer le "temps tenu" de chaque bloqueur sur chaque action.

**Livrable** : `data/processed/blocks.csv` avec colonnes :
```
gameId, playId, blockerId, blockerName, blockerPos, team,
defenderId, defenderName, temps_tenu, perdu (bool),
pressure_allowed, sack_allowed, down, yardsToGo,
nb_rushers, stunt, pff_playAction, offenseFormation,
passResult, playDescription
```

**Calcul du temps tenu** :
1. Repérer le snap (`ball_snap`)
2. Repérer la fin (`pass_forward`, `qb_sack`, etc.)
3. Pour chaque bloqueur, distance défenseur↔QB par frame
4. Temps tenu = (frame où distance < 2 yards - frame snap) / 10
5. Si jamais atteint, temps = fin - snap

### ⏳ Partie 3 : App & Pitch (À faire par vos coéquipiers)

**Fichier** : `app.py`

**Mission** : Interface Streamlit pour le coach.

**Fonctionnalités** :
- Sidebar : équipe adverse, filtres (3e down, blitz, stunt, play action)
- Classement des bloqueurs : temps tenu moyen, % duels perdus, pressions
- Clic sur joueur → liste de duels perdus → replay avec `make_replay()`
- Cache avec `@st.cache_data`

## 🔧 Installation

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## 🧪 Tester le Replay

```bash
# Test rapide
python test_replay.py

# Ouvrir les fichiers HTML générés dans un navigateur
```

## 📊 Données

### Fichiers Utilisés par le Replay

| Fichier | Colonnes Utilisées |
|---------|-------------------|
| `tracking_*.csv` | gameId, playId, nflId, frameId, x, y, s, team, jerseyNumber, playDirection |
| `plays.csv` | gameId, playId, playDescription, quarter, down, yardsToGo, passResult, possessionTeam |
| `pffScoutingData.csv` | gameId, playId, nflId, pff_role, pff_nflIdBlockedPlayer |
| `players.csv` | nflId, displayName, officialPosition |

### Logique du Retournement

Si `playDirection == "left"`, les coordonnées sont retournées :
```python
x → 120 - x
y → 53.3 - y
```
L'attaque va toujours vers la droite dans le replay.

## 🎨 Couleurs et Symboles

- **QB** : ⭐ Étoile dorée
- **Bloqueur focus** : 💎 Diamant vert
- **Défenseur focus** : 🟧 Carré orange
- **Attaque** : 🔵 Bleu
- **Défense** : 🔴 Rouge
- **Ballon** : 🟤 Marron
- **Ligne défenseur→QB** : 🟢 Verte (safe) / 🔴 Rouge (< 2 yards)

## 🔗 Intégration avec les Autres Parties

### Depuis la Partie 1 (metrics.py)
```python
# Après avoir calculé blocks.csv, utiliser le replay :
from src.replay import make_replay

# Afficher les actions perdues d'un bloqueur
lost_blocks = blocks_df[
    (blocks_df['blockerId'] == blocker_id) & 
    (blocks_df['perdu'] == True)
]

for _, block in lost_blocks.iterrows():
    fig = make_replay(
        game_id=block['gameId'],
        play_id=block['playId'],
        focus_blocker_id=blocker_id
    )
    # Sauvegarder ou afficher
```

### Depuis la Partie 3 (app.py)
```python
import streamlit as st
from src.replay import make_replay

# Dans l'app Streamlit :
if st.button("Voir le replay"):
    fig = make_replay(game_id, play_id, focus_blocker_id)
    st.plotly_chart(fig, use_container_width=True)
```

## 📝 Notes Techniques

### Seuil de Pression
`PRESSURE_THRESHOLD = 2` yards (modifiable dans `replay.py`)

### Performance
- Cache possible avec `@st.cache_data` sur `make_replay()`
- Commencer avec 2-3 matchs pour tester

### Limitation
- 8 semaines de données seulement
- Tracking à 10 Hz (10 frames/seconde)
- Le seuil de 2 yards est une convention

## 🎯 Points de Synchro

- **1:00** : Chacun montre son livrable de base
- **2:00** : Intégration des 3 parties
- **2:30** : Code gelé, focus sur le pitch

## 📞 Contact

**Partie 2 (Replay)** : ✅ Complétée et prête à l'emploi

Pour questions sur le replay :
- Voir `src/replay.py` (tout documenté)
- Tester avec `test_replay.py`
- Les fonctions sont prêtes pour l'intégration

---

**Bon hackathon !** 🏆
