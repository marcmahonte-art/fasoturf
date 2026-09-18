# ADR-001 — LONAB comme socle, fournisseurs externes derrière adapters

- **Statut :** Accepté
- **Date :** 2026-09-13
- **Phase :** 0 (architecture)
- **Décideur :** propriétaire du projet
- **Impacte :** Phases 3, 4, 12, 13, 21, 24

---

## 1. Contexte

L'audit (`AUDIT_REPORT.md`) a établi deux faits :

1. **Le socle LONAB existe déjà et il est solide** : 2 756 PDF bruts immuables,
   99,7 % parsés, 20 tables, 711 courses labellisées exploitables immédiatement.
2. **Les données externes manquent** : `api_meteo` vide, aucune évolution de
   cote, aucun identifiant externe.

La tentation naturelle serait de « brancher les vraies API » dès le début pour
combler les trous. **C'est précisément ce qu'il faut éviter.**

Les conditions d'accès et de réutilisation des sources externes
(PMU, LeTROT, France Galop, Turf.bzh, fournisseurs météo) peuvent changer :
tarification, quotas, CGU, disponibilité, fermeture d'endpoint. Une plateforme
dont la logique métier dépend d'un tiers non contractuel devient fragile et
non reproductible.

---

## 2. Décision

### 2.1 LONAB est le socle — il n'est jamais remplacé

> **Les données LONAB sont la source de vérité. Le moteur les enrichit,
> il ne les substitue jamais.**

Règles opérationnelles :

| Règle | Conséquence technique |
|---|---|
| Une donnée LONAB n'est jamais écrasée par une donnée externe | Écriture externe dans des tables séparées, jamais en `UPDATE` sur les tables LONAB |
| Les PDF bruts restent immuables | `data/raw/` en lecture seule (§52) |
| Une panne externe ne casse jamais le pipeline LONAB | Le pipeline doit produire un résultat complet **sans aucune source externe** |
| Toute donnée externe est traçable | `provider`, `source_id`, `source_timestamp`, `retrieved_at` obligatoires |
| Les identifiants coexistent | Un `horse_id` interne peut porter N identifiants externes (§14) |

### 2.2 Tous les fournisseurs externes sont derrière des adapters, **désactivés par défaut**

Aucune source externe n'est requise pour faire tourner le système.
Elles sont **opt-in**, activées une par une, après vérification.

```
providers/
    lonab/           ← SOCLE, toujours actif
    mock/            ← DEMO, aucune dépendance
    turf_bzh/        ← à vérifier, désactivé
    letrot/          ← à vérifier, désactivé
    france_galop/    ← à vérifier, désactivé
    pmu/             ← à vérifier, désactivé
    weather/         ← à vérifier, désactivé
```

### 2.3 Un adapter ne s'active qu'après vérification manuelle

> **Aucun endpoint, champ, quota ou clé n'est inventé.** (spec §12)

Chaque adapter démarre à l'état `UNVERIFIED` et lève explicitement une erreur
tant que ses conditions d'accès et de réutilisation n'ont pas été confirmées
par une source officielle. Un adapter non vérifié **ne peut pas** être activé
en production.

---

## 3. Contrat d'interface

Tout adapter implémente la même interface — le moteur ne connaît jamais un
fournisseur concret (déjà en place dans `hippo-engine/ml/data/providers/base.py`) :

```python
class DataProvider(ABC):
    name: str
    status: ProviderStatus          # ACTIVE | UNVERIFIED | DISABLED

    def get_races(date) -> list[Race]
    def get_race(race_id) -> Race | None
    def get_runners(race_id) -> list[Runner]
    def get_horse_history(horse_id) -> list[dict]
    def get_jockey_history(jockey_id) -> list[dict]
    def get_trainer_history(trainer_id) -> list[dict]
    def get_odds(race_id) -> dict
    def get_results(race_id) -> RaceResult | None
    def get_weather(race_id) -> Weather | None      # optionnel
```

Chaque adapter doit fournir, sans exception :

`configuration` · `logs` · `timeout` · `retry` · `rate limit` · `cache` · `tests`

---

## 4. Matrice des fournisseurs — état réel, rien d'inventé

| Fournisseur | Statut | Donnée attendue | Vérification requise |
|---|---|---|---|
| **LONAB** | ✅ **ACTIF (socle)** | Programme, partants, résultats, REP, ECD, commentaires presse | — |
| **Mock** | ✅ **ACTIF (DEMO)** | Dataset synthétique déterministe | — |
| **PMU** | ⚪ `UNVERIFIED` | Programmes, cotes, partants | Conditions d'accès et de réutilisation **à confirmer** |
| **LeTROT** | ⚪ `UNVERIFIED` | Courses trot, drivers | **À confirmer** |
| **France Galop** | ⚪ `UNVERIFIED` | Programmes plat/obstacle, engagements | **À confirmer** (partenariat ?) |
| **Turf.bzh** | ⚪ `UNVERIFIED` | **Capacités inconnues — non documentées dans ce projet** | **À documenter avant toute ligne de code** |
| **Météo** | ⚪ `UNVERIFIED` | Température, vent, précipitations | Fournisseur **non choisi** ; ne pas coder avant sélection |

