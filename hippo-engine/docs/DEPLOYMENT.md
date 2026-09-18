# Déploiement et automatisation (#34, #40, #41)

## 1. Prérequis

| Composant | Version | Obligatoire |
|---|---|---|
| Python | 3.11+ | oui |
| PostgreSQL / Supabase | 14+ | non (SQLite par défaut) |
| Redis | 6+ | non (cache) |
| Node.js | 20+ | pour le frontend Next.js |

Le moteur tourne **sans aucune dépendance externe**.

## 2. Installation

```bash
cd hippo-engine
python -m venv .venv
.venv/Scripts/activate        # Windows
pip install -r requirements.txt   # optionnel
cp .env.example .env
```

## 3. Base de données

### SQLite (par défaut)

Rien à faire : le provider `sqlite` lit `pmu_lonab.db` directement.

### PostgreSQL / Supabase

```bash
psql "$DATABASE_URL" -f db/migrations/001_init.sql
psql "$DATABASE_URL" -f db/migrations/002_views.sql
```

Puis dans `.env` :

```
DATABASE_URL=postgresql://...
DATA_PROVIDER=sqlite   # le provider reste sqlite tant que la synchro n'est pas faite
```

Les vues `v_accuracy_summary` et `v_prediction_accuracy` alimentent le
dashboard admin — elles incluent **période et volume**, conformément à #31.

## 4. Jobs d'automatisation (#34)

| Job | Moment | Commande |
|---|---|---|
| `SYNC_RACES` | matin | `python -m ml.scripts.run_prediction --list` |
| `SYNC_ODDS` | quelques heures avant course | provider `pmu` |
| `GENERATE_PREDICTIONS` | avant course | `python -m ml.scripts.run_prediction --race ID` |
| `SYNC_RESULTS` | après course | provider `pmu` |
| `CALCULATE_PERFORMANCE` | après résultats | `python -m ml.scripts.backtest_cli` |
| `RETRAIN_MODELS` | hebdomadaire | `python -m ml.scripts.train` |

### Exemple de planification (cron Unix)

```cron
0 7  * * *  cd /app/hippo-engine && python -m ml.scripts.run_prediction --list
30 8 * * *  cd /app/hippo-engine && python -m ml.scripts.run_prediction --date $(date +\%F)
0 22 * * *  cd /app/hippo-engine && python -m ml.scripts.backtest_cli --from $(date +\%F)
0 3  * * 1  cd /app/hippo-engine && python -m ml.scripts.train
```

Sur Windows, utiliser le Planificateur de tâches avec les mêmes commandes.

## 5. Sécurité (#40)

- **L'API admin ne doit jamais être publique.** Les endpoints
  `/api/admin/*` exigent une authentification.
- Les clés (`EXTERNAL_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`) restent dans
  `.env`, **jamais dans le frontend**.
- Validation Zod côté TypeScript / `validate_*` côté Python avant toute
  écriture en base.
- Rate limiting sur les routes publiques.
- RLS Supabase si Supabase est utilisé.

## 6. Cache (#35)

Les prédictions peuvent être mises en cache, mais elles doivent **toujours**
être liées à :

```
prediction_version   model_version   data_timestamp
```

Sans ces trois clés, une prédiction mise en cache n'est plus traçable.

## 7. Frontend (phase ultérieure)

Le contrat d'API est déjà défini par `Prediction.as_api_payload()` (#27).
Routes à exposer :

```
GET  /api/races
GET  /api/races/:id
GET  /api/races/:id/runners
GET  /api/predictions/:raceId
POST /api/predictions/generate
GET  /api/odds/:raceId
GET  /api/results/:raceId
GET  /api/performance
POST /api/admin/train-model
GET  /api/admin/model-status
GET  /api/admin/data-status
```
