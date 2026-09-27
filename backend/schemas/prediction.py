#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schémas « prédictions ».

Les probabilités proviennent exclusivement du moteur Hippo Engine
(`generate_prediction` / `as_api_payload`). Le frontend ne recalcule jamais
une probabilité (spec §44).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from .common import DataOrigin

#: Niveau de confiance exposé par le moteur.
Confidence = str


class Prediction(BaseModel):
    """Ligne de pronostic présentable dans le Dashboard."""

    horseId: str
    horseName: str
    horseNumber: int
    winProbability: float | None = None
    top3Probability: float | None = None
    top5Probability: float | None = None
    rank: int
    confidence: Confidence | None = None
    modelVersion: str
    predictionVersion: str
    raceLabel: str
    raceId: str
    odds: float | None = None
    valueEdge: float | None = None
    factorsPositive: list[str] = Field(default_factory=list)
    factorsNegative: list[str] = Field(default_factory=list)
    origin: DataOrigin = "prediction"


class RacePrediction(BaseModel):
    """Pronostic complet d'une course, tel que produit par le moteur."""

    raceId: str
    raceLabel: str
    modelVersion: str
    predictionVersion: str
    dataTimestamp: str | None = None
    dataQuality: str | None = None
    confidence: Confidence | None = None
    confidenceReasons: list[str] = Field(default_factory=list)
    bases: list[int] = Field(default_factory=list)
    chances: list[int] = Field(default_factory=list)
    outsiders: list[int] = Field(default_factory=list)
    quinte: list[int] = Field(default_factory=list)
    tierce: list[int] = Field(default_factory=list)
    quarte: list[int] = Field(default_factory=list)
    runners: list[Prediction] = Field(default_factory=list)
    origin: DataOrigin = "prediction"


class PredictionUnavailable(BaseModel):
    """Réponse explicite lorsque le moteur ne peut pas produire de pronostic."""

    available: bool = False
    reason: str
