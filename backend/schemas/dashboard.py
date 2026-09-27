#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schémas du Dashboard (spec §39 et §58).

Règle de séparation (spec §2.3) : chaque bloc expose son `origin`. Ce qui
n'existe pas encore est déclaré indisponible avec une raison explicite —
jamais remplacé par une valeur inventée.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .prediction import Prediction
from .race import RaceSummary
from .statistics import CoverageStats


class UserSummary(BaseModel):
    id: str
    firstName: str
    lastName: str
    avatarUrl: str | None = None
    statusLabel: str


class SubscriptionSummary(BaseModel):
    """État d'abonnement. `configured = false` tant qu'aucun compte n'existe."""

    plan: Literal["FREE", "PRO", "NONE"] = "NONE"
    status: Literal["ACTIVE", "EXPIRED", "CANCELLED", "NONE"] = "NONE"
    expiresAt: str | None = None
    configured: bool = False


class NotificationItem(BaseModel):
    id: str
    title: str
    createdAt: str
    read: bool = False
    href: str | None = None
    origin: str = "real"


class NotificationSummary(BaseModel):
    """Notifications. `configured = false` tant qu'aucun compte n'existe."""

    unreadCount: int = 0
    items: list[NotificationItem] = Field(default_factory=list)
    configured: bool = False
    origin: str = "real"


class DataStatus(BaseModel):
    status: Literal["CURRENT", "SYNCING", "ERROR"] = "CURRENT"
    lastUpdatedAt: str
    source: str
    raceCount: int = 0
    origin: str = "real"


class DashboardResponse(BaseModel):
    """Charge utile complète de la page /dashboard."""

    #: Journée effectivement affichée (résolue par le backend, jamais devinée
    #: par le frontend).
    targetDate: str | None = None
    user: UserSummary | None = None
    subscription: SubscriptionSummary
    nextRace: RaceSummary | None = None
    followedRaces: list[RaceSummary] = Field(default_factory=list)
    topPredictions: list[Prediction] = Field(default_factory=list)
    predictionContext: str | None = None
    predictionUnavailableReason: str | None = None
    performance: None = None
    performanceUnavailableReason: str | None = None
    coverage: CoverageStats
    notifications: NotificationSummary
    dataStatus: DataStatus
    isLive: bool = False
