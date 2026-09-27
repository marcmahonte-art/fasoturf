#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Routeur « chevaux »."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..schemas.entities import HorseDetail, HorseSummary
from ..services import horse_service

router = APIRouter(tags=["chevaux"])


@router.get("/api/horses", response_model=list[HorseSummary])
def search_horses(
    q: str | None = Query(None, description="Recherche par nom (accents ignorés)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[HorseSummary]:
    """Recherche de chevaux référencés."""
    return horse_service.search(q, limit=limit, offset=offset)


@router.get("/api/horses/count")
def count_horses() -> dict[str, int]:
    """Nombre de chevaux référencés."""
    return {"count": horse_service.count()}


@router.get("/api/horses/{horse_id}", response_model=HorseDetail)
def get_horse(horse_id: str) -> HorseDetail:
    """Fiche d'un cheval : identité, statistiques réelles, dernières courses."""
    detail = horse_service.get(horse_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Cheval introuvable")
    return detail
