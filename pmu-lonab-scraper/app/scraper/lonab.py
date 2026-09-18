"""
Scraper de base pour le site LONAB.

Gère la session HTTP, les délais entre requêtes,
les retries et le parsing HTML commun.
"""

from __future__ import annotations

import re
import time
from datetime import date
from typing import Optional
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup, Tag

from app.models.document import DocumentMetadata, DocumentType, DocumentStatus
from app.utils.logging_config import get_logger

logger = get_logger("scraper.lonab")

# Mapping des mois français vers leur numéro
FRENCH_MONTHS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3,
    "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
    "aout": 8, "août": 8, "septembre": 9, "octobre": 10,
    "novembre": 11, "décembre": 12, "decembre": 12,
}

# Regex pour extraire une date française depuis un titre
DATE_PATTERN = re.compile(
    r"(\d{1,2})\s+"
    r"(janvier|février|fevrier|mars|avril|mai|juin|juillet|aout|août|septembre|octobre|novembre|décembre|decembre)\s+"
    r"(\d{4})",
    re.IGNORECASE,
)

BASE_URL = "https://lonab.bf"


class LonabScraper:
    """
    Classe de base pour le scraping du site LONAB.

    Gère la session HTTP avec User-Agent, timeouts, retries,
    et les délais entre requêtes pour respecter le serveur.
    """

    def __init__(
        self,
        request_delay: float = 2.0,
        request_timeout: int = 30,
        max_retries: int = 3,
    ):
        self.request_delay = request_delay
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self._last_request_time: float = 0.0

        # Session HTTP réutilisable
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PMU-B-Scraper/0.1 (Data collection for analysis; contact: admin@example.com)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9",
        })

        # Adapter pour retries automatiques sur erreurs réseau
        adapter = requests.adapters.HTTPAdapter(
            max_retries=requests.adapters.Retry(
                total=max_retries,
                backoff_factor=1.0,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=["GET"],
            )
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _wait_between_requests(self) -> None:
        """Applique un délai entre les requêtes pour ne pas surcharger le serveur."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_delay:
            sleep_time = self.request_delay - elapsed
            logger.debug("Attente de %.1fs avant la prochaine requête", sleep_time)
            time.sleep(sleep_time)

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Télécharge et parse une page HTML.

        Args:
            url: URL de la page à récupérer.

        Returns:
            BeautifulSoup si succès, None en cas d'erreur.
        """
        self._wait_between_requests()

        try:
            logger.info("Récupération de la page: %s", url)
            response = self.session.get(url, timeout=self.request_timeout)
            self._last_request_time = time.time()

            response.raise_for_status()

            # Vérifier que c'est bien du HTML
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                logger.warning("Contenu inattendu (Content-Type: %s) pour: %s", content_type, url)
                return None

            return BeautifulSoup(response.text, "html.parser")

        except requests.exceptions.Timeout:
            logger.error("Timeout lors de la récupération de: %s", url)
            return None
        except requests.exceptions.HTTPError as e:
            logger.error("Erreur HTTP %s pour: %s", e.response.status_code, url)
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Erreur de connexion pour: %s", url)
            return None
        except requests.exceptions.RequestException as e:
            logger.error("Erreur inattendue lors de la récupération de %s: %s", url, e)
            return None

    def get_next_page_url(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        Extrait l'URL de la page suivante depuis la pagination Drupal.

        La pagination utilise <li class="next"><a href="...">

        Args:
            soup: Le BeautifulSoup de la page actuelle.
            current_url: L'URL actuelle (pour résoudre les URLs relatives).

        Returns:
            L'URL absolue de la page suivante, ou None si c'est la dernière page.
        """
        next_li = soup.find("li", class_="next")
        if not next_li:
            logger.info("Pas de page suivante trouvée — fin de la pagination")
            return None

        next_link = next_li.find("a", href=True)
        if not next_link:
            logger.warning("Élément 'next' trouvé mais pas de lien <a>")
            return None

        next_url = urljoin(BASE_URL, next_link["href"])
        logger.info("Page suivante trouvée: %s", next_url)
        return next_url

    @staticmethod
    def parse_french_date(text: str) -> Optional[date]:
        """
        Extrait une date à partir d'un texte contenant un mois en français.

        Exemples:
            "journal hippique PMU'B du 08 septembre 2026" → date(2026, 9, 8)
            "résultats PMU'B du 31 AOUT 2026" → date(2026, 8, 31)

        Args:
            text: Le texte contenant la date.

        Returns:
            Un objet date, ou None si aucune date n'est trouvée.
        """
        match = DATE_PATTERN.search(text)
        if not match:
            return None

        day = int(match.group(1))
        month_str = match.group(2).lower()
        year = int(match.group(3))

        month = FRENCH_MONTHS.get(month_str)
        if not month:
            return None

        try:
            return date(year, month, day)
        except ValueError:
            logger.warning("Date invalide extraite: %d/%d/%d depuis '%s'", day, month, year, text)
            return None

    @staticmethod
    def extract_pdf_filename(pdf_url: str) -> str:
        """
        Extrait le nom de fichier depuis une URL de PDF.

        Gère le URL-encoding (ex: %27 → ').

        Args:
            pdf_url: URL complète du PDF.

        Returns:
            Nom de fichier décodé.
        """
        parsed = urlparse(pdf_url)
        path = unquote(parsed.path)
        return path.split("/")[-1]

    @staticmethod
    def classify_document(title: str, pdf_url: str) -> DocumentType:
        """
        Détermine le type de document à partir de son titre et de l'URL PDF.

        Args:
            title: Titre du document depuis la page.
            pdf_url: URL du PDF.

        Returns:
            Le type de document.
        """
        title_lower = title.lower() if title else ""
        url_lower = pdf_url.lower()

        if "journal hippique" in title_lower or "/jh_" in url_lower:
            return DocumentType.JOURNAL_HIPPIQUE
        elif "résultat" in title_lower or "resultat" in title_lower or "/res" in url_lower:
            return DocumentType.RESULTAT
        elif "récapitulatif" in title_lower or "recapitulatif" in title_lower or "/recap" in url_lower:
            return DocumentType.RECAPITULATIF
        else:
            return DocumentType.UNKNOWN

    def extract_documents_from_table(
        self,
        soup: BeautifulSoup,
        source_url: str,
        pdf_field_class: str,
        default_type: DocumentType = DocumentType.UNKNOWN,
    ) -> list[DocumentMetadata]:
        """
        Extrait les documents depuis un tableau Drupal Views.

        Chaque ligne <tr> du tableau contient :
        - Une cellule titre (views-field-title)
        - Une cellule avec le lien PDF (pdf_field_class)

        Args:
            soup: Le BeautifulSoup de la page.
            source_url: L'URL de la page source.
            pdf_field_class: La classe CSS de la cellule contenant le lien PDF.
            default_type: Type par défaut pour les documents.

        Returns:
            Liste de DocumentMetadata découverts.
        """
        documents: list[DocumentMetadata] = []

        # Trouver toutes les lignes du tableau
        rows = soup.find_all("tr")
        if not rows:
            logger.warning("Aucune ligne de tableau trouvée sur: %s", source_url)
            return documents

        for row in rows:
            try:
                # Extraire le titre
                title_cell = row.find("td", class_="views-field-title")
                title = title_cell.get_text(strip=True) if title_cell else None

                # Extraire le lien PDF
                pdf_cell = row.find("td", class_=pdf_field_class)
                if not pdf_cell:
                    continue

                pdf_link = pdf_cell.find("a", href=True)
                if not pdf_link:
                    continue

                href = pdf_link["href"]

                # Vérifier que c'est un PDF
                if not href.lower().endswith(".pdf"):
                    logger.warning("Lien non-PDF ignoré: %s", href)
                    continue

                # Construire l'URL absolue
                pdf_url = urljoin(BASE_URL, href)

                # Extraire la date du titre
                pub_date = self.parse_french_date(title) if title else None

                # Classifier le document
                doc_type = self.classify_document(title or "", pdf_url)
                if doc_type == DocumentType.UNKNOWN:
                    doc_type = default_type

                # Créer les métadonnées
                doc = DocumentMetadata.create(
                    pdf_url=pdf_url,
                    source_url=source_url,
                    document_type=doc_type,
                    title=title,
                    publication_date=pub_date,
                )

                documents.append(doc)
                logger.debug("Document trouvé: %s — %s", title, pdf_url)

            except Exception as e:
                logger.error("Erreur lors du parsing d'une ligne du tableau: %s", e)
                continue

        logger.info("%d document(s) trouvé(s) sur: %s", len(documents), source_url)
        return documents
