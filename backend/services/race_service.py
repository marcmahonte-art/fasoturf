#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service « courses ».

Transforme les lignes SQL en modèles d'API et calcule les seuls champs qui
relèvent de la présentation (numérotation R/C, libellés, statut lisible).

Aucune valeur n'est inventée : lorsqu'une donnée est absente, le champ vaut
`None` et l'interface affiche « — ».
"""

from __future__ import annotations

import re
import sqlite3

from ..db.repositories import race_repository as repo
from ..schemas.race import MeteoOut, RaceOut, RaceSummary, RunnerOut

#: Préfixe numérique isolé en tête de titre : « 3 - NORVILLE : … ».
_TITLE_INDEX_PREFIX = re.compile(r"^\s*\d+\s*[-–—]\s*")

#: Accents graphiques cycliques (détail visuel, sans portée métier).
_ACCENTS = ("green", "gold", "red")

#: Mots de liaison qui restent en minuscules dans un titre français.
_SMALL_WORDS = {
    "de", "du", "des", "la", "le", "les", "l", "d", "et", "aux", "au",
    "en", "sur", "pour", "par", "a", "un", "une", "the", "of", "and",
}

_STATUS_LABELS = {
    "arrival_available": "Arrivée validée",
    "OFFICIAL": "Arrivée officielle",
    "SCHEDULED": "Programmée",
    "no_arrival_for_date": "Arrivée non publiée",
    "sentinel_date": "Date non renseignée",
}

#: Libellé affiché lorsqu'aucune source ne fournit le lieu de la course.
UNKNOWN_HIPPODROME = "Hippodrome non renseigné"


def _pretty(value: str) -> str:
    """Casse lisible pour un libellé : « PRIX DU MONT » → « Prix du Mont »."""
    words = []
    for index, word in enumerate(value.split()):
        lowered = word.lower()
        if index > 0 and lowered in _SMALL_WORDS:
            words.append(lowered)
        else:
            words.append(word[:1].upper() + word[1:].lower())
    return " ".join(words)


def _venue_from_title(titre: str | None) -> str | None:
    """
    Extrait le lieu d'une course depuis son titre.

    Deux formes coexistent en base :
      - « PARIS-VINCENNES - PRIX DU MONT SAINT MICHEL »      → avant « - »
      - « 3 - NORVILLE : Ce placé de Groupe 1 (…) »          → avant « : »

    Le préfixe numérique isolé (« 3 - ») est un index de réunion, pas un lieu.
    """
    if not titre:
        return None

    text = _TITLE_INDEX_PREFIX.sub("", titre.strip())
    head = text.split(":")[0].split(" - ")[0].strip()
    head = head.replace("-", " ").strip()

    # Garde-fous : un lieu est court et n'est jamais un nombre.
    if not head or head.isdigit() or len(head) > 26 or len(head.split()) > 3:
        return None
    return head


# --------------------------------------------------------------------------
# Normalisation d'affichage
# --------------------------------------------------------------------------


def clean_hippodrome(canonical: str | None, hippo_raw: str | None, titre: str | None) -> str:
    """
    Nom d'hippodrome lisible.

    Ordre de résolution : libellé canonique → libellé brut → titre de la course.
    Aucun lieu n'est **déduit** d'un autre champ (ni de la discipline, ni du
    nombre de partants) : si aucune source ne le fournit, la valeur affichée est
    explicitement « non renseigné ».
    """
    for candidate in (canonical, hippo_raw):
        raw = (candidate or "").strip()
        if raw and not raw.isdigit():
            return _normalise_venue(raw)

    from_title = _venue_from_title(titre)
    if from_title:
        return _normalise_venue(from_title)

    return UNKNOWN_HIPPODROME


def _normalise_venue(raw: str) -> str:
    """Orthographe d'affichage des hippodromes connus."""
    clean = _pretty(raw.replace("_", " ").strip())
    replacements = {
        "Paris Vincennes": "Paris-Vincennes",
        "Paris Longchamp": "ParisLongchamp",
        "Saint Cloud": "Saint-Cloud",
        "Deauville La Touques": "Deauville",
        "Deauville La Touques Nocturne": "Deauville",
    }
    return replacements.get(clean, clean)


