from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

@dataclass
class Course:
    """Représente une course hippique."""
    course_id: str
    date: str
    reunion: str = ""
    course_num: int = 0
    hippodrome: str = ""
    discipline: str = ""
    distance_raw: str = ""
    distance_m: Optional[int] = None
    montant_raw: str = ""
    montant_euros: Optional[int] = None
    partants_declares: int = 0
    partants_effectifs: int = 0
    type_course: str = ""
    titre: str = ""
    heure_depart: str = ""
    heure_arret_jeux: str = ""
    raw_text: str = ""
    
    def to_dict(self) -> dict:
        return {
            'course_id': self.course_id,
            'date': self.date,
            'reunion': self.reunion,
            'course_num': self.course_num,
            'hippodrome': self.hippodrome,
            'discipline': self.discipline,
            'distance': {
                'raw': self.distance_raw,
                'meters': self.distance_m
            },
            'montant': {
                'raw': self.montant_raw,
                'euros': self.montant_euros
            },
            'partants_declares': self.partants_declares,
            'partants_effectifs': self.partants_effectifs,
            'type_course': self.type_course,
            'titre': self.titre,
            'heure_depart': self.heure_depart,
            'heure_arret_jeux': self.heure_arret_jeux
        }

@dataclass
class Partant:
    """Représente un partant (cheval) dans une course."""
    course_id: str
    numero: int
    nom_cheval_raw: str = ""
    nom_cheval_normalized: str = ""
    sexe: str = ""
    age: str = ""
    poids: str = ""
    corde: str = ""
    distance_raw: str = ""
    distance_m: Optional[int] = None
    chrono_raw: str = ""
    chrono_normalized: str = ""
    performances_raw: str = ""
    performances_structured: List = field(default_factory=list)
    gains_raw: str = ""
    gains_euros: Optional[int] = None
    driver_raw: str = ""
    driver_normalized: str = ""
    entraineur_raw: str = ""
    entraineur_normalized: str = ""
    proprietaire_raw: str = ""
    proprietaire_normalized: str = ""
    cote_raw: str = ""
    cote_decimale: Optional[float] = None
    commentaire: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            'course_id': self.course_id,
            'numero': self.numero,
            'nom_cheval': {
                'raw': self.nom_cheval_raw,
                'normalized': self.nom_cheval_normalized
            },
            'sexe': self.sexe,
            'age': self.age,
            'poids': self.poids,
            'corde': self.corde,
            'distance': {
                'raw': self.distance_raw,
                'meters': self.distance_m
            },
            'chrono': {
                'raw': self.chrono_raw,
                'normalized': self.chrono_normalized
            },
            'performances': {
                'raw': self.performances_raw,
                'structured': self.performances_structured
            },
            'gains': {
                'raw': self.gains_raw,
                'euros': self.gains_euros
            },
            'driver': {
                'raw': self.driver_raw,
                'normalized': self.driver_normalized
            },
            'entraineur': {
                'raw': self.entraineur_raw,
                'normalized': self.entraineur_normalized
            },
            'proprietaire': {
                'raw': self.proprietaire_raw,
                'normalized': self.proprietaire_normalized
            },
            'cote': {
                'raw': self.cote_raw,
                'decimale': self.cote_decimale
            },
            'commentaire': self.commentaire,
            'raw_data': self.raw_data
        }

@dataclass
class MediaSelection:
    """Sélection d'un média pour une course."""
    course_id: str
    source: str
    selection: List[int]
    rang: List[int] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'course_id': self.course_id,
            'source': self.source,
            'selection': self.selection,
            'rang': self.rang
        }

@dataclass
class Classement:
    """Classements trouvés dans le journal."""
    course_id: str
    forme: List[int] = field(default_factory=list)
    classe: List[int] = field(default_factory=list)
    progres: List[int] = field(default_factory=list)
    regularite: List[int] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'course_id': self.course_id,
            'forme': self.forme,
            'classe': self.classe,
            'progres': self.progres,
            'regularite': self.regularite
        }

