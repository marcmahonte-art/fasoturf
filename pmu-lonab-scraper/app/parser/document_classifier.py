"""Document classifier for LONAB PMU'B PDFs."""

import re
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class DocumentType(Enum):
    """Types of documents in the corpus."""
    RESULTAT_QUARTE = "RESULTAT_QUARTE"
    RESULTAT_TIERCE = "RESULTAT_TIERCE"
    RESULTAT_OTHER = "RESULTAT_OTHER"
    REP = "REP"
    ECD = "ECD"
    PROGRAMME = "PROGRAMME"
    UNKNOWN = "UNKNOWN"


@dataclass
class ClassificationResult:
    """Result of document classification."""
    document_type: DocumentType
    game_type: Optional[str] = None
    confidence: float = 0.0
    markers: list = None
    warnings: list = None
    
    def __post_init__(self):
        if self.markers is None:
            self.markers = []
        if self.warnings is None:
            self.warnings = []


class DocumentClassifier:
    """Classifies PDF documents based on filename and content."""
    
    def __init__(self):
        # Markers for each document type (content-based, highest priority)
        self.content_markers = {
            DocumentType.RESULTAT_QUARTE: [
                r'QUARTE\s+DU',
                r'MAP\s+QUARTE',
                r'ARR\s*[:=]\s*\d+(?:\s*[-–]\s*\d+){3,}',  # 4+ numbers in arrival
            ],
            DocumentType.RESULTAT_TIERCE: [
                r'TIERCE\s+DU',
                r'MAP\s+TIERCE',
                r'ARR\s*[:=]\s*\d+(?:\s*[-–]\s*\d+){2}',  # 3 numbers in arrival
            ],
            DocumentType.REP: [
                r'REPORT\s+ORD\.',
                r'REPORT\s+ORD\s*"?\d+\+?\d*"?\s+DU',
                r'RAPPORT\s+ORD\.',
            ],
            DocumentType.ECD: [
                r'ESPACE\s+COURSE\s+EN\s+DIRECT',
                r'RECAPITULATIF\s+DES\s+ARRIVEES\s+DES\s+COURSES',
                r'\b(?:1ère|2ième|3ième|4ième|5ième|6ième|7ième|8ième|9ième)\b.*ARRIVEE',
            ],
            DocumentType.PROGRAMME: [
                r'JOURNAL\s+HIPPIQUE',
                r'PROGRAMME\s+OFFICIEL',
                r'\d+\s+CONCURRENTS',
                r'PRIX\s+DE\s+',
            ],
        }
        
        # Filename patterns (lower priority, used as hints)
        self.filename_patterns = {
            DocumentType.RESULTAT_QUARTE: [r'Res_.*_QUARTE\.pdf$', r'Res_\d+_\d+_\d+_QUARTE'],
            DocumentType.RESULTAT_TIERCE: [r'Res_.*_TIERCE\.pdf$', r'Res_\d+_\d+_\d+_TIERCE'],
            DocumentType.REP: [r'Rep(?:t)?\d+_\d+_\d+_\d+\.pdf$', r'Rept\d+_'],
            DocumentType.ECD: [r'ECD_\d+-\d+-\d+_R\d+'],
            DocumentType.PROGRAMME: [r'JH_PMUB_DU_'],
        }
        
        # Game type detection within RESULTAT
        self.game_type_markers = {
            'QUARTE': [r'QUARTE\s+DU', r'MAP\s+QUARTE'],
            'TIERCE': [r'TIERCE\s+DU', r'MAP\s+TIERCE'],
            '4+1': [r'REPORT\s+ORD\.\s*"?4\+1"?', r'4\+1'],
            'COUPLE': [r'COUPLE\s+DU', r'MAP\s+COUPLE'],
        }
    
    def classify(self, filename: str, text: str) -> ClassificationResult:
        """
        Classify a document based on filename and extracted text.
        
        Priority: content markers > filename patterns
        """
        upper_text = text.upper()
        upper_filename = filename.upper()
        
        # Check content markers first (highest confidence)
        for doc_type, patterns in self.content_markers.items():
            for pattern in patterns:
                if re.search(pattern, upper_text, re.IGNORECASE):
                    confidence = 0.9
                    markers = [pattern]
                    
                    # Determine game_type for RESULTAT types
                    game_type = None
                    if doc_type in (DocumentType.RESULTAT_QUARTE, DocumentType.RESULTAT_TIERCE):
                        game_type = self._detect_game_type(upper_text)
                    
                    return ClassificationResult(
                        document_type=doc_type,
                        game_type=game_type,
                        confidence=confidence,
                        markers=markers
                    )
        
        # Fall back to filename patterns
        for doc_type, patterns in self.filename_patterns.items():
            for pattern in patterns:
                if re.search(pattern, upper_filename, re.IGNORECASE):
                    confidence = 0.6
                    markers = [f"filename:{pattern}"]
                    
                    game_type = None
                    if doc_type == DocumentType.RESULTAT_QUARTE:
                        game_type = 'QUARTE'
                    elif doc_type == DocumentType.RESULTAT_TIERCE:
                        game_type = 'TIERCE'
                    
                    return ClassificationResult(
                        document_type=doc_type,
                        game_type=game_type,
                        confidence=confidence,
                        markers=markers,
                        warnings=["Classification based on filename only"]
                    )
        
        # Unknown
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            warnings=["No markers matched - manual review needed"]
        )
    
    def _detect_game_type(self, text: str) -> Optional[str]:
        """Detect the game type within a RESULTAT document."""
        for game_type, patterns in self.game_type_markers.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return game_type
        return None
    
    def get_parser_type(self, classification: ClassificationResult) -> str:
        """Get the parser type to use for a classification."""
        if classification.document_type in (DocumentType.RESULTAT_QUARTE, DocumentType.RESULTAT_TIERCE, DocumentType.RESULTAT_OTHER):
            return 'resultat'
        elif classification.document_type == DocumentType.REP:
            return 'rep'
        elif classification.document_type == DocumentType.ECD:
            return 'ecd'
        elif classification.document_type == DocumentType.PROGRAMME:
            return 'journal'
        else:
            return 'unknown'


def classify_document(filename: str, text: str) -> ClassificationResult:
    """Convenience function for single classification."""
    classifier = DocumentClassifier()
    return classifier.classify(filename, text)