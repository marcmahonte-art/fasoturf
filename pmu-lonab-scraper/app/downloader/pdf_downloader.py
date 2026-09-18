"""
Téléchargeur de PDF avec vérification, hashing et gestion d'erreurs.

Télécharge les fichiers PDF depuis les URLs découvertes par les scrapers,
les enregistre localement avec une structure de dossiers par date,
et met à jour les métadonnées.
"""

from __future__ import annotations

import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

from app.models.document import DocumentMetadata, DocumentStatus
from app.utils.hashing import compute_sha256
from app.utils.logging_config import get_logger

logger = get_logger("downloader")


class PDFDownloader:
    """
    Téléchargeur robuste de fichiers PDF.

    Fonctionnalités :
    - Vérification du Content-Type (application/pdf)
    - Structure de dossiers par année/mois
    - Conservation du nom de fichier original
    - Calcul du SHA-256
    - Skip des fichiers déjà téléchargés
    - Retries avec backoff
    """

    def __init__(
        self,
        data_dir: Path,
        request_timeout: int = 30,
        max_retries: int = 3,
        request_delay: float = 1.0,
    ):
        self.data_dir = data_dir
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.request_delay = request_delay
        self._last_request_time: float = 0.0

        # Session HTTP
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PMU-B-Scraper/0.1 (PDF download; contact: admin@example.com)",
        })

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
        """Délai entre les requêtes."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)

    def _build_local_path(self, doc: DocumentMetadata) -> Path:
        """
        Construit le chemin local pour un fichier PDF.

        Structure: data/raw/{type}/YYYY/MM/nom_original.pdf

        Si la date de publication est disponible, utilise année/mois.
        Sinon, utilise "unknown_date/".
        """
        # Déterminer le sous-dossier par type
        type_folder = doc.document_type.value  # journal_hippique, resultat, etc.

        # Sous-dossier par date
        if doc.publication_date:
            year = str(doc.publication_date.year)
            month = f"{doc.publication_date.month:02d}"
            date_folder = Path(year) / month
        else:
            date_folder = Path("unknown_date")

        # Nom de fichier original (décodé depuis l'URL)
        parsed = urlparse(doc.pdf_url)
        original_filename = unquote(parsed.path.split("/")[-1])

        # Nettoyer le nom de fichier (garder uniquement les caractères sûrs)
        safe_filename = self._sanitize_filename(original_filename)

        return self.data_dir / "raw" / type_folder / date_folder / safe_filename

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """
        Nettoie un nom de fichier en conservant les caractères sûrs.

        Remplace les caractères problématiques par des underscores.
        """
        # Remplacer les caractères spéciaux courants
        safe = filename.replace("'", "_").replace("'", "_")

        # Garder uniquement les caractères alphanumériques, underscores, tirets, points
        result = []
        for char in safe:
            if char.isalnum() or char in "-_.":
                result.append(char)
            else:
                result.append("_")

        cleaned = "".join(result)

        # Éviter les doubles underscores
        while "__" in cleaned:
            cleaned = cleaned.replace("__", "_")

        return cleaned

    def download(self, doc: DocumentMetadata) -> DocumentMetadata:
        """
        Télécharge un PDF et met à jour les métadonnées.

        Args:
            doc: Le document à télécharger.

        Returns:
            Le document avec métadonnées mises à jour (local_path, sha256, etc.).
        """
        local_path = self._build_local_path(doc)

        # Vérifier si le fichier existe déjà
        if local_path.exists():
            logger.info("Fichier déjà existant, skip: %s", local_path)
            existing_sha = compute_sha256(local_path)
            doc.local_path = str(local_path)
            doc.sha256 = existing_sha
            doc.file_size = local_path.stat().st_size
            doc.status = DocumentStatus.SKIPPED
            return doc

        # Créer les répertoires
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Télécharger
        self._wait_between_requests()

        try:
            logger.info("Téléchargement: %s", doc.pdf_url)
            response = self.session.get(doc.pdf_url, timeout=self.request_timeout, stream=True)
            self._last_request_time = time.time()

            response.raise_for_status()

            # Vérifier le Content-Type
            content_type = response.headers.get("Content-Type", "").lower()
            if "application/pdf" not in content_type and "application/octet-stream" not in content_type:
                logger.warning(
                    "Content-Type inattendu '%s' pour: %s — tentative de vérification du contenu",
                    content_type, doc.pdf_url,
                )

            # Lire le contenu
            content = response.content

            # Vérifier la signature PDF (%PDF-)
            if not content[:5].startswith(b"%PDF-"):
                logger.error(
                    "Le fichier n'est pas un PDF valide (signature manquante): %s",
                    doc.pdf_url,
                )
                doc.status = DocumentStatus.FAILED
                return doc

            # Écrire le fichier
            local_path.write_bytes(content)

            # Calculer SHA-256 et taille
            doc.local_path = str(local_path)
            doc.sha256 = compute_sha256(local_path)
            doc.file_size = local_path.stat().st_size
            doc.status = DocumentStatus.DOWNLOADED

            logger.info(
                "Téléchargé: %s (%d octets, SHA-256: %s...)",
                local_path.name, doc.file_size, doc.sha256[:16],
            )

        except requests.exceptions.Timeout:
            logger.error("Timeout lors du téléchargement: %s", doc.pdf_url)
            doc.status = DocumentStatus.FAILED
        except requests.exceptions.HTTPError as e:
            logger.error("Erreur HTTP %s pour: %s", e.response.status_code, doc.pdf_url)
            doc.status = DocumentStatus.FAILED
        except requests.exceptions.ConnectionError:
            logger.error("Erreur de connexion pour: %s", doc.pdf_url)
            doc.status = DocumentStatus.FAILED
        except requests.exceptions.RequestException as e:
            logger.error("Erreur lors du téléchargement de %s: %s", doc.pdf_url, e)
            doc.status = DocumentStatus.FAILED
        except OSError as e:
            logger.error("Erreur d'écriture du fichier %s: %s", local_path, e)
            doc.status = DocumentStatus.FAILED

        return doc

    def download_all(self, documents: list[DocumentMetadata]) -> list[DocumentMetadata]:
        """
        Télécharge une liste de documents.

        Args:
            documents: Liste des documents à télécharger.

        Returns:
            Liste des documents avec métadonnées mises à jour.
        """
        results: list[DocumentMetadata] = []
        total = len(documents)

        for i, doc in enumerate(documents, 1):
            logger.info("--- [%d/%d] ---", i, total)
            updated_doc = self.download(doc)
            results.append(updated_doc)

        # Résumé
        downloaded = sum(1 for d in results if d.status == DocumentStatus.DOWNLOADED)
        skipped = sum(1 for d in results if d.status == DocumentStatus.SKIPPED)
        failed = sum(1 for d in results if d.status == DocumentStatus.FAILED)

        logger.info(
            "=== Résumé téléchargement: %d téléchargés, %d skippés, %d échoués ===",
            downloaded, skipped, failed,
        )

        return results
