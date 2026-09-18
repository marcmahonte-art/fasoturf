"""
Tests unitaires pour le scraper PMU'B LONAB.

Utilise des fixtures HTML locales — ne fait aucune requête réseau.
"""

from __future__ import annotations

import json
import tempfile
from datetime import date
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from app.models.document import DocumentMetadata, DocumentType, DocumentStatus
from app.scraper.lonab import LonabScraper
from app.utils.hashing import compute_sha256
from tests.fixtures import (
    PROGRAMMES_PAGE_HTML,
    RESULTATS_PAGE_HTML,
    LAST_PAGE_HTML,
    EMPTY_PAGE_HTML,
    NON_PDF_LINK_HTML,
)


# ──────────────────────────────────────────────
# Tests: Extraction de dates françaises
# ──────────────────────────────────────────────

class TestParseFrenchDate:
    """Tests pour LonabScraper.parse_french_date()."""

    def test_date_septembre_minuscule(self):
        result = LonabScraper.parse_french_date("journal hippique PMU'B du 08 septembre 2026")
        assert result == date(2026, 9, 8)

    def test_date_septembre_majuscule(self):
        result = LonabScraper.parse_french_date("résultats PMU'B du 07 Septembre 2026")
        assert result == date(2026, 9, 7)

    def test_date_aout_majuscule(self):
        result = LonabScraper.parse_french_date("journal hippique PMU'B du 31 AOUT 2026")
        assert result == date(2026, 8, 31)

    def test_date_aout_accent(self):
        result = LonabScraper.parse_french_date("document du 15 août 2025")
        assert result == date(2025, 8, 15)

    def test_date_janvier(self):
        result = LonabScraper.parse_french_date("journal hippique du 01 janvier 2024")
        assert result == date(2024, 1, 1)

    def test_date_fevrier_sans_accent(self):
        result = LonabScraper.parse_french_date("document du 14 fevrier 2025")
        assert result == date(2025, 2, 14)

    def test_date_decembre(self):
        result = LonabScraper.parse_french_date("résultats du 25 décembre 2023")
        assert result == date(2023, 12, 25)

    def test_pas_de_date(self):
        result = LonabScraper.parse_french_date("document sans date")
        assert result is None

    def test_texte_vide(self):
        result = LonabScraper.parse_french_date("")
        assert result is None

    def test_date_avec_html_entities(self):
        """Le titre après parsing BS4 contient PMU'B (pas l'entité HTML)."""
        result = LonabScraper.parse_french_date("journal hippique PMU'B du 09 septembre 2026")
        assert result == date(2026, 9, 9)


# ──────────────────────────────────────────────
# Tests: Extraction de liens PDF
# ──────────────────────────────────────────────

class TestExtractDocumentsFromTable:
    """Tests pour l'extraction des documents depuis les tableaux HTML."""

    def setup_method(self):
        self.scraper = LonabScraper()

    def test_extract_programmes(self):
        """Extrait correctement les 3 programmes de la fixture."""
        soup = BeautifulSoup(PROGRAMMES_PAGE_HTML, "html.parser")
        docs = self.scraper.extract_documents_from_table(
            soup=soup,
            source_url="https://lonab.bf/programme-pmub",
            pdf_field_class="views-field-field-ajouter-un-fichier",
            default_type=DocumentType.JOURNAL_HIPPIQUE,
        )

        assert len(docs) == 3

        # Premier document
        assert docs[0].title == "journal hippique PMU'B du 09 septembre 2026"
        assert docs[0].pdf_url == "https://lonab.bf/sites/default/files/2026-09/JH_PMU%27B_DU_09-09-2026_0.pdf"
        assert docs[0].publication_date == date(2026, 9, 9)
        assert docs[0].document_type == DocumentType.JOURNAL_HIPPIQUE

        # Troisième document (mois en majuscule)
        assert docs[2].publication_date == date(2026, 8, 31)

    def test_extract_resultats_with_drupal_typo(self):
        """Extrait correctement les résultats avec la classe 'docuent'."""
        soup = BeautifulSoup(RESULTATS_PAGE_HTML, "html.parser")
        docs = self.scraper.extract_documents_from_table(
            soup=soup,
            source_url="https://lonab.bf/resultats-gains-pmub",
            pdf_field_class="views-field-field-ajouter-un-docuent",
            default_type=DocumentType.RESULTAT,
        )

        assert len(docs) == 3
        assert docs[0].pdf_url.endswith("Res_07_09_2026_QUARTE.pdf")
        assert docs[0].document_type == DocumentType.RESULTAT

    def test_same_date_different_pdfs(self):
        """Deux résultats pour le 06 septembre avec des PDF différents."""
        soup = BeautifulSoup(RESULTATS_PAGE_HTML, "html.parser")
        docs = self.scraper.extract_documents_from_table(
            soup=soup,
            source_url="https://lonab.bf/resultats-gains-pmub",
            pdf_field_class="views-field-field-ajouter-un-docuent",
            default_type=DocumentType.RESULTAT,
        )

        # Deux docs avec la même date mais des URLs différentes
        sept6_docs = [d for d in docs if d.publication_date == date(2026, 9, 6)]
        assert len(sept6_docs) == 2
        assert sept6_docs[0].pdf_url != sept6_docs[1].pdf_url

    def test_empty_page(self):
        """Page sans tableau retourne une liste vide."""
        soup = BeautifulSoup(EMPTY_PAGE_HTML, "html.parser")
        docs = self.scraper.extract_documents_from_table(
            soup=soup,
            source_url="https://lonab.bf/programme-pmub",
            pdf_field_class="views-field-field-ajouter-un-fichier",
        )
        assert len(docs) == 0

    def test_non_pdf_link_filtered(self):
        """Les liens non-PDF (.html) sont ignorés."""
        soup = BeautifulSoup(NON_PDF_LINK_HTML, "html.parser")
        docs = self.scraper.extract_documents_from_table(
            soup=soup,
            source_url="https://lonab.bf/programme-pmub",
            pdf_field_class="views-field-field-ajouter-un-fichier",
        )

        assert len(docs) == 1  # Seul le PDF est retenu
        assert docs[0].pdf_url.endswith(".pdf")


