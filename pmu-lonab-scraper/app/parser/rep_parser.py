"""Parser for REP (Report) documents."""

import re
import fitz
from typing import Optional
from app.models.parser_models import RepDocument, ParsedRepDocument
from app.parser.normalizer import parse_date_fr, parse_gains


class RepParser:
    """Parser pour les documents REP (Rapports) LONAB."""
    
    def parse(self, pdf_path: str) -> ParsedRepDocument:
        filename = pdf_path.split('\\')[-1].split('/')[-1]
        doc = fitz.open(pdf_path)
        
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        
        parsed = ParsedRepDocument(
            filename=filename,
            doc_type='REP',
            date_publication='',
            pages=len(doc)
        )
        
        rep_doc = self._parse_rep(full_text, filename)
        parsed.rep_document = rep_doc
        parsed.date_publication = rep_doc.date_document or rep_doc.date_course_cible or ""
        
        doc.close()
        return parsed
    
    def _parse_rep(self, text: str, filename: str) -> RepDocument:
        """Parse le texte complet d'un document REP."""
        r = RepDocument(raw_text=text)
        
        # 1. Extraire la date du document (souvent à la fin: "15/01/2025")
        # Pattern: DD/MM/YYYY à la fin ou isolé
        m = re.search(r'(\d{2}/\d{2}/\d{4})\s*$', text.strip(), re.MULTILINE)
        if m:
            r.date_document_raw = m.group(1)
            r.date_document = self._parse_date_ddmmyyyy(m.group(1))
        
        # 2. Extraire la date de la course cible (dans "REPORT ORD. ... DU VENDREDI 17/01/2025")
        m = re.search(r'REPORT\s+ORD\.?\s*"?[\d\+\s]*"?\s+DU\s+([A-Z]+\s+\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
        if m:
            r.date_course_cible_raw = m.group(1)
            r.date_course_cible = self._parse_date_fr_with_day(m.group(1))
        
        # Alternative pattern: "DU VENDREDI 17/01/2025:" ou "DU 17/01/2025"
        if not r.date_course_cible:
            m = re.search(r'\bDU\s+([A-Z]+\s+\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
            if m:
                r.date_course_cible_raw = m.group(1)
                r.date_course_cible = self._parse_date_fr_with_day(m.group(1))
        
        # 3. Extraire le type de jeu (ex: "4+1", "QUARTE", "TIERCE")
        # Pattern: REPORT ORD. "4+1" ou REPORT ORD. 4+1
        m = re.search(r'REPORT\s+ORD\.?\s*"?([\d\+\s]+)"?', text, re.IGNORECASE)
        if m:
            r.game_type = m.group(1).strip().replace(' ', '')
        
        # 4. Extraire le montant du rapport ordre
        # Pattern: "VENDREDI 17/01/2025:\n59 386 377" ou sur la même ligne
        m = re.search(r'REPORT\s+ORD\.?\s*"?[\d\+\s]*"?\s+DU\s+[A-Z]+\s+\d{2}/\d{2}/\d{4}\s*[:：]\s*([\d\s\u202f\xa0]+)', text, re.IGNORECASE)
        if m:
            r.report_ordre_raw = m.group(1).strip()
            r.report_ordre = parse_gains(r.report_ordre_raw)[1]
        
        # Alternative: chercher un gros montant après la date de course
        if r.report_ordre is None:
            # Chercher un nombre à 6+ chiffres après la date de course cible
            if r.date_course_cible_raw:
                # Position de la date de course dans le texte
                idx = text.find(r.date_course_cible_raw)
                if idx >= 0:
                    after_date = text[idx + len(r.date_course_cible_raw):idx + 200]
                    # Capturer le montant mais s'arrêter avant une date DD/MM/YYYY
                    m = re.search(r'[:：]\s*([\d\s\u202f\xa0]+?)(?:\s*\d{2}/\d{2}/\d{4}|\s*$)', after_date)
                    if m:
                        r.report_ordre_raw = m.group(1).strip()
                        r.report_ordre = parse_gains(r.report_ordre_raw)[1]
        
        # 5. Chercher ligne TIERCE V. (ne doit PAS être confondue avec l'arrivée)
        m = re.search(r'TIERCE\s+V\.?\s*[:：]?\s*([^\n]+)', text, re.IGNORECASE)
        if m:
            r.tierce_v_raw = m.group(0).strip()
            r.tierce_v_value = m.group(1).strip()
        
        return r
    
    def _parse_date_ddmmyyyy(self, date_str: str) -> str:
        """Parse DD/MM/YYYY -> YYYY-MM-DD"""
        try:
            day, month, year = date_str.split('/')
            return f"{year}-{month}-{day}"
        except:
            return ""
    
    def _parse_date_fr_with_day(self, date_str: str) -> str:
        """Parse 'VENDREDI 17/01/2025' -> '2025-01-17'"""
        # Extraire juste la partie date
        m = re.search(r'(\d{2}/\d{2}/\d{4})', date_str)
        if m:
            return self._parse_date_ddmmyyyy(m.group(1))
        return ""


def parse_rep_document(pdf_path: str) -> ParsedRepDocument:
    """Convenience function to parse a REP document."""
    parser = RepParser()
    return parser.parse(pdf_path)