@dataclass
class Commentaire:
    """Commentaire sur un cheval."""
    course_id: str
    numero_cheval: int
    texte: str
    
    def to_dict(self) -> dict:
        return {
            'course_id': self.course_id,
            'numero_cheval': self.numero_cheval,
            'texte': self.texte
        }

@dataclass
class Resultat:
    """Résultat d'une course (arrivée, gains, etc.)."""
    course_id: str
    date: str
    type_pari: str = ""
    arrivee_raw: str = ""
    arrivee: List[int] = field(default_factory=list)
    arrivee_complete: List[dict] = field(default_factory=list)
    npo: int = 0
    np: int = 0
    disqualifies: List[int] = field(default_factory=list)
    non_partants: List[int] = field(default_factory=list)
    gains_ordre_raw: str = ""
    gains_ordre_euros: Optional[int] = None
    gains_desordre_raw: str = ""
    gains_desordre_euros: Optional[int] = None
    gains_bonus_raw: str = ""
    gains_bonus_euros: Optional[int] = None
    nb_gagnants_ordre: Optional[int] = None
    nb_gagnants_desordre: Optional[int] = None
    nb_gagnants_bonus: Optional[int] = None
    masse_partager_raw: str = ""
    masse_partager_euros: Optional[int] = None
    rapport_gagnant_raw: str = ""
    rapport_gagnant_euros: Optional[int] = None
    rapport_place_a_raw: str = ""
    rapport_place_a_euros: Optional[int] = None
    rapport_place_b_raw: str = ""
    rapport_place_b_euros: Optional[int] = None
    map_paris_raw: str = ""
    map_paris_euros: Optional[int] = None
    tierce_v_raw: str = ""
    tierce_v_value: Optional[str] = None
    raw_text: str = ""
    
    def to_dict(self) -> dict:
        return {
            'course_id': self.course_id,
            'date': self.date,
            'type_pari': self.type_pari,
            'arrivee_raw': self.arrivee_raw,
            'arrivee': self.arrivee,
            'arrivee_complete': self.arrivee_complete,
            'npo': self.npo,
            'np': self.np,
            'disqualifies': self.disqualifies,
            'non_partants': self.non_partants,
            'gains_ordre': {'raw': self.gains_ordre_raw, 'euros': self.gains_ordre_euros},
            'gains_desordre': {'raw': self.gains_desordre_raw, 'euros': self.gains_desordre_euros},
            'gains_bonus': {'raw': self.gains_bonus_raw, 'euros': self.gains_bonus_euros},
            'nb_gagnants': {
                'ordre': self.nb_gagnants_ordre,
                'desordre': self.nb_gagnants_desordre,
                'bonus': self.nb_gagnants_bonus
            },
            'masse_partager': {'raw': self.masse_partager_raw, 'euros': self.masse_partager_euros},
            'rapports': {
                'gagnant': {'raw': self.rapport_gagnant_raw, 'euros': self.rapport_gagnant_euros},
                'place_a': {'raw': self.rapport_place_a_raw, 'euros': self.rapport_place_a_euros},
                'place_b': {'raw': self.rapport_place_b_raw, 'euros': self.rapport_place_b_euros}
            },
            'map_paris': {'raw': self.map_paris_raw, 'euros': self.map_paris_euros},
            'tierce_v': {'raw': self.tierce_v_raw, 'value': self.tierce_v_value}
        }

