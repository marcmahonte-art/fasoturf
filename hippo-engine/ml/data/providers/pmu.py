"""
PmUProvider — données PMU en direct.

Utilise les endpoints publics documentés dans ``infos.md`` :

    GET /services/racing/program/{date}
    GET /services/racing/card/{date}/{reunion}/{course}
    GET /services/racing/results/{date}

Le fournisseur **dégrade proprement** : s'il n'y a pas de réseau, il lève
``ProviderUnavailable`` et la factory bascule sur un autre provider. Aucune
clé n'est requise ; aucune clé n'est jamais exposée au frontend.
"""
from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from ..schema import OddsPoint, Race, RaceResult, Runner
from ..normalize import normalize_odds, normalize_runner
from .base import DataProvider

PMU_BASE = "https://www.pmu.fr/services/racing"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HippoEngine/1.0)",
    "Accept": "application/json",
}


class ProviderUnavailable(RuntimeError):
    """Le fournisseur n'est pas joignable."""


class PmUProvider(DataProvider):
    name = "pmu"

    def __init__(self, base_url: str = PMU_BASE, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # -- HTTP --------------------------------------------------------

    def _get(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        request = Request(url, headers=DEFAULT_HEADERS)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise ProviderUnavailable(f"PMU injoignable : {exc}") from exc

    @staticmethod
    def _pmu_date(date: str) -> str:
        """YYYY-MM-DD -> DDMMYYYY (format attendu par l'API)."""
        parts = date.replace("/", "-").split("-")
        if len(parts) == 3:
            return f"{parts[2]}{parts[1]}{parts[0]}"
        return date

    # -- DataProvider ------------------------------------------------

    def get_meetings(self, date: str) -> list[dict]:
        program = self._get(f"program/{self._pmu_date(date)}")
        reunions = program.get("programme", {}).get("reunions", [])
        return [
            {
                "id": r.get("numOfficiel"),
                "date": date,
                "hippodrome": (r.get("hippodrome") or {}).get("libelleLong", ""),
                "pays": (r.get("pays") or {}).get("libelle", ""),
            }
            for r in reunions
        ]

    def get_races(self, date: str) -> list[Race]:
        program = self._get(f"program/{self._pmu_date(date)}")
        races: list[Race] = []
        for reunion in program.get("programme", {}).get("reunions", []):
            for course in reunion.get("courses", []):
                races.append(Race(
                    date=date,
                    hippodrome=(reunion.get("hippodrome") or {}).get("libelleCourt", ""),
                    external_id=f"{self._pmu_date(date)}-R{reunion.get('numOfficiel')}-C{course.get('numOrdre')}",
                    start_time=str(course.get("heureDepart", ""))[:5],
                    country=(reunion.get("pays") or {}).get("libelle", ""),
                    discipline=(course.get("discipline") or "").upper(),
                    race_type=course.get("categorieParticularite") or "",
                    distance=course.get("distance"),
                    terrain=(course.get("penetrometre") or {}).get("intitule", ""),
                    prize=course.get("montantPrix"),
                    number_of_runners=course.get("nombreDeclaresPartants"),
                    status="scheduled",
                ))
        return races

    def _parse_race_id(self, race_id: str) -> tuple[str, str, str]:
        """``DDMMYYYY-R1-C3`` -> (date_api, reunion, course)."""
        try:
            date_part, reunion_part, course_part = race_id.split("-")
            return date_part, reunion_part.replace("R", ""), course_part.replace("C", "")
        except ValueError as exc:
            raise ProviderUnavailable(f"race_id PMU invalide : {race_id}") from exc

    def get_race(self, race_id: str) -> Race | None:
        date_api, reunion, course_num = self._parse_race_id(race_id)
        card = self._get(f"card/{date_api}/{reunion}/{course_num}")
        course = card.get("course") or {}
        participants = card.get("participants", [])
        iso_date = f"{date_api[4:8]}-{date_api[2:4]}-{date_api[0:2]}"
        race = Race(
            date=iso_date,
            hippodrome=(course.get("hippodrome") or {}).get("libelleCourt", ""),
            external_id=race_id,
            start_time=str(course.get("heureDepart", ""))[:5],
            discipline=(course.get("discipline") or "").upper(),
            distance=course.get("distance"),
            prize=course.get("montantPrix"),
            number_of_runners=len(participants),
            status="open",
        )
        race.runners = [self._participant_to_runner(p) for p in participants]
        return race

    def _participant_to_runner(self, participant: dict[str, Any]) -> Runner:
        direct = (participant.get("dernierRapportDirect") or {}).get("rapport")
        reference = (participant.get("dernierRapportReference") or {}).get("rapport")
        runner = normalize_runner({
            "number": participant.get("numPmu"),
            "horse": {"name": participant.get("nom", "")},
            "jockey": {"name": participant.get("driver", "")},
            "trainer": {"name": participant.get("entraineur", "")},
            "draw": participant.get("placeCorde"),
            "weight": participant.get("poidsConditionMonte"),
            "official_rating": participant.get("valeur"),
            "current_odds": normalize_odds(direct),
            "morning_odds": normalize_odds(reference),
            "status": "non_runner" if participant.get("statut") == "NON_PARTANT" else "declared",
            "history": participant.get("musique", ""),
        })
        runner.odds_history = [
            OddsPoint(odds=o, timestamp="", source="pmu")
            for o in (normalize_odds(reference), normalize_odds(direct))
            if o
        ]
        return runner

    def get_runners(self, race_id: str) -> list[Runner]:
        race = self.get_race(race_id)
        return list(race.runners) if race else []

    def get_horse_history(self, horse_id: str) -> list[dict]:
        # L'API PMU n'expose pas d'historique complet sans partenariat.
        return []

    def get_jockey_history(self, jockey_id: str) -> list[dict]:
        return []

    def get_trainer_history(self, trainer_id: str) -> list[dict]:
        return []

    def get_odds(self, race_id: str) -> dict[int, list[dict]]:
        race = self.get_race(race_id)
        if not race:
            return {}
        return {
            r.number: [{"odds": p.odds, "timestamp": p.timestamp} for p in r.odds_history]
            for r in race.runners
        }

    def get_results(self, race_id: str) -> RaceResult | None:
        date_api, reunion, course_num = self._parse_race_id(race_id)
        try:
            payload = self._get(f"results/{date_api}")
        except ProviderUnavailable:
            return None
        for res in payload.get("resultats", []):
            if str(res.get("numReunion")) == reunion and str(res.get("numCourse")) == course_num:
                order = [
                    int(p["numPmu"])
                    for p in res.get("participants", [])
                    if p.get("ordreArrivee")
                ]
                return RaceResult(race_id=race_id, finish_order=sorted(
                    order,
                    key=lambda n: next(
                        (int(p["ordreArrivee"]) for p in res.get("participants", [])
                         if p.get("numPmu") == n), 99
                    ),
                ))
        return None
