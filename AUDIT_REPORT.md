# AUDIT_REPORT.md

**Projet :** PMU'B LONAB — plateforme d'analyse et de pronostics hippiques
**Phase :** 0 — AUDIT EXISTANT (règle 0 : audit avant de coder)
**Date de l'audit :** 2026-09-13
**Périmètre :** `C:\Users\Lenovo\Desktop\PMU` (repo + base de données)
**Statut :** ⚠️ Aucune modification effectuée. Audit en lecture seule.

---

## 1. Architecture actuelle

### 1.1 Vue d'ensemble

```
Scrapers LONAB ──> PDF bruts ──> Parseurs ──> SQLite ──> Prédicteur heuristique
   (requests)      (data/raw)     (PyMuPDF)  (pmu_lonab.db)   (race_predictor)
                                                                    │
                                            Enrichissement PMU ─────┘
```

**Langage :** Python 3.13 (aucun projet Node/Next.js existant)
**Framework :** aucun — scripts CLI + modules `app/`
**Base :** SQLite unique, 37 Mo, 20 tables
**Point d'entrée :** `pmu-lonab-scraper/main.py` (1 248 lignes)

### 1.2 Structure des dossiers

| Dossier | Contenu | Rôle |
|---|---|---|
| `pmu-lonab-scraper/app/scraper/` | `lonab.py`, `programmes.py`, `resultats.py`, `course_direct.py` | Collecte LONAB |
| `pmu-lonab-scraper/app/downloader/` | `pdf_downloader.py` | Téléchargement PDF |
| `pmu-lonab-scraper/app/parser/` | `document_classifier`, `journal_parser`, `resultat_parser`, `rep_parser`, `course_direct_parser`, `normalizer`, `matcher` | Extraction |
| `pmu-lonab-scraper/app/enrichment/` | `enricher.py`, `matcher.py`, `pmu_client.py` | Enrichissement PMU |
| `pmu-lonab-scraper/app/prediction/` | `race_predictor.py`, `jockey_activity.py` | Prédicteur heuristique |
| `pmu-lonab-scraper/app/quality/` | `validator.py` | Contrôle qualité |
| `pmu-lonab-scraper/app/models/` | `document.py`, `parser_models.py` | Modèles Pydantic |
| `pmu-lonab-scraper/data/raw/` | 2 756 PDF | **Données sources immuables** |
| `pmu-lonab-scraper/data/processed/` | `pmu_lonab.db` | Base unifiée |
| `hippo-engine/` | Moteur ML Python (travail antérieur) | Voir §7 |
| `classeur/` | `aspiturf_2020_01.csv` (44 Mo) | Donnée externe |

---

## 2. Base de données actuelle

**Fichier :** `pmu-lonab-scraper/data/processed/pmu_lonab.db` (37,8 Mo)
**SGBD :** SQLite 3 — **pas de PostgreSQL installé sur la machine**

### 2.1 Tables et volumes réels (vérifiés)

| Table | Lignes | Usage | État |
|---|---|---|---|
| `documents` | 2 711 | Métadonnées PDF (SHA, type, date) | ✅ |
| `courses` | 929 | Courses parsées | ⚠️ |
| `partants` | 13 163 | Chevaux par course | ✅ |
| `resultats` | 939 | Arrivées + rapports | ⚠️ |
| `commentaires` | 14 015 | **Commentaires presse par cheval** | ⚠️ |
| `api_cotes` | 27 243 | Cotes par type de pari | ⚠️ |
| `api_courses` | 407 | Courses via API PMU | ✅ |
| `api_pronostics` | 407 | Pronostics presse (DATAHIPPIQUE) | ✅ |
| `api_rapports` | 2 492 | Rapports API | ✅ |
| `api_ecuries` | 2 | Écuries | ❌ quasi vide |
| `ecd_documents` | 800 | Espace Course en Direct | ✅ |
| `ecd_courses` | 6 509 | Courses ECD | ✅ |
| `ecd_paris` | 11 879 | Paris ECD | ✅ |
| `rep_documents` | 45 | Reports (REP) | ✅ |
| `partants_enrichis` | 185 | Déferré, musique, généalogie | ❌ 1,4 % |
| `api_meteo` | **0** | Météo | ❌ **VIDE** |
| `api_partants` | **0** | Partants API | ❌ **VIDE** |
| `media_selections` | **0** | Sélections média | ❌ **VIDE** |
| `classements` | 1 | — | ❌ inutilisée |

