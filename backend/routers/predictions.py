#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routeur « pronostics ».

Les probabilités proviennent **exclusivement** du moteur Hippo Engine. Lorsque
celui-ci est indisponible, la réponse est explicite (`available: false` + raison)
et jamais remplacée par une estimation.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..config import DASHBOARD_PREDICTION_BUDGET_S
from ..schemas.prediction import PredictionUnavailable, RacePrediction
from ..services import prediction_service

router = APIRouter(tags=["pronostics"])


@router.get("/api/predictions/featured", response_model=None)
def featured_predictions(
    date: str | None = Query(None, description="Journée à considérer (AAAA-MM-JJ)"),
    limit: int = Query(10, ge=1, le=30, description="Nombre de partants à retourner"),
) -> dict[str, object]:
    """
    Pronostics mis en avant pour une journée.

    Réponse toujours de la même forme : `raceId`, `context`, `predictions`,
    `unavailableReason`. Les deux derniers sont mutuellement exclusifs — un
    pronostic, ou la raison de son absence. Jamais de liste inventée.
    """
    race_id, context, predictions, reason = prediction_service.featured_predictions(
        date, limit=limit, timeout_s=DASHBOARD_PREDICTION_BUDGET_S
    )
    return {
        "raceId": race_id,
        "context": context,
        "predictions": [item.model_dump() for item in predictions],
        "unavailableReason": reason,
    }


@router.get("/api/predictions/race/{race_id}")
def predict_race(
    race_id: str,
    limit: int | None = Query(None, ge=1, le=30, description="Limiter le nombre de partants"),
    refresh: bool = Query(False, description="Ignorer le cache et relancer le moteur"),
) -> RacePrediction | PredictionUnavailable:
    """Pronostic complet d'une course."""
    result = prediction_service.predict_race_by_race_id(race_id, limit=limit, refresh=refresh)
    if result is None:
        raise HTTPException(status_code=404, detail="Course introuvable")
    return result


@router.get("/api/predictions/document/{document_id}")
def predict_document(
    document_id: int,
    limit: int | None = Query(None, ge=1, le=30),
    refresh: bool = Query(False, description="Ignorer le cache et relancer le moteur"),
) -> RacePrediction | PredictionUnavailable:
    """Pronostic à partir de l'identifiant de document source."""
    return prediction_service.predict_race(document_id, limit=limit, refresh=refresh)


@router.get("/api/predictions/status")
def engine_status() -> dict[str, object]:
    """Disponibilité du moteur de pronostics."""
    available = prediction_service.engine_available()
    return {
        "available": available,
        "reason": None
        if available
        else "Moteur Hippo Engine désactivé ou introuvable sur le disque.",
    }


@router.post("/api/predictions/cache/invalidate")
def invalidate_cache(
    document_id: str | None = Query(None, description="Vider uniquement cette course"),
) -> dict[str, object]:
    """Vide le cache de pronostics (action explicite de l'utilisateur)."""
    prediction_service.invalidate_cache(document_id)
    return {"invalidated": True, "documentId": document_id}
