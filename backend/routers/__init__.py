#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agrégation des routeurs de l'API.

`main.py` ne monte qu'un seul routeur : l'ordre de déclaration est celui de la
liste ci-dessous.
"""

from __future__ import annotations

from fastapi import APIRouter

from . import (
    dashboard,
    health,
    hippodromes,
    horses,
    persons,
    predictions,
    races,
    statistics,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(races.router)
api_router.include_router(horses.router)
api_router.include_router(persons.router)
api_router.include_router(hippodromes.router)
api_router.include_router(statistics.router)
api_router.include_router(predictions.router)
api_router.include_router(dashboard.router)

__all__ = ["api_router"]
