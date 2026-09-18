# MEMORY — PMU'B LONAB V2 (conventions durables)

> Détail FasoTurf → **`FASOTURF.md`**. Chiffres par phase → **`PHASEN_*.md`**. Ne pas dupliquer ici.

## 1. ADR-001 — architecture (non négociable)
- `pmu-lonab-scraper/data/processed/pmu_lonab.db` = **SOCLE, source de vérité, JAMAIS modifié** →
  `sqlite3.connect("file:{path}?mode=ro", uri=True)`. Couche dérivée = `data/master/pmu_master.db`.
- Le moteur **enrichit**, ne remplace jamais. Externes : **adapters OFF par défaut**, aucun endpoint
  inventé, écritures limitées à `external_*` / `weather_race`, jamais d'`UPDATE` sur tables LONAB,
  dégradation gracieuse obligatoire.
- **SHA-256 du socle à vérifier avant ET après** :
  `d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42`.

## 2. Workflow (spec §0, §66)
**AUDIT AVANT DE CODER.** Une phase à la fois → **arrêt + validation humaine**. Scripts reproductibles
`scripts/phaseN/`, rapports `PHASEN_*.md`. Environnement : **pas de PostgreSQL**, sandbox **bloque
pip** → **Python stdlib** d'abord. **Phase 14+ : interdite sans validation humaine explicite.**