def clean_discipline(disc: str | None, titre: str | None) -> str:
    """Discipline normalisée. Retourne « Non renseignée » si absente."""
    if disc:
        upper = disc.upper()
        if "ATTELE" in upper or "TROT" in upper:
            return "Trot Attelé"
        if "MONTE" in upper:
            return "Trot Monté"
        if "PLAT" in upper:
            return "Plat"
        if "OBSTACLE" in upper or "HAIES" in upper or "STEEPLE" in upper:
            return "Haies / Obstacle"
        return _pretty(disc)

    if titre:
        upper = titre.upper()
        if "ATTELE" in upper:
            return "Trot Attelé"
        if "MONTE" in upper:
            return "Trot Monté"
        if "STEEPLE" in upper or "HAIES" in upper or "OBSTACLE" in upper:
            return "Obstacle"
    return "Non renseignée"


def clean_title(titre: str | None) -> str:
    """
    Titre de course lisible.

    Deux formes en base :
      - « PARIS-VINCENNES - PRIX DU MONT SAINT MICHEL »  → après « - »
      - « 3 - NORVILLE : Ce placé de Groupe 1 (…) »      → après « : »
    """
    if not titre:
        return "Course sans titre"

    text = _TITLE_INDEX_PREFIX.sub("", titre.strip())

    head, separator, tail = text.partition(":")
    if separator and tail.strip():
        return _pretty(tail.strip())

    if " - " in text:
        parts = text.split(" - ")
        if len(parts) >= 2 and parts[1].strip():
            return _pretty(parts[1].strip())

    return _pretty(text) or "Course sans titre"


def format_distance(distance_m: int | None) -> str:
    """2700 → « 2 700 m ». Chaîne vide si la distance est inconnue."""
    if not distance_m:
        return ""
    return f"{distance_m:,} m".replace(",", " ")


def format_time(heure_depart: str | None) -> str:
    """
    Heure de départ réelle.

    `heure_depart` est stocké au format « HH:MM ». Aucune heure n'est
    fabriquée : si elle est absente, la chaîne retournée est vide.
    """
    if not heure_depart:
        return ""
    return heure_depart.strip()[:5]


def _parse_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    match = re.search(r"-?\d+", text)
    return int(match.group()) if match else None


def _music(performances_structured: str | None) -> str:
    """« [2, 2, 9] » → « 2, 2, 9 » (contrat historique de l'API publique)."""
    if not performances_structured:
        return ""
    return (
        performances_structured.replace('"', "").replace("[", "").replace("]", "").strip()
    )


def _status_label(result_status: str | None) -> str:
    if not result_status:
        return "Statut inconnu"
    return _STATUS_LABELS.get(result_status, result_status)


def _is_finished(result_status: str | None) -> bool:
    return result_status in ("arrival_available", "OFFICIAL")


# --------------------------------------------------------------------------
# Numérotation réunion / course
# --------------------------------------------------------------------------


def _assign_numbers(rows: list[sqlite3.Row]) -> dict[str, tuple[int, int]]:
    """
    Attribue à chaque course un couple (réunion, course).

    Les valeurs réellement présentes en base (`reunion_num`, `course_num`) sont
    conservées telles quelles ; les autres courses se voient attribuer le
    premier numéro libre de leur hippodrome pour la date considérée.
    """
    assignments: dict[str, tuple[int, int]] = {}

    # 1. Valeurs réelles
    for row in rows:
        reunion = _parse_int(row["reunion_num"])
        course = _parse_int(row["course_num"])
        if reunion is not None and course is not None:
            assignments[row["race_id"]] = (reunion, course)

    # 2. Complétion déterministe par hippodrome
    used: dict[str, set[int]] = {}
    course_used: dict[tuple[int, str], set[int]] = {}

    for race_id, (reunion, course) in assignments.items():
        row = next((r for r in rows if r["race_id"] == race_id), None)
        if row is None:
            continue
        hippo = clean_hippodrome(
            row["label_canonical"], row["hippodrome_label_raw"], row["titre"]
        )
        used.setdefault(hippo, set()).add(reunion)
        course_used.setdefault((reunion, hippo), set()).add(course)

    next_reunion: dict[str, int] = {}

    for row in rows:
        race_id = row["race_id"]
        if race_id in assignments:
            continue

        hippo = clean_hippodrome(
            row["label_canonical"], row["hippodrome_label_raw"], row["titre"]
        )
        taken = used.setdefault(hippo, set())

        reunion = next_reunion.get(hippo)
        if reunion is None or reunion in taken:
            candidate = 1
            while candidate in taken:
                candidate += 1
            reunion = candidate
        next_reunion[hippo] = reunion
        taken.add(reunion)

        courses = course_used.setdefault((reunion, hippo), set())
        course = 1
        while course in courses:
            course += 1
        courses.add(course)

        assignments[race_id] = (reunion, course)

    return assignments


