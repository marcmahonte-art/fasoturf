#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schémas « statistiques ».

Chaque mesure publiée porte **sa méthode, sa période et son volume** : c'est
une exigence du moteur (règle « pas de surpromesse », spec §52).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Measure(BaseModel):
    """Mesure statistique accompagnée de son mode de calcul."""

    value: float | None = None
    numerator: int | None = None
    denominator: int | None = None
    unit: str = "ratio"
    method: str
    period: str | None = None
    volume: int = 0


class CoverageStats(BaseModel):
    """Volumes réellement présents dans la base."""

    races: int = 0
    exploitableRaces: int = 0
    racesWithResult: int = 0
    runners: int = 0
    horses: int = 0
    jockeys: int = 0
    trainers: int = 0
    hippodromes: int = 0
    oddsSnapshots: int = 0


class DisciplineStat(BaseModel):
    discipline: str
    races: int
    avgDistance: float | None = None


class HippodromeStat(BaseModel):
    hippodrome: str
    races: int
    days: int


class MonthStat(BaseModel):
    month: str
    races: int


class DataVersionItem(BaseModel):
    scope: str | None = None
    version: str | None = None
    sourceSha256: str | None = None
    createdAt: str | None = None
    notes: str | None = None


class StatisticsOverview(BaseModel):
    coverage: CoverageStats
    favouriteWinRate: Measure
    oddsCoverage: Measure
    resultCoverage: Measure
    byDiscipline: list[DisciplineStat] = Field(default_factory=list)
    byHippodrome: list[HippodromeStat] = Field(default_factory=list)
    monthlyActivity: list[MonthStat] = Field(default_factory=list)
    dataVersions: list[DataVersionItem] = Field(default_factory=list)
