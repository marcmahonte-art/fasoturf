#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schémas « chevaux », « personnes » et « hippodromes »."""

from __future__ import annotations

from pydantic import BaseModel


class HorseSummary(BaseModel):
    id: str
    name: str
    starts: int | None = None
    firstSeenDate: str | None = None
    lastSeenDate: str | None = None
    sexBirthyearVariants: str | None = None
    father: str | None = None
    mother: str | None = None
    coat: str | None = None
    breed: str | None = None
    homonymRisk: str | None = None


class HorseStatistics(BaseModel):
    starts: int
    wins: int
    top3: int
    top5: int
    unknown: int
    winRate: float | None = None
    top3Rate: float | None = None


class HorseRun(BaseModel):
    raceId: str
    date: str
    hippodrome: str | None = None
    discipline: str | None = None
    distanceMeters: int | None = None
    title: str | None = None
    number: int | None = None
    position: int | None = None
    odds: float | None = None


class HorseDetail(BaseModel):
    horse: HorseSummary
    statistics: HorseStatistics
    recentRuns: list[HorseRun]


class PersonSummary(BaseModel):
    id: str
    name: str
    role: str
    appearances: int | None = None
    resolutionConfidence: float | None = None


class PersonStatistics(BaseModel):
    mounts: int
    wins: int
    top3: int
    unknown: int
    winRate: float | None = None
    top3Rate: float | None = None


class PersonRun(BaseModel):
    raceId: str
    date: str
    hippodrome: str | None = None
    discipline: str | None = None
    distanceMeters: int | None = None
    title: str | None = None
    horseName: str | None = None
    number: int | None = None
    position: int | None = None
    odds: float | None = None


class PersonDetail(BaseModel):
    person: PersonSummary
    statistics: PersonStatistics
    recentRuns: list[PersonRun]


class HippodromeSummary(BaseModel):
    id: str
    name: str
    country: str | None = None
    races: int | None = None
    isValid: bool = True
    qualityFlag: str | None = None


class HippodromeDetail(BaseModel):
    hippodrome: HippodromeSummary
    statistics: dict[str, object]
