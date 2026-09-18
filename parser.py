import fitz
import os
import re
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import json

@dataclass
class Course:
    course_id: str
    date: str
    reunion: str
    course_num: int
    hippodrome: str
    discipline: str
    distance: str
    montant: str
    partants: int
    type_course: str
    titre: str

@dataclass
class Partant:
    numero: int
    nom: str
    sexe: str
    age: str
    driver: str
    entraineur: str
    proprietaire: str
    distance: str
    performance: str
    gains: str
    chrono: str
    cote: Optional[str] = None

@dataclass
class JournalHippique:
    filename: str
    date_publication: str
    courses: List[Course] = field(default_factory=list)
    partants: List[Partant] = field(default_factory=list)

@dataclass
class Resultat:
    filename: str
    date: str
    type_pari: str
    arrivee: List[int]
    npo: int
    np: int
    gains_ordre: Optional[str] = None
    gains_desordre: Optional[str] = None
    gains_bonus: Optional[str] = None
    nb_gagnants_ordre: Optional[int] = None
    nb_gagnants_desordre: Optional[int] = None
    nb_gagnants_bonus: Optional[int] = None
    masse_partager: Optional[str] = None

def detect_type(filename: str, text: str) -> str:
    """Détecte si c'est un JOURNAL ou RÉSULTAT"""
    fname = filename.upper()
    if 'JH_PMUB' in fname or 'JOURNAL' in fname:
        return 'JOURNAL'
    if 'RES_' in fname or 'RES41_' in fname or 'RÉSULTAT' in text.upper() or 'ARR :' in text:
        return 'RESULTAT'
    return 'UNKNOWN'

def parse_date_fr(text: str) -> Optional[str]:
    """Extrait une date en français"""
    months = {
        'JANVIER': 1, 'FEVRIER': 2, 'MARS': 3, 'AVRIL': 4, 'MAI': 5, 'JUIN': 6,
        'JUILLET': 7, 'AOUT': 8, 'SEPTEMBRE': 9, 'OCTOBRE': 10, 'NOVEMBRE': 11, 'DECEMBRE': 12
    }
    # Pattern: "DU MARDI 01 JUILLET 2025" or "01/07/2025"
    m = re.search(r'(\d{1,2})\s+(JANVIER|FEVRIER|MARS|AVRIL|MAI|JUIN|JUILLET|AOUT|SEPTEMBRE|OCTOBRE|NOVEMBRE|DECEMBRE)\s+(\d{4})', text, re.IGNORECASE)
    if m:
        return f"{m.group(3)}-{months[m.group(2).upper()]:02d}-{int(m.group(1)):02d}"
    m = re.search(r'(\d{2})/(\d{2})/(\d{4})', text)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return None

def parse_journal_page1(text: str, filename: str) -> Course:
    """Parse la page 1 du journal pour extraire les infos de la course"""
    course = Course(
        course_id="",
        date="",
        reunion="",
        course_num=0,
        hippodrome="",
        discipline="",
        distance="",
        montant="",
        partants=0,
        type_course="",
        titre=""
    )
    
    # Date
    course.date = parse_date_fr(text) or ""
    
    # Titre / Hippodrome / Prix
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if 'PRIX' in line.upper() and ('HIPPODROME' in line.upper() or '-' in line):
            course.titre = line
            # Extract hippodrome
            if ' - ' in line:
                course.hippodrome = line.split(' - ')[0].strip()
    
    # Discipline, partants, course num, distance, montant
    patterns = {
        'discipline': r'(ATTELE|PLAT|OBSTACLE)',
        'partants': r'(\d+)\s+CONCURRENTS',
        'course_num': r'(\d+)(?:me|ère|ème)\s+COURSE',
        'distance': r'(\d+\s+\w+)\s*\)',
        'montant': r'([\d\s]+ EUROS)',
        'type_course': r'(AUTOSTART|DEPART VOLTE|HANDICAP)',
    }
    
    for key, pattern in patterns.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            setattr(course, key, m.group(1).strip())
    
    # Generate course_id from filename
    m = re.search(r'JH_PMUB_DU_(\d{2}[-/]\d{2}[-/]\d{4})', filename)
    if m:
        date_str = m.group(1).replace('/', '-')
        course.course_id = f"JH_{date_str}"
        if not course.reunion:
            course.reunion = "R1"  # Default
    
    return course

def parse_journal_page2(page) -> List[Partant]:
    """Parse la page 2 (tableau des partants) en utilisant les coordonnées"""
    blocks = page.get_text("blocks")
    
    # Organiser les blocs par colonnes (x) et lignes (y)
    rows = {}
    
    for b in blocks:
        bbox = b[:4]
        txt = b[4].strip()
        if not txt or len(txt) > 200:
            continue
        x_center = (bbox[0] + bbox[2]) / 2
        y_center = (bbox[1] + bbox[3]) / 2
        
        # Grouper par ligne (y)
        y_key = round(y_center / 5) * 5
        if y_key not in rows:
            rows[y_key] = {}
        rows[y_key][round(x_center / 10) * 10] = txt
    
    # Trier les lignes par y
    sorted_rows = sorted(rows.items())
    
    partants = []
    current_num = None
    
    for y, cols in sorted_rows:
        # Numéro de partant (colonne ~25)
        num_text = cols.get(30) or cols.get(20) or cols.get(40)
        if num_text and num_text.isdigit():
            try:
                num = int(num_text)
                if 1 <= num <= 20:
                    current_num = num
            except:
                pass
        
        if current_num:
            # Construire le partant à partir des colonnes
            # Colonnes typiques observées:
            # x~25: Numéro
            # x~37-40: Nom cheval
            # x~91: Driver
            # x~135: Entraineur
            # x~187: Propriétaire
            # x~247: Sexe/Âge
            # x~263: Distance
            # x~287: Chrono
            # x~312: Performance
            # x~338: Gains
            
            nom = None
            for cx in [30, 35, 40, 45]:
                if cx in cols and len(cols[cx]) > 2 and not cols[cx].isdigit():
                    nom = cols[cx]
                    break
            
            if nom and len(nom) > 1:
                partant = Partant(
                    numero=current_num,
                    nom=nom,
                    sexe=cols.get(250, '') or cols.get(240, ''),
                    age=cols.get(260, ''),
                    driver=cols.get(90, '') or cols.get(100, ''),
                    entraineur=cols.get(130, '') or cols.get(140, ''),
                    proprietaire=cols.get(180, '') or cols.get(190, ''),
                    distance=cols.get(260, '') or cols.get(270, ''),
                    performance=cols.get(310, '') or cols.get(320, ''),
                    gains=cols.get(340, '') or cols.get(330, ''),
                    chrono=cols.get(290, '') or cols.get(280, ''),
                )
                partants.append(partant)
    
    return partants

