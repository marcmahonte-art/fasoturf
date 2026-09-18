# Architecture — Hippo Engine

Moteur IA de pronostics hippiques. Ce document décrit **ce qui existe déjà**,
**l'architecture cible**, et **la frontière entre les deux**.

---

## 1. Inventaire technique (état au 2026-09-13)

### 1.1 Ce qui existe et qui est réutilisable

| Actif | Emplacement | État | Réutilisation |
|---|---|---|---|
| Base SQLite unifiée (37 Mo) | `pmu-lonab-scraper/data/processed/pmu_lonab.db` | 20 tables, données réelles | **Source principale du provider `sqlite`** |
| Scrapers LONAB | `pmu-lonab-scraper/app/scraper/` | fonctionnel | Provider `pmu` / cron de synchro |
| Parseurs PDF | `pmu-lonab-scraper/app/parser/` | 99.7 % de succès | Alimente la base |
| Enrichissement PMU | `pmu-lonab-scraper/app/enrichment/` | `PMUDataEnricher`, `pmu_client` | Réutilisé tel quel |
| Prédicteur existant | `pmu-lonab-scraper/app/prediction/race_predictor.py` | heuristique (cote + musique + déferrage) | **Legacy** : remplacé par le moteur RANK/CatBoost, conservé pour comparaison |
| Tests | `pmu-lonab-scraper/tests/` | pytest | Complétés par `ml/tests/` |
| CSV externe | `classeur/aspiturf_2020_01.csv` | 44 Mo | Feature secondaire |

### 1.2 Contenu réel de la base (vérifié)

| Table | Lignes | Qualité |
|---|---|---|
| `courses` | 929 | 1995→2026, 734 jours, 86 hippodromes |
| `partants` | 13 163 | 98 % avec cote, 93 % gains, 100 % chrono + performances |
| `resultats` | 939 | 920 avec arrivée réelle, 930 avec rapport |
| `api_cotes` | 27 243 | par type de pari — **`evolution_cote` vide** |
| `api_pronostics` | 407 | source DATAHIPPIQUE |
| `ecd_courses` / `ecd_paris` | 6 509 / 11 879 | courses en direct |
| `partants_enrichis` | 185 | déferré, musique, père/mère, robe |

**Lacunes identifiées :** `api_meteo` et `api_partants` sont **vides** ;
`partants_enrichis` est sous-peuplée (185 lignes sur 13 163).

### 1.3 Ce qui n'existe PAS

- Aucun projet Next.js / TypeScript.
- Aucun serveur PostgreSQL (seulement SQLite).
- Aucun modèle ML entraîné (ni RANK, ni CatBoost).
- Aucune API interne, aucun dashboard.

---

## 2. Décision d'architecture

Le cahier des charges demande Next.js + PostgreSQL. L'environnement local
n'a **ni Postgres ni serveur Node persistant**. Pour ne pas bloquer :

- **Le moteur ML est écrit en Python pur** (dépendances lourdes optionnelles).
  Il lit la base réelle via une abstraction `DataProvider`.
- **Le schéma PostgreSQL est fourni** (`db/migrations/`) et le provider `postgres`
  est prêt, mais reste inactif tant que `DATABASE_URL` n'est pas défini.
- **Le frontend Next.js** consomme l'API interne — phase ultérieure.

Principe directeur : **le système fonctionne en DEMO sans aucune API externe**,
et bascule sur les données réelles dès que `DATA_PROVIDER != mock`.

---

## 3. Architecture cible

```
Next.js (App Router)
      │
      ▼
API interne  ── Route Handlers + Zod
      │
      ▼
Prediction Service  ── generatePrediction(raceId)
      │
      ├──────────────┐
      ▼              ▼
Python ML Service   PostgreSQL / SQLite
 (features, RANK,    (données normalisées)
  CatBoost, Value,
  Fusion, Quinté)
```

### 3.1 Arborescence implémentée

```
hippo-engine/
├── db/migrations/          001_init.sql, 002_views.sql
├── docs/                   ARCHITECTURE, DATA_PIPELINE, ML, MODELS,
│                           BACKTEST, DATA_PROVIDER, PRONOSTIC_LOGIC
└── ml/
    ├── config.py           Config centralisée (env)
    ├── data/
    │   ├── schema.py       Schéma interne + validation
    │   ├── normalize.py    normalizeRace/Runner/Horse/Jockey/Trainer/Odds/Result
    │   └── providers/      base, mock, sqlite, pmu, factory
    ├── features/
    │   └── engineering.py  Vecteurs de features (anti-leakage)
    ├── models/
    │   ├── rank.py         RANK_SCORE explicable
    │   ├── win.py / top3.py / top5.py
    │   ├── catboost_model.py
    │   └── artifacts/      Modèles sérialisés
    ├── prediction/
    │   ├── value.py        Value engine
    │   ├── fusion.py       Fusion engine
    │   ├── quinte.py       Générateurs Quinté/Tiercé/Quarté
    │   └── engine.py       Orchestrateur generatePrediction()
    ├── evaluation/         metrics.py, backtest.py
    ├── registry/           Model registry
    ├── scripts/            run_prediction.py, train.py, backtest_cli.py
    └── tests/
```

---

## 4. Frontière DONNÉE RÉELLE / DEMO / PRÉDICTION

Règle absolue (#49 du cahier des charges) — chaque objet porte son origine :

| Catégorie | Marqueur | Interdiction |
|---|---|---|
| Donnée réelle | `source="real"` | — |
| Donnée demo | `source="demo"`, préfixe `DEMO` | Ne jamais l'afficher comme un résultat réel |
| Prédiction | `prediction_version` + `model_version` | Ne jamais la présenter comme un résultat |
| Résultat réel | `race_results` | — |
| Statistique calculée | période + n + méthode obligatoires | Jamais de « 95 % fiable » sans base vérifiable |

Toute statistique affichée doit porter : **période · nombre de courses · définition · méthodologie**.
