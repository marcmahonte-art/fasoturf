import fitz
import re
from typing import List, Optional, Dict, Any
from app.models.parser_models import Course, Partant, MediaSelection, Classement, Commentaire, ParsedDocument
from app.parser.normalizer import (
    normalize_horse_name, normalize_driver_name, normalize_performance,
    parse_distance, parse_chrono, parse_cote, parse_sexe_age,
    parse_gains, parse_montant, parse_date_fr, generate_course_id,
    parse_media_selections, parse_classements, parse_arrivee, parse_nb_gagnants
)

class JournalParser:
    """Parser pour les journaux hippiques LONAB (2 pages)."""
    
    def parse(self, pdf_path: str) -> ParsedDocument:
        filename = pdf_path.split('\\')[-1].split('/')[-1]
        doc = fitz.open(pdf_path)
        
        parsed = ParsedDocument(
            filename=filename,
            doc_type='JOURNAL',
            date_publication='',
            pages=len(doc)
        )
        
        # Page 1: Infos course + commentaires + résultats précédents + pronostics médias
        if len(doc) >= 1:
            page1_text = doc[0].get_text()
            page1_blocks = doc[0].get_text("blocks")
            self._parse_page1(parsed, page1_text, page1_blocks)
        
        # Page 2: Tableau des partants
        if len(doc) >= 2:
            page2 = doc[1]
            self._parse_page2(parsed, page2)
        
        doc.close()
        
        # Post-traitement
        self._finalize(parsed)
        
        return parsed
    
    def _parse_page1(self, parsed: ParsedDocument, text: str, blocks: List):
        """Parse la page 1 du journal."""
        # Date de publication
        parsed.date_publication = parse_date_fr(text) or ""
        
        # Infos course
        course = self._extract_course_info(text, parsed.filename)
        parsed.courses.append(course)
        
        # Commentaires des chevaux
        commentaires = self._extract_commentaires(text, course.course_id)
        parsed.commentaires.extend(commentaires)
        
        # Pronostics médias
        media_sels = parse_media_selections(text)
        for ms in media_sels:
            ms['course_id'] = course.course_id
            parsed.media_selections.append(MediaSelection(**ms))
        
        # Classements
        classements_data = parse_classements(text)
        if classements_data:
            cl = Classement(course_id=course.course_id, **classements_data)
            parsed.classements.append(cl)
        
        # Heures
        self._extract_heures(text, course)
        
        # Stocker le texte brut
        course.raw_text = text
    
    def _extract_course_info(self, text: str, filename: str) -> Course:
        """Extrait les infos de la course depuis le texte."""
        course = Course(
            course_id="",
            date=parse_date_fr(text) or "",
            raw_text=text
        )
        
        # Course ID depuis le nom de fichier
        m = re.search(r'JH_PMUB_DU_(\d{2}[-/]\d{2}[-/]\d{4})', filename)
        if m:
            date_str = m.group(1).replace('/', '-')
            # Reconstruire en YYYY-MM-DD
            parts = date_str.split('-')
            if len(parts) == 3:
                course.date = f"{parts[2]}-{parts[1]}-{parts[0]}"
            course.course_id = f"JH_{date_str}"
        
        # Hippodrome, titre, discipline, etc.
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            upper = line.upper()
            
            # Hippodrome et Prix
            if 'PRIX' in upper and ' - ' in line:
                parts = line.split(' - ')
                if len(parts) >= 2:
                    course.hippodrome = parts[0].strip()
                    course.titre = line
                    # Discipline
                    if 'ATTELE' in upper:
                        course.discipline = 'ATTELE'
                    elif 'PLAT' in upper:
                        course.discipline = 'PLAT'
                    elif 'OBSTACLE' in upper or 'HAIES' in upper or 'STEEPLE' in upper:
                        course.discipline = 'OBSTACLE'
            
            # Partants
            m = re.search(r'(\d+)\s+CONCURRENTS', upper)
            if m:
                course.partants_declares = int(m.group(1))
            
            # Numéro de course
            m = re.search(r'(\d+)(?:ME|ÈME|EME)\s+COURSE', upper)
            if m:
                course.course_num = int(m.group(1))
            
            # Distance
            m = re.search(r'(\d[\d\s]*)\s*M[ÈE]TRES', upper)
            if m:
                course.distance_raw = m.group(1).strip()
                course.distance_m = int(course.distance_raw.replace(' ', ''))
            
            # Montant
            m = re.search(r'([\d\s]+)\s*EUROS', upper)
            if m:
                course.montant_raw = m.group(1).strip()
                course.montant_euros = int(course.montant_raw.replace(' ', ''))
            
            # Type de course
            if 'AUTOSTART' in upper:
                course.type_course = 'AUTOSTART'
            elif 'DEPART VOLTE' in upper:
                course.type_course = 'DEPART_VOLTE'
            elif 'HANDICAP' in upper:
                course.type_course = 'HANDICAP'
        
        # Générer course_id complet si possible
        if course.date and course.hippodrome and course.course_num:
            course.course_id = generate_course_id(course.date, course.hippodrome, course.course_num)
        
        return course
    
    def _extract_heures(self, text: str, course: Course):
        """Extrait les heures d'arrêt des jeux et de départ."""
        m = re.search(r'ARR[ÊE]T DES JEUX EST FIX[EÉ]\s*[:：]\s*(\d{1,2}h\s*\d{2}mn)', text, re.IGNORECASE)
        if m:
            course.heure_arret_jeux = m.group(1)
        
        m = re.search(r'D[EÉ]PART DE LA COURSE\s*[:：]\s*(\d{1,2}h\s*\d{2}\s*mn)', text, re.IGNORECASE)
        if m:
            course.heure_depart = m.group(1)
    
    def _extract_commentaires(self, text: str, course_id: str) -> List[Commentaire]:
        """Extrait les commentaires sur chaque cheval."""
        commentaires = []
        
        # Pattern: "1 - NOM : commentaire" ou "1 - NOM : commentaire"
        # Les commentaires sont généralement après la liste des partants
        lines = text.split('\n')
        
        in_commentaires = False
        current_num = None
        current_text = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            
            # Détecter début commentaires (après la liste des partants)
            if re.match(r'^\d+\s*[-–]\s*[A-Z]', stripped):
                # Nouveau cheval
                if current_num is not None and current_text:
                    commentaires.append(Commentaire(
                        course_id=course_id,
                        numero_cheval=current_num,
                        texte=' '.join(current_text).strip()
                    ))
                
                # Extraire numéro
                m = re.match(r'^(\d+)\s*[-–]', stripped)
                if m:
                    current_num = int(m.group(1))
                    # Le reste du texte après le tiret
                    rest = stripped[m.end():].strip()
                    if rest:
                        current_text = [rest]
                    else:
                        current_text = []
                else:
                    current_num = None
                    current_text = []
            elif current_num is not None and stripped:
                # Continuation du commentaire
                current_text.append(stripped)
        
        # Dernier commentaire
        if current_num is not None and current_text:
            commentaires.append(Commentaire(
                course_id=course_id,
                numero_cheval=current_num,
                texte=' '.join(current_text).strip()
            ))
        
        return commentaires
    
    def _parse_page2(self, parsed: ParsedDocument, page):
        """Parse la page 2 (tableau des partants) en utilisant les coordonnées."""
        blocks = page.get_text("blocks")
        
        # Organiser par lignes (y) et colonnes (x)
        rows = {}
        
        for b in blocks:
            bbox = b[:4]
            txt = b[4].strip()
            if not txt or len(txt) > 200:
                continue
            
            x_center = (bbox[0] + bbox[2]) / 2
            y_center = (bbox[1] + bbox[3]) / 2
            
            # Grouper par ligne (arrondi à 15 pixels pour capturer les colonnes décalées)
            y_key = round(y_center / 15) * 15
            if y_key not in rows:
                rows[y_key] = {}
            rows[y_key][round(x_center / 10) * 10] = txt
        
        # Trier les lignes par y
        sorted_rows = sorted(rows.items())
        
        current_course = parsed.courses[0] if parsed.courses else None
        if not current_course:
            return
        
        course_id = current_course.course_id
        current_num = None
        partant_data = {}
        
        for y, cols in sorted_rows:
            # Chercher le numéro (colonne ~25-30)
            num_text = None
            for cx in [20, 25, 30, 35]:
                if cx in cols:
                    val = cols[cx].strip()
                    if val.isdigit():
                        n = int(val)
                        if 1 <= n <= 20:
                            num_text = val
                            break
            
            if num_text:
                # Sauver le partant précédent
                if current_num is not None and partant_data:
                    partant = self._build_partant(course_id, current_num, partant_data)
                    if partant:
                        parsed.partants.append(partant)
                
                current_num = int(num_text)
                partant_data = {cx: cols[cx] for cx in cols}
            elif current_num is not None:
                # Ajouter aux données du partant courant
                for cx, val in cols.items():
                    if cx not in partant_data:
                        partant_data[cx] = val
        
        # Dernier partant
        if current_num is not None and partant_data:
            partant = self._build_partant(course_id, current_num, partant_data)
            if partant:
                parsed.partants.append(partant)
        
        current_course.partants_effectifs = len(parsed.partants)
    
    def _build_partant(self, course_id: str, numero: int, cols: Dict[int, str]) -> Optional[Partant]:
        """Construit un objet Partant à partir des colonnes détectées."""
        
        # Trouver le nom du cheval (colonne ~50-70)
        nom_raw = ""
        for cx in [50, 55, 60, 65, 70]:
            if cx in cols and len(cols[cx]) > 1:
                val = cols[cx].strip()
                # Vérifier que ce n'est pas un chiffre ou une abréviation courte
                if not val.isdigit() and len(val) > 2 and not re.match(r'^[HFM]\.?\d+$', val):
                    nom_raw = val
                    break
        
        if not nom_raw:
            return None
        
        nom_norm = normalize_horse_name(nom_raw)
        
        # Sexe/Âge (colonne ~240-260)
        sexe_raw = ""
        age_raw = ""
        for cx in [240, 245, 250, 255, 260]:
            if cx in cols:
                val = cols[cx].strip()
                s, a = parse_sexe_age(val)
                if s:
                    sexe_raw = val
                    age_raw = a
                    break
        
        # Driver (colonne ~100-120)
        driver_raw = ""
        for cx in [100, 105, 110, 115, 120]:
            if cx in cols:
                driver_raw = cols[cx].strip()
                break
        driver_norm = normalize_driver_name(driver_raw)
        
        # Entraineur (colonne ~140-170)
        entraineur_raw = ""
        for cx in [140, 145, 150, 155, 160, 165, 170]:
            if cx in cols:
                entraineur_raw = cols[cx].strip()
                break
        entraineur_norm = normalize_driver_name(entraineur_raw)
        
        # Propriétaire (colonne ~190-220)
        proprietaire_raw = ""
        for cx in [190, 195, 200, 205, 210, 215, 220]:
            if cx in cols:
                proprietaire_raw = cols[cx].strip()
                break
        proprietaire_norm = normalize_driver_name(proprietaire_raw)
        
        # Distance (colonne ~260-270)
        distance_raw = ""
        distance_m = None
        for cx in [260, 265, 270]:
            if cx in cols:
                val = cols[cx].strip()
                raw, m = parse_distance(val)
                if m:
                    distance_raw = raw
                    distance_m = m
                    break
                elif val and val != distance_raw:
                    distance_raw = val
        
        # Chrono (colonne ~290-300)
        chrono_raw = ""
        chrono_norm = ""
        for cx in [290, 295, 300]:
            if cx in cols:
                val = cols[cx].strip()
                raw, norm = parse_chrono(val)
                if norm:
                    chrono_raw = raw
                    chrono_norm = norm
                    break
                elif val:
                    chrono_raw = val
        
        # Performances (colonne ~310-320)
        performances_raw = ""
        performances_struct = []
        for cx in [310, 315, 320]:
            if cx in cols:
                val = cols[cx].strip()
                raw, struct = normalize_performance(val)
                if struct:
                    performances_raw = raw
                    performances_struct = struct
                    break
                elif val:
                    performances_raw = val
        
        # Gains (colonne ~340-350)
        gains_raw = ""
        gains_euros = None
        for cx in [340, 345, 350]:
            if cx in cols:
                val = cols[cx].strip()
                raw, euros = parse_gains(val)
                if euros is not None:
                    gains_raw = raw
                    gains_euros = euros
                    break
                elif val:
                    gains_raw = val
        
        # Cote (colonne ~380-400) - cotes PMU
        cote_raw = ""
        cote_dec = None
        for cx in [380, 385, 390, 395, 400]:
            if cx in cols:
                val = cols[cx].strip()
                if re.match(r'^\d+/\d+$', val) or re.match(r'^\d+\.?\d*$', val):
                    raw, dec = parse_cote(val)
                    if dec is not None:
                        cote_raw = raw
                        cote_dec = dec
                        break
                    elif val:
                        cote_raw = val
        
        partant = Partant(
            course_id=course_id,
            numero=numero,
            nom_cheval_raw=nom_raw,
            nom_cheval_normalized=nom_norm,
            sexe=sexe_raw,
            age=age_raw,
            driver_raw=driver_raw,
            driver_normalized=driver_norm,
            entraineur_raw=entraineur_raw,
            entraineur_normalized=entraineur_norm,
            proprietaire_raw=proprietaire_raw,
            proprietaire_normalized=proprietaire_norm,
            distance_raw=distance_raw,
            distance_m=distance_m,
            chrono_raw=chrono_raw,
            chrono_normalized=chrono_norm,
            performances_raw=performances_raw,
            performances_structured=performances_struct,
            gains_raw=gains_raw,
            gains_euros=gains_euros,
            cote_raw=cote_raw,
            cote_decimale=cote_dec,
            raw_data=cols
        )
        
        return partant
    
    def _finalize(self, parsed: ParsedDocument):
        """Finalise le parsing: associer commentaires aux partants, etc."""
        # Associer commentaires
        commentaires_by_num = {c.numero_cheval: c.texte for c in parsed.commentaires}
        for partant in parsed.partants:
            if partant.numero in commentaires_by_num:
                partant.commentaire = commentaires_by_num[partant.numero]
        
        # Dédupliquer partants (par numéro)
        seen = set()
        unique_partants = []
        for p in parsed.partants:
            if p.numero not in seen:
                seen.add(p.numero)
                unique_partants.append(p)
        parsed.partants = unique_partants