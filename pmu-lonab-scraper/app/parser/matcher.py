from typing import List, Optional, Tuple
from dataclasses import dataclass
from app.models.parser_models import ParsedDocument, Course, Resultat

@dataclass
class MatchResult:
    journal_doc: ParsedDocument
    resultat_doc: ParsedDocument
    course: Course
    resultat: Resultat
    confidence: float
    reasons: List[str]

class JournalResultMatcher:
    """Associe les journaux hippiques aux résultats correspondants."""
    
    def __init__(self):
        self.matches: List[MatchResult] = []
        self.unmatched_journals: List[ParsedDocument] = []
        self.unmatched_results: List[ParsedDocument] = []
    
    def match(self, journals: List[ParsedDocument], results: List[ParsedDocument]) -> List[MatchResult]:
        """Effectue le matching entre journaux et résultats."""
        self.matches = []
        self.unmatched_journals = journals.copy()
        self.unmatched_results = results.copy()
        
        for journal in journals:
            best_match = None
            best_score = 0.0
            best_reasons = []
            
            for resultat in results:
                score, reasons = self._calculate_match_score(journal, resultat)
                if score > best_score:
                    best_score = score
                    best_match = resultat
                    best_reasons = reasons
            
            if best_match and best_score >= 0.7:
                # Match trouvé
                self.matches.append(MatchResult(
                    journal_doc=journal,
                    resultat_doc=best_match,
                    course=journal.courses[0] if journal.courses else None,
                    resultat=best_match.resultat,
                    confidence=best_score,
                    reasons=best_reasons
                ))
                self.unmatched_journals.remove(journal)
                self.unmatched_results.remove(best_match)
            else:
                # Pas de match assez fiable
                pass
        
        return self.matches
    
    def _calculate_match_score(self, journal: ParsedDocument, resultat: ParsedDocument) -> Tuple[float, List[str]]:
        """Calcule un score de similarité entre un journal et un résultat."""
        reasons = []
        score = 0.0
        max_score = 0.0
        
        course = journal.courses[0] if journal.courses else None
        res = resultat.resultat
        
        if not course or not res:
            return 0.0, ["Pas de course ou résultat"]
        
        # 1. Date (poids: 0.4)
        max_score += 0.4
        if course.date and res.date and course.date == res.date:
            score += 0.4
            reasons.append(f"Date identique: {course.date}")
        elif course.date and res.date:
            reasons.append(f"Dates différentes: {course.date} vs {res.date}")
        
        # 2. Type de pari / Discipline (poids: 0.2)
        max_score += 0.2
        if self._types_compatible(course, res):
            score += 0.2
            reasons.append(f"Type compatible: {course.discipline} / {res.type_pari}")
        else:
            reasons.append(f"Type incompatible: {course.discipline} / {res.type_pari}")
        
        # 3. Hippodrome / Course title (poids: 0.2)
        max_score += 0.2
        if course.hippodrome and res.raw_text:
            if course.hippodrome.upper() in res.raw_text.upper():
                score += 0.2
                reasons.append(f"Hippodrome trouvé dans résultat: {course.hippodrome}")
            else:
                reasons.append(f"Hippodrome non trouvé: {course.hippodrome}")
        
        # 4. Nombre de partants / Arrivée (poids: 0.1)
        max_score += 0.1
        if course.partants_declares > 0 and res.arrivee:
            if len(res.arrivee) <= course.partants_declares:
                score += 0.1
                reasons.append(f"Arrivée cohérente: {len(res.arrivee)}/{course.partants_declares}")
            else:
                reasons.append(f"Arrivée incohérente: {len(res.arrivee)}/{course.partants_declares}")
        
        # 5. Numéros dans l'arrivée présents dans les partants (poids: 0.1)
        max_score += 0.1
        if journal.partants and res.arrivee:
            partant_nums = {p.numero for p in journal.partants}
            arrivee_in_partants = sum(1 for n in res.arrivee if n in partant_nums)
            if arrivee_in_partants == len(res.arrivee):
                score += 0.1
                reasons.append("Tous les numéros d'arrivée sont dans les partants")
            elif arrivee_in_partants > 0:
                score += 0.05
                reasons.append(f"{arrivee_in_partants}/{len(res.arrivee)} numéros d'arrivée dans les partants")
        
        return score, reasons
    
    def _types_compatible(self, course: Course, resultat: Resultat) -> bool:
        """Vérifie si le type de course et le type de pari sont compatibles."""
        discipline = course.discipline.upper()
        type_pari = resultat.type_pari.upper()
        
        # QUARTE/4+1 généralement sur courses d'attelé ou plat
        # TIERCE aussi
        # Pour l'instant, on accepte tout
        return True
    
    def get_unmatched_report(self) -> dict:
        """Génère un rapport des éléments non matchés."""
        return {
            'unmatched_journals': [
                {
                    'filename': j.filename,
                    'date': j.courses[0].date if j.courses else '',
                    'hippodrome': j.courses[0].hippodrome if j.courses else '',
                    'course_num': j.courses[0].course_num if j.courses else 0
                }
                for j in self.unmatched_journals
            ],
            'unmatched_results': [
                {
                    'filename': r.filename,
                    'date': r.resultat.date if r.resultat else '',
                    'type_pari': r.resultat.type_pari if r.resultat else '',
                    'arrivee': r.resultat.arrivee if r.resultat else []
                }
                for r in self.unmatched_results
            ]
        }