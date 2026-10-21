# Weak Link — l'app (Partie 3)

Scouting de protection de passe pour un coach, sur un écran : **quel bloqueur adverse
craque, dans quelles situations, avec le replay animé comme preuve.**

## Lancer

```bash
pip install -r ../requirements.txt
cd frontend
streamlit run app.py
```

L'app tourne telle quelle, sans attendre les autres parties : elle démarre en **mode
démo** et bascule automatiquement sur les vraies données quand elles arrivent.

## Le contrat avec les autres parties

- **Partie 1 (data & métrique)** — dès que `data/processed/blocks.csv` existe au format
  prévu (`gameId, playId, blockerId, temps_tenu, perdu, …`), l'app le lit à la place de
  la démo. Les colonnes manquantes sont complétées depuis les CSV bruts, donc une version
  partielle suffit. Le bandeau « mode démo » disparaît tout seul.
- **Partie 2 (replay)** — si `src/replay.py` expose
  `make_replay(game_id, play_id, focus_blocker_id=None) -> go.Figure`, l'app l'utilise.
  Sinon elle affiche son propre terrain animé (même signature). Si le module de l'équipe
  plante, repli automatique et message discret, l'app ne casse jamais pendant la démo.

Le mode démo utilise les **vrais duels PFF** (bloqueur, défenseur bloqué, pressions,
sacks) ; seul le `temps_tenu` est simulé en attendant la métrique tracking.

## Organisation

```
frontend/
  app.py              orchestration : filtres, verdict, ligne, classement, dossier, replay
  .streamlit/
    config.toml       thème (couleurs, polices auto-hébergées, static serving)
  static/fonts/       Archivo + IBM Plex Mono (licence OFL incluse)
  weaklink/
    data.py           chargement + bascule démo/réel, cache par mtime
    mock.py           blocks.csv de démo au format exact de la Partie 1
    stats.py          classement, indice de poste, intervalles, courbe de rupture
    charts.py         graphiques Plotly
    replay.py         terrain animé (fallback) + pont vers src/replay.py
    ui.py             blocs HTML (st.html) et composants cliquables (components v2)
    theme.py          design system : couleurs, polices, template Plotly
    labels.py         vocabulaire FR + formatage des nombres
    paths.py          résolution des chemins (data/ ou data/raw/)
```

## Choix de design

- **Rapport de scouting imprimé** : papier crème, encre presque noire, rouge « crayon
  gras », surligneur jaune. Une famille condensée (Archivo) pour les titres, mono (IBM
  Plex) pour les chiffres. Pas de dégradé, pas de carte flottante générique.
- **Honnête sur les petits échantillons** : chaque taux montre son intervalle de
  confiance à 80 % ; en dessous du seuil de duels, le joueur est affiché mais non classé.
- **Comparaison par poste** : un tackle est comparé aux tackles, pas aux centres.
  L'indice 100 = moyenne NFL du poste dans la même situation.
- **Courbe de rupture (Kaplan–Meier)** : ne pénalise pas les passes rapides, contrairement
  à une simple moyenne du temps tenu.