# --------------------------------------------------------------------------
# Construction des modèles
# --------------------------------------------------------------------------


def _runner_to_model(row: sqlite3.Row) -> RunnerOut:
    age = _parse_int(row["f_age"])
    if age is None:
        age = _parse_int(row["age_raw"])

    position = _parse_int(row["result_position"])
    market_prob = row["m_prob_norm"]
    if market_prob is None:
        market_prob = row["m_implied"]

    return RunnerOut(
        number=_parse_int(row["numero"]) or 0,
        name=(row["horse_name"] or "Partant non identifié").title(),
        age=age,
        music=_music(row["performances_structured"]),
        jockey=(row["jockey_name"] or "").title(),
        trainer=(row["trainer_name"] or "").title(),
        odds=float(row["cote_decimale"]) if row["cote_decimale"] is not None else None,
        marketProb=round(float(market_prob) * 100, 1) if market_prob is not None else None,
        marketRank=_parse_int(row["m_rank"]),
        isWinner=position == 1,
        position=position,
    )


def _derive_arrival(runners: list[RunnerOut]) -> str | None:
    """Ordre d'arrivée déduit des positions réellement enregistrées."""
    placed = sorted(
        (r for r in runners if r.position is not None),
        key=lambda r: r.position or 0,
    )
    if not placed:
        return None
    return "-".join(str(r.number) for r in placed[:5])


def _to_race_out(row: sqlite3.Row, numbers: tuple[int, int], index: int) -> RaceOut:
    runners = [_runner_to_model(r) for r in repo.list_runners(row["race_id"])]
    runners.sort(key=lambda r: r.number)

    odds = [r.odds for r in runners if r.odds is not None and r.odds > 0]
    favorite = min(odds) if odds else 0.0

    arrivee_officielle = row["arrivee_officielle"]
    derived = _derive_arrival(runners)
    if arrivee_officielle:
        arrivee, source = arrivee_officielle, "lonab"
    elif derived:
        arrivee, source = derived, "positions"
    else:
        arrivee, source = None, None

    meteo = None
    if row["meteo_temperature"] is not None or row["meteo_nebulosite"]:
        meteo = MeteoOut(
            temperature=row["meteo_temperature"],
            nebulosite=row["meteo_nebulosite"],
            ventForce=row["meteo_vent_force"],
            ventDirection=row["meteo_vent_direction"],
        )

    return RaceOut(
        id=row["race_id"],
        date=row["date"],
        reunion=f"R{numbers[0]}",
        course=f"C{numbers[1]}",
        hippodrome=clean_hippodrome(
            row["label_canonical"], row["hippodrome_label_raw"], row["titre"]
        ),
        title=clean_title(row["titre"]),
        discipline=clean_discipline(row["discipline"], row["titre"]),
        distance=format_distance(row["distance_m"]),
        # Le terrain n'est pas exposé par les sources : jamais inventé.
        terrain=None,
        starters=len(runners) or int(row["n_runners_linked"] or 0),
        time=format_time(row["heure_depart"]),
        status=_status_label(row["result_status"]),
        hasResult=bool(arrivee),
        favoriteOdds=round(favorite, 1),
        accent=_ACCENTS[index % len(_ACCENTS)],
        runners=runners,
        meteo=meteo,
        isLonab=bool(row["is_lonab"]),
        lonabBet=row["lonab_bet"],
        lonabJournalBet=row["lonab_journal_bet"],
        lonabJournalVenue=row["lonab_journal_venue"],
        arrivee=arrivee,
        arriveeSource=source,
        quinteDividende=row["quinte_dividende"],
        quinteGagnants=row["nb_gagnants_quinte"],
    )


def _resolve_bet_type(row: sqlite3.Row) -> str | None:
    """Type de pari issu de la donnée LONAB — jamais déduit du nombre de partants."""
    journal = (row["lonab_journal_bet"] or "").upper()
    if "QUARTE" in journal:
        return "Quarté+"
    if "TIERCE" in journal:
        return "Tiercé"
    if "4+1" in journal or "5+1" in journal:
        return "Quinté+"

    declared = (row["lonab_bet"] or "").strip()
    if declared:
        return declared.split("/")[0].strip() or None
    return None


