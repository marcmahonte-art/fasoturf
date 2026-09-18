import csv
import re
from typing import List, Dict, Any
from dataclasses import dataclass
from app.models.parser_models import ParsedDocument, Course, Partant, Resultat, ParsedRepDocument, RepDocument


EXPECTED_ARRIVAL_LENGTH = {
    'QUARTE': 4,
    'TIERCE': 3,
    '4+1': 4,
    'COUPLE': 2,
}


@dataclass
class QualityIssue:
    filename: str
    course_id: str
    field: str
    severity: str  # ERROR, WARNING, INFO
    message: str
    expected: str = ""
    actual: str = ""


class QualityValidator:
    """Valide la qualité du parsing."""
    
    def __init__(self):
        self.issues: List[QualityIssue] = []
    
    def validate(self, parsed) -> Any:
        """Valide un document parsé et calcule le score de qualité."""
        self.issues = []
        
        if hasattr(parsed, 'doc_type'):
            if parsed.doc_type == 'JOURNAL':
                self._validate_journal(parsed)
            elif parsed.doc_type == 'RESULTAT':
                self._validate_resultat(parsed)
            elif parsed.doc_type == 'REP':
                self._validate_rep(parsed)
        
        # Calculer score
        parsed.quality_score, parsed.quality_status = self._calculate_score(parsed)
        parsed.quality_details = self._get_details(parsed)
        parsed.parsing_errors = [f"{i.severity}: {i.field} - {i.message}" for i in self.issues]
        
        return parsed
    
    def _validate_journal(self, parsed: ParsedDocument):
        """Valide un journal hippique."""
        if not parsed.courses:
            self._add_issue(parsed.filename, "", "course", "ERROR", "Aucune course détectée")
            return
        
        course = parsed.courses[0]
        
        # Date valide
        if not course.date:
            self._add_issue(parsed.filename, course.course_id, "date", "ERROR", "Date manquante")
        elif not self._is_valid_date(course.date):
            self._add_issue(parsed.filename, course.course_id, "date", "WARNING", f"Format date suspect: {course.date}")
        
        # Hippodrome
        if not course.hippodrome:
            self._add_issue(parsed.filename, course.course_id, "hippodrome", "WARNING", "Hippodrome manquant")
        
        # Nombre de partants
        if course.partants_declares <= 0:
            self._add_issue(parsed.filename, course.course_id, "partants_declares", "ERROR", "Partants déclarés invalides")
        
        # Partants effectifs
        if len(parsed.partants) == 0:
            self._add_issue(parsed.filename, course.course_id, "partants", "ERROR", "Aucun partant extrait")
        elif course.partants_declares > 0 and len(parsed.partants) != course.partants_declares:
            self._add_issue(
                parsed.filename, course.course_id, "partants_count", "WARNING",
                f"Nombre partants incohérent: {len(parsed.partants)} extraits vs {course.partants_declares} déclarés"
            )
        
        # Numéros uniques
        nums = [p.numero for p in parsed.partants]
        if len(nums) != len(set(nums)):
            duplicates = [n for n in nums if nums.count(n) > 1]
            self._add_issue(parsed.filename, course.course_id, "numero_unique", "ERROR", f"Numéros dupliqués: {set(duplicates)}")
        
        # Noms des chevaux
        for p in parsed.partants:
            if not p.nom_cheval_raw:
                self._add_issue(parsed.filename, course.course_id, f"partant_{p.numero}_nom", "ERROR", "Nom cheval vide")
            if not p.nom_cheval_normalized:
                self._add_issue(parsed.filename, course.course_id, f"partant_{p.numero}_nom_norm", "WARNING", "Nom normalisé vide")
        
        # Distance
        if not course.distance_m:
            self._add_issue(parsed.filename, course.course_id, "distance", "WARNING", "Distance en mètres non extraite")
        
        # Montant
        if not course.montant_euros:
            self._add_issue(parsed.filename, course.course_id, "montant", "INFO", "Montant non extrait")
    
    def _validate_resultat(self, parsed: ParsedDocument):
        """Valide un résultat."""
        if not parsed.resultat:
            self._add_issue(parsed.filename, "", "resultat", "ERROR", "Aucun résultat extrait")
            return
        
        r = parsed.resultat
        
        # Date
        if not r.date:
            self._add_issue(parsed.filename, r.course_id, "date", "ERROR", "Date manquante")
        elif not self._is_valid_date(r.date):
            self._add_issue(parsed.filename, r.course_id, "date", "WARNING", f"Format date suspect: {r.date}")
        
        # Type pari
        if not r.type_pari:
            self._add_issue(parsed.filename, r.course_id, "type_pari", "WARNING", "Type de pari non détecté")
        
        # Arrivée
        if not r.arrivee:
            self._add_issue(parsed.filename, r.course_id, "arrivee", "ERROR", "Arrivée manquante")
        else:
            # Positions uniques
            if len(r.arrivee) != len(set(r.arrivee)):
                self._add_issue(parsed.filename, r.course_id, "arrivee_unique", "ERROR", "Positions dupliquées dans l'arrivée")
            
            # Numéros valides (1-20)
            for n in r.arrivee:
                if n < 1 or n > 20:
                    self._add_issue(parsed.filename, r.course_id, "arrivee_numero", "WARNING", f"Numéro suspect dans arrivée: {n}")
            
            # Longueur arrivée cohérente avec type de jeu
            expected = EXPECTED_ARRIVAL_LENGTH.get(r.type_pari)
            if expected is not None:
                actual = len(r.arrivee)
                if actual != expected:
                    self._add_issue(
                        parsed.filename, r.course_id, "arrivee_length", "ERROR",
                        f"Longueur arrivée incohérente pour {r.type_pari}: {actual} numéros (attendu: {expected})",
                        expected=str(expected), actual=str(actual)
                    )
        
        # Gains
        if r.gains_ordre_euros is None and r.gains_desordre_euros is None:
            self._add_issue(parsed.filename, r.course_id, "gains", "WARNING", "Aucun gain extrait")
        
        # NPO/NP
        if r.npo < 0 or r.np < 0:
            self._add_issue(parsed.filename, r.course_id, "npo_np", "WARNING", f"NPO/NP suspects: NPO={r.npo}, NP={r.np}")
    
    def _validate_rep(self, parsed: ParsedRepDocument):
        """Valide un document REP (Rapport)."""
        if not parsed.rep_document:
            self._add_issue(parsed.filename, "", "rep_document", "ERROR", "Aucun document REP extrait")
            return
        
        r = parsed.rep_document
        
        # Date du document
        if not r.date_document:
            self._add_issue(parsed.filename, "", "date_document", "ERROR", "Date du document manquante")
        elif not self._is_valid_date(r.date_document):
            self._add_issue(parsed.filename, "", "date_document", "WARNING", f"Format date document suspect: {r.date_document}")
        
        # Date de la course cible
        if not r.date_course_cible:
            self._add_issue(parsed.filename, "", "date_course_cible", "ERROR", "Date de la course cible manquante")
        elif not self._is_valid_date(r.date_course_cible):
            self._add_issue(parsed.filename, "", "date_course_cible", "WARNING", f"Format date course cible suspect: {r.date_course_cible}")
        
        # Les deux dates doivent être différentes
        if r.date_document and r.date_course_cible and r.date_document == r.date_course_cible:
            self._add_issue(parsed.filename, "", "date_mismatch", "WARNING", "Date document = date course cible (inhabituel pour un REP)")
        
        # Type de jeu
        if not r.game_type:
            self._add_issue(parsed.filename, "", "game_type", "WARNING", "Type de jeu non détecté")
        
        # Montant du rapport
        if r.report_ordre is None:
            self._add_issue(parsed.filename, "", "report_ordre", "ERROR", "Montant du rapport ordre manquant")
        elif r.report_ordre <= 0:
            self._add_issue(parsed.filename, "", "report_ordre", "WARNING", f"Montant rapport suspect: {r.report_ordre}")
        
        # Ne doit PAS avoir d'arrivée
        if hasattr(r, 'arrivee') and r.arrivee:
            self._add_issue(parsed.filename, "", "arrivee", "WARNING", "Document REP ne devrait pas avoir d'arrivée")
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Vérifie si une date est au format YYYY-MM-DD valide."""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return False
        try:
            year, month, day = map(int, date_str.split('-'))
            if year < 2020 or year > 2030:
                return False
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
            return True
        except:
            return False
    
    def _add_issue(self, filename: str, course_id: str, field: str, severity: str, message: str, expected: str = "", actual: str = ""):
        self.issues.append(QualityIssue(
            filename=filename,
            course_id=course_id,
            field=field,
            severity=severity,
            message=message,
            expected=expected,
            actual=actual
        ))
    
    def _calculate_score(self, parsed: Any) -> tuple:
        """Calcule le score de qualité (0-100) et le statut."""
        if not self.issues:
            return 100, "SUCCESS"
        
        errors = sum(1 for i in self.issues if i.severity == "ERROR")
        warnings = sum(1 for i in self.issues if i.severity == "WARNING")
        infos = sum(1 for i in self.issues if i.severity == "INFO")
        
        # Score de base
        score = 100
        score -= errors * 20
        score -= warnings * 5
        score -= infos * 1
        score = max(0, score)
        
        if score >= 90:
            status = "SUCCESS"
        elif score >= 70:
            status = "PARTIAL"
        else:
            status = "FAILED"
        
        return score, status
    
    def _get_details(self, parsed: Any) -> Dict[str, Any]:
        return {
            'total_issues': len(self.issues),
            'errors': sum(1 for i in self.issues if i.severity == "ERROR"),
            'warnings': sum(1 for i in self.issues if i.severity == "WARNING"),
            'infos': sum(1 for i in self.issues if i.severity == "INFO"),
            'issues_by_field': self._group_by_field()
        }
    
    def _group_by_field(self) -> Dict[str, int]:
        grouped = {}
        for issue in self.issues:
            grouped[issue.field] = grouped.get(issue.field, 0) + 1
        return grouped
    
    def export_issues_csv(self, output_path: str):
        """Exporte les problèmes en CSV."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'course_id', 'field', 'severity', 'message', 'expected', 'actual'])
            for issue in self.issues:
                writer.writerow([
                    issue.filename, issue.course_id, issue.field,
                    issue.severity, issue.message, issue.expected, issue.actual
                ])
    
    def generate_quality_report(self, all_parsed: List[Any], output_path: str):
        """Génère un rapport qualité global."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'filename', 'doc_type', 'course_id', 'quality_score', 'quality_status',
                'courses', 'partants', 'errors', 'warnings', 'infos'
            ])
            
            for p in all_parsed:
                course_id = ""
                if hasattr(p, 'courses') and p.courses:
                    course_id = p.courses[0].course_id
                elif hasattr(p, 'resultat') and p.resultat:
                    course_id = p.resultat.course_id
                elif hasattr(p, 'rep_document') and p.rep_document:
                    course_id = f"REP_{p.rep_document.date_course_cible}"
                
                writer.writerow([
                    p.filename, p.doc_type, course_id,
                    p.quality_score, p.quality_status,
                    len(getattr(p, 'courses', [])),
                    len(getattr(p, 'partants', [])),
                    p.quality_details.get('errors', 0),
                    p.quality_details.get('warnings', 0),
                    p.quality_details.get('infos', 0)
                ])