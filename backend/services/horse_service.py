#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service « chevaux ».

Traduit les lignes SQL en modèles d'API et calcule les seuls indicateurs
directement dérivables des données présentes. Un taux n'est publié que si son
dénominateur est connu (les positions nulles sont exclues).
"""

from __future__ import annotations

import sqlite3

from ..db.repositories import horse_repository as repo
from ..schemas.entities import HorseDetail, HorseRun, HorseStatistics, HorseSummary


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


def _to_summary(row: sqlite3.Row) -> HorseSummary:
    return HorseSummary(
        id=row["horse_id"],
        name=_clean_name(row["name_normalized"]),
        starts=_as_int(row["n_starts"]),
        firstSeenDate=row["first_seen_date"],
        lastSeenDate=row["last_seen_date"],
        sexBirthyearVariants=row["sex_birthyear_variants"],
        father=row["pedigree_pere"],
        mother=row["pedigree_mere"],
        coat=row["robe"],
        breed=row["race"],
        homonymRisk=row["homonym_risk"],
    )


def _to_run(row: sqlite3.Row) -> HorseRun:
    return HorseRun(
        raceId=row["race_id"],
        date=row["date"],
        hippodrome=row["hippodrome"],
        discipline=row["discipline"],
        distanceMeters=_as_int(row["distance_m"]),
        title=row["titre"],
        number=_as_int(row["numero"]),
        position=_as_int(row["result_position"]),
        odds=_as_float(row["cote_decimale"]),
    )


def search(query: str | None = None, limit: int = 50, offset: int = 0) -> list[HorseSummary]:
    """Recherche de chevaux par nom (insensible aux accents et à la casse)."""
    return [_to_summary(row) for row in repo.search_horses(query, limit, offset)]


def get(horse_id: str) -> HorseDetail | None:
    """Fiche complète d'un cheval : identité, statistiques réelles, dernières courses."""
    row = repo.get_horse(horse_id)
    if row is None:
        return None

    stats = repo.horse_statistics(horse_id)
    runs = [_to_run(r) for r in repo.horse_results(horse_id, limit=20)]

    return HorseDetail(
        horse=_to_summary(row),
        statistics=HorseStatistics(**stats),  # type: ignore[arg-type]
        recentRuns=runs,
    )


def count() -> int:
    """Nombre de chevaux référencés."""
    return repo.count_horses()
