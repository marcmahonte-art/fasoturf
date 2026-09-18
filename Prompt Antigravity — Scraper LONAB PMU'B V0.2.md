# Mission — Lancer le scraper LONAB PMU'B et télécharger tous les PDF

Tu travailles sur un projet Python appelé `pmu-lonab-scraper`.

## Objectif

Je veux maintenant passer de la phase de test à un scraper fonctionnel capable de :

1. visiter automatiquement les pages officielles LONAB ;
2. détecter les liens vers les PDF PMU'B ;
3. parcourir les pages d'archives/pagination ;
4. identifier les PDF de programmes/journaux et de résultats ;
5. extraire automatiquement la date depuis le nom du fichier ou l'URL ;
6. télécharger les PDF ;
7. organiser les fichiers par date et type ;
8. éviter les doublons grâce au SHA-256 ;
9. enregistrer les métadonnées de chaque document ;
10. produire un rapport clair à la fin du scraping.

## Sources officielles à scraper

Programme PMU'B :

https://lonab.bf/programme-pmub

Résultats PMU'B :

https://lonab.bf/resultats-gains-pmub

IMPORTANT :
- utiliser uniquement les pages officielles LONAB ;
- ne pas inventer d'URL ;
- ne pas contourner de CAPTCHA, authentification ou protection ;
- respecter les limitations raisonnables du site ;
- ajouter un délai raisonnable entre les requêtes ;
- gérer les erreurs réseau et les PDF indisponibles sans arrêter tout le scraping.

---

# 1. Structure du projet

Conserve et améliore la structure existante :

pmu-lonab-scraper/

├── app/
│   ├── scraper/
│   │   ├── lonab.py
│   │   ├── programmes.py
│   │   └── resultats.py
│   │
│   ├── downloader/
│   │   └── pdf_downloader.py
│   │
│   ├── models/
│   │   └── document.py
│   │
│   └── utils/
│       ├── hashing.py
│       └── logging_config.py
│
├── data/
│   ├── raw/
│   │   ├── programmes/
│   │   └── resultats/
│   │
│   └── metadata/
│
├── tests/
│
├── main.py
├── requirements.txt
├── .env.example
└── README.md

Ne casse pas le code existant qui fonctionne déjà.

---

# 2. Extraction automatique des PDF

Le scraper doit rechercher dans le HTML les liens :

- `<a href="...pdf">`
- liens absolus ;
- liens relatifs ;
- liens PDF contenant `/sites/default/files/`.

Il doit normaliser les URL.

Exemple :

https://lonab.bf/sites/default/files/2026-09/Res_08_09_2026_QUARTE.pdf

doit être reconnu comme un PDF valide.

---

# 3. Détection du type de document

Détecter automatiquement :

### Résultat

Si le nom contient par exemple :

- `Res_`
- `Resultat`
- `Resultats`

alors :

```python
DocumentType.RESULTAT
```

### Programme / Journal

Si le nom contient par exemple :

- `JH_`
- `JOURNAL`
- `PROGRAMME`

alors :

```python
DocumentType.PROGRAMME
```

Ne pas dépendre d'une seule convention de nommage.

Si le type ne peut pas être déterminé :

```python
DocumentType.UNKNOWN
```

et enregistrer le document pour inspection.

---

# 4. Extraction de la date

Créer une fonction robuste :

```python
extract_date_from_filename_or_url()
```

Elle doit reconnaître au minimum les formats :

```text
08_09_2026
08-09-2026
2026-09-08
08/09/2026
```

Exemple :

```text
Res_08_09_2026_QUARTE.pdf
```

doit produire :

```text
2026-09-08
```

Autre exemple :

```text
JH_PMUB_DU_08-09-2026.pdf
```

doit produire :

```text
2026-09-08
```

La date doit être stockée comme un véritable objet `date`, pas uniquement comme une chaîne.

Si aucune date n'est trouvée :

```text
unknown_date
```

---