@dataclass
class ParsedDocument:
    """Document parsé complet."""
    filename: str
    doc_type: str  # JOURNAL ou RESULTAT
    date_publication: str
    pages: int
    courses: List[Course] = field(default_factory=list)
    partants: List[Partant] = field(default_factory=list)
    media_selections: List[MediaSelection] = field(default_factory=list)
    classements: List[Classement] = field(default_factory=list)
    commentaires: List[Commentaire] = field(default_factory=list)
    resultat: Optional[Resultat] = None
    quality_score: int = 0
    quality_status: str = "PENDING"
    quality_details: Dict[str, Any] = field(default_factory=dict)
    parsing_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'filename': self.filename,
            'doc_type': self.doc_type,
            'date_publication': self.date_publication,
            'pages': self.pages,
            'courses': [c.to_dict() for c in self.courses],
            'partants': [p.to_dict() for p in self.partants],
            'media_selections': [m.to_dict() for m in self.media_selections],
            'classements': [c.to_dict() for c in self.classements],
            'commentaires': [c.to_dict() for c in self.commentaires],
            'resultat': self.resultat.to_dict() if self.resultat else None,
            'quality': {
                'score': self.quality_score,
                'status': self.quality_status,
                'details': self.quality_details,
                'errors': self.parsing_errors
            }
        }
    
    def save_json(self, output_dir: str):
        """Sauvegarde le document parsé en JSON."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        outfile = os.path.join(output_dir, self.filename.replace('.pdf', '.json'))
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return outfile


# ============================================================
# ECD (Espace Course En Direct) Models
# ============================================================

@dataclass
class CourseDirectBet:
    """Représente un pari/gain dans une course ECD."""
    type_pari: str = ""           # GAGNANT, PLACE, JUM GAGNANT, JUM PLACE, JUM ORDRE, TRIO
    combinaison_raw: str = ""     # ex: "8 - 14", "8 - 14 - 9"
    combinaison_normalized: List[int] = field(default_factory=list)
    montant_raw: str = ""         # ex: "333 200"
    montant_euros: Optional[int] = None
    nb_paris: Optional[int] = None
    position: Optional[int] = None  # 1ère, 2ième, etc. si applicable
    uncertain: bool = False       # True si la structure est ambiguë
    
    def to_dict(self) -> dict:
        return {
            'type_pari': self.type_pari,
            'combinaison': {
                'raw': self.combinaison_raw,
                'normalized': self.combinaison_normalized
            },
            'montant': {
                'raw': self.montant_raw,
                'euros': self.montant_euros
            },
            'nb_paris': self.nb_paris,
            'position': self.position,
            'uncertain': self.uncertain
        }


@dataclass
class CourseDirectArrival:
    """Arrivée d'une course ECD."""
    arrivee_raw: str = ""           # ex: "8 - 14 - 9"
    positions: List[int] = field(default_factory=list)  # [8, 14, 9]
    gains_total_raw: str = ""       # ex: "333 200"
    gains_total_euros: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            'arrivee_raw': self.arrivee_raw,
            'positions': self.positions,
            'gains_total': {
                'raw': self.gains_total_raw,
                'euros': self.gains_total_euros
            }
        }


@dataclass
class CourseDirect:
    """Représente une course dans un document ECD."""
    course_id: str
    document_id: str
    numero_course: int = 0
    arrivee: Optional[CourseDirectArrival] = None
    paris: List[CourseDirectBet] = field(default_factory=list)
    page_num: int = 0
    y_position: float = 0.0
    raw_text: str = ""
    
    def to_dict(self) -> dict:
        return {
            'course_id': self.course_id,
            'document_id': self.document_id,
            'numero_course': self.numero_course,
            'arrivee': self.arrivee.to_dict() if self.arrivee else None,
            'paris': [p.to_dict() for p in self.paris],
            'page_num': self.page_num,
            'y_position': self.y_position,
            'raw_text': self.raw_text
        }


@dataclass
class ECDDocument:
    """Métadonnées du document ECD."""
    document_id: str
    filename: str
    date: str = ""
    reunion: str = ""
    hippodrome: str = ""
    nombre_courses_detectees: int = 0
    pages: int = 0
    raw_text: str = ""
    
    def to_dict(self) -> dict:
        return {
            'document_id': self.document_id,
            'filename': self.filename,
            'date': self.date,
            'reunion': self.reunion,
            'hippodrome': self.hippodrome,
            'nombre_courses_detectees': self.nombre_courses_detectees,
            'pages': self.pages,
            'raw_text': self.raw_text
        }


