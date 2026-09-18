import re
from typing import Optional, List, Tuple

def normalize_horse_name(name: str) -> str:
    """Normalise un nom de cheval en conservant les accents."""
    if not name:
        return ""
    
    # Remplacer les caractères spéciaux courants
    name = name.replace('\xa0', ' ')  # espace insécable
    name = name.replace('\u2019', "'")  # apostrophe courbe
    name = name.replace('\u2018', "'")
    name = name.replace('\u201c', '"')
    name = name.replace('\u201d', '"')
    
    # Espaces multiples -> un seul
    name = re.sub(r'\s+', ' ', name)
    
    # Supprimer espaces début/fin
    name = name.strip()
    
    return name

def normalize_driver_name(name: str) -> str:
    """Normalise un nom de driver/jockey."""
    if not name:
        return ""
    
    name = name.replace('\xa0', ' ')
    name = re.sub(r'\s+', ' ', name)
    name = name.strip()
    
    # Format: "P.J. CORDEAU" -> "P.J. CORDEAU" (conserver)
    # Format: "Théo RADOUX" -> "THÉO RADOUX" (majuscules pour cohérence)
    # On garde la casse originale pour les initiaux
    return name

def normalize_performance(perf: str) -> Tuple[str, List]:
    """
    Normalise une chaîne de performance.
    Exemple: "D.6.2.0.0" -> ("D.6.2.0.0", ["D", 6, 2, 0, 0])
    """
    raw = perf.strip() if perf else ""
    if not raw:
        return "", []
    
    structured = []
    parts = raw.split('.')
    for p in parts:
        p = p.strip()
        if p.isdigit():
            structured.append(int(p))
        else:
            # Peut contenir lettres (D, A, T, etc.)
            structured.append(p.upper())
    
    return raw, structured

def parse_distance(dist: str) -> Tuple[str, Optional[int]]:
    """Extrait la distance en mètres."""
    raw = dist.strip() if dist else ""
    if not raw:
        return "", None
    
    # Pattern: "2 800.M" or "2800 M" or "2 800 M"
    m = re.search(r'(\d[\d\s]*)\s*[Mm]', raw.replace(' ', ''))
    if m:
        meters = int(m.group(1).replace(' ', ''))
        return raw, meters
    
    return raw, None

def parse_chrono(chrono: str) -> Tuple[str, Optional[str]]:
    """Normalise un chrono: '1.11.60' -> ('1.11.60', '1:11.60')"""
    raw = chrono.strip() if chrono else ""
    if not raw:
        return "", None
    
    # Format: 1.11.60 -> 1:11.60 (minutes:secondes.centièmes)
    parts = raw.split('.')
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        normalized = f"{parts[0]}:{parts[1]}.{parts[2]}"
        return raw, normalized
    
    return raw, raw

def parse_cote(cote: str) -> Tuple[str, Optional[float]]:
    """Normalise une cote: '7/1' -> ('7/1', 7.0)"""
    raw = cote.strip() if cote else ""
    if not raw:
        return "", None
    
    # Format: "7/1" ou "11/1" ou "51/1"
    m = re.match(r'^(\d+)\s*/\s*(\d+)$', raw)
    if m:
        num = int(m.group(1))
        den = int(m.group(2))
        if den != 0:
            return raw, round(num / den, 2)
    
    # Format décimal: "3.50"
    try:
        return raw, float(raw.replace(',', '.'))
    except:
        pass
    
    return raw, None

def parse_sexe_age(sexe_age: str) -> Tuple[str, str]:
    """Parse 'H.9' -> ('H', '9') ou 'F.8' -> ('F', '8')"""
    raw = sexe_age.strip() if sexe_age else ""
    if not raw:
        return "", ""
    
    # Format: H.9, F.8, M.6, etc.
    m = re.match(r'^([HFM])\.?(\d+)$', raw.replace(' ', ''), re.IGNORECASE)
    if m:
        return m.group(1).upper(), m.group(2)
    
    return raw, ""

def parse_gains(gains: str) -> Tuple[str, Optional[int]]:
    """Parse gains: '188 295' -> ('188 295', 188295)"""
    raw = gains.strip() if gains else ""
    if not raw:
        return "", None
    
    # Enlever espaces, virgules, espaces insécables, espaces fines (U+202F)
    cleaned = raw.replace(' ', '').replace(',', '').replace('\xa0', '').replace('\u202f', '')
    try:
        return raw, int(cleaned)
    except:
        return raw, None


def clean_montant(text: str) -> str:
    """Nettoie un montant pour le parsing (espaces, U+202F, etc.)."""
    if not text:
        return ""
    return text.replace(' ', '').replace(',', '').replace('\xa0', '').replace('\u202f', '')

