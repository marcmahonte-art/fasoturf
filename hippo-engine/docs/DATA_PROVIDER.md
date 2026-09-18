# Brancher une vraie API de données (#4, #20)

Le moteur ne connaît **jamais** un fournisseur concret : il ne parle qu'à
l'interface `DataProvider`. Ajouter une source = ajouter une classe.

## 1. L'interface

`ml/data/providers/base.py`

```python
class DataProvider(ABC):
    def get_meetings(self, date: str) -> list[dict]: ...
    def get_races(self, date: str) -> list[Race]: ...
    def get_race(self, race_id: str) -> Race | None: ...
    def get_runners(self, race_id: str) -> list[Runner]: ...
    def get_horse_history(self, horse_id: str) -> list[dict]: ...
    def get_jockey_history(self, jockey_id: str) -> list[dict]: ...
    def get_trainer_history(self, trainer_id: str) -> list[dict]: ...
    def get_odds(self, race_id: str) -> dict[int, list[dict]]: ...
    def get_results(self, race_id: str) -> RaceResult | None: ...
```

## 2. Les fournisseurs livrés

| `DATA_PROVIDER` | Classe | Source | Réseau requis |
|---|---|---|---|
| `mock` | `MockDataProvider` | dataset DEMO déterministe | non |
| `sqlite` | `SqliteDataProvider` | `pmu_lonab.db` (réel) | non |
| `pmu` | `PmUProvider` | API PMU en direct | oui |
| `external` | `PmUProvider` | API tierce (`EXTERNAL_API_URL`) | oui |

Le mode `mock` garantit que **le système fonctionne en DEMO sans aucune API
externe**. Dès que `DATA_PROVIDER != mock`, les données réelles sont utilisées.

Si `pmu` est demandé mais que le réseau est indisponible, la factory
(`build_provider`) retombe automatiquement sur `sqlite`, puis sur `mock`.

## 3. Ajouter votre propre fournisseur

```python
# ml/data/providers/mon_api.py
from .base import DataProvider

class MonApiProvider(DataProvider):
    name = "mon_api"

    def get_race(self, race_id: str) -> Race | None:
        raw = self._http_get(f"/races/{race_id}")
        return normalize_race(raw)      # <-- normalisation OBLIGATOIRE
```

Puis dans `factory.py` :

```python
if kind == "mon_api":
    return MonApiProvider(...)
```

### Règle absolue

**Aucune donnée externe n'entre sans passer par `normalize_*`** (#6). Les
formats varient d'un fournisseur à l'autre :

```
Fournisseur A :  {"horse_name": "..."}
Fournisseur B :  {"runner": {"horse": {"name": "..."}}}
Format interne : runner.horse.name          <- toujours
```

`ml/data/normalize.py` sait déjà résoudre les emplacements courants
(`HORSE_NAME_PATHS`) et convertit les cotes fractionnelles (`"15/1"` → `16.0`).

## 4. Mapping du schéma source réel

Le schéma `pmu_lonab.db` ne possède pas de clé `course_id` exploitable
(**elle est vide**). Le mapping retenu, vérifié le 2026-09-13 :

```
courses.document_id  ==  partants.document_id   (1 course = 1 document)
courses.date         ==  resultats.date         (726/734 dates : 1 course)
```

Statistiques du dataset étiqueté réel :

- **711** courses exploitables (≥ 8 partants, arrivée connue)
- **10 044** lignes partant
- **708** courses utilisables pour l'entraînement

## 5. Limites connues du schéma source

| Champ | Problème | Conséquence |
|---|---|---|
| `courses.course_id` | vide | jointure par `document_id` |
| `courses.distance_m` | parfois `25` (parsing) | distance < 400 ignorée |
| `courses.discipline` | vide dans 718/929 lignes | discipline parfois inconnue |
| `api_meteo` | table vide | pas de feature terrain/météo |
| `api_partants` | table vide | — |
| `partants_enrichis` | 185 lignes / 13 163 | enrichissement à industrialiser |
| `api_cotes.evolution_cote` | vide | pas de détection de mouvement réelle |
| `resultats.arrivee` | 3 à 5 chevaux | cible Top5 souvent inconnue |

Ces limites sont **explicites** : le moteur ne fait pas semblant de les ignorer.
