"""
MockDataProvider (#33) — dataset de démonstration.

Génère des courses **clairement identifiées DEMO**. Aucune donnée réelle.
Le générateur est déterministe (seed) pour que les tests soient reproductibles.

Règle #49 : toute entité produite ici porte ``source="demo"``.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from ..schema import (
    HistoricalRun,
    Horse,
    OddsPoint,
    Person,
    Race,
    RaceResult,
    Runner,
)

DEMO_PREFIX = "DEMO"
DEMO_HIPPODROMES = ["DEMO-VINCENNES", "DEMO-LONGCHAMP", "DEMO-DEAUVILLE"]
DEMO_DISCIPLINES = ["ATTELE", "PLAT", "OBSTACLE"]

_SYLLABLES = [
    "BIG", "LOG", "AMI", "NACO", "THING", "HOT", "ROI", "DU", "MONDE", "VENT",
    "ECLAIR", "NORD", "SUD", "ORAGE", "PRINCE", "LUNE", "SOLEIL", "TONNERRE",
    "FEU", "GLACE", "AIGLE", "LOUP", "RENARD", "OURS", "TIGRE",
]


class MockDataProvider:
    """Fournisseur 100 % synthétique, sans dépendance externe."""

    name = "mock"

    def __init__(self, seed: int = 42, n_races: int = 6) -> None:
        self._rng = random.Random(seed)
        self._races: dict[str, Race] = {}
        self._results: dict[str, RaceResult] = {}
        self._build(n_races)

    # -- Construction ------------------------------------------------

    def _horse_name(self) -> str:
        return f"{DEMO_PREFIX} {self._rng.choice(_SYLLABLES)} {self._rng.choice(_SYLLABLES)}"

    def _build(self, n_races: int) -> None:
        base = date(2026, 9, 13)
        for i in range(n_races):
            race_date = (base + timedelta(days=i)).isoformat()
            hippodrome = DEMO_HIPPODROMES[i % len(DEMO_HIPPODROMES)]
            discipline = DEMO_DISCIPLINES[i % len(DEMO_DISCIPLINES)]
            race_id = f"demo-{race_date}-{hippodrome}-{i + 1}"
            n_runners = self._rng.randint(10, 18)

            runners: list[Runner] = []
            for num in range(1, n_runners + 1):
                # Niveau latent : détermine à la fois la cote et l'historique,
                # de sorte que le modèle ait un signal réel à apprendre.
                latent = self._rng.gauss(0.5, 0.22)
                latent = min(max(latent, 0.02), 0.98)

                odds = round(max(1.4, (1.0 - latent) * 38 + 1.4), 2)
                history = self._history_from_latent(latent, race_date)
                runners.append(Runner(
                    number=num,
                    horse=Horse(name=self._horse_name(), source="demo"),
                    jockey=Person(name=f"{DEMO_PREFIX} JOCKEY {self._rng.randint(1, 20)}", source="demo"),
                    trainer=Person(name=f"{DEMO_PREFIX} TRAINER {self._rng.randint(1, 15)}", source="demo"),
                    draw=self._rng.randint(1, n_runners),
                    weight=round(self._rng.uniform(52, 62), 1),
                    official_rating=round(latent * 60 + 20, 1),
                    morning_odds=round(odds * self._rng.uniform(0.9, 1.2), 2),
                    current_odds=odds,
                    odds_history=[
                        OddsPoint(odds=round(odds * f, 2), timestamp=f"{race_date}T{h:02d}:00:00")
                        for h, f in ((10, 1.15), (12, 1.05), (14, 1.0))
                    ],
                    history=history,
                ))

            race = Race(
                date=race_date,
                hippodrome=hippodrome,
                external_id=race_id,
                start_time=f"{12 + i:02d}:30",
                country="XX",
                discipline=discipline,
                race_type="DEMO",
                distance=self._rng.choice([1600, 2000, 2400, 3000]),
                terrain=self._rng.choice(["BON", "SOUPLE", "COLLANT"]),
                prize=self._rng.choice([10000, 25000, 50000]),
                number_of_runners=n_runners,
                status="scheduled",
                runners=runners,
                source="demo",
            )
            self._races[race_id] = race

            # Résultat DEMO cohérent avec le niveau latent (post-course).
            order = sorted(runners, key=lambda r: r.official_rating or 0, reverse=True)
            order = [r.number for r in order]
            self._results[race_id] = RaceResult(race_id=race_id, finish_order=order)

    def _history_from_latent(self, latent: float, race_date: str) -> list[HistoricalRun]:
        runs: list[HistoricalRun] = []
        for k in range(8):
            noise = self._rng.gauss(0, 0.18)
            strength = min(max(latent + noise, 0.01), 0.99)
            pos = max(1, min(18, int(round((1.0 - strength) * 14)) + 1))
            d = (date.fromisoformat(race_date) - timedelta(days=21 * (k + 1))).isoformat()
            runs.append(HistoricalRun(
                date=d,
                finish_position=pos,
                distance=self._rng.choice([1600, 2000, 2400, 3000]),
                terrain=self._rng.choice(["BON", "SOUPLE", "COLLANT"]),
                hippodrome=self._rng.choice(DEMO_HIPPODROMES),
                weight=round(self._rng.uniform(52, 62), 1),
                draw=self._rng.randint(1, 16),
                official_rating=round(strength * 60 + 20, 1),
                jockey=f"{DEMO_PREFIX} JOCKEY {self._rng.randint(1, 20)}",
                trainer=f"{DEMO_PREFIX} TRAINER {self._rng.randint(1, 15)}",
                odds=round(max(1.5, (1.0 - strength) * 30 + 1.5), 2),
            ))
        return runs

    # -- DataProvider ------------------------------------------------

    def get_meetings(self, date: str) -> list[dict]:
        return [
            {"id": f"{date}-{h}", "date": date, "hippodrome": h, "source": "demo"}
            for h in DEMO_HIPPODROMES
        ]

    def get_races(self, date: str) -> list[Race]:
        return [r for r in self._races.values() if r.date == date]

    def get_race(self, race_id: str) -> Race | None:
        return self._races.get(race_id)

    def get_runners(self, race_id: str) -> list[Runner]:
        race = self._races.get(race_id)
        return list(race.runners) if race else []

    def get_horse_history(self, horse_id: str) -> list[dict]:
        for race in self._races.values():
            for runner in race.runners:
                if runner.horse.key == horse_id:
                    return [
                        {
                            "date": r.date,
                            "finish_position": r.finish_position,
                            "distance": r.distance,
                            "hippodrome": r.hippodrome,
                            "jockey": r.jockey,
                            "trainer": r.trainer,
                            "odds": r.odds,
                        }
                        for r in runner.history
                    ]
        return []

    def get_jockey_history(self, jockey_id: str) -> list[dict]:
        return [{"jockey": jockey_id, "starts": 0, "demo": True}]

    def get_trainer_history(self, trainer_id: str) -> list[dict]:
        return [{"trainer": trainer_id, "starts": 0, "demo": True}]

    def get_odds(self, race_id: str) -> dict[int, list[dict]]:
        race = self._races.get(race_id)
        if not race:
            return {}
        return {
            r.number: [{"odds": p.odds, "timestamp": p.timestamp} for p in r.odds_history]
            for r in race.runners
        }

    def get_results(self, race_id: str) -> RaceResult | None:
        return self._results.get(race_id)

    def all_race_ids(self) -> list[str]:
        return list(self._races.keys())