# ──────────────────────────────────────────────
# Tests: Pagination
# ──────────────────────────────────────────────

class TestPagination:
    """Tests pour la détection de la pagination."""

    def setup_method(self):
        self.scraper = LonabScraper()

    def test_next_page_detected(self):
        """Détecte le lien vers la page suivante."""
        soup = BeautifulSoup(PROGRAMMES_PAGE_HTML, "html.parser")
        next_url = self.scraper.get_next_page_url(soup, "https://lonab.bf/programme-pmub")

        assert next_url is not None
        assert "page=1" in next_url

    def test_last_page_no_next(self):
        """La dernière page n'a pas de lien 'next'."""
        soup = BeautifulSoup(LAST_PAGE_HTML, "html.parser")
        next_url = self.scraper.get_next_page_url(soup, "https://lonab.bf/programme-pmub?page=42")

        assert next_url is None


# ──────────────────────────────────────────────
# Tests: Classification des documents
# ──────────────────────────────────────────────

class TestClassifyDocument:
    """Tests pour la classification des types de documents."""

    def test_journal_hippique_from_title(self):
        doc_type = LonabScraper.classify_document(
            "journal hippique PMU'B du 08 septembre 2026",
            "https://lonab.bf/sites/default/files/2026-09/JH_PMUB_DU_08-09-2026.pdf",
        )
        assert doc_type == DocumentType.JOURNAL_HIPPIQUE

    def test_journal_hippique_from_url(self):
        doc_type = LonabScraper.classify_document(
            "Document inconnu",
            "https://lonab.bf/sites/default/files/2026-09/JH_PMUB_DU_08-09-2026.pdf",
        )
        assert doc_type == DocumentType.JOURNAL_HIPPIQUE

    def test_resultat_from_title(self):
        doc_type = LonabScraper.classify_document(
            "Télécharger les résultats PMU'B du 07 Septembre 2026",
            "https://lonab.bf/sites/default/files/2026-09/Res_07_09_2026_QUARTE.pdf",
        )
        assert doc_type == DocumentType.RESULTAT

    def test_resultat_from_url(self):
        doc_type = LonabScraper.classify_document(
            "Document",
            "https://lonab.bf/sites/default/files/2026-09/Res41_06_09_2026.pdf",
        )
        assert doc_type == DocumentType.RESULTAT

    def test_unknown(self):
        doc_type = LonabScraper.classify_document(
            "Autre document",
            "https://lonab.bf/sites/default/files/2026-09/autre.pdf",
        )
        assert doc_type == DocumentType.UNKNOWN


# ──────────────────────────────────────────────
# Tests: SHA-256
# ──────────────────────────────────────────────

