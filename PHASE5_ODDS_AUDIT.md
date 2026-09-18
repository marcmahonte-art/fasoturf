# PHASE 5 — ADDENDUM : AUDIT EXHAUSTIF DES SOURCES DE COTES DU SOCLE

**Date :** 2026-09-13  
**Statut :** `PASS`  
**Type :** audit read-only — aucune écriture, aucune API externe, aucun modèle.

## Objectif

Le rapport `PHASE5_RECON_REPORT.md` conclut « marché efficient, aucun +EV » sur la base de  
`partants.cote_decimale`. Avant de figer cette conclusion, il fallait vérifier une hypothèse  
critique : **existe-t-il ailleurs dans le socle une source de cotes plus fiable, ou un  
mouvement de cote exploitable ?** Cet addendum inventorie **toutes** les sources de cotes.

## Inventaire — tous les champs liés aux cotes

| Table          | Champs liés aux cotes                                                                 | État réel mesuré                                                      |
| -------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `partants`     | `cote_raw`, `cote_decimale`                                                           | **12 885 lignes remplies (~98 %)** — seule source de cotes utilisable |
| `api_cotes`    | `numero`, `cote_directe`, `masse_enjeu`, `cote_reference`, `evolution_cote`, `risque` | **COQUILLE VIDE** (voir ci-dessous)                                   |
| `api_partants` | `dernier_rapport_direct`, `dernier_rapport_reference`                                 | **0 ligne** (table vide)                                              |
| `api_rapports` | `rapports_consolides`, `masse_partager`, `data_json`                                  | **2 492 lignes** — dividendes **finaux** (387 courses en SG)          |
| `resultats`    | `rapport_gagnant_euros`, `rapport_place_a/b`, `map_paris_euros`                       | présents (paiements finaux)                                           |
| `api_meteo`    | —                                                                                     | **0 ligne**                                                           |
| `ecd_paris`    | `type_pari`, `nb_paris`                                                               | masses de paris ECD, sans cote par cheval                             |

## 🔴 Découverte n°1 — `api_cotes` est une coquille vide

**27 243 lignes, mais AUCUNE donnée de cote.** Couverture mesurée (type `E_SIMPLE_GAGNANT`) :

| Colonne          | Valeur non nulle |
| ---------------- | ---------------- |
| `numero`         | **0**            |
| `cote_directe`   | **0**            |
| `masse_enjeu`    | **0**            |
| `cote_reference` | **0**            |
| `evolution_cote` | **0**            |
| `risque`         | **0**            |
| `updatetime`     | 4 255            |
| `synced_at`      | 4 255            |

➡️ Le scraper a créé les lignes et écrit **uniquement les horodatages**. Il n'y a  
**aucune cote PMU directe**, **aucune masse d'enjeu**, **aucune évolution de cote** dans le socle.  
Les 387 courses × types de pari ne portent que `updatetime` / `synced_at`.

**Vérification du mouvement de cote** : pour chaque couple (course, type, cheval),  
`COUNT(DISTINCT updatetime) = 1` → **un seul instantané**, pas de série temporelle.

## 🔴 Découverte n°2 — les seules cotes sont au format fractionnaire

`partants.cote_raw` est au format **`N/1`** (ex. `35/1`, `39/1`, `26/1`, `9/1`), et  
`cote_decimale = N` (le numérateur seul). Statistiques : min 2,00 · moyenne 24,17 · max 200,00.

⚠️ **Deux réserves importantes** :

1. Le format `N/1` est un format **britannique / bookmaker**, pas le format pari-mutuel français  
   (`rapport` décimal). La provenance exacte de ces cotes n'est **pas établie** par le socle.
2. Le **booksum médian = 1,075** (overround ~7,5 %) et **226/704 courses ont un booksum < 1**  
   (impossible pour un marché clôturé cohérent). Ces cotes ne forment donc **pas un marché  
   pari-mutuel final** — ce sont des cotes **probables pré-course**.

## Ce que cela change (et ce que cela ne change pas)

**Ce qui NE change pas — la conclusion de fond reste valide :**

- Il n'existe **aucun mouvement de cote** dans le socle (instantané unique) → l'information des  
  parieurs informés, seul edge théorique documenté, est **absente**.
- Aucune source alternative ne fournit un marché par cheval exploitable.
- Quelle que soit la source, **le prélèvement structurel doit être battu** et aucune tranche  
  n'y parvient (Phase 5 : meilleure tranche −9,66 %, favori −11,79 %).

**Ce qui DOIT être nuancé :**

- L'**amplitude** exacte (−17,08 % de ROI global) repose sur **une seule source de cotes, d'un  
  seul instantané, de provenance non vérifiée**. Elle doit être lue comme **indicative**, pas exacte.
- Il n'a **pas été possible** d'apparier `partants` (format `date_hippodrome_Cn`) aux dividendes  
  finaux `api_rapports` (format `DDMMYYYY_Rn_Cn`) : `courses.reunion` et `courses.course_num` sont  
  vides. La validation croisée cote pré-course ↔ dividende final **reste à faire** (bloquée par  
  l'absence de clé de réunion/course).

## Verdict de l'addendum

> **La limite structurelle du socle est confirmée et aggravée.**  
> Non seulement les cotes sont un instantané pré-course, mais la table censée porter les cotes  
> PMU (`api_cotes`) est **vide**, et la seule source disponible est au **format fractionnaire de  
> provenance incertaine**. Il n'existe **ni mouvement de cote, ni masse d'enjeu, ni cote finale  
> par cheval** dans le socle.

➡️ **Conséquence stratégique inchangée mais renforcée** : aucun edge exploitable ne peut être  
extrait du socle en l'état. Un vrai edge exigerait une **donnée absente** (mouvement de cote  
temps réel, masse d'enjeu, météo, non-partants) → dépend d'**adapters externes** (ADR-001,  
actuellement désactivés).

## Intégrité

| Contrôle               | Valeur                                                             |
| ---------------------- | ------------------------------------------------------------------ |
| Socle LONAB SHA-256    | `d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42` |
| Socle inchangé         | ✅ OUI                                                              |
| Écriture dans le socle | aucune (mode=ro)                                                   |
| API externe appelée    | aucune                                                             |
| Modèle entraîné        | aucun (audit pur)                                                  |



---

**PHASE 5 (ADDENDUM AUDIT) COMPLETE — WAITING FOR HUMAN VALIDATION**