### 2.2 Relations réelles (⚠️ point critique)

> **CORRECTION (mesurée en Phase 1) — `course_id` n'est PAS vide.**
> `courses.course_id` est renseigné sur **610 / 929 lignes (66 %)** et
> `partants.course_id` sur **8 642 / 13 163 (66 %)** ; `resultats.course_id`
> sur 934 / 939 (99 %).
>
> **Mais il n'est pas exploitable comme clé** — pour une raison différente :
> 1. **Non unique** : 610 lignes remplies → seulement **604 valeurs distinctes**
>    (6 collisions, ex. `1995-07-18_DEAUVILLELATOUQUES_C8` rattaché à **4 documents**).
> 2. **Format hétérogène** : deux familles coexistent —
>    `JH_<date>` (296 lignes) et `<date>_<HIPPODROME>_C<n>` (314 lignes).
> 3. **Sémantique documentaire** : la valeur est dérivée du PDF source, pas d'un
>    identifiant de course PMU. Toutes les lignes `courses` proviennent de
>    documents `JOURNAL` (929 / 929).

Les jointures réelles, vérifiées :

```
courses.document_id  ==  partants.document_id    (1 course = 1 document)
courses.date         ==  resultats.date          (710 dates communes)
courses.date         == ecd_documents.date       (non vérifié à ce stade)
resultats.document_id ∈ espace d'ID distinct de courses.document_id
```

**Conséquence :** toute la migration doit se baser sur `document_id` + `date`,
jamais sur `course_id` (non unique).

### 2.3 Champs clés disponibles

