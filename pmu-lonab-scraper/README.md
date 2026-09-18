# PMU'B LONAB Scraper

Scraper Python pour collecter automatiquement les journaux hippiques (programmes) et les résultats/gains PMU'B depuis le site officiel de la LONAB (Burkina Faso).

## Architecture

Le site LONAB utilise **Drupal 9** avec rendu HTML statique côté serveur via **Drupal Views**. Aucun navigateur headless (Playwright/Puppeteer) n'est nécessaire — le contenu est directement disponible en HTML.

- **`app/scraper/lonab.py`** — Scraper de base (session HTTP, retries, parsing commun)
- **`app/scraper/programmes.py`** — Scraping des programmes (journaux hippiques)
- **`app/scraper/resultats.py`** — Scraping des résultats/gains
- **`app/models/document.py`** — Modèle Pydantic `DocumentMetadata`
- **`app/downloader/pdf_downloader.py`** — Téléchargement PDF avec hashing SHA-256
- **`app/utils/hashing.py`** — Calcul de hash SHA-256
- **`app/utils/logging_config.py`** — Configuration centralisée du logging
- **`main.py`** — Point d'entrée CLI

## Installation

```bash
cd pmu-lonab-scraper
pip install -r requirements.txt
cp .env.example .env
```

## Utilisation

```bash
# Analyse sans téléchargement
python main.py --dry-run

# Télécharger tout
python main.py --download

# Télécharger seulement les programmes
python main.py --download --source programmes

# Télécharger seulement les résultats
python main.py --download --source resultats

# Niveau de log détaillé
python main.py --dry-run --log-level DEBUG
```

## Structure des données

```
data/
├── raw/
│   ├── journal_hippique/YYYY/MM/nom_original.pdf
│   ├── resultat/YYYY/MM/nom_original.pdf
│   └── ...
└── metadata/documents.jsonl
```

## Tests

```bash
pip install pytest
pytest tests/ -v
```

Les tests utilisent des fixtures HTML locales reproduisant la structure exacte observée sur le site LONAB. Aucune requête réseau n'est effectuée.

## Technologies

- `requests` + `BeautifulSoup4` — Récupération et parsing HTML
- `Pydantic v2` — Validation des métadonnées
- `pathlib` — Gestion des chemins cross-platform
- `hashlib` — SHA-256 des fichiers
- `python-dotenv` — Gestion de la configuration
- `pytest` — Tests unitaires

## Configuration

Copiez `.env.example` en `.env` et ajustez les paramètres :

- `REQUEST_DELAY` — Délai entre les requêtes (secondes)
- `REQUEST_TIMEOUT` — Timeout HTTP (secondes)
- `MAX_RETRIES` — Nombre de tentatives en cas d'échec
- `DATA_DIR` — Répertoire de stockage des données
- `LOG_LEVEL` — Niveau de logging

## Remarques

- Le nommage des fichiers PDF sur le site LONAB n'est pas cohérent — le nom original est conservé.
- La déduplication se fait par URL du PDF, pas par date.
- La colonne PDF des résultats utilise la classe CSS `views-field-field-ajouter-un-docuent` (faute de frappe Drupal).
