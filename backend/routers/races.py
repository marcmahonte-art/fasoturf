#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routeur « courses ».

Le contrat de `/api/races` est **inchangé** par rapport à la version historique :
la page publique qui le consomme continue de fonctionner à l'identique.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..schemas.race import DateItem, RaceOut, RaceSummary
from ..services import race_service

router = APIRouter(tags=["courses"])


# NOTE : `/api/races/today` doit être déclaré AVANT `/api/races/{race_id}`,
# sinon « today » serait interprété comme un identifiant de course.


@router.get("/api/races/today", response_model=list[RaceOut])
def today_races(limit: int = Query(50, ge=1, le=100)) -> list[RaceOut]:
    """Courses de la journée de travail (jour même, sinon journée la plus récente)."""
    target = race_service.resolve_target_date()
    if not target:
        return []
    return race_service.list_races(date=target, limit=limit)


@router.get("/api/races", response_model=list[RaceOut])
def list_races(
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
    date: str | None = Query(None, description="Filtrer par date (AAAA-MM-JJ)"),
    hippodrome: str | None = Query(None, description="Libellé d'hippodrome"),
    discipline: str | None = Query(None, description="Discipline exacte"),
    only_lonab: bool = Query(False, description="Ne garder que les courses couvertes par LONAB"),
) -> list[RaceOut]:
    """Liste détaillée des courses (partants inclus)."""
    return race_service.list_races(
        date=date,
        hippodrome=hippodrome,
        discipline=discipline,
        only_lonab=only_lonab,
        limit=limit,
        offset=offset,
    )


@router.get("/api/races/summary", response_model=list[RaceSummary])
def list_race_summaries(
    limit: int = Query(25, ge=1, le=200),
    offset: int = Query(0, ge=0),
    date: str | None = Query(None, description="Filtrer par date (AAAA-MM-JJ)"),
    hippodrome: str | None = Query(None, description="Libellé d'hippodrome"),
    discipline: str | None = Query(None, description="Discipline exacte"),
    only_lonab: bool = Query(False, description="Ne garder que les courses couvertes par LONAB"),
    analysable: bool = Query(
        False,
        description="Ne garder que les courses rattachées à un document source (analysables par le moteur)",
    ),
) -> list[RaceSummary]:
    """Vue légère des courses, sans partants."""
    return race_service.list_race_summaries(
        date=date,
        hippodrome=hippodrome,
        discipline=discipline,
        only_lonab=only_lonab,
        analysable=analysable,
        limit=limit,
        offset=offset,
    )


@router.get("/api/dates", response_model=list[DateItem])
def list_dates(limit: int = Query(30, ge=1, le=120)) -> list[DateItem]:
    """Dates de courses disponibles, avec libellé français."""
    return [DateItem(**item) for item in race_service.list_dates(limit)]


@router.get("/api/disciplines", response_model=list[str])
def list_disciplines() -> list[str]:
    """Disciplines réellement présentes en base."""
    from ..db.repositories import race_repository

    return race_repository.list_disciplines()


@router.get("/api/races/{race_id}", response_model=RaceOut)
def get_race(race_id: str) -> RaceOut:
    """Détail d'une course."""
    race = race_service.get_race(race_id)
    if race is None:
        raise HTTPException(status_code=404, detail="Course introuvable")
    return race
