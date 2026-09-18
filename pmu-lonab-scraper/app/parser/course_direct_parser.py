import fitz
import re
from typing import List, Optional, Dict, Any
from app.models.parser_models import ParsedECDDocument, ECDDocument, CourseDirect, CourseDirectArrival, CourseDirectBet
from app.parser.normalizer import (
    parse_date_fr, parse_arrivee, generate_course_id, parse_gains
)

class ECDParser:
    """Parser pour les documents 'Espace Course En Direct' LONAB."""
    
    # Types de paris connus dans les ECD
    BET_TYPES = [
        'GAGNANT',
        'PLACE',
        'JUM GAGNANT',
        'JUM PLACE',
        'JUMELE PLACE',
        'JUM ORDRE',
        'TRIO',
    ]
    
    # Ordinals pour identifier les courses
    ORDINALS = [
        '1ère', '1ere', '1er', '1ière',
        '2ième', '2ieme', '2nd', '2nde',
        '3ième', '3ieme', '3ème',
        '4ième', '4ieme', '4ème',
        '5ième', '5ieme', '5ème',
        '6ième', '6ieme', '6ème',
        '7ième', '7ieme', '7ème',
        '8ième', '8ieme', '8ème',
        '9ième', '9ieme', '9ème',
    ]
    
    def parse(self, pdf_path: str) -> ParsedECDDocument:
        filename = pdf_path.split('\\')[-1].split('/')[-1]
        doc = fitz.open(pdf_path)
        
        parsed = ParsedECDDocument(
            filename=filename,
            doc_type='COURSE_EN_DIRECT',
            date_publication='',
            pages=len(doc)
        )
        
        # Concaténer tout le texte pour analyse globale
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        
        # Extraire les métadonnées du document
        ecd_doc = self._parse_document_metadata(full_text, filename, len(doc))
        parsed.ecd_document = ecd_doc
        parsed.date_publication = ecd_doc.date
        
        # Parser chaque page pour extraire les courses
        courses = self._parse_all_pages(doc, ecd_doc.document_id)
        parsed.courses = courses
        ecd_doc.nombre_courses_detectees = len(courses)
        
        doc.close()
        
        # Post-traitement
        self._finalize(parsed)
        
        return parsed
    
    def _parse_document_metadata(self, text: str, filename: str, pages: int) -> ECDDocument:
        """Extrait les métadonnées globales du document ECD."""
        # Document ID depuis le nom de fichier
        doc_id = filename.replace('.pdf', '')
        
        # Date
        date = parse_date_fr(text) or ""
        
        # Réunion
        reunion = ""
        m = re.search(r'REUNION\s*[-–]\s*(\d+)', text, re.IGNORECASE)
        if m:
            reunion = m.group(1)
        else:
            m = re.search(r'R(\d+)', filename, re.IGNORECASE)
            if m:
                reunion = m.group(1)
        
        # Hippodrome
        hippodrome = ""
        m = re.search(r'\(\s*([A-Z][A-Z\s]+?)\s*\)', text)
        if m:
            hippodrome = m.group(1).strip()
        
        return ECDDocument(
            document_id=doc_id,
            filename=filename,
            date=date,
            reunion=reunion,
            hippodrome=hippodrome,
            pages=pages,
            raw_text=text
        )
    
    def _parse_all_pages(self, doc: fitz.Document, document_id: str) -> List[CourseDirect]:
        """Parse toutes les pages pour extraire les courses."""
        all_courses = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            blocks = page.get_text("blocks")
            
            # Extraire les courses de cette page
            page_courses = self._parse_page(text, blocks, document_id, page_num + 1)
            all_courses.extend(page_courses)
        
        return all_courses
    
    def _parse_page(self, text: str, blocks: List, document_id: str, page_num: int) -> List[CourseDirect]:
        """Parse une page pour extraire les courses."""
        courses = []
        
        # Trouver les positions des ordinaux (1ère, 2ième, etc.) qui délimitent les courses
        course_starts = self._find_course_starts(text)
        
        for i, (start_pos, ordinal_text) in enumerate(course_starts):
            # Déterminer la fin de cette course (début de la suivante ou fin du texte)
            end_pos = course_starts[i + 1][0] if i + 1 < len(course_starts) else len(text)
            
            course_text = text[start_pos:end_pos]
            
            # Extraire le numéro de course
            course_num = self._extract_course_number(ordinal_text)
            
            # Parser la course
            course = self._parse_course_text(course_text, document_id, course_num, page_num, start_pos)
            if course:
                courses.append(course)
        
        return courses
    
    def _find_course_starts(self, text: str) -> List[tuple]:
        """Trouve les positions de début de chaque course (ordinaux)."""
        starts = []
        for ordinal in self.ORDINALS:
            # Chercher l'ordinal comme mot complet
            pattern = r'\b' + re.escape(ordinal) + r'\b'
            for m in re.finditer(pattern, text, re.IGNORECASE):
                starts.append((m.start(), m.group()))
        
        # Trier par position
        starts.sort(key=lambda x: x[0])
        return starts
    
    def _extract_course_number(self, ordinal_text: str) -> int:
        """Extrait le numéro de course depuis l'ordinal."""
        ordinal_map = {
            '1ère': 1, '1ere': 1, '1er': 1, '1ière': 1,
            '2ième': 2, '2ieme': 2, '2nd': 2, '2nde': 2,
            '3ième': 3, '3ieme': 3, '3ème': 3,
            '4ième': 4, '4ieme': 4, '4ème': 4,
            '5ième': 5, '5ieme': 5, '5ème': 5,
            '6ième': 6, '6ieme': 6, '6ème': 6,
            '7ième': 7, '7ieme': 7, '7ème': 7,
            '8ième': 8, '8ieme': 8, '8ème': 8,
            '9ième': 9, '9ieme': 9, '9ème': 9,
        }
        return ordinal_map.get(ordinal_text.lower(), 0)
    
    def _parse_course_text(self, text: str, document_id: str, course_num: int, page_num: int, y_pos: float) -> Optional[CourseDirect]:
        """Parse le texte d'une course individuelle."""
        if course_num == 0:
            return None
        
        course_id = f"{document_id}_C{course_num}"
        
        # 1. Extraire l'arrivée
        arrival = self._parse_arrival(text)
        
        # 2. Extraire les paris/gains
        bets = self._parse_bets(text)
        
        # 3. Générer course_id stable
        ecd_doc_id = document_id
        stable_course_id = f"{ecd_doc_id}_C{course_num}"
        
        course = CourseDirect(
            course_id=stable_course_id,
            document_id=document_id,
            numero_course=course_num,
            arrivee=arrival,
            paris=bets,
            page_num=page_num,
            y_position=y_pos,
            raw_text=text[:1000]  # Garder un échantillon
        )
        
        return course
    
    def _parse_arrival(self, text: str) -> Optional[CourseDirectArrival]:
        """Extrait l'arrivée et les gains totaux."""
        # Pattern: "Arrivee" ou "Arrivée" suivi de chiffres et gains
        # L'arrivée peut être sur la même ligne ou les lignes suivantes
        
        arrival = CourseDirectArrival()
        
        # Chercher "Arrivee" ou "Arrivée"
        m = re.search(r'(?:ARRIVEE|ARRIV[EÉ]E)\s*[:\n\r]*\s*([\d\s\-\,\.]+)', text, re.IGNORECASE)
        if m:
            arrival.arrivee_raw = m.group(1).strip()
            arrival.positions = parse_arrivee(arrival.arrivee_raw)
        
        # Chercher les gains totaux (après l'arrivée, souvent un gros montant)
        # Pattern: montant suivi de "0\n0\n0\n0" (zéros de padding)
        m = re.search(r'(?:ARRIVEE|ARRIV[EÉ]E).*?(\d[\d\s\u202f]*)\s*\n\s*0\s*\n\s*0\s*\n\s*0\s*\n\s*0', text, re.IGNORECASE | re.DOTALL)
        if m:
            arrival.gains_total_raw = m.group(1).strip()
            arrival.gains_total_euros = parse_gains(arrival.gains_total_raw)[1]
        
        if not arrival.positions and not arrival.gains_total_euros:
            return None
        
        return arrival
    
    def _parse_bets(self, text: str) -> List[CourseDirectBet]:
        """Extrait tous les paris/gains d'une course."""
        bets = []
        
        # Pour chaque type de pari connu, chercher les occurrences
        for bet_type in self.BET_TYPES:
            bet_matches = self._extract_bet_type(text, bet_type)
            bets.extend(bet_matches)
        
        return bets
    
    def _extract_bet_type(self, text: str, bet_type: str) -> List[CourseDirectBet]:
        """Extrait toutes les occurrences d'un type de pari spécifique."""
        bets = []
        
        # Pattern flexible pour trouver le type de pari et ses données
        # Le format typique: "TYPE_PARI\nnuméro\nmontant\nnb\ncombinaison\nmontant\nnb..."
        escaped_type = re.escape(bet_type)
        pattern = rf'{escaped_type}\s*(.*?)(?=(?:{"|".join(map(re.escape, self.BET_TYPES))}|ARRIVEE|ARRIV[EÉ]E|ESPACE COURSE|FOLIO|RECAPITULATIF|$))'
        
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not match:
            return bets
        
        bet_section = match.group(1)
        
        # Parser la section de pari
        # Format typique par lignes:
        # numéro_cheval
        # montant_gain
        # nb_paris
        # (répété pour chaque combinaison)
        
        lines = [l.strip() for l in bet_section.split('\n') if l.strip()]
        
        i = 0
        while i < len(lines):
            # Essayer de parser: numéro, montant, nb, puis combinaison
            if i + 2 < len(lines):
                num_text = lines[i]
                montant_text = lines[i + 1]
                nb_text = lines[i + 2]
                
                # Vérifier que num_text est un numéro de cheval (1-20)
                if num_text.isdigit() and 1 <= int(num_text) <= 20:
                    cheval_num = int(num_text)
                    
                    # Montant
                    montant_raw = montant_text
                    _, montant_euros = parse_gains(montant_raw)
                    
                    # Nombre de paris
                    nb_paris = None
                    try:
                        nb_paris = int(nb_text)
                    except:
                        pass
                    
                    # Combinaison (peut être sur la ligne suivante ou la même)
                    combinaison_raw = ""
                    if i + 3 < len(lines):
                        next_line = lines[i + 3]
                        # Si la ligne contient des tirets, c'est une combinaison
                        if '-' in next_line or '–' in next_line:
                            combinaison_raw = next_line
                            i += 4
                        else:
                            i += 3
                    else:
                        i += 3
                    
                    # Normaliser la combinaison
                    combinaison_norm = []
                    if combinaison_raw:
                        nums = re.findall(r'\d+', combinaison_raw)
                        combinaison_norm = [int(n) for n in nums]
                    
                    bet = CourseDirectBet(
                        type_pari=bet_type,
                        combinaison_raw=combinaison_raw,
                        combinaison_normalized=combinaison_norm,
                        montant_raw=montant_raw,
                        montant_euros=montant_euros,
                        nb_paris=nb_paris,
                        position=None  # Sera déduit du contexte si possible
                    )
                    bets.append(bet)
                else:
                    i += 1
            else:
                i += 1
        
        return bets
    
    def _finalize(self, parsed: ParsedECDDocument):
        """Finalise le parsing."""
        # Associer les positions (1ère, 2ième...) aux paris JUM GAGNANT/PLACE
        for course in parsed.courses:
            # Trouver les paris avec position
            for bet in course.paris:
                # La position peut être déduite de l'ordinal de la course
                # ou du contexte dans le texte
                pass
        
        # Dédupliquer les courses par numero_course
        seen = set()
        unique_courses = []
        for c in parsed.courses:
            key = (c.document_id, c.numero_course)
            if key not in seen:
                seen.add(key)
                unique_courses.append(c)
        parsed.courses = unique_courses