# Hippo Engine

Moteur IA de pronostics hippiques — ingestion, features, modèles, value,
fusion, génération de Quinté, backtest et traçabilité.

> **Ce n'est pas un site vitrine.** C'est un moteur exécutable, branché sur la
> base réelle du projet (`pmu_lonab.db`, 711 courses exploitables).

---

## Démarrage rapide

Aucune dépendance externe n'est requise (Python 3.11+ suffit).

```bash
cd hippo-engine

# 1. Lister les courses exploitables de la base réelle
python -m ml.scripts.run_prediction --list

# 2. Générer le pronostic complet d'une course
python -m ml.scripts.run_prediction --race 929

# 3. Sortie JSON (format de l'API interne, #27)
python -m ml.scripts.run_prediction --race 929 --json

# 4. Mode DEMO (aucune donnée réelle)
python -m ml.scripts.run_prediction --demo
```

### Entraînement et backtest

```bash
# Entraîner Win / Top3 / Top5 (découpage chronologique)
python -m ml.scripts.train --train-until 2025-06-30 --valid-until 2025-12-31

# Backtest hors-échantillon avec les modèles entraînés
python -m ml.scripts.backtest_cli --from 2026-01-01 --to 2026-09-30 --models

# Backtest complet
python -m ml.scripts.backtest_cli --all --models
```

### Tests

```bash
python -m ml.tests.run_tests      # 47 tests, sans dépendance
python -m pytest ml/tests         # si pytest est installé
```

---

## Résultats mesurés (données réelles, hors échantillon)

Ces chiffres proviennent du backtest sur **228 courses de 2026** jamais vues
à l'entraînement. Ils sont publiés **tels quels**, y compris quand ils sont
mauvais (règle #31 : aucune surpromesse).

| Métrique | Modèle | Favori du marché | Écart |
|---|---|---|---|
| Gagnant trouvé | 18.0 % | 23.2 % | **−5.3 pts** |
| Précision Top 3 | 33.0 % | 36.0 % | −3.0 pts |
| Brier (Top3) | 0.146 | — | 0.25 = aléatoire |

**Lecture honnête : le moteur est proche du marché mais ne le bat pas
encore.** C'est le point de départ attendu sur un marché semi-efficient.
Le premier essai (score RANK seul, sans entraînement) ne faisait que
10.2 % — l'entraînement apporte donc **+7.8 points**.

Piste d'amélioration identifiée : intégrer la cote comme composante du
Fusion Engine, et ajouter les données manquantes (`api_meteo` vide,
`partants_enrichis` à 185 lignes sur 13 163).

### Qualité des modèles entraînés (validation)

| Modèle | ROC-AUC | Brier | Log loss | n |
|---|---|---|---|---|
| win | 0.677 | 0.062 | 0.236 | 2 408 |
| top3 | 0.675 | 0.148 | 0.464 | 2 408 |
| top5 | 0.658 | 0.208 | 0.603 | 1 115 |

Tous > 0.5 : le signal est réel, mais faible (marché efficace).

---

## Architecture

```
Next.js (App Router)  <- phase ultérieure
      |
API interne
      |
Prediction Service  -- generate_prediction(raceId)
      |
      +--> Python ML Service (features, RANK, modèles, value, fusion, quinté)
      +--> SQLite / PostgreSQL (données normalisées)
```

Détail complet : [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

---

## Les 20 briques du cahier des charges

| # | Brique | Fichier | État |
|---|---|---|---|
| 1 | Ingestion | `ml/data/providers/` | fait |
| 2 | Normalisation | `ml/data/normalize.py` | fait |
| 3 | Stockage | `db/migrations/`, `sqlite_provider.py` | fait |
| 4 | Historique | `sqlite_provider._build_history_index` | fait |
| 5 | Feature engineering | `ml/features/engineering.py` | fait |
| 6 | Modèle RANK | `ml/models/rank.py` | fait |
| 7 | Modèle TOP3 | `ml/models/probabilistic.py` | fait |
| 8 | Modèle CATBOOST | `ml/models/catboost_model.py` | fait |
| 9 | Value engine | `ml/prediction/value.py` | fait |
| 10 | Fusion engine | `ml/prediction/fusion.py` | fait |
| 11 | Génération Quinté | `ml/prediction/quinte.py` | fait |
| 12 | Tiercé / Quarté+ | `ml/prediction/quinte.py` | fait |
| 13 | Confiance | `ml/prediction/engine.py` | fait |
| 14 | Traçabilité | `model_version`, `prediction_version` | fait |
| 15 | Validation résultats | `ml/evaluation/backtest.py` | fait |
| 16 | Calcul des performances | `ml/evaluation/metrics.py` | fait |
| 17 | API interne | contrat dans `engine.as_api_payload()` | contrat prêt |
| 18 | Admin | `db/migrations/002_views.sql` | vues prêtes |
| 19 | Dashboard public | — | phase ultérieure |
| 20 | API réelles | `providers/pmu.py` | fait |

---

## Règles non négociables

1. **Pas de data leakage** — test bloquant : `ml/tests/test_no_leakage.py`
2. **Pas de surpromesse** — toute stat publiée porte période + volume + méthode
3. **Séparation stricte** — donnée réelle / demo / prédiction / résultat
4. **Tout est explicable** — RANK expose ses contributions, les facteurs sont
   dérivés des features réellement calculées

---

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — inventaire + architecture cible
- [`docs/PRONOSTIC_LOGIC.md`](docs/PRONOSTIC_LOGIC.md) — logique de sélection
- [`docs/DATA_PROVIDER.md`](docs/DATA_PROVIDER.md) — brancher une vraie API
- [`docs/ML.md`](docs/ML.md) — modèles et entraînement
- [`docs/BACKTEST.md`](docs/BACKTEST.md) — méthodologie de backtest
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) — déploiement et cron
