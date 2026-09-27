#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routeur « statistiques ».

Chaque mesure publiée porte sa méthode, sa période et son volume : aucune
statistique n'est présentée sans son mode de calcul.
"""

from __future__ import annotations

from fastapi import APIRouter

from ..schemas.statistics import (
    CoverageStats,
    DisciplineStat,
    HippodromeStat,
    Measure,
    MonthStat,
    StatisticsOverview,
)
from ..services import statistics_service

router = APIRouter(tags=["statistiques"])


@router.get("/api/statistics", response_model=StatisticsOverview)
def get_statistics() -> StatisticsOverview:
    """Vue complète des statistiques réellement disponibles."""
    return statistics_service.overview()


@router.get("/api/statistics/coverage", response_model=CoverageStats)
def get_coverage() -> CoverageStats:
    """Volumes disponibles dans la base."""
    return statistics_service.coverage()


@router.get("/api/statistics/favourite", response_model=Measure)
def get_favourite_win_rate() -> Measure:
    """
    Taux de victoire du favori du marché.

    Mesure de référence — ce n'est **pas** une promesse de gain.
    """
    return statistics_service.favourite_win_rate()


@router.get("/api/statistics/disciplines", response_model=list[DisciplineStat])
def get_disciplines() -> list[DisciplineStat]:
    """Répartition des courses par discipline."""
    return statistics_service.by_discipline()


@router.get("/api/statistics/hippodromes", response_model=list[HippodromeStat])
def get_hippodromes() -> list[HippodromeStat]:
    """Hippodromes les plus actifs."""
    return statistics_service.by_hippodrome()


@router.get("/api/statistics/months", response_model=list[MonthStat])
def get_months() -> list[MonthStat]:
    """Activité mensuelle."""
    return statistics_service.monthly_activity()
