#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schémas « courses ».

`RaceOut` conserve **exactement** le contrat historique consommé par la page
publique (`/api/races`) ; les champs ajoutés en fin de modèle sont additifs et
exposent la donnée réelle du socle (météo, marquage LONAB, arrivée officielle).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import DataOrigin, RaceStatus


class MeteoOut(BaseModel):
    temperature: float | None = None
    nebulosite: str | None = None
    ventForce: float | None = None
    ventDirection: str | None = None


class RunnerOut(BaseModel):
    number: int
    name: str
    age: int | None = None
    music: str = ""
    jockey: str = ""
    trainer: str = ""
    odds: float | None = None
    marketProb: float | None = None
    marketRank: int | None = None
    isWinner: bool = False
    position: int | None = None


class RaceOut(BaseModel):
    """Contrat historique de /api/races (inchangé)."""

    id: str
    date: str
    reunion: str
    course: str
    hippodrome: str
    title: str
    discipline: str
    distance: str
    terrain: str | None = None
    starters: int
    time: str
    status: str
    hasResult: bool
    favoriteOdds: float
    accent: str
    runners: list[RunnerOut] = Field(default_factory=list)

    # --- Champs réels additionnels ---
    meteo: MeteoOut | None = None
    isLonab: bool = False
    lonabBet: str | None = None
    lonabJournalBet: str | None = None
    lonabJournalVenue: str | None = None
    arrivee: str | None = None
    arriveeSource: str | None = None
    quinteDividende: float | None = None
    quinteGagnants: float | None = None


class RaceSummary(BaseModel):
    """Vue légère utilisée par le Dashboard (sans partants)."""

    id: str
    meetingNumber: int
    raceNumber: int
    hippodrome: str
    participantCount: int
    distanceMeters: int
    startTime: str
    betType: str | None = None
    discipline: str | None = None
    imageUrl: str | None = None
    status: RaceStatus
    date: str
    isLonab: bool = False
    origin: DataOrigin = "real"


class DateItem(BaseModel):
    date: str
    label: str
    count: int
    isToday: bool
