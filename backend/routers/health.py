#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routeur « santé ».

Expose l'état du service et les métadonnées de la base réellement utilisée :
c'est le point de contrôle de l'auto-détection de la base.
"""

from __future__ import annotations

from fastapi import APIRouter

from ..config import HIPPO_ENGINE_DIR, database_path
from ..db.client import database_info
from ..services import prediction_service, statistics_service

router = APIRouter(tags=["santé"])


@router.get("/api/health")
def health() -> dict[str, object]:
    """État du service, base détectée et volumes disponibles."""
    info = database_info()
    coverage = statistics_service.coverage()
    return {
        "status": "online",
        "database": info["name"],
        "database_path": info["path"],
        "database_size_mb": info["size_mb"],
        "engine": {
            "enabled": prediction_service.engine_available(),
            "directory": str(HIPPO_ENGINE_DIR),
        },
        "coverage": coverage.model_dump(),
    }


@router.get("/api/health/database")
def health_database() -> dict[str, object]:
    """Chemin exact et volumétrie de la base exploitée."""
    path = database_path()
    return {
        **database_info(),
        "read_only": True,
        "resolved_from": "auto-détection (FASOTURF_DB → candidats connus → balayage du projet)",
    }
