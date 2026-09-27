#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Service « hippodromes »."""

from __future__ import annotations

import sqlite3

from ..db.repositories import hippodrome_repository as repo
from ..schemas.entities import HippodromeDetail, HippodromeSummary


def _clean_label(value: object) -> str:
    text = str(value or "").strip()
    if not text or text.isdigit():
        return "Hippodrome non renseigné"
    return text.replace("-", " ").title()


def _to_summary(row: sqlite3.Row) -> HippodromeSummary:
    return HippodromeSummary(
        id=row["hippodrome_id"],
        name=_clean_label(row["label_canonical"]),
        country=row["country"],
        races=int(row["n_courses"] or 0),
        isValid=bool(row["is_valid"]) if row["is_valid"] is not None else True,
        qualityFlag=row["quality_flag"],
    )


def list_all(limit: int = 200) -> list[HippodromeSummary]:
    """Hippodromes référencés, du plus actif au moins actif."""
    return [_to_summary(row) for row in repo.list_hippodromes(limit)]


def get(hippodrome_id: str) -> HippodromeDetail | None:
    """Fiche d'un hippodrome et statistiques réelles de ses courses."""
    row = repo.get_hippodrome(hippodrome_id)
    if row is None:
        return None
    return HippodromeDetail(
        hippodrome=_to_summary(row),
        statistics=repo.hippodrome_statistics(hippodrome_id),
    )


def count() -> int:
    """Nombre d'hippodromes référencés."""
    return repo.count_hippodromes()
