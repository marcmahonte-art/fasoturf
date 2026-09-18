"""
Modèle Pydantic pour les métadonnées des documents PMU'B.

Chaque document (journal hippique ou résultat) est représenté par
une instance de DocumentMetadata. Les champs non disponibles sont null.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Type de document PMU'B."""
    JOURNAL_HIPPIQUE = "journal_hippique"
    RESULTAT = "resultat"
    RECAPITULATIF = "recapitulatif"
    COURSE_EN_DIRECT = "course_en_direct"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    """Statut du cycle de vie d'un document."""
    DISCOVERED = "discovered"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    SKIPPED = "skipped"


def _generate_id(pdf_url: str) -> str:
    """Génère un ID déterministe basé sur l'URL du PDF."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, pdf_url))


class DocumentMetadata(BaseModel):
    """Métadonnées complètes d'un document PMU'B."""

    id: str = Field(description="UUID déterministe basé sur pdf_url")
    document_type: DocumentType = Field(
        default=DocumentType.UNKNOWN,
        description="Type de document: journal_hippique, resultat, recapitulatif, unknown"
    )
    source_url: str = Field(description="URL de la page LONAB où le document a été découvert")
    pdf_url: str = Field(description="URL directe du fichier PDF")
    title: Optional[str] = Field(default=None, description="Titre du document tel qu'affiché sur le site")
    publication_date: Optional[date] = Field(
        default=None,
        description="Date de publication extraite du titre (peut être null)"
    )
    discovered_at: datetime = Field(
        default_factory=datetime.now,
        description="Date et heure de découverte par le scraper"
    )
    local_path: Optional[str] = Field(
        default=None,
        description="Chemin local du fichier PDF téléchargé"
    )
    sha256: Optional[str] = Field(
        default=None,
        description="Hash SHA-256 du fichier téléchargé"
    )
    file_size: Optional[int] = Field(
        default=None,
        description="Taille du fichier en octets"
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.DISCOVERED,
        description="Statut du document dans le pipeline"
    )

    @classmethod
    def create(
        cls,
        pdf_url: str,
        source_url: str,
        document_type: DocumentType = DocumentType.UNKNOWN,
        title: Optional[str] = None,
        publication_date: Optional[date] = None,
    ) -> DocumentMetadata:
        """Factory method pour créer un document avec un ID déterministe."""
        return cls(
            id=_generate_id(pdf_url),
            document_type=document_type,
            source_url=source_url,
            pdf_url=pdf_url,
            title=title,
            publication_date=publication_date,
        )

    def to_jsonl(self) -> str:
        """Sérialise en une ligne JSON pour le fichier JSONL."""
        return self.model_dump_json()

    @classmethod
    def from_jsonl(cls, line: str) -> DocumentMetadata:
        """Désérialise depuis une ligne JSON."""
        return cls.model_validate_json(line.strip())