def parse_nb_gagnants(text: str) -> Optional[int]:
    """Parse '11 G' -> 11, or '3 612' -> 3612, or '120' -> 120"""
    if not text:
        return None
    # Pattern with G
    m = re.search(r'(\d+)\s*G', text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # Pattern: plain number (possibly with spaces)
    cleaned = text.replace(' ', '').replace('\xa0', '').replace('\u202f', '')
    if cleaned.isdigit():
        return int(cleaned)
    return None

def parse_montant(montant: str) -> Tuple[str, Optional[int]]:
    """Parse '37 000 EUROS' -> ('37 000 EUROS', 37000)"""
    raw = montant.strip() if montant else ""
    if not raw:
        return "", None
    
    m = re.search(r'([\d\s]+)\s*EUROS', raw, re.IGNORECASE)
    if m:
        val = int(m.group(1).replace(' ', ''))
        return raw, val
    return raw, None

def parse_date_fr(text: str) -> Optional[str]:
    """Extrait une date en français: 'MARDI 01 JUILLET 2025' -> '2025-07-01'"""
    months = {
        'JANVIER': 1, 'FEVRIER': 2, 'MARS': 3, 'AVRIL': 4, 'MAI': 5, 'JUIN': 6,
        'JUILLET': 7, 'AOUT': 8, 'SEPTEMBRE': 9, 'OCTOBRE': 10, 'NOVEMBRE': 11, 'DECEMBRE': 12
    }
    
    # Pattern: "DU MARDI 01 JUILLET 2025"
    m = re.search(r'(\d{1,2})\s+(JANVIER|FEVRIER|MARS|AVRIL|MAI|JUIN|JUILLET|AOUT|SEPTEMBRE|OCTOBRE|NOVEMBRE|DECEMBRE)\s+(\d{4})', text, re.IGNORECASE)
    if m:
        return f"{m.group(3)}-{months[m.group(2).upper()]:02d}-{int(m.group(1)):02d}"
    
    # Pattern: "01/07/2025"
    m = re.search(r'(\d{2})/(\d{2})/(\d{4})', text)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    
    return None

def generate_course_id(date_str: str, hippodrome: str, course_num: int) -> str:
    """Génère un ID de course stable et déterministe."""
    # Format: 2025-07-01_VICHY_C1
    safe_hippo = re.sub(r'[^A-Z0-9]', '', hippodrome.upper())
    return f"{date_str}_{safe_hippo}_C{course_num}"

def parse_arrivee(arrivee_text: str) -> List[int]:
    """Parse 'ARR : 9 - 2 - 16 - 12 - 1' -> [9, 2, 16, 12, 1]"""
    if not arrivee_text:
        return []
    nums = re.findall(r'\d+', arrivee_text)
    return [int(n) for n in nums]

def parse_media_selections(text: str) -> List[dict]:
    """Extrait les sélections des médias du journal."""
    selections = []
    
    # Patterns pour les médias connus
    media_patterns = [
        (r'LE PARISIEN\s+([\d\s\-\,\.]+)', 'LE PARISIEN'),
        (r'EQUIDIA\s+([\d\s\-\,\.]+)', 'EQUIDIA'),
        (r'ZONE-TURF\.fr\s+([\d\s\-\,\.]+)', 'ZONE-TURF.fr'),
        (r'CENTRE-FRANCE\s+([\d\s\-\,\.]+)', 'CENTRE-FRANCE'),
        (r'L\'ALSACE\s+([\d\s\-\,\.]+)', "L'ALSACE"),
        (r'TURFOMANIA\s+([\d\s\-\,\.]+)', 'TURFOMANIA'),
        (r'TURF-FR\.COM\s+([\d\s\-\,\.]+)', 'TURF-FR.COM'),
        (r'SUD OUEST\s+([\d\s\-\,\.]+)', 'SUD OUEST'),
    ]
    
    for pattern, source in media_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            nums = re.findall(r'\d+', m.group(1))
            selection = [int(n) for n in nums if 1 <= int(n) <= 20]
            if selection:
                selections.append({
                    'source': source,
                    'selection': selection
                })
    
    return selections

def parse_classements(text: str) -> dict:
    """Extrait les classements: FORME, CLASSE, PROGRES, REGULARITE"""
    classements = {}
    
    patterns = {
        'forme': r'FORME\s*[:：]\s*([\d\s\-\,\.]+)',
        'classe': r'CLASSE\s*[:：]\s*([\d\s\-\,\.]+)',
        'progres': r'PROGRES\s*[:：]\s*([\d\s\-\,\.]+)',
        'regularite': r'REGULARITE\s*[:：]\s*([\d\s\-\,\.]+)',
    }
    
    for key, pattern in patterns.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            nums = re.findall(r'\d+', m.group(1))
            classements[key] = [int(n) for n in nums if 1 <= int(n) <= 20]
    
    return classements