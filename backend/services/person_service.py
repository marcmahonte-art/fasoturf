#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service « personnes » (jockeys et entraîneurs).

Le rôle est stocké en **casse mixte** dans la base (`jockey` / `JOCKEY`,
`trainer` / `TRAINER`) : toutes les requêtes passent par `lower(role)`.
"""

from __future__ import annotations

import sqlite3

from ..db.repositories import person_repository as repo
from ..schemas.entities import PersonDetail, PersonRun, PersonStatistics, PersonSummary

#: Rôles exposés par l'API.
ROLES = (repo.ROLE_JOCKEY, repo.ROLE_TRAINER)


def _as_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_name(value: object) -> str:
    text = str(value or "").strip()
    return text.title() if text else "Nom non renseigné"


def normalise_role(role: str | None) -> str | None:
    """Retourne un rôle valide, ou None si le rôle est inconnu."""
    if not role:
        return None
    lowered = role.strip().lower()
    return lowered if lowered in ROLES else None


def _to_summary(row: sqlite3.Row) -> PersonSummary:
    return PersonSummary(
        id=row["person_id"],
        name=_clean_name(row["name_normalized"]),
        role=str(row["role"] or "").lower(),
        appearances=_as_int(row["n_appearances"]),
        resolutionConfidence=_as_float(row["resolution_confidence"]),
    )


def _to_run(row: sqlite3.Row) -> PersonRun:
    horse = row["horse_name"]
    return PersonRun(
        raceId=row["race_id"],
        date=row["date"],
        hippodrome=row["hippodrome"],
        discipline=row["discipline"],
        distanceMeters=_as_int(row["distance_m"]),
        title=row["titre"],
        horseName=_clean_name(horse) if horse else None,
        number=_as_int(row["numero"]),
        position=_as_int(row["result_position"]),
        odds=_as_float(row["cote_decimale"]),
    )


def search(
    role: str | None = None,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[PersonSummary]:
    """Recherche de jockeys ou d'entraîneurs."""
    return [
        _to_summary(row)
        for row in repo.search_persons(normalise_role(role), query, limit, offset)
    ]


def get(person_id: str) -> PersonDetail | None:
    """Fiche complète d'une personne : identité, statistiques réelles, dernières courses."""
    row = repo.get_person(person_id)
    if row is None:
        return None

    role = normalise_role(str(row["role"] or "")) or repo.ROLE_JOCKEY
    stats = repo.person_statistics(person_id, role)
    runs = [_to_run(r) for r in repo.person_recent_races(person_id, role, limit=15)]

    return PersonDetail(
        person=_to_summary(row),
        statistics=PersonStatistics(**stats),  # type: ignore[arg-type]
        recentRuns=runs,
    )


def count(role: str | None = None) -> int:
    """Nombre de personnes référencées, éventuellement filtrées par rôle."""
    return repo.count_persons(normalise_role(role))
