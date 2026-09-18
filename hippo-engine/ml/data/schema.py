"""
Schéma interne normalisé (#6).

Format interne unique, quel que soit le fournisseur :

    runner.horse.name

Les dataclasses ci-dessous sont la **seule** représentation acceptée par le
moteur. Aucune donnée externe n'entre sans passer par ``validate_*``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date
from typing import Any, Literal

Source = Literal["real", "demo"]
Confidence = Literal["HIGH", "MEDIUM", "LOW"]
DataQuality = Literal["DATA_COMPLETE", "DATA_PARTIAL", "DATA_INSUFFICIENT"]

VALID_DISCIPLINES = {"PLAT", "ATTELE", "MONTE", "OBSTACLE", "HAIES", "STEEPLE", ""}


class ValidationError(ValueError):
    """Levée quand une donnée externe est invalide."""


def _clean_str(value: Any, *, upper: bool = False, max_len: int = 200) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = " ".join(text.split())
    if upper:
        text = text.upper()
    return text[:max_len]


def _as_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------
# Entités
# ---------------------------------------------------------------

@dataclass(slots=True)
class Horse:
    name: str
    external_id: str | None = None
    sex: str = ""
    age: int | None = None
    country: str = ""
    source: Source = "real"

    @property
    def key(self) -> str:
        return self.external_id or self.name.upper()


@dataclass(slots=True)
class Person:
    """Jockey ou entraîneur."""
    name: str
    external_id: str | None = None
    source: Source = "real"


@dataclass(slots=True)
class OddsPoint:
    odds: float
    timestamp: str = ""
    source: str = "pmu"


@dataclass(slots=True)
class Runner:
    number: int
    horse: Horse
    jockey: Person | None = None
    trainer: Person | None = None
    draw: int | None = None
    weight: float | None = None
    official_rating: float | None = None
    morning_odds: float | None = None
    current_odds: float | None = None
    final_odds: float | None = None
    odds_history: list[OddsPoint] = field(default_factory=list)
    status: Literal["declared", "non_runner", "withdrawn"] = "declared"
    # Features historiques pré-calculées (remplies par le provider).
    history: list["HistoricalRun"] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        return self.status == "declared"


@dataclass(slots=True)
class HistoricalRun:
    """Une sortie passée. ``finish_position`` est une donnée POST-course."""
    date: str
    finish_position: int | None = None
    distance: int | None = None
    terrain: str = ""
    hippodrome: str = ""
    weight: float | None = None
    draw: int | None = None
    official_rating: float | None = None
    jockey: str = ""
    trainer: str = ""
    odds: float | None = None


@dataclass(slots=True)
class Race:
    date: str
    hippodrome: str
    external_id: str | None = None
    start_time: str = ""
    country: str = "FR"
    discipline: str = ""
    race_type: str = ""
    distance: int | None = None
    terrain: str = ""
    prize: float | None = None
    number_of_runners: int | None = None
    status: str = "scheduled"
    runners: list[Runner] = field(default_factory=list)
    source: Source = "real"

    @property
    def key(self) -> str:
        return self.external_id or f"{self.date}-{self.hippodrome}-{self.start_time}"

    @property
    def active_runners(self) -> list[Runner]:
        return [r for r in self.runners if r.is_active]


@dataclass(slots=True)
class RaceResult:
    race_id: str
    finish_order: list[int] = field(default_factory=list)
    official: bool = True


# ---------------------------------------------------------------
# Validation (#6) — aucune donnée externe sans passer ici
# ---------------------------------------------------------------

def validate_horse(raw: dict[str, Any]) -> Horse:
    name = _clean_str(raw.get("name") or raw.get("nom") or raw.get("horse_name"), upper=True)
    if not name:
        raise ValidationError("Cheval sans nom")
    return Horse(
        name=name,
        external_id=_clean_str(raw.get("external_id") or raw.get("id")) or None,
        sex=_clean_str(raw.get("sex") or raw.get("sexe"), upper=True)[:1],
        age=_as_int(raw.get("age")),
        country=_clean_str(raw.get("country") or raw.get("pays"), upper=True)[:3],
        source="demo" if raw.get("source") == "demo" else "real",
    )


def validate_person(raw: dict[str, Any] | str | None) -> Person | None:
    if not raw:
        return None
    if isinstance(raw, str):
        name = _clean_str(raw, upper=True)
        return Person(name=name) if name else None
    name = _clean_str(raw.get("name") or raw.get("nom"), upper=True)
    if not name:
        return None
    return Person(
        name=name,
        external_id=_clean_str(raw.get("external_id") or raw.get("id")) or None,
        source="demo" if raw.get("source") == "demo" else "real",
    )


def validate_runner(raw: dict[str, Any] | "Runner") -> Runner:
    if isinstance(raw, Runner):
        return raw
    number = _as_int(raw.get("number") or raw.get("numero"))
    if number is None:
        raise ValidationError("Partant sans numéro")
    horse_raw = raw.get("horse") or raw
    runner = Runner(
        number=number,
        horse=validate_horse(horse_raw),
        jockey=validate_person(raw.get("jockey") or raw.get("driver")),
        trainer=validate_person(raw.get("trainer") or raw.get("entraineur")),
        draw=_as_int(raw.get("draw") or raw.get("corde")),
        weight=_as_float(raw.get("weight") or raw.get("poids")),
        official_rating=_as_float(raw.get("official_rating") or raw.get("valeur")),
        morning_odds=_as_float(raw.get("morning_odds")),
        current_odds=_as_float(raw.get("current_odds") or raw.get("cote") or raw.get("cote_decimale")),
        final_odds=_as_float(raw.get("final_odds")),
        status=raw.get("status") or ("non_runner" if raw.get("non_partant") else "declared"),
    )
    return runner


def validate_race(raw: dict[str, Any]) -> Race:
    hippodrome = _clean_str(raw.get("hippodrome") or raw.get("track"), upper=True)
    race_date = _clean_str(raw.get("date"))
    if not hippodrome:
        raise ValidationError("Course sans hippodrome")
    if not race_date:
        raise ValidationError("Course sans date")
    discipline = _clean_str(raw.get("discipline"), upper=True)
    if discipline not in VALID_DISCIPLINES:
        discipline = discipline[:20]
    runners = [r if isinstance(r, Runner) else validate_runner(r) for r in raw.get("runners", [])]
    return Race(
        date=race_date,
        hippodrome=hippodrome,
        external_id=_clean_str(raw.get("external_id") or raw.get("id")) or None,
        start_time=_clean_str(raw.get("start_time") or raw.get("heure_depart"))[:5],
        country=_clean_str(raw.get("country") or raw.get("pays"), upper=True)[:3] or "FR",
        discipline=discipline,
        race_type=_clean_str(raw.get("race_type") or raw.get("type_course"), upper=True),
        distance=_as_int(raw.get("distance") or raw.get("distance_m")),
        terrain=_clean_str(raw.get("terrain"), upper=True),
        prize=_as_float(raw.get("prize") or raw.get("montant_euros")),
        number_of_runners=_as_int(raw.get("number_of_runners")) or (len(runners) or None),
        status=raw.get("status") or "scheduled",
        runners=runners,
        source="demo" if raw.get("source") == "demo" else "real",
    )


def validate_result(raw: dict[str, Any]) -> RaceResult:
    order = raw.get("finish_order") or raw.get("arrivee") or []
    clean: list[int] = []
    for item in order:
        value = _as_int(item)
        if value is not None:
            clean.append(value)
    return RaceResult(
        race_id=_clean_str(raw.get("race_id")),
        finish_order=clean,
        official=bool(raw.get("official", True)),
    )