def parse_resultat(text: str, filename: str) -> Resultat:
    """Parse un PDF de résultat"""
    r = Resultat(
        filename=filename,
        date="",
        type_pari="",
        arrivee=[],
        npo=0,
        np=0
    )
    
    # Date
    r.date = parse_date_fr(text) or ""
    
    # Type de pari
    if 'QUARTE' in text.upper():
        r.type_pari = 'QUARTE'
    elif '4+1' in text or '4 1' in text:
        r.type_pari = '4+1'
    elif 'TIERCE' in text.upper():
        r.type_pari = 'TIERCE'
    
    # Arrivée: "ARR : 9 - 2 - 16 - 12 - 1" or "ARR :1-2-8-6"
    m = re.search(r'ARR\s*[:=]\s*([\d\s\-\,]+)', text, re.IGNORECASE)
    if m:
        nums = re.findall(r'\d+', m.group(1))
        r.arrivee = [int(n) for n in nums]
    
    # NPO / NP
    m = re.search(r'NPO\s*[:=]\s*(\d+)', text, re.IGNORECASE)
    if m: r.npo = int(m.group(1))
    m = re.search(r'NP\s*[:=]\s*(\d+)', text, re.IGNORECASE)
    if m: r.np = int(m.group(1))
    
    # Gains
    patterns = {
        'gains_ordre': r'ORDRE\s*[:\-]\s*([\d\s]+)',
        'gains_desordre': r'D[EÉ]SORDRE\s*[:\-]\s*([\d\s]+)',
        'gains_bonus': r'BONUS\s*[:\-]\s*([\d\s]+)',
        'nb_gagnants_ordre': r'ORDRE\s*[:\-]\s*[\d\s]+\s*\((\d+)\s*G\)',
        'nb_gagnants_desordre': r'D[EÉ]SORDRE\s*[:\-]\s*[\d\s]+\s*\((\d+)\s*G\)',
        'masse_partager': r'MASSE\s*[AÀ]\s*PARTAGER\s*[:\-]\s*([\d\s]+)',
    }
    
    for key, pattern in patterns.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).replace(' ', '').replace('\xa0', '')
            if 'nb_gagnants' in key:
                setattr(r, key, int(val))
            else:
                setattr(r, key, val)
    
    return r

def parse_pdf(path: str) -> dict:
    """Point d'entrée principal pour parser un PDF"""
    filename = os.path.basename(path)
    doc = fitz.open(path)
    
    # Lire la première page pour détecter le type
    first_page_text = doc[0].get_text()
    doc_type = detect_type(filename, first_page_text)
    
    result = {
        'filename': filename,
        'type': doc_type,
        'pages': len(doc),
        'data': None
    }
    
    if doc_type == 'JOURNAL':
        journal = JournalHippique(filename=filename, date_publication=parse_date_fr(first_page_text) or "")
        
        # Page 1: infos course
        if len(doc) >= 1:
            course = parse_journal_page1(first_page_text, filename)
            journal.courses.append(course)
        
        # Page 2: partants
        if len(doc) >= 2:
            partants = parse_journal_page2(doc[1])
            journal.partants = partants
        
        result['data'] = {
            'date_publication': journal.date_publication,
            'courses': [c.__dict__ for c in journal.courses],
            'partants': [p.__dict__ for p in journal.partants]
        }
    
    elif doc_type == 'RESULTAT':
        # Concatener tout le texte (généralement 1 page)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        
        resultat = parse_resultat(full_text, filename)
        result['data'] = resultat.__dict__
    
    doc.close()
    return result

if __name__ == '__main__':
    folder = r'C:\Users\Lenovo\Desktop\PMU\echantillon'
    output_dir = r'C:\Users\Lenovo\Desktop\PMU\data\processed'
    os.makedirs(output_dir, exist_ok=True)
    
    all_results = []
    
    for f in sorted(os.listdir(folder)):
        if f.endswith('.pdf'):
            path = os.path.join(folder, f)
            print(f"Parsing {f}...")
            try:
                result = parse_pdf(path)
                all_results.append(result)
                
                # Save individual result
                out_file = os.path.join(output_dir, f.replace('.pdf', '.json'))
                with open(out_file, 'w', encoding='utf-8') as out:
                    json.dump(result, out, ensure_ascii=False, indent=2)
                print(f"  -> Sauve: {out_file}")
            except Exception as e:
                print(f"  ERREUR: {e}")
    
    # Save combined
    with open(os.path.join(output_dir, 'all_parsed.json'), 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\nTerminé. {len(all_results)} fichiers parsés.")