> ⚠️ **Aucune ligne de cette matrice n'autorise à écrire un endpoint.**
> Le tableau décrit des *intentions*, pas des capacités vérifiées.

### 4.1 Point de vigilance — Turf.bzh

Turf.bzh a été mentionné comme source envisageable. **Ses capacités, ses
conditions d'accès et la licéité de réutilisation de ses données ne sont pas
établies.** Avant tout développement :

1. identifier la nature du service (éditorial ? agrégateur ? opérateur ?) ;
2. lire ses conditions d'utilisation et sa politique de réutilisation ;
3. vérifier l'existence d'une API publique ou d'une autorisation écrite ;
4. **en l'absence de ces éléments : ne rien implémenter.**

---

## 5. Enrichissement, jamais substitution — schéma

```
        SOCLE LONAB (source de vérité)
                │
                │  jamais écrasé
                ▼
    ┌───────────────────────────┐
    │  tables LONAB             │
    │  documents, courses,      │
    │  partants, resultats,     │
    │  rep_documents, ecd_*     │
    └───────────────────────────┘
                │
                │  jointure par identifiants internes
                ▼
    ┌───────────────────────────┐
    │  tables d'enrichissement  │   ← écriture externe ICI uniquement
    │  external_entities        │
    │  external_entity_mapping  │
    │  weather_race             │
    │  race_odds (externe)      │
    └───────────────────────────┘
```

Une donnée externe absente produit un **trou explicite**, jamais une valeur
inventée ni une valeur LONAB modifiée.

---

## 6. Dégradation gracieuse

| Situation | Comportement attendu |
|---|---|
| Aucun fournisseur externe configuré | Le moteur produit une prédiction complète sur le socle LONAB |
| Fournisseur externe en panne | Pipeline LONAB terminé normalement ; l'erreur est journalisée |
| Donnée externe partielle | Feature correspondante marquée indisponible ; qualité dégradée explicitement |
| Adapter `UNVERIFIED` sollicité | Erreur explicite, jamais de donnée simulée silencieuse |

> **Test d'acceptation (spec §64, test 8) :**
> « API indisponible → le pipeline ne casse pas les données LONAB. »

---

## 7. Conséquences

### Positives

- Le système est **reproductible et exécutable hors ligne** dès la Phase 1.
- Aucune dépendance contractuelle non maîtrisée.
- Ajouter une source = ajouter un adapter, **sans toucher au moteur**.
- La provenance est garantie : on sait toujours d'où vient chaque donnée.
- Une source qui ferme n'invalide pas l'historique déjà collecté.

### Négatives / coûts assumés

- Certaines features (météo, évolution de cotes) resteront **indisponibles**
  tant qu'aucun fournisseur n'est vérifié. C'est un choix, pas un oubli.
- L'intégration d'un fournisseur prendra plus de temps (vérification préalable).
- Le dataset d'entraînement reste limité au socle LONAB + ECD en attendant.

### Arbitrage retenu

> **Mieux vaut un moteur complet sur données maîtrisées qu'un moteur
> incomplet dépendant de sources non contractuelles.**

---

## 8. Impacts sur les phases

| Phase | Impact |
|---|---|
| 3 — Migration LONAB | Le socle est migré **tel quel**, sans altération |
| 4 — Matching | Les tables `external_*` sont créées **vides** ; le matching fonctionne en interne d'abord |
| 6 — Feature Engine | Chaque feature externe est **optionnelle** et marquée `unavailable` si absente |
| 12-14 — Modèles | Entraînés **sans** feature externe au départ ; l'ajout se mesure ensuite (§73) |
| 21-24 — API / Automation | Les jobs `external_sync` et `weather_sync` sont **désactivés** par défaut (§55) |

---

## 9. Décisions liées

- `AUDIT_REPORT.md` — état des lieux et plan de migration
- §9-10 de la spec V2 — identifiants internes et entity matching
- §12-14 — providers, provenance
- §52 — raw data immuable
- §68 — mode DEMO sans secret
- §71 — DATA QUALITY > MODEL COMPLEXITY

---

*Cette décision s'applique à compter de la Phase 1. Toute introduction d'un
fournisseur externe nécessitera un nouvel ADR documentant la vérification
préalable de ses conditions d'accès.*
