#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Routeur « Dashboard ».

Un seul appel agrégé alimente la page `/dashboard` : le frontend ne compose
jamais lui-même plusieurs endpoints pour afficher un bloc.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from ..schemas.dashboard import DashboardResponse
from ..services import dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard(
    date: str | None = Query(
        None, description="Forcer une journée (AAAA-MM-JJ) ; sinon résolue par le backend"
    ),
) -> DashboardResponse:
    """
    Charge utile complète du Dashboard.

    Chaque bloc porte son origine. Les blocs qui dépendent d'un compte
    utilisateur (abonnement, notifications, performances personnelles) sont
    déclarés indisponibles avec leur raison.
    """
    return dashboard_service.build_dashboard(date)
