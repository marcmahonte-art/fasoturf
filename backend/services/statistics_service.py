#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service « statistiques ».

Chaque mesure publiée porte **sa méthode, sa période et son volume** : c'est une
exigence du moteur (règle « pas de surpromesse », spec §52). Une mesure dont le
dénominateur est nul n'est jamais convertie en 0 % — elle reste `None`.
"""

from __future__ import annotations

import sqlite3

from ..db.repositories import statistics_repository as repo
from ..schemas.statistics import (
    CoverageStats,
    DataVersionItem,
    DisciplineStat,
    HippodromeStat,
    Measure,
    MonthStat,
    StatisticsOverview,
)

#: Période couverte par les mesures globales (toute la base disponible).
PERIOD_ALL = "ensemble de la base disponible"


def _ratio(value: object) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None


def coverage() -> CoverageStats:
    """Volumes réellement présents dans la base."""
    raw = repo.overview()
    return CoverageStats(
        races=int(raw.get("races") or 0),
        exploitableRaces=int(raw.get("exploitableRaces") or 0),
        racesWithResult=int(raw.get("racesWithResult") or 0),
        runners=int(raw.get("runners") or 0),
        horses=int(raw.get("horses") or 0),
        jockeys=int(raw.get("jockeys") or 0),
        trainers=int(raw.get("trainers") or 0),
        hippodromes=int(raw.get("hippodromes") or 0),
        oddsSnapshots=int(raw.get("oddsSnapshots") or 0),
    )


def favourite_win_rate() -> Measure:
    """
    Taux de victoire du favori du marché.

    Mesure de **référence** : elle sert de point de comparaison, jamais de
    promesse de gain.
    """
    raw = repo.favourite_win_rate()
    favourites = int(raw.get("favourites") or 0)
    wins = int(raw.get("wins") or 0)
    return Measure(
        value=_ratio(raw.get("rate")),
        numerator=wins,
        denominator=favourites,
        unit="ratio",
        method="Victoires du favori du marché divisées par le nombre de favoris observés "
               "(partants dont la position d'arrivée est connue).",
        period=PERIOD_ALL,
        volume=favourites,
    )


def odds_coverage() -> Measure:
    """Part des partants disposant réellement d'une cote."""
    raw = repo.odds_coverage()
    runners = int(raw.get("runners") or 0)
    with_odds = int(raw.get("withOdds") or 0)
    return Measure(
        value=_ratio(raw.get("coverage")),
        numerator=with_odds,
        denominator=runners,
        unit="ratio",
        method="Partants dont la cote décimale est renseignée, sur l'ensemble des partants.",
        period=PERIOD_ALL,
        volume=runners,
    )


def result_coverage() -> Measure:
    """Part des courses disposant d'une arrivée exploitable."""
    raw = repo.result_coverage()
    races = int(raw.get("races") or 0)
    with_result = int(raw.get("withResult") or 0)
    return Measure(
        value=_ratio(raw.get("coverage")),
        numerator=with_result,
        denominator=races,
        unit="ratio",
        method="Courses dont le statut de résultat est « arrivée disponible » ou « officielle ».",
        period=PERIOD_ALL,
        volume=races,
    )


def by_discipline(limit: int = 10) -> list[DisciplineStat]:
    """Répartition des courses par discipline."""
    return [DisciplineStat(**item) for item in repo.by_discipline(limit)]  # type: ignore[arg-type]


def by_hippodrome(limit: int = 10) -> list[HippodromeStat]:
    """Hippodromes les plus actifs."""
    return [HippodromeStat(**item) for item in repo.by_hippodrome(limit)]  # type: ignore[arg-type]


def monthly_activity(limit: int = 12) -> list[MonthStat]:
    """Nombre de courses par mois."""
    return [MonthStat(**item) for item in repo.monthly_activity(limit)]  # type: ignore[arg-type]


def _to_version(row: sqlite3.Row) -> DataVersionItem:
    return DataVersionItem(
        scope=row["scope"],
        version=row["version"],
        sourceSha256=row["source_sha256"],
        createdAt=row["created_at"],
        notes=row["notes"],
    )


def data_versions() -> list[DataVersionItem]:
    """Versions de données enregistrées (traçabilité du socle)."""
    return [_to_version(row) for row in repo.data_versions()]


def overview() -> StatisticsOverview:
    """Vue complète des statistiques disponibles."""
    return StatisticsOverview(
        coverage=coverage(),
        favouriteWinRate=favourite_win_rate(),
        oddsCoverage=odds_coverage(),
        resultCoverage=result_coverage(),
        byDiscipline=by_discipline(),
        byHippodrome=by_hippodrome(),
        monthlyActivity=monthly_activity(),
        dataVersions=data_versions(),
    )