def _to_summary(row: sqlite3.Row, numbers: tuple[int, int]) -> RaceSummary:
    from ..config import ORIGIN_REAL

    return RaceSummary(
        id=row["race_id"],
        meetingNumber=numbers[0],
        raceNumber=numbers[1],
        hippodrome=clean_hippodrome(
            row["label_canonical"], row["hippodrome_label_raw"], row["titre"]
        ),
        participantCount=int(row["n_runners_linked"] or 0),
        distanceMeters=int(row["distance_m"] or 0),
        startTime=format_time(row["heure_depart"]),
        betType=_resolve_bet_type(row),
        discipline=clean_discipline(row["discipline"], row["titre"]),
        imageUrl=None,
        status="finished" if _is_finished(row["result_status"]) else "upcoming",
        date=row["date"],
        isLonab=bool(row["is_lonab"]),
        origin=ORIGIN_REAL,
    )


# --------------------------------------------------------------------------
# API du service
# --------------------------------------------------------------------------


def list_races(
    *,
    date: str | None = None,
    hippodrome: str | None = None,
    discipline: str | None = None,
    only_lonab: bool = False,
    limit: int = 25,
    offset: int = 0,
) -> list[RaceOut]:
    """Liste détaillée des courses (partants inclus)."""
    rows = repo.list_races(
        date=date,
        hippodrome=hippodrome,
        discipline=discipline,
        only_lonab=only_lonab,
        limit=limit,
        offset=offset,
    )
    numbers = _assign_numbers(rows)
    return [
        _to_race_out(row, numbers[row["race_id"]], index)
        for index, row in enumerate(rows)
    ]


def list_race_summaries(
    *,
    date: str | None = None,
    hippodrome: str | None = None,
    discipline: str | None = None,
    only_lonab: bool = False,
    analysable: bool = False,
    limit: int = 25,
    offset: int = 0,
) -> list[RaceSummary]:
    """Vue légère des courses (sans partants), filtrable."""
    rows = repo.list_races(
        date=date,
        hippodrome=hippodrome,
        discipline=discipline,
        only_lonab=only_lonab,
        analysable=analysable,
        limit=limit,
        offset=offset,
    )
    numbers = _assign_numbers(rows)
    return [_to_summary(row, numbers[row["race_id"]]) for row in rows]


def get_race(race_id: str) -> RaceOut | None:
    """Détail d'une course."""
    row = repo.get_race(race_id)
    if row is None:
        return None
    numbers = _assign_numbers([row])
    return _to_race_out(row, numbers[race_id], 0)


def get_race_by_document_id(document_id: int) -> RaceOut | None:
    """Détail d'une course à partir de son identifiant de document source."""
    row = repo.get_race_by_document_id(document_id)
    if row is None:
        return None
    numbers = _assign_numbers([row])
    return _to_race_out(row, numbers[row["race_id"]], 0)


_MONTHS_SHORT_FR = {
    "01": "Janv", "02": "Févr", "03": "Mars", "04": "Avr", "05": "Mai", "06": "Juin",
    "07": "Juil", "08": "Août", "09": "Sept", "10": "Oct", "11": "Nov", "12": "Déc",
}


def list_dates(limit: int = 30, today: str | None = None) -> list[dict[str, object]]:
    """Dates disponibles, avec libellé français et marqueur « aujourd'hui »."""
    import datetime

    today_str = today or datetime.date.today().strftime("%Y-%m-%d")
    result = []
    for row in repo.list_dates(limit):
        date = row["date"]
        parts = date.split("-")
        is_today = date == today_str
        if len(parts) == 3:
            label = "Aujourd'hui" if is_today else f"{parts[2]} {_MONTHS_SHORT_FR.get(parts[1], parts[1])}"
        else:
            label = date
        result.append(
            {"date": date, "label": label, "count": int(row["n_races"] or 0), "isToday": is_today}
        )
    return result


def resolve_target_date(today: str | None = None) -> str | None:
    """
    Date de travail du Dashboard.

    On privilégie la date du jour si des courses y sont exploitables ; sinon la
    date future la plus proche ; sinon la date la plus récente disponible.
    """
    import datetime

    from ..db.client import query_scalar

    today_str = today or datetime.date.today().strftime("%Y-%m-%d")

    if repo.count_races_for_date(today_str) > 0:
        return today_str

    upcoming = query_scalar(
        """
        SELECT min(date) FROM master_race
        WHERE date > ? AND n_runners_linked >= 8 AND COALESCE(date_is_sentinel, 0) = 0
        """,
        (today_str,),
    )
    if upcoming:
        return str(upcoming)

    return repo.latest_date()