| Table | Champs exploitables | Champs vides / inutilisables |
|---|---|---|
| `courses` | `date`, `hippodrome`, `discipline`, `distance_m`, `montant_euros`, `titre` | `reunion`, `course_num`, `heure_depart`, `type_course` ; `course_id` renseigné à 66 % mais **non unique** |
| `partants` | `numero`, `nom_cheval_normalized`, `cote_decimale`, `gains_euros`, `driver_normalized`, `entraineur_normalized`, `performances_structured`, `age`, `sexe` | `poids`, `corde` ; `course_id` renseigné à 66 % |
| `resultats` | `date`, `type_pari`, `arrivee` (entiers), `arrivee_complete` (dicts), `rapport_gagnant_euros` | `course_id` renseigné à 99 % (espace d'ID distinct) |
| `rep_documents` | `game_type`, `date_document`, `date_course_cible`, `report_ordre_euros`, `tierce_v_value` | — |

**Formats d'arrivée (deux formats coexistent) :**

```
arrivee          : '[8, 11, 12, 6, 2]'                    → entiers
arrivee_complete : '[{"position":1,"numero":8}, ...]'      → dicts
```

---

## 3. Données disponibles

### 3.1 Volume exploitable

| Indicateur | Valeur |
|---|---|
| Courses avec ≥ 8 partants **et** arrivée connue | **711** |
| Lignes partant labellisables | **10 044** |
| Chevaux distincts | **4 889** |
| Hippodromes distincts | 86 |
| Période couverte | 1995-07-18 → 2026-09-10 |
| Période réellement exploitable (arrivées) | 2024-02-09 → 2026-09-08 |
| ECD (course en direct) | 2025-07-26 → 2026-09-06 |

### 3.2 Sources média / presse — **disponibles mais sous-exploitées**

| Source | Table | Volume | Statut |
|---|---|---|---|
| Commentaires presse par cheval | `commentaires` | 14 015 | ⚠️ 4 945 sans `course_id` |
| Pronostics presse externe | `api_pronostics` | 407 | ✅ source DATAHIPPIQUE |
| Sélections média | `media_selections` | 0 | ❌ **table vide** |

> **Le Media Consensus Engine (spec §20) est donc réalisable à ~70 %** :
> les commentaires existent, mais il faut les rattacher aux courses
> (`course_id` manquant sur 35 % des lignes) et **aucune sélection média
> structurée n'est stockée**. La liste des médias cités dans la spec
> (TURF-FR, LE PARISIEN, L'ALSACE…) **n'est pas vérifiable dans la base** :
> à confirmer par extraction depuis les PDF avant de la coder.

---

## 4. Données manquantes

| Donnée | Table attendue | État réel | Impact |
|---|---|---|---|
| **Météo** | `api_meteo` | **0 ligne** | Weather Engine (§22) impossible en l'état |
| **État de piste officiel** | — | absent | `track_condition` non séparable de la météo |
| **Évolution des cotes** | `api_cotes.evolution_cote` | **vide** | Market Engine (§21) limité : pas de `opening_odds` |
| **Cote de référence** | `api_cotes.cote_reference` | **vide** | idem |
| **Enrichissement cheval** | `partants_enrichis` | 185 / 13 163 (1,4 %) | Père/mère, robe, œillères inexploitables |
| **Poids / corde** | `partants.poids`, `partants.corde` | vides | Features poids/corde (§9) indisponibles |
| **Non-partants structurés** | — | partiel | `NON PARTANT` apparaît comme nom de cheval (35 occurrences) |
| **Identifiants externes** | — | absents | Entity Matching (§10) part de zéro |

---

## 5. Parseurs existants

| Parseur | Fichier | Rôle |
|---|---|---|
| Classifieur de documents | `app/parser/document_classifier.py` | JOURNAL / RESULTAT / REP / ECD |
| Journal hippique | `app/parser/journal_parser.py` | Programme + partants + commentaires |
| Résultats | `app/parser/resultat_parser.py` | Arrivées + rapports |
| REP | `app/parser/rep_parser.py` | Reports — **parse correctement `date_document` ≠ `date_course_cible`** ✅ |
| Course en direct | `app/parser/course_direct_parser.py` | ECD + paris |
| Normalisation | `app/parser/normalizer.py` | Noms, distances, montants |
| Matching | `app/parser/matcher.py` | Rapprochement interne |

**Qualité de parsing déclarée :** 99,7 % de succès sur 2 756 PDF.

### 5.1 Conformité aux exigences V2

| Exigence V2 | État |
|---|---|
| §5 REP ≠ résultat | ✅ `rep_documents` est bien une entité distincte, avec les **deux dates** |
| §6 Arrivées dynamiques (3 ou 4 positions) | ⚠️ partiel — l'arrivée est parsée dynamiquement, mais **3 à 5 positions seulement** |
| §7 TIERCE V séparé | ✅ champ `tierce_v_value` existe et est distinct de `report_ordre` |
| §4 Séparer document_type / game_type | ⚠️ `document_type` existe, `game_type` existe sur REP seulement |

---

## 6. Qualité actuelle — problèmes mesurés

### 6.1 Anomalies chiffrées

| Anomalie | Volume | Sévérité |
|---|---|---|
| `courses.discipline` vide | **718 / 929 (77 %)** | 🔴 Critique |
| `resultats` sans course correspondante (par date) | 220 / 939 | 🟠 Élevée |
| `commentaires.course_id` vide | 4 945 / 14 015 (35 %) | 🟠 Élevée |
| `courses.distance_m` < 400 m (parsing erroné, ex. `25`) | 166 | 🟠 Élevée |
| Cotes nulles ou ≤ 0 | 278 / 13 163 | 🟡 Moyenne |
| Doublons `date` + `hippodrome` | 36 groupes | 🟡 Moyenne |
| Courses sans aucun partant | 5 | 🟡 Moyenne |
| Chevaux nommés `NON PARTANT` | 35 | 🟡 Moyenne |
| `hippodrome` = valeur numérique (ex. `'3'`, `'11'`) | non quantifié | 🟡 Moyenne |

### 6.2 Anomalies structurelles

1. **Clé primaire métier absente** — `course_id` renseigné mais **non unique**
   (604 distincts / 610 remplis), `horse_id` inexistant.
   Les noms sont utilisés comme identifiants (§9 l'interdit).
2. **Pas de séparation RAW / NORMALIZED** — tout est dans une seule base.
3. **Pas de versioning** (`data_version`, `feature_version`, `model_version`).
4. **Pas de `prediction_snapshot`** — impossible de reconstruire l'état au cutoff.
5. **Pas de table de matching externe** (`external_entity_mapping`).

---

## 7. Travail ML déjà réalisé (à réconcilier, pas à refaire)

Le dossier `hippo-engine/` contient un moteur fonctionnel construit lors d'une
itération précédente. **Il ne fait pas partie du périmètre V2 mais doit être
audité avant toute réécriture.**

### 7.1 Ce qui existe et fonctionne

| Brique V2 | État dans `hippo-engine/` |
|---|---|
| Feature Engine (§23-24) | ✅ 34 features, test anti-leakage |
| Baseline Rank (§28) | ✅ `models/rank.py` |
| CatBoost WIN/TOP3/TOP5 (§30) | ✅ 3 modèles entraînés (backend Python pur) |
| Probability Engine (§33) | ✅ Plackett-Luce |
| Value Engine (§45) | ✅ `prediction/value.py` |
| Selection Engine (§42) | ✅ 3 modes partiels |
| Backtest (§38) | ✅ `evaluation/backtest.py` |
| Tests | ✅ 47 tests, 0 échec |

### 7.2 Résultats mesurés — **honnêtes, hors échantillon**

Backtest sur 228 courses de 2026 jamais vues à l'entraînement :

| Stratégie | Gagnant trouvé | Précision Top 3 |
|---|---|---|
| RANK seul (aucun entraînement) | 10,2 % | 23,4 % |
| **Favori du marché (référence)** | **23,2 %** | **36,1 %** |
| Proba Top3 | 20,6 % | 35,4 % |
| Proba modèle WIN | 21,1 % | 35,8 % |
| Fusion actuelle | 18,0 % | 33,0 % |

**Conclusion : le moteur n'a pas encore battu le marché.**

### 7.3 Enseignement majeur pour la V2

> Le diagnostic est sans ambiguïté : **la Fusion actuelle (18,0 %) fait moins
> bien que le modèle WIN seul (21,1 %)**, lui-même en dessous du marché (23,2 %).
> La fusion pondérée dilue le meilleur signal.
>
> Cela **valide la mise en garde de la spec §35** : « NE PAS commencer par
> 30 % CatBoost / 25 % Top3 / 20 % Rank — ces poids peuvent compter plusieurs
> fois la même information. »
>
> **Recommandation : abandonner les pondérations manuelles et passer à un
> ensemble appris sur les données de validation (stacking / meta-model).**

---

## 8. Risques

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| **Le marché est efficient** — le moteur ne battra peut-être jamais la cote | Élevée | 🔴 | Objectif réaliste : égaler puis dépasser marginalement ; mesurer vs favori systématiquement |
| **Données insuffisantes** — 708 courses, 34 features | Élevée | 🔴 | ⚠️ **CORRIGÉ (reconnaissance Phase 3)** : ECD **ne peut PAS** élargir le dataset d'entraînement — `ecd_courses` ne contient **aucun partant** (ni cheval, ni jockey, ni cote), seulement une arrivée de 3 numéros. Les 6 509 courses ECD sont un **corpus course-level** séparé, pas 9× le dataset actuel. Voir `PHASE3_PLAN.md` §2. |
| **Fuite temporelle** lors de la migration | Moyenne | 🔴 | Tests de leakage bloquants (§25, §64) |
| **Matching externe incertain** fusionné à tort | Moyenne | 🟠 | Statut `REVIEW` non auto-promu (§10, §64 test 7) |
| **77 % de disciplines vides** | Certaine | 🟠 | Re-parsing ciblé depuis les PDF bruts |
| **`pip` bloqué par le sandbox** | Certaine | 🟠 | Moteur en Python pur ; CatBoost non installable localement |
| **Pas de PostgreSQL** | Certaine | 🟡 | Migrations SQL fournies, exécutables ailleurs |
| **Écraser la base existante** | Faible | 🔴 | Backup obligatoire avant toute migration (§8) |
| **Surpromesse de performance** | Moyenne | 🔴 | Toute stat publiée porte période + n + méthode (§31) |

---

## 9. Recommandations

### 9.1 Immédiat (avant tout code ML)

1. **Backup de `pmu_lonab.db`** + export CSV de contrôle + SHA256. Non négociable.
2. **Ne pas réécrire les parseurs** — ils fonctionnent (99,7 %).
3. **Ne pas migrer vers PostgreSQL tout de suite** : le schéma V2 doit d'abord
   être validé, et un mapping SQLite→PostgreSQL est trivial ensuite.
4. **Créer les identifiants internes stables** (`horse_id`, `jockey_id`,
   `trainer_id`, `hippodrome_id`) **avant** les features — c'est le vrai
   prérequis bloquant (§9).
5. **Créer un `race_id` déterministe** (le `course_id` existant est rempli à 66 %
   mais **non unique** → inutilisable tel quel) :
   `race_id = sha1(date + hippodrome + document_id)`.

### 9.2 Décisions d'architecture

| Sujet | Recommandation | Justification |
|---|---|---|
| Fusion Engine | **Remplacer les poids manuels par un meta-modèle appris** | §35 + mesure §7.3 |
| Rank Engine | **Conserver comme feature, pas comme vérité** | §28-29 |
| Probabilités | **Calibrer** (Platt / Isotonic) avant publication | §34 |
| Modèle de ranking | **Ajouter CatBoostRanker** — plus adapté que la classification par cheval | §30-D |
| Frontend | **Reporter** — dashboard minimal seulement après validation ML | §57, §69 |
| Infra | **Monolithe modulaire**, pas de Redis/Kafka/Celery | §69 |
| **Sources externes** | **Derrière adapters, désactivées par défaut, LONAB = socle jamais remplacé** | **`docs/ADR-001-socle-lonab-et-adapters.md`** |

### 9.3 Priorité des gains de performance

Par ordre d'impact mesuré ou attendu :

1. **Intégrer le marché dans le modèle** (le favori = 23,2 %, meilleur signal connu)
2. ~~Utiliser les 6 509 courses ECD au lieu des 708 courses actuelles~~ → ⚠️ **INVALIDÉ (reconnaissance Phase 3)** : ECD n'a pas de partants, donc **aucune ligne d'entraînement supplémentaire**. ECD sert à un **modèle course-level** et à l'analyse des masses, pas au modèle par partant. Voir `PHASE3_PLAN.md` §2.
3. **Récupérer les disciplines manquantes** (77 % vides) → re-parsing
4. **Exploiter les 14 015 commentaires presse** comme feature consensus
5. **CatBoostRanker** plutôt que classification indépendante

---

## 10. Plan de migration proposé

Aligné sur l'ordre obligatoire de la spec (§65), adapté à l'état réel.

| Phase | Objet | Prérequis | Bloquant ? |
|---|---|---|---|
| **0** | **Audit** (ce document) | — | ✅ fait |
| 1 | Backup + inventaire données | Phase 0 | 🔴 **oui** |
| 2 | Master Database + identifiants internes | Phase 1 | 🔴 oui |
| 3 | Migration / adaptation LONAB | Phase 2 | 🔴 oui |
| 4 | Race & Entity Matching | Phase 3 | 🟠 |
| 5 | Data Quality | Phase 3 | 🟠 |
| 6 | Feature Engine | Phases 2-5 | 🔴 oui |
| 7 | Baseline Rank | Phase 6 | 🟡 |
| 8 | Backtest Baseline | Phase 7 | 🔴 oui (porte de sortie) |
| 9-12 | CatBoost WIN / TOP3 / TOP5 / Ranker | Phase 8 | 🟡 |
| 13 | Calibration | Phase 9-12 | 🟡 |
| 14 | Ensemble appris | Phase 13 | 🟡 |
| 15-19 | Difficulty / Value / Decision / Selection | Phase 14 | 🟡 |
| 20 | Explanation (LLM) | Phase 19 | 🟡 |
| 21-25 | API / Frontend / Admin / Automation / Monitoring | Phase 20 | ⚪ |

### Points d'arrêt obligatoires (validation avant phase suivante)

- **Après Phase 1** : backup vérifié (checksum) — aucune écriture avant.
- **Après Phase 2** : schéma validé + mapping SQLite→PostgreSQL documenté.
- **Après Phase 8** : **la baseline doit être comparée au favori du marché.**
  Si elle ne fait pas au moins aussi bien, **ne pas passer au ML**.
- **Après Phase 14** : chaque nouveau modèle doit battre le précédent sur
  *même période, même dataset, même cutoff* (§73).

---

## 11. Synthèse

**Ce qui est solide :**
- 2 756 PDF bruts immuables, 99,7 % parsés
- Une base unifiée cohérente (20 tables, 37 Mo)
- Le parsing REP/TIERCE V est **conforme aux exigences V2**
- 711 courses labellisées exploitables immédiatement

**Ce qui bloque :**
- **Pas d'identifiants internes stables** (`course_id` non unique, `horse_id` absent) → prérequis n°1
- 77 % de disciplines vides, 220 résultats orphelins
- Météo, cotes d'évolution, sélections média : **absentes**
- Le moteur ML actuel **n'atteint pas le marché** (18,0 % vs 23,2 %)

**La décision structurante :**
> Le facteur limitant n'est pas le modèle, c'est **la donnée et les
> identifiants**. Conformément au principe §71 (DATA QUALITY > MODEL COMPLEXITY),
> les phases 1 à 6 doivent être traitées avant toute nouvelle itération ML.

---

*Rapport produit en lecture seule. Aucun fichier du projet existant n'a été
modifié. En attente de validation avant Phase 1.*