## 3. ⚠️ HONNÊTETÉ DE LA DONNÉE — règle transverse (spec §2.3, §32, §53)
- **Ne jamais fabriquer de valeur.** Absent ⇒ `None` / `""` / « — », jamais un chiffre plausible.
- **Un repli silencieux est un mock qui s'ignore.** Un repli doit être **déclaré**
  (`source: "api" | "snapshot"` + `snapshotDate`) et l'interface doit dire lequel elle affiche.
  Jamais de compteur inventé (`{todayCount || 8}`) ni de date en dur ; `toISOString()` = **UTC**
  (faux d'un jour selon le fuseau) → `todayIso()` / `formatDayMonth*`.
- Badge d'origine obligatoire (`real` / `prediction` / `official` / `demo`) ; ce qui n'existe pas est
  déclaré **indisponible avec une raison**.
- **Toujours publier les résultats négatifs** ; **toujours calculer le ROI sans le plus gros gain** —
  un résultat qui s'effondre en retirant une course n'est PAS une piste.

## 4. BILAN SCIENTIFIQUE (Phases 3→13) — résultat central
**Aucune piste ne survit.** Sur l'échantillon étendu (739 courses, ×2,5) les conclusions négatives
sont **confirmées et renforcées** (IC resserrés) : SG, Placé, Couple Gagnant, Trio, 2sur4 **tous
efficients**. Le socle **ne contient aucune information exploitable au-delà de la cote**, et le
**marché réel PMU est efficient** dans toutes les familles testées. ➡️ **Négatif SOLIDE.**
- Favori 22,5 % = ensemble appris 22,5 % → gain net 0 ; commentaires presse **dégradent** l'AUC
  (0,6386 vs 0,6856) → BRUIT. Phase 7 : divergence « validée » puis invalidée (moitiés temporelles au
  signe inversé, permutation p=0,301) → **BRUIT**.
- Phase 12 (mouvement des cotes) : 1er test **NON significatif** (p=0,3779 ; ROI +113 % porté par un
  seul longshot → **−34 % sans lui**). Capture forward opérationnelle → **accumuler**.
- **Règle durable** : toute feature doit prouver un **gain net > 0 sur les désaccords avec le favori
  du marché** (baseline obligatoire).

## 5. ⚠️ PIÈGE D'UNITÉ DES DIVIDENDES PMU (critique)
`dividende` de `rapports-definitifs` = **par mise de base** (`miseBase`, centimes), **PAS par euro**.
`miseBase` varie : SG/Placé/Couple/Trio/Pick5 = **100**, 2sur4/Multi/Mini-Multi = **300**,
Quarté+ = **150**, Quinté+ = **200**. → **Toujours lire `dividendePourUnEuro`** (présent à 100 %).
Jamais `dividende/100` seul. Erreur Phase 11 → faux ROI +114,95 % au lieu de −28,35 %.
**Un ROI supérieur au prélèvement est IMPOSSIBLE en pari-mutuel → suspecter une erreur d'unité.**
⚠️ `external_pmu_results.arrivee` vaut souvent la **chaîne** `'null'` (pas NULL) → lire `data_json`
(`rapports[0].combinaison[0]`). Champs réels : `numOfficiel` (réunion), `numOrdre` (course).

## 6. ⚠️ LIMITE STRUCTURANTE DU SOCLE
- **`api_cotes` = COQUILLE VIDE** : 27 243 lignes mais `numero`, `cote_directe`, `masse_enjeu`,
  `cote_reference`, `evolution_cote`, `risque` = **100 % NULL** ; `COUNT(DISTINCT updatetime)=1`.
  `api_partants`, `api_meteo`, `media_selections` = 0 ligne ; `partants_enrichis` = 185 lignes.
- **Seule source de cotes = `partants.cote_raw` / `cote_decimale`**, format **`N/1`**, provenance non
  établie. Ce n'est **PAS un rapport final** : 32,1 % des courses ont booksum < 1, médiane 1,075 <
  prélèvement → **instantané pré-course**. **Le mouvement ouverture→clôture est ABSENT du socle.**
- `api_rapports` = dividendes **FINAUX** (387 courses SG) mais **non appariables** à `partants`.

## 7. Pièges de données du socle (mesurés)
- **Date sentinelle `1995-07-18`** : 188 courses (20 %), défaut du parseur → **À EXCLURE** de toute
  jointure par date et de tout calcul d'année de naissance (`date_is_sentinel = 1`).
- `course_id` rempli à 66 % mais **non unique** → clé inutilisable. Vraie jointure : `document_id`
  (1 course = 1 document). `courses.date == resultats.date` pour l'arrivée.
- **`partants.sexe` encode sexe + âge** : `'H.7'` = hongre 7 ans. Sexes valides {H,F,M} ; `'AGE'`,
  `'1'`, `'P'` = artefacts. Colonne `age` vide sur 2 096 lignes.
- **`resultats.arrivee` = 3 à 5 places** : un partant absent = *hors arrivée* (normal).
- **ECD : `ecd_courses.arrivee_positions` CORROMPU à 100 %** ; vraie arrivée dans `raw_text`
  (récupérable à 99,9 %). Motif (**ordinaux obligatoires**, sinon 12 %) :
  `^\s*\d+\s*(?:ère|ième|ème|er|e)\s*[\s\n]*(\d{1,2}(?:\s*[\s\n]*-\s*[\s\n]*\d{1,2})+)`
- **ECD ne contient AUCUN partant** → ne jamais l'utiliser pour élargir `master_runner`. Les
  `commentaires` viennent **100 % de documents `JOURNAL`**.

## 8. Identifiants internes (Phase 2, figés)
- **UUIDv5 déterministe**, namespace `6f1a4c2e-9b7d-5a31-8c4f-2d6e0b9a7c15` — **NE JAMAIS CHANGER**.
  Schémas : `race|LONAB|{document_id}`, `horse|{name_key}`, `person|{role}|{name_key}`,
  `hippodrome|{label_canonique}`, `runner|{document_id}|{numero}`. `race_id` basé sur `document_id`
  (pas `date+hippodrome`, à cause du sentinel).
- **Aucun nom ne sert de clé étrangère.** Normalisation : `NFKD` → sans accents → MAJUSCULES →
  `[^A-Z0-9]+` → espaces → collapse.
- **Tie-breaking** : sélecteur déterministe explicite `min(entries, key=lambda e: (-prob, id))` —
  deux règles de départage différentes créent des « désaccords » fictifs.

## 9. Outils d'analyse (Phase 6 = PIVOT durable)
Objectif **plus de battre le marché** → **outil d'analyse honnête**, sans promesse de gain.
- `scripts/phase6/race_reader.py` (CLI `--list N | --date YYYY-MM-DD | --race <id>`, `+ --out/--csv/
  --json`), `fit_form_model.py`, `evaluate_divergence.py`. Modèle figé `models/form_model_v1.json` :
  AUC test **0,6856** < marché **0,7560**.
- `scripts/phase8/build_site.py` → `site/index.html` (SPA **fichier unique**, hors ligne). Son « rang
  forme » vient du **modèle figé** (signal invalidé, cf. §4) → **ne jamais substituer une heuristique
  maison** sous un avertissement qui cite un résultat mesuré.

## 10. Réseau / adapters externes
- Sandbox **bloque l'HTTP sortant** → `dangerouslyDisableSandbox` + `--noproxy '*'` +
  `--resolve online.turfinfo.api.pmu.fr:443:99.86.159.69` ; `ProxyHandler({})` + patch DNS.
  Endpoints vérifiés **uniquement** : `.../rest/client/61/programme/{date}/R{n}/C{n}/citations` et
  `.../rapports-definitifs` sur `online.turfinfo.api.pmu.fr`.
- Cadence du marché : `updatetime` n'avance que **~toutes les 15 min** → capturer longtemps et **près
  du départ**. `external_pmu_citations` déduplique par `api_updatetime`.
- ⚠️ Analyse Phase 12 **SANS `--date`** (pooler toutes les dates), sinon les résultats arrivés plus
  tard ne sont jamais vus. `--backfill-results` comble le trou.
- PDF LONAB : `https://lonab.bf/sites/default/files/{YYYY-MM}/JH_PMUB_DU_{DD}-{MM}-{YYYY}.pdf` ;
  ⚠️ `filename` **non normalisé** (tirets OU underscores) → `LIKE '%07%03%2024%'`. Élargir le socle
  **casserait le SHA gelé** → décision explicite requise.
