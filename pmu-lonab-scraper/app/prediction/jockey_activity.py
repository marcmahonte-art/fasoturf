"""
Calculateur d'activité quotidienne des jockeys et drivers.
Basé sur les études quantitatives Aspiturf démontrant l'impact du volume de montes
sur le taux de réussite (de 5.92% pour 1 course à 12.71% pour 7+ courses).
"""
import re
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from app.enrichment.pmu_client import PMUApiClient

logger = logging.getLogger(__name__)

CACHE_DIR = Path(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\cache")

class JockeyActivityCalculator:
    """Calcule l'activité journalière des jockeys/drivers via le programme PMU."""

    def __init__(self, pmu_client: Optional[PMUApiClient] = None):
        self.client = pmu_client or PMUApiClient()
        self._cache: Dict[str, Counter] = {}
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalise un nom de jockey (ex: 'E. RAFFIN' -> 'E RAFFIN')."""
        if not name:
            return ""
        clean = name.upper().strip()
        clean = re.sub(r'[^A-Z\s]', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def get_daily_activity(self, date_str: str) -> Counter:
        """
        Récupère et compte le nombre de montes de chaque jockey pour la journée.
        date_str: '2024-02-11' ou '11022024'.
        """
        # Normaliser la date en JJMMAAAA pour l'API
        clean_date = date_str.replace("-", "").replace("/", "").strip()
        if len(clean_date) == 8 and (clean_date.startswith("20") or clean_date.startswith("19")):
            clean_date = f"{clean_date[6:8]}{clean_date[4:6]}{clean_date[0:4]}"

        if clean_date in self._cache:
            return self._cache[clean_date]

        cache_file = CACHE_DIR / f"jockey_activity_{clean_date}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cnt = Counter(data)
                    self._cache[clean_date] = cnt
                    return cnt
            except Exception as e:
                logger.debug("Erreur lecture cache %s : %s", cache_file, e)

        jockeys = Counter()
        try:
            prog = self.client.get_programme(clean_date)
        except Exception as e:
            logger.warning("Erreur récupération programme pour %s : %s", clean_date, e)
            return jockeys

        if not prog or "programme" not in prog:
            return jockeys

        # Préparer les paires (r_num, c_num)
        tasks = []
        reunions = prog["programme"].get("reunions", [])
        for r in reunions:
            r_num = r.get("numOfficiel")
            for c in r.get("courses", []):
                c_num = c.get("numOrdre")
                tasks.append((r_num, c_num))

        def _fetch_course_drivers(item):
            rn, cn = item
            res = []
            try:
                p_data = self.client.get_participants(clean_date, rn, cn)
                if p_data and "participants" in p_data:
                    for p in p_data["participants"]:
                        d = p.get("driver")
                        if d:
                            nd = self.normalize_name(d)
                            if nd:
                                res.append(nd)
            except Exception:
                pass
            return res

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = executor.map(_fetch_course_drivers, tasks)
            for drivers in results:
                for d in drivers:
                    jockeys[d] += 1

        self._cache[clean_date] = jockeys
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(dict(jockeys), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug("Erreur écriture cache %s : %s", cache_file, e)

        return jockeys

    def get_jockey_montes(self, date_str: str, jockey_name: str) -> int:
        """Retourne le nombre de montes d'un jockey pour une date donnée."""
        activity = self.get_daily_activity(date_str)
        norm_jockey = self.normalize_name(jockey_name)
        
        # Correspondance exacte
        if norm_jockey in activity:
            return activity[norm_jockey]
        
        # Correspondance partielle (nom de famille)
        parts = norm_jockey.split()
        if parts:
            last_name = parts[-1]
            for candidate, cnt in activity.items():
                if last_name in candidate.split():
                    return cnt

        return 1  # Valeur par défaut si non trouvé

    @staticmethod
    def get_profile(montes_count: int) -> Dict[str, Any]:
        """
        Retourne le profil statistique du jockey selon son nombre de courses du jour.
        D'après les analyses statistiques Aspiturf (195 638 courses).
        """
        if montes_count >= 7:
            return {
                "profile": "Marathonien",
                "emoji": "[TOP]",
                "score_bonus": 3.0,
                "coeff": 1.15,
                "taux_reussite_estime": "12.71%",
                "action": "Base prioritaire absolue (+115% de reussite)",
                "color": "green"
            }
        elif montes_count == 6:
            return {
                "profile": "Ultra-Poly",
                "emoji": "[+++]",
                "score_bonus": 2.5,
                "coeff": 1.12,
                "taux_reussite_estime": "11.70%",
                "action": "Tres forte attention (Meilleur ROI 70%)",
                "color": "green"
            }
        elif montes_count == 5:
            return {
                "profile": "Polyvalent",
                "emoji": "[++ ]",
                "score_bonus": 2.0,
                "coeff": 1.10,
                "taux_reussite_estime": "10.61%",
                "action": "Attention soutenue",
                "color": "cyan"
            }
        elif montes_count == 4:
            return {
                "profile": "Regulier",
                "emoji": "[+  ]",
                "score_bonus": 1.5,
                "coeff": 1.08,
                "taux_reussite_estime": "9.20%",
                "action": "Surveillance positive",
                "color": "cyan"
            }
        elif montes_count in (2, 3):
            return {
                "profile": "Selectif",
                "emoji": "[~  ]",
                "score_bonus": 0.5 if montes_count == 3 else 0.0,
                "coeff": 1.02 if montes_count == 3 else 1.00,
                "taux_reussite_estime": "7.85%" if montes_count == 3 else "6.67%",
                "action": "Neutre / Prudence",
                "color": "yellow"
            }
        else:
            return {
                "profile": "Occasionnel",
                "emoji": "[-  ]",
                "score_bonus": -1.0,
                "coeff": 0.95,
                "taux_reussite_estime": "5.92%",
                "action": "Mefiance (94% d'echecs)",
                "color": "red"
            }
