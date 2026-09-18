"""
Module d'appariement entre les courses des journaux LONAB et le programme officiel PMU.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

class PMURaceMatcher:
    """Apparie une course issue des journaux LONAB avec la réunion et course officielle PMU."""

    def __init__(self, pmu_client):
        self.client = pmu_client

    def find_matching_course(
        self,
        date_str: str,
        lonab_horses: List[str],
        hippodrome_hint: Optional[str] = None
    ) -> Optional[Tuple[int, int, Dict[str, Any]]]:
        """
        Trouve (reunion_num, course_num, course_data) correspondant aux chevaux de la LONAB.
        """
        try:
            prog_data = self.client.get_programme(date_str)
        except Exception as e:
            logger.warning("Impossible de récupérer le programme pour %s: %s", date_str, e)
            return None

        if not prog_data or "programme" not in prog_data:
            return None

        reunions = prog_data["programme"].get("reunions", [])
        if not reunions:
            return None

        # Priorité aux réunions françaises diurnes (généralement R1)
        reunions_sorted = sorted(
            reunions,
            key=lambda r: (0 if r.get("numOfficiel") == 1 else 1, r.get("numOfficiel", 99))
        )

        norm_lonab = {self._norm(h) for h in lonab_horses if h}

        best_match = None
        best_score = 0

        for r in reunions_sorted:
            r_num = r.get("numOfficiel")
            r_hippo = (r.get("hippodrome", {}).get("libelleCourt") or "").upper()
            
            # Si un indice d'hippodrome est fourni et correspond
            hippo_match = False
            if hippodrome_hint and hippodrome_hint.upper() in r_hippo:
                hippo_match = True

            for c in r.get("courses", []):
                c_num = c.get("numOrdre")
                
                # Récupérer les partants PMU pour vérifier le chevauchement
                pmu_parts = self.client.get_participants(date_str, r_num, c_num)
                if not pmu_parts or "participants" not in pmu_parts:
                    continue

                pmu_horses = {self._norm(p.get("nom", "")) for p in pmu_parts["participants"]}
                overlap = len(norm_lonab.intersection(pmu_horses))
                
                # Bonus si l'hippodrome correspond
                score = overlap + (2 if hippo_match else 0)

                # Si plus de la moitié des chevaux correspondent, c'est un match certain
                if overlap >= max(4, len(norm_lonab) * 0.4):
                    logger.debug("Match trouvé: R%dC%d (%s) avec %d chevaux en commun", r_num, c_num, r_hippo, overlap)
                    return (r_num, c_num, c)

                if score > best_score:
                    best_score = score
                    best_match = (r_num, c_num, c)

        if best_score >= 4:
            return best_match

        return None

    @staticmethod
    def _norm(name: str) -> str:
        """Normalise un nom pour la comparaison."""
        if not name:
            return ""
        return "".join(c for c in name.upper() if c.isalnum())
