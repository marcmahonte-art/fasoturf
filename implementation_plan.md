# Scraper PMU'B LONAB — V0.1 Pipeline de Collecte

## Contexte

Construction d'un scraper Python robuste pour collecter automatiquement les journaux hippiques (programmes) et les résultats/gains PMU'B depuis le site officiel de la LONAB (Burkina Faso).

## Résultats de l'Analyse du Site (Étape 1 ✅)

### Architecture Technique
- **CMS** : Drupal 9.5.11 avec thème Bootstrap 3.4.1
- **Rendu** : HTML statique côté serveur via **Drupal Views** — **Playwright NON nécessaire**
- **Protection** : Cloudflare (email obfuscation uniquement, pas de challenge JS)
- **robots.txt** : Très permissif — seuls les CSS/JS du core sont mentionnés, pas de blocage des PDF ni des pages de listing

### Structure HTML Commune (Programmes & Résultats)

```
<div class="view view-programmes"> / <div class="view view-resultats-gains">
  └── <table class="table">
        └── <tbody>
              └── <tr>  (une ligne par document)
                    ├── <td class="views-field views-field-title">  → titre du document
                    ├── <td class="views-field views-field-body">   → vide (champ inutilisé)
                    └── <td class="views-field views-field-field-ajouter-un-fichier">
                    │        └── <a href="/sites/default/files/...pdf">Télécharger</a>
                    └── (résultats: views-field-field-ajouter-un-docuent)  ← typo "docuent" dans le code Drupal
```

> [!IMPORTANT]
> La colonne PDF des résultats utilise la classe `views-field-field-ajouter-un-docuent` (avec une faute de frappe — **docuent** au lieu de **document**). Le scraper doit gérer les deux sélecteurs.

### Pagination
- **URL pattern** : `?page=N` (0-indexé)
- Programmes : `/fr/programme-pmub?page=N`
- Résultats : `/fr/resultats-gains-pmub?page=N`
- **10 éléments par page**
- Détection de la page suivante : lien `<a>` dans `<li class="next">`
- Fin de pagination : absence du `<li class="next">`

### Structure des URLs PDF

| Source | Pattern URL | Exemples observés |
|--------|------------|-------------------|
| Programmes | `/sites/default/files/YYYY-MM/JH_PMU[B]_DU_DD-MM-YYYY.pdf` | `JH_PMUB_DU_08-09-2026.pdf`, `JH_PMU%27B_DU_09-09-2026_0.pdf`, `JH_PMU_DU_24-08-2026.pdf` |
| Résultats | `/sites/default/files/YYYY-MM/Res[type]_DD_MM_YYYY[_suffix].pdf` | `Res_07_09_2026_QUARTE.pdf`, `Rept41_06_09_2026.pdf`, `Res41_03_09_2026_Masse_Commune_UEMOA_2026.pdf` |

> [!WARNING]
> Le nommage des fichiers **n'est PAS cohérent** :
> - Séparateurs variables : `_` ou `-` dans la date
> - Préfixes variables : `JH_PMUB`, `JH_PMU%27B`, `JH_PMU`
> - Suffixes aléatoires : `_0`, `_QUARTE`, `_TIERCE`, `_Masse_Commune_UEMOA_2026`
> - Même date peut avoir plusieurs documents de résultats
> 
> → **Le nom de fichier d'origine doit être conservé** et ne pas être reconstruit.

### Extraction des Dates
- **Dans le titre** : `"journal hippique PMU'B du DD MOIS YYYY"` / `"Télécharger les résultats PMU'B du DD MOIS YYYY"`
- Mois en français : `septembre`, `AOUT`, `Septembre` (casse variable)
- **Regex proposée** : `(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|aout|août|septembre|octobre|novembre|décembre)\s+(\d{4})`

### Duplications Observées
- Les résultats peuvent contenir **plusieurs lignes pour la même date** (ex: 06/09 et 03/09 apparaissent 2 fois chacun avec des PDF différents)
- La déduplication doit se faire sur l'**URL du PDF**, pas sur la date

## Choix Technologiques (Étape 2)