# 5. Organisation des fichiers

Les fichiers doivent être stockés ainsi :

data/raw/resultats/YYYY-MM-DD/

et :

data/raw/programmes/YYYY-MM-DD/

Exemple :

data/raw/resultats/2026-09-08/Res_08_09_2026_QUARTE.pdf

et :

data/raw/programmes/2026-09-08/JH_PMUB_DU_08-09-2026.pdf

Pour les documents sans date :

data/raw/resultats/unknown_date/

ou :

data/raw/programmes/unknown_date/

---

# 6. Pagination et archives

Le scraper ne doit PAS récupérer uniquement la première page.

Analyse le HTML des deux pages pour identifier :

- pagination ;
- `?page=`;
- boutons "Suivant" ;
- liens vers pages précédentes ;
- éventuelles archives ;
- autres mécanismes de navigation.

Continue jusqu'à ce qu'il n'y ait plus de nouvelles pages.

Évite les boucles infinies.

Maintenir un ensemble des URL déjà visitées :

```python
visited_urls = set()
```

Limiter également le nombre maximum de pages configurable par CLI.

Exemple :

```bash
python main.py --max-pages 100
```

---

# 7. Téléchargement

Utilise le `PDFDownloader` existant.

Le téléchargement doit :

- utiliser un timeout ;
- gérer les erreurs HTTP ;
- réessayer en cas d'erreur temporaire ;
- vérifier que le contenu téléchargé est réellement un PDF ;
- calculer le SHA-256 ;
- sauvegarder le fichier ;
- retourner son statut.

Ne télécharge pas deux fois un fichier déjà connu.

---

# 8. Déduplication

Le SHA-256 doit être utilisé comme identifiant du contenu.

Si deux URL différentes pointent vers exactement le même PDF :

```text
SHA256 identique
```

alors ne pas conserver inutilement deux copies.

Le système doit indiquer :

```text
DUPLICATE
```

dans les logs/métadonnées.

---

# 9. Métadonnées

Créer ou améliorer :

```text
data/metadata/documents.jsonl
```

Une ligne JSON par document.

Exemple :

```json
{
  "url": "https://lonab.bf/sites/default/files/2026-09/Res_08_09_2026_QUARTE.pdf",
  "source_url": "https://lonab.bf/resultats-gains-pmub",
  "document_type": "resultat",
  "title": "Résultats 08/09/2026",
  "publication_date": "2026-09-08",
  "local_path": "data/raw/resultats/2026-09-08/Res_08_09_2026_QUARTE.pdf",
  "sha256": "...",
  "file_size": 123456,
  "status": "downloaded"
}
```

Ajouter si utile :

```text
scraped_at
http_status
content_type
filename
```

---

# 10. CLI

Le fichier `main.py` doit permettre :

### Dry run

```bash
python main.py --dry-run
```

Analyse les pages et affiche les PDF trouvés sans les télécharger.

### Télécharger tout

```bash
python main.py --download
```

### Seulement les programmes

```bash
python main.py --download --source programmes
```

### Seulement les résultats

```bash
python main.py --download --source resultats
```

### Tout

```bash
python main.py --download --source all
```

### Limiter le nombre de pages

```bash
python main.py --download --max-pages 100
```

### Limiter le nombre de documents

Ajouter si pertinent :

```bash
python main.py --download --max-documents 100
```

---

# 11. Mode résumé

À la fin du scraping, afficher quelque chose comme :

```text
========================================
LONAB PMU'B SCRAPER
========================================

Pages visitées        : 24
PDF trouvés           : 187
Programmes trouvés    : 92
Résultats trouvés     : 95

Téléchargés           : 181
Déjà présents         : 4
Doublons              : 2
Erreurs                : 0

Dates détectées       : 2026-01-01 → 2026-09-08

Dossier programmes :
data/raw/programmes/

Dossier résultats :
data/raw/resultats/

Métadonnées :
data/metadata/documents.jsonl

========================================
SCRAPING TERMINÉ
========================================
```

