#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Routeur « hippodromes »."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..schemas.entities import HippodromeDetail, HippodromeSummary
from ..services import hippodrome_service

router = APIRouter(tags=["hippodromes"])


@router.get("/api/hippodromes", response_model=list[HippodromeSummary])
def list_hippodromes(
    limit: int = Query(200, ge=1, le=500),
) -> list[HippodromeSummary]:
    """Hippodromes référencés, du plus actif au moins actif."""
    return hippodrome_service.list_all(limit=limit)


@router.get("/api/hippodromes/count")
def count_hippodromes() -> dict[str, int]:
    """Nombre d'hippodromes référencés."""
    return {"count": hippodrome_service.count()}


@router.get("/api/hippodromes/{hippodrome_id}", response_model=HippodromeDetail)
def get_hippodrome(hippodrome_id: str) -> HippodromeDetail:
    """Fiche d'un hippodrome et statistiques de ses courses."""
    detail = hippodrome_service.get(hippodrome_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Hippodrome introuvable")
    return detail