| Outil | Justification |
|-------|---------------|
| `requests` + `BeautifulSoup4` | HTML statique, rendu côté serveur |
| `Pydantic v2` | Validation des métadonnées |
| `pathlib` | Gestion des chemins cross-platform |
| `hashlib` | SHA-256 des fichiers |
| `logging` | Traçabilité complète |
| **Pas de Playwright** | Contenu non-JS, confirmé par l'analyse |

## Proposed Changes

### Modèle de données (`app/models/document.py`)

#### [NEW] [document.py](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/app/models/document.py)

Modèle Pydantic `DocumentMetadata` avec :
- `id` : UUID généré à partir de `pdf_url`
- `document_type` : enum `journal_hippique | resultat | recapitulatif | unknown`
- `source_url`, `pdf_url`, `title`, `publication_date` (nullable)
- `discovered_at` : datetime auto
- `local_path`, `sha256`, `file_size` : remplis après téléchargement
- `status` : enum `discovered | downloaded | failed | skipped`

---

### Scraper base + Programmes + Résultats

#### [NEW] [lonab.py](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/app/scraper/lonab.py)

Classe `LonabScraper` (base) :
- Session `requests` avec User-Agent, timeouts, retries
- Méthode `fetch_page(url)` avec gestion d'erreurs
- Délai configurable entre requêtes (défaut 2s)

#### [NEW] [programmes.py](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/app/scraper/programmes.py)

Classe `ProgrammesScraper(LonabScraper)` :
- Parse le tableau `view-programmes`
- Sélecteur PDF : `views-field-field-ajouter-un-fichier a[href$=".pdf"]`
- Pagination automatique via détection `li.next a`
- Extraction date depuis le titre

#### [NEW] [resultats.py](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/app/scraper/resultats.py)

Classe `ResultatsScraper(LonabScraper)` :
- Parse le tableau `view-resultats-gains`
- Sélecteur PDF : `views-field-field-ajouter-un-docuent a[href$=".pdf"]` (typo Drupal)
- Même logique de pagination

---

### Téléchargeur PDF

#### [NEW] [pdf_downloader.py](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/app/downloader/pdf_downloader.py)

- Téléchargement avec vérification Content-Type `application/pdf`
- Structure dossiers : `data/raw/{type}/YYYY/MM/`
- Nom de fichier : nom d'origine du PDF (nettoyé) 
- SHA-256 calculé après écriture
- Skip si fichier existe déjà (vérification par chemin + SHA-256)
- Retry (3 tentatives), timeout 30s

---

### Utilitaires

#### [NEW] [hashing.py](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/app/utils/hashing.py)
#### [NEW] [logging_config.py](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/app/utils/logging_config.py)

---

### Point d'entrée

#### [NEW] [main.py](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/main.py)

```
python main.py --dry-run                        # analyse sans téléchargement
python main.py --download                       # télécharge tout
python main.py --download --source programmes   # programmes uniquement
python main.py --download --source resultats    # résultats uniquement
```

---

### Métadonnées

#### [NEW] `data/metadata/documents.jsonl`

Une ligne JSON par document, mise à jour à chaque exécution. Utilisé pour la déduplication.

---

### Tests

#### [NEW] [tests/](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/tests/)

Fixtures HTML locales reproduisant la structure exacte observée. Tests unitaires pour :
- Extraction des liens PDF
- Parsing des dates françaises
- Génération des chemins de fichiers
- SHA-256
- Déduplication par URL
- Détection de la pagination
- Gestion des erreurs

---

### Documentation

#### [NEW] [README.md](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/README.md)
#### [NEW] [.env.example](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/.env.example)
#### [NEW] [requirements.txt](file:///c:/Users/Lenovo/Desktop/PMU/pmu-lonab-scraper/requirements.txt)

## Verification Plan

### Automated Tests
- `python -m pytest tests/ -v`

### Manual Verification
1. `python main.py --dry-run` — vérifier que les documents sont correctement listés
2. `python main.py --download --source programmes` — télécharger quelques programmes
3. Vérifier que `data/metadata/documents.jsonl` contient les bonnes métadonnées
4. Relancer → confirmer qu'aucun doublon n'est recréé
5. Vérifier que les PDF téléchargés sont des vrais PDF (signature `%PDF-`)