@dataclass
class ParsedECDDocument:
    """Document ECD parsé complet."""
    filename: str
    doc_type: str = "COURSE_EN_DIRECT"
    date_publication: str = ""
    pages: int = 0
    ecd_document: Optional[ECDDocument] = None
    courses: List[CourseDirect] = field(default_factory=list)
    quality_score: int = 0
    quality_status: str = "PENDING"
    quality_details: Dict[str, Any] = field(default_factory=dict)
    parsing_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'filename': self.filename,
            'doc_type': self.doc_type,
            'date_publication': self.date_publication,
            'pages': self.pages,
            'ecd_document': self.ecd_document.to_dict() if self.ecd_document else None,
            'courses': [c.to_dict() for c in self.courses],
            'quality': {
                'score': self.quality_score,
                'status': self.quality_status,
                'details': self.quality_details,
                'errors': self.parsing_errors
            }
        }
    
    def save_json(self, output_dir: str):
        """Sauvegarde le document parsé en JSON."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        outfile = os.path.join(output_dir, self.filename.replace('.pdf', '.json'))
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return outfile


# ============================================================
# REP (Report) Models
# ============================================================

@dataclass
class RepDocument:
    """Représente un document de rapport (REP) - pas un résultat de course."""
    document_type: str = "REP"
    date_document: str = ""           # Date du document (ex: 2025-01-15)
    date_document_raw: str = ""       # Date brute du document (ex: 15/01/2025)
    date_course_cible: str = ""       # Date de la course concernée (ex: 2025-01-17)
    date_course_cible_raw: str = ""   # Date brute de la course cible (ex: VENDREDI 17/01/2025)
    game_type: str = ""               # Type de jeu (ex: "4+1", "QUARTE", "TIERCE")
    report_ordre_raw: str = ""        # Montant brut (ex: "59 386 377")
    report_ordre: Optional[int] = None # Montant normalisé (ex: 59386377)
    tierce_v_raw: str = ""            # Ligne TIERCE V. si présente
    tierce_v_value: Optional[str] = None  # Valeur extraite de TIERCE V.
    raw_text: str = ""                # Texte complet du PDF
    
    def to_dict(self) -> dict:
        return {
            'document_type': self.document_type,
            'date_document': self.date_document,
            'date_document_raw': self.date_document_raw,
            'date_course_cible': self.date_course_cible,
            'date_course_cible_raw': self.date_course_cible_raw,
            'game_type': self.game_type,
            'report_ordre': {'raw': self.report_ordre_raw, 'euros': self.report_ordre},
            'tierce_v': {'raw': self.tierce_v_raw, 'value': self.tierce_v_value},
            'raw_text': self.raw_text
        }


@dataclass
class ParsedRepDocument:
    """Document REP parsé complet."""
    filename: str
    doc_type: str = "REP"
    date_publication: str = ""
    pages: int = 0
    rep_document: Optional[RepDocument] = None
    quality_score: int = 0
    quality_status: str = "PENDING"
    quality_details: Dict[str, Any] = field(default_factory=dict)
    parsing_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'filename': self.filename,
            'doc_type': self.doc_type,
            'date_publication': self.date_publication,
            'pages': self.pages,
            'rep_document': self.rep_document.to_dict() if self.rep_document else None,
            'quality': {
                'score': self.quality_score,
                'status': self.quality_status,
                'details': self.quality_details,
                'errors': self.parsing_errors
            }
        }
    
    def save_json(self, output_dir: str):
        """Sauvegarde le document parsé en JSON."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        outfile = os.path.join(output_dir, self.filename.replace('.pdf', '.json'))
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return outfile