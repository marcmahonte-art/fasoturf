#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routeur « personnes » (jockeys et entraîneurs).

Deux familles d'URLs sont exposées : `/api/jockeys` et `/api/trainers`, qui
partagent le même service avec un rôle fixé.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..schemas.entities import PersonDetail, PersonSummary
from ..services import person_service

router = APIRouter(tags=["personnes"])


@router.get("/api/jockeys", response_model=list[PersonSummary])
def search_jockeys(
    q: str | None = Query(None, description="Recherche par nom"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[PersonSummary]:
    """Recherche de jockeys."""
    return person_service.search("jockey", q, limit=limit, offset=offset)


@router.get("/api/jockeys/count")
def count_jockeys() -> dict[str, int]:
    """Nombre de jockeys référencés."""
    return {"count": person_service.count("jockey")}


@router.get("/api/jockeys/{person_id}", response_model=PersonDetail)
def get_jockey(person_id: str) -> PersonDetail:
    """Fiche d'un jockey."""
    detail = person_service.get(person_id)
    if detail is None or detail.person.role != "jockey":
        raise HTTPException(status_code=404, detail="Jockey introuvable")
    return detail


@router.get("/api/trainers", response_model=list[PersonSummary])
def search_trainers(
    q: str | None = Query(None, description="Recherche par nom"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[PersonSummary]:
    """Recherche d'entraîneurs."""
    return person_service.search("trainer", q, limit=limit, offset=offset)


@router.get("/api/trainers/count")
def count_trainers() -> dict[str, int]:
    """Nombre d'entraîneurs référencés."""
    return {"count": person_service.count("trainer")}


@router.get("/api/trainers/{person_id}", response_model=PersonDetail)
def get_trainer(person_id: str) -> PersonDetail:
    """Fiche d'un entraîneur."""
    detail = person_service.get(person_id)
    if detail is None or detail.person.role != "trainer":
        raise HTTPException(status_code=404, detail="Entraîneur introuvable")
    return detail
