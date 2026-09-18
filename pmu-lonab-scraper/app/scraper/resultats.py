"""
Scraper pour les résultats/gains PMU'B.

Source: https://lonab.bf/resultats-gains-pmub
Structure Drupal: vue "resultats_gains" avec tableau HTML et pagination ?page=N.

NOTE: Le nom du champ Drupal contient une faute de frappe dans le code source
du site LONAB : "ajouter-un-docuent" (au lieu de "ajouter-un-document").
"""

from __future__ import annotations

from app.models.document import DocumentMetadata, DocumentType
from app.scraper.lonab import LonabScraper, BASE_URL
from app.utils.logging_config import get_logger

logger = get_logger("scraper.resultats")

# URL de départ pour les résultats
RESULTATS_URL = f"{BASE_URL}/resultats-gains-pmub"

# Classe CSS du champ PDF dans le tableau Drupal
# ATTENTION: typo dans le HTML Drupal — "docuent" au lieu de "document"
PDF_FIELD_CLASS = "views-field-field-ajouter-un-docuent"


class ResultatsScraper(LonabScraper):
    """
    Scraper spécialisé pour les résultats/gains PMU'B.

    Parcourt toutes les pages de résultats, extrait les métadonnées
    et les liens PDF.
    """

    def scrape_all(self, max_pages: int = 100) -> list[DocumentMetadata]:
        """
        Parcourt toutes les pages de résultats et collecte les documents.

        Args:
            max_pages: Nombre maximum de pages à parcourir (sécurité).

        Returns:
            Liste dédupliquée de DocumentMetadata.
        """
        all_documents: list[DocumentMetadata] = []
        seen_urls: set[str] = set()
        current_url = RESULTATS_URL
        page_count = 0

        logger.info("=== Début du scraping des résultats PMU'B ===")

        while current_url and page_count < max_pages:
            page_count += 1
            logger.info("--- Page %d: %s ---", page_count, current_url)

            soup = self.fetch_page(current_url)
            if not soup:
                logger.error("Impossible de récupérer la page %d, arrêt", page_count)
                break

            # Extraire les documents du tableau
            documents = self.extract_documents_from_table(
                soup=soup,
                source_url=current_url,
                pdf_field_class=PDF_FIELD_CLASS,
                default_type=DocumentType.RESULTAT,
            )

            # Dédupliquer par URL PDF
            new_count = 0
            for doc in documents:
                if doc.pdf_url not in seen_urls:
                    seen_urls.add(doc.pdf_url)
                    all_documents.append(doc)
                    new_count += 1
                else:
                    logger.debug("Doublon ignoré: %s", doc.pdf_url)

            logger.info(
                "Page %d: %d documents, %d nouveaux, %d doublons",
                page_count, len(documents), new_count, len(documents) - new_count,
            )

            # Passer à la page suivante
            current_url = self.get_next_page_url(soup, current_url)

        logger.info(
            "=== Fin du scraping résultats: %d pages, %d documents uniques ===",
            page_count, len(all_documents),
        )

        return all_documents
