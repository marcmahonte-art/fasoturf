"""
Scraper pour les PDF "Espace Course En Direct" (ECD) LONAB.

Source: https://lonab.bf/resultats-gains-ecd
Structure Drupal: vue avec tableau HTML et pagination ?page=N.

La page contient des liens "Télécharger" vers les PDF ECD.
Chaque ligne contient :
- Date et réunion (ex: "Récapitulatif des arrivées des courses du : 08-09-2026 - Réunion 1")
- Lien "Télécharger" vers le PDF ECD
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional
from urllib.parse import urljoin, urlparse

from app.models.document import DocumentMetadata, DocumentType
from app.scraper.lonab import LonabScraper, BASE_URL
from app.utils.logging_config import get_logger

logger = get_logger("scraper.course_direct")

# URL de départ pour les ECD
ECD_URL = f"{BASE_URL}/resultats-gains-ecd"

# Regex pour extraire date et réunion depuis le texte
# Format observé: "Récapitulatif des arrivées des courses du : 08-09-2026 - Réunion 1"
ECD_DATE_REUNION_PATTERN = re.compile(
    r"récapitulatif\s+des\s+arrivées\s+des\s+courses\s+du\s*:\s*"
    r"(\d{2}-\d{2}-\d{4})\s*-\s*réunion\s*(\d+)",
    re.IGNORECASE,
)

# Pattern alternatif pour date seule
ECD_DATE_PATTERN = re.compile(
    r"(\d{2}-\d{2}-\d{4})",
)


class CourseDirectScraper(LonabScraper):
    """
    Scraper spécialisé pour les PDF Espace Course En Direct (ECD).

    Parcourt toutes les pages d'archives ECD, extrait les métadonnées
    et les liens PDF.
    """

    def scrape_all(self, max_pages: int = 100) -> list[DocumentMetadata]:
        """
        Parcourt toutes les pages ECD et collecte les documents.

        Args:
            max_pages: Nombre maximum de pages à parcourir (sécurité).

        Returns:
            Liste dédupliquée de DocumentMetadata.
        """
        all_documents: list[DocumentMetadata] = []
        seen_urls: set[str] = set()
        current_url = ECD_URL
        page_count = 0

        logger.info("=== Début du scraping ECD (Course En Direct) ===")

        while current_url and page_count < max_pages:
            page_count += 1
            logger.info("--- Page ECD %d: %s ---", page_count, current_url)

            soup = self.fetch_page(current_url)
            if not soup:
                logger.error("Impossible de récupérer la page ECD %d, arrêt", page_count)
                break

            # Extraire les documents de la page
            documents = self._extract_ecd_documents(soup, current_url)

            # Dédupliquer par URL PDF
            new_count = 0
            for doc in documents:
                if doc.pdf_url not in seen_urls:
                    seen_urls.add(doc.pdf_url)
                    all_documents.append(doc)
                    new_count += 1
                else:
                    logger.debug("Doublon ECD ignoré: %s", doc.pdf_url)

            logger.info(
                "Page ECD %d: %d documents, %d nouveaux, %d doublons",
                page_count, len(documents), new_count, len(documents) - new_count,
            )

            # Passer à la page suivante
            current_url = self.get_next_page_url(soup, current_url)

        logger.info(
            "=== Fin du scraping ECD: %d pages, %d documents uniques ===",
            page_count, len(all_documents),
        )

        return all_documents

    def _extract_ecd_documents(self, soup, source_url: str) -> list[DocumentMetadata]:
        """
        Extrait les documents ECD depuis la page.

        La structure est un tableau Drupal Views où chaque ligne contient :
        - Une cellule avec la date et la réunion
        - Une cellule avec le lien "Télécharger" vers le PDF

        Args:
            soup: Le BeautifulSoup de la page.
            source_url: L'URL de la page source.

        Returns:
            Liste de DocumentMetadata.
        """
        documents: list[DocumentMetadata] = []

        # Trouver toutes les lignes du tableau
        rows = soup.find_all("tr")
        if not rows:
            logger.warning("Aucune ligne de tableau trouvée sur: %s", source_url)
            return documents

        for row in rows:
            try:
                # Extraire le texte de la ligne pour trouver date et réunion
                row_text = row.get_text(" ", strip=True)

                # Chercher date et réunion
                date_match = ECD_DATE_REUNION_PATTERN.search(row_text)
                pub_date = None
                reunion = None

                if date_match:
                    date_str = date_match.group(1)
                    reunion = int(date_match.group(2))
                    try:
                        day, month, year = map(int, date_str.split("-"))
                        pub_date = date(year, month, day)
                    except ValueError:
                        logger.warning("Date invalide extraite: %s", date_str)
                else:
                    # Essayer de trouver juste une date
                    date_match = ECD_DATE_PATTERN.search(row_text)
                    if date_match:
                        date_str = date_match.group(1)
                        try:
                            day, month, year = map(int, date_str.split("-"))
                            pub_date = date(year, month, day)
                        except ValueError:
                            pass

                # Extraire le lien PDF
                pdf_link = row.find("a", href=True, string=re.compile(r"télécharger", re.IGNORECASE))
                if not pdf_link:
                    # Essayer de trouver tout lien PDF dans la ligne
                    pdf_link = row.find("a", href=True)
                    if pdf_link and not pdf_link["href"].lower().endswith(".pdf"):
                        pdf_link = None

                if not pdf_link:
                    continue

                href = pdf_link["href"]

                # Vérifier que c'est un PDF
                if not href.lower().endswith(".pdf"):
                    logger.warning("Lien non-PDF ignoré: %s", href)
                    continue

                # Construire l'URL absolue
                pdf_url = urljoin(BASE_URL, href)

                # Nom du fichier
                filename = self.extract_pdf_filename(pdf_url)

                # Titre
                title = f"ECD {pub_date} - Réunion {reunion}" if pub_date and reunion else f"ECD {filename}"

                # Créer les métadonnées
                doc = DocumentMetadata.create(
                    pdf_url=pdf_url,
                    source_url=source_url,
                    document_type=DocumentType.COURSE_EN_DIRECT,
                    title=title,
                    publication_date=pub_date,
                )

                # Ajouter réunion dans les métadonnées si disponible
                # On peut l'ajouter dans le titre ou comme info supplémentaire
                documents.append(doc)
                logger.debug("Document ECD trouvé: %s — %s (Réunion: %s)", title, pdf_url, reunion)

            except Exception as e:
                logger.error("Erreur lors du parsing d'une ligne ECD: %s", e)
                continue

        logger.info("%d document(s) ECD trouvé(s) sur: %s", len(documents), source_url)
        return documents