Les chiffres doivent évidemment être calculés dynamiquement.

---

# 12. Logging

Créer des logs lisibles :

```text
[INFO] Opening https://lonab.bf/programme-pmub
[INFO] Found 12 PDF links
[INFO] Found pagination page=1
[INFO] Found pagination page=2
[INFO] PDF detected: JH_PMUB_DU_08-09-2026.pdf
[INFO] Date detected: 2026-09-08
[INFO] Downloading PDF...
[INFO] SHA256: ...
[INFO] Saved to data/raw/programmes/2026-09-08/
```

En cas d'erreur :

```text
[ERROR] Failed to download ...
```

mais continuer avec les autres documents.

---

# 13. Tests

Ajouter des tests unitaires pour :

### Extraction de date

Tester :

```text
Res_08_09_2026_QUARTE.pdf
JH_PMUB_DU_08-09-2026.pdf
2026-09-08-document.pdf
```

### Classification

Tester :

```text
Res_08_09_2026_QUARTE.pdf → RESULTAT
JH_PMUB_DU_08-09-2026.pdf → PROGRAMME
```

### URL

Tester :

- URL absolue ;
- URL relative ;
- URL avec paramètres.

### Déduplication

Tester deux fichiers ayant le même SHA-256.

### Downloader

Utiliser des fixtures locales ou mocks.

Ne pas dépendre du site LONAB pour les tests unitaires.

---

# 14. Sécurité et robustesse

Ne jamais :

- contourner une protection ;
- essayer de bypasser CAPTCHA ;
- effectuer un grand nombre de requêtes simultanées ;
- scraper agressivement ;
- supprimer les données déjà téléchargées.

Utiliser :

```text
timeout
retry
backoff
rate limiting
```

Le scraper doit être relançable sans casser les données existantes.

---

# 15. Important : ne PAS parser les chevaux maintenant

Pour cette version, ne fais PAS encore :

- extraction des chevaux ;
- extraction des jockeys ;
- extraction des entraîneurs ;
- extraction des cotes ;
- extraction des performances ;
- ML ;
- prédictions ;
- LLM.

Cette étape viendra dans V0.3.

L'objectif actuel est uniquement :

**RÉCUPÉRER PROPREMENT TOUS LES PDF PMU'B DISPONIBLES.**

---

# 16. Exécution réelle

Après avoir implémenté le code :

1. lance les tests ;
2. corrige les erreurs ;
3. lance un dry-run ;
4. montre combien de PDF sont détectés ;
5. si le dry-run fonctionne, lance le téléchargement ;
6. vérifie physiquement que les fichiers PDF existent ;
7. vérifie quelques fichiers avec leur SHA-256 ;
8. vérifie `documents.jsonl`.

Ne prétends jamais avoir téléchargé un fichier si le téléchargement n'a pas réellement réussi.

---

# 17. Rapport final obligatoire

À la fin, donne-moi un rapport :

## Scraping

- pages visitées ;
- pagination détectée ;
- nombre de PDF trouvés ;
- nombre de programmes ;
- nombre de résultats.

## Téléchargement

- nombre téléchargé ;
- nombre déjà existant ;
- nombre de doublons ;
- nombre d'erreurs.

## Données

- première date trouvée ;
- dernière date trouvée ;
- exemples de fichiers téléchargés ;
- emplacement exact des fichiers.

## Technique

- requests utilisé ou Playwright ;
- pourquoi Playwright était ou non nécessaire ;
- problèmes rencontrés ;
- URLs particulières découvertes.

## Prochaine étape

Proposer ensuite la V0.3 :

**parser automatiquement les journaux hippiques PDF afin de transformer les 16 chevaux de chaque course en données structurées exploitables par PostgreSQL/ML.**

Commence maintenant par inspecter le code existant, puis implémente cette V0.2 sans réécrire inutilement les composants déjà fonctionnels.