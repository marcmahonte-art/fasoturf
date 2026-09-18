import re
from typing import List, Optional, Tuple
from app.models.parser_models import Resultat, ParsedDocument
from app.parser.normalizer import (
    parse_date_fr, parse_arrivee, parse_nb_gagnants,
    generate_course_id, parse_gains
)


EXPECTED_ARRIVAL_LENGTH = {
    'QUARTE': 4,
    'TIERCE': 3,
    '4+1': 4,
    'COUPLE': 2,
}


class ResultatParser:
    """Parser pour les PDF de résultats LONAB (1 page généralement)."""
    
    def parse(self, pdf_path: str) -> ParsedDocument:
        import fitz
        filename = pdf_path.split('\\')[-1].split('/')[-1]
        doc = fitz.open(pdf_path)
        
        # Concaténer tout le texte
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        
        parsed = ParsedDocument(
            filename=filename,
            doc_type='RESULTAT',
            date_publication=parse_date_fr(full_text) or "",
            pages=len(doc)
        )
        
        # Parser le résultat
        resultat = self._parse_resultat(full_text, filename)
        parsed.resultat = resultat
        
        # Si on a une date et un type, générer course_id
        if resultat.date and resultat.type_pari:
            safe_type = resultat.type_pari.replace('+', 'PLUS')
            resultat.course_id = f"{resultat.date}_{safe_type}_R1"
        
        doc.close()
        return parsed
    
    def _parse_resultat(self, text: str, filename: str) -> Resultat:
        """Parse le texte complet d'un résultat."""
        r = Resultat(
            course_id="",
            date=parse_date_fr(text) or "",
            raw_text=text
        )
        
        # Type de pari
        upper = text.upper()
        if 'QUARTE' in upper:
            r.type_pari = 'QUARTE'
        elif '4+1' in text or '4 1' in text or '4 PLUS 1' in upper:
            r.type_pari = '4+1'
        elif 'TIERCE' in upper:
            r.type_pari = 'TIERCE'
        elif 'COUPLE' in upper:
            r.type_pari = 'COUPLE'
        
        # Arrivée: "ARR : 9 - 2 - 16 - 12 - 1" ou "ARR :1-2-8-6"
        m = re.search(r'ARR\s*[:=]\s*([\d\s\-\,\.]+)', text, re.IGNORECASE)
        if m:
            arrivee_raw = m.group(1).strip()
            r.arrivee_raw = arrivee_raw
            r.arrivee = parse_arrivee(arrivee_raw)
            # Construire arrivée complète avec positions
            r.arrivee_complete = [
                {'position': i+1, 'numero': num} 
                for i, num in enumerate(r.arrivee)
            ]
        
        # NPO / NP
        m = re.search(r'NPO\s*[:=]\s*(\d+)', text, re.IGNORECASE)
        if m: r.npo = int(m.group(1))
        m = re.search(r'NP\s*[:=]\s*(\d+)', text, re.IGNORECASE)
        if m: r.np = int(m.group(1))
        
        # Disqualifiés / non-partants
        m = re.search(r'DISQUALIFI[EÉ]\s*[:=]\s*(\d+)', text, re.IGNORECASE)
        if m: r.disqualifies = [int(m.group(1))]
        m = re.search(r'TOMB[EÉ]\s*[:=]\s*(\d+)', text, re.IGNORECASE)
        if m: r.non_partants = [int(m.group(1))]
        m = re.search(r'ARR[ÊE]T[EÉ]\s*[:=]\s*(\d+)', text, re.IGNORECASE)
        if m: r.non_partants.extend([int(m.group(1))])
        
        # Gains ORDRE, DESORDRE, BONUS - utiliser le helper
        r.gains_ordre_raw, r.gains_ordre_euros, r.nb_gagnants_ordre = self._parse_gains_section(text, 'ORDRE')
        r.gains_desordre_raw, r.gains_desordre_euros, r.nb_gagnants_desordre = self._parse_gains_section(text, r'D[EÉ]SORDRE')
        r.gains_bonus_raw, r.gains_bonus_euros, r.nb_gagnants_bonus = self._parse_gains_section(text, 'BONUS')
        
        # Masse à partager
        m = re.search(r'MASSE\s*[AÀ]\s*PARTAGER\s*[:\-]\s*([\d\s\n]+)', text, re.IGNORECASE)
        if m:
            raw_gains = m.group(1).strip()
            r.masse_partager_raw = raw_gains
            r.masse_partager_euros = parse_gains(raw_gains)[1]
        
        # Rapports (pour QUARTE/TIERCE)
        r.rapport_gagnant_raw, r.rapport_gagnant_euros, _ = self._parse_gains_section(text, 'GAGNANT')
        r.rapport_place_a_raw, r.rapport_place_a_euros, _ = self._parse_gains_section(text, r'PLACE\s*A')
        r.rapport_place_b_raw, r.rapport_place_b_euros, _ = self._parse_gains_section(text, r'PLACE\s*B')
        
        # MAP (masse des paris)
        m = re.search(r'MAP\s+\w+\s*[:\-]\s*([\d\s\n]+)', text, re.IGNORECASE)
        if m:
            raw_gains = m.group(1).strip()
            r.map_paris_raw = raw_gains
            r.map_paris_euros = parse_gains(raw_gains)[1]
        
        # Tierce V. (info séparée, ne modifie pas l'arrivée)
        m = re.search(r'TIERCE\s+V\.?\s*[:：]?\s*([^\n]+)', text, re.IGNORECASE)
        if m:
            r.tierce_v_raw = m.group(0).strip()
            r.tierce_v_value = m.group(1).strip()
        
        return r
    
    def _parse_gains_section(self, text: str, section_name: str) -> Tuple[str, Optional[int], Optional[int]]:
        """
        Parse une section de gains (ORDRE, DESORDRE, BONUS, GAGNANT, PLACE A, PLACE B).
        
        Retourne: (raw_text, amount_euros, nb_gagnants)
        
        Le format typique est:
        ORDRE :
        20 000 
                
        3 612
        
        Ou sur une ligne: ORDRE : 20 000 (3 612 G)
        """
        # Trouver la position de la section
        section_pattern = rf'{section_name}\s*[:\-]'
        m_section = re.search(section_pattern, text, re.IGNORECASE)
        if not m_section:
            return "", None, None
        
        start_pos = m_section.end()
        
        # Trouver la fin de la section (début de la section suivante ou fin de texte)
        # Sections connues qui peuvent suivre
        next_sections = ['ORDRE', r'D[EÉ]SORDRE', 'BONUS', 'GAGNANT', r'PLACE\s*A', r'PLACE\s*B', 
                         r'MAP\s+\w+', r'MASSE\s*[AÀ]\s*PARTAGER', r'NOMBRE\s+GAGNANTS']
        
        end_pos = len(text)
        for next_sec in next_sections:
            # Ignorer la section courante
            if re.search(rf'^{next_sec}$', section_name, re.IGNORECASE):
                continue
            m_next = re.search(rf'\n{next_sec}\s*[:\-]', text[start_pos:], re.IGNORECASE)
            if m_next:
                candidate_end = start_pos + m_next.start()
                if candidate_end < end_pos:
                    end_pos = candidate_end
        
        # Extraire le contenu de la section
        section_text = text[start_pos:end_pos].strip()
        
        # Nettoyer: garder seulement les lignes avec des chiffres
        lines = [l.strip() for l in section_text.split('\n') if l.strip()]
        
        # Filtrer les lignes qui contiennent des chiffres (montants ou nb gagnants)
        numeric_lines = []
        for l in lines:
            # Ligne avec des chiffres et éventuellement espaces/séparateurs
            if re.search(r'\d', l) and not re.search(r'[A-Z]{3,}', l):  # Pas de mots longs
                numeric_lines.append(l)
        
        if not numeric_lines:
            return section_text, None, None
        
        # Première ligne numérique = montant
        amount_raw = numeric_lines[0]
        amount_euros = parse_gains(amount_raw)[1]
        
        # Deuxième ligne numérique = nb gagnants (si présent)
        nb_gagnants = None
        if len(numeric_lines) > 1:
            nb_gagnants = parse_nb_gagnants(numeric_lines[1])
        
        # Vérifier aussi le pattern (nb G) dans le texte original
        m_g = re.search(rf'{section_name}\s*[:\-].*?\(\s*(\d[\d\s\xa0\u202f]*)\s*G\s*\)', text[start_pos:end_pos], re.IGNORECASE | re.DOTALL)
        if m_g:
            nb_gagnants = parse_nb_gagnants(m_g.group(1))
        
        return section_text, amount_euros, nb_gagnants
    
    def validate_arrival_length(self, resultat: Resultat) -> Tuple[bool, Optional[str]]:
        """
        Valide que la longueur de l'arrivée correspond au type de jeu.
        
        Retourne: (is_valid, error_message)
        """
        if not resultat.type_pari:
            return True, None  # Pas de type, on ne peut pas valider
        
        expected = EXPECTED_ARRIVAL_LENGTH.get(resultat.type_pari)
        if expected is None:
            return True, None  # Type inconnu, pas de validation
        
        actual = len(resultat.arrivee)
        if actual == 0:
            return False, f"Arrivée vide pour {resultat.type_pari} (attendu: {expected})"
        
        if actual != expected:
            return False, f"Longueur arrivée incohérente pour {resultat.type_pari}: {actual} numéros (attendu: {expected})"
        
        return True, None


def parse_resultat_document(pdf_path: str) -> ParsedDocument:
    """Convenience function to parse a resultat document."""
    parser = ResultatParser()
    return parser.parse(pdf_path)