class TestSHA256:
    """Tests pour le calcul SHA-256."""

    def test_sha256_known_content(self):
        """Vérifie le SHA-256 d'un contenu connu."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(b"%PDF-1.4 test content")
            f.flush()
            path = Path(f.name)

        try:
            sha = compute_sha256(path)
            assert len(sha) == 64  # SHA-256 hex = 64 chars
            assert sha.isalnum()

            # Même contenu = même hash
            sha2 = compute_sha256(path)
            assert sha == sha2
        finally:
            path.unlink()

    def test_sha256_different_content(self):
        """Deux contenus différents donnent des hash différents."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f1:
            f1.write(b"content A")
            f1.flush()
            path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f2:
            f2.write(b"content B")
            f2.flush()
            path2 = Path(f2.name)

        try:
            assert compute_sha256(path1) != compute_sha256(path2)
        finally:
            path1.unlink()
            path2.unlink()


# ──────────────────────────────────────────────
# Tests: Déduplication
# ──────────────────────────────────────────────

class TestDeduplication:
    """Tests pour la déduplication des documents."""

    def test_deterministic_id(self):
        """Le même pdf_url génère toujours le même ID."""
        doc1 = DocumentMetadata.create(
            pdf_url="https://lonab.bf/sites/default/files/test.pdf",
            source_url="https://lonab.bf/programme-pmub",
        )
        doc2 = DocumentMetadata.create(
            pdf_url="https://lonab.bf/sites/default/files/test.pdf",
            source_url="https://lonab.bf/programme-pmub",
        )
        assert doc1.id == doc2.id

    def test_different_url_different_id(self):
        """Deux URLs différentes donnent des IDs différents."""
        doc1 = DocumentMetadata.create(
            pdf_url="https://lonab.bf/sites/default/files/test1.pdf",
            source_url="https://lonab.bf/programme-pmub",
        )
        doc2 = DocumentMetadata.create(
            pdf_url="https://lonab.bf/sites/default/files/test2.pdf",
            source_url="https://lonab.bf/programme-pmub",
        )
        assert doc1.id != doc2.id


# ──────────────────────────────────────────────
# Tests: Sérialisation JSONL
# ──────────────────────────────────────────────

class TestJSONLSerialization:
    """Tests pour la sérialisation/désérialisation JSONL."""

    def test_roundtrip(self):
        """Un document peut être sérialisé puis désérialisé sans perte."""
        doc = DocumentMetadata.create(
            pdf_url="https://lonab.bf/sites/default/files/2026-09/test.pdf",
            source_url="https://lonab.bf/programme-pmub",
            document_type=DocumentType.JOURNAL_HIPPIQUE,
            title="journal hippique PMU'B du 08 septembre 2026",
            publication_date=date(2026, 9, 8),
        )

        jsonl = doc.to_jsonl()
        restored = DocumentMetadata.from_jsonl(jsonl)

        assert restored.id == doc.id
        assert restored.pdf_url == doc.pdf_url
        assert restored.publication_date == doc.publication_date
        assert restored.document_type == DocumentType.JOURNAL_HIPPIQUE
        assert restored.status == DocumentStatus.DISCOVERED

    def test_null_fields_preserved(self):
        """Les champs null sont correctement sérialisés."""
        doc = DocumentMetadata.create(
            pdf_url="https://lonab.bf/test.pdf",
            source_url="https://lonab.bf/programme-pmub",
        )

        jsonl = doc.to_jsonl()
        data = json.loads(jsonl)

        assert data["publication_date"] is None
        assert data["local_path"] is None
        assert data["sha256"] is None
        assert data["file_size"] is None


# ──────────────────────────────────────────────
# Tests: Extraction du nom de fichier
# ──────────────────────────────────────────────

class TestExtractPDFFilename:
    """Tests pour l'extraction du nom de fichier depuis l'URL."""

    def test_simple_filename(self):
        name = LonabScraper.extract_pdf_filename(
            "https://lonab.bf/sites/default/files/2026-09/JH_PMUB_DU_08-09-2026.pdf"
        )
        assert name == "JH_PMUB_DU_08-09-2026.pdf"

    def test_url_encoded_filename(self):
        name = LonabScraper.extract_pdf_filename(
            "https://lonab.bf/sites/default/files/2026-09/JH_PMU%27B_DU_09-09-2026_0.pdf"
        )
        assert name == "JH_PMU'B_DU_09-09-2026_0.pdf"

    def test_resultat_filename(self):
        name = LonabScraper.extract_pdf_filename(
            "https://lonab.bf/sites/default/files/2026-09/Res_07_09_2026_QUARTE.pdf"
        )
        assert name == "Res_07_09_2026_QUARTE.pdf"
