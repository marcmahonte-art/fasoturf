#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repository « hippodromes ». SQL uniquement."""

from __future__ import annotations

import sqlite3

from ..client import query_all, query_one, query_scalar


def list_hippodromes(limit: int = 200) -> list[sqlite3.Row]:
    """Hippodromes référencés, du plus actif au moins actif."""
    return query_all(
        """
        SELECT hippodrome_id, label_canonical, label_variants, country,
               is_valid, quality_flag, n_courses
        FROM master_hippodrome
        ORDER BY COALESCE(n_courses, 0) DESC, label_canonical
        LIMIT ?
        """,
        (limit,),
    )


def get_hippodrome(hippodrome_id: str) -> sqlite3.Row | None:
    """Fiche d'un hippodrome."""
    return query_one(
        """
        SELECT hippodrome_id, label_canonical, label_variants, country,
               is_valid, quality_flag, n_courses
        FROM master_hippodrome
        WHERE hippodrome_id = ?
        """,
        (hippodrome_id,),
    )


def hippodrome_statistics(hippodrome_id: str) -> dict[str, object]:
    """Statistiques réelles des courses tenues sur un hippodrome."""
    row = query_one(
        """
        SELECT
            count(*)                                        AS races,
            count(DISTINCT date)                            AS days,
            avg(distance_m)                                 AS avg_distance,
            sum(CASE WHEN result_status IN ('arrival_available','OFFICIAL') THEN 1 ELSE 0 END) AS with_result
        FROM master_race
        WHERE hippodrome_id = ? AND COALESCE(date_is_sentinel, 0) = 0
        """,
        (hippodrome_id,),
    )
    if row is None:
        return {"races": 0, "days": 0, "avgDistance": None, "withResult": 0}
    return {
        "races": int(row["races"] or 0),
        "days": int(row["days"] or 0),
        "avgDistance": round(float(row["avg_distance"]), 0) if row["avg_distance"] else None,
        "withResult": int(row["with_result"] or 0),
    }


def count_hippodromes() -> int:
    """Nombre d'hippodromes référencés."""
    return int(query_scalar("SELECT count(*) FROM master_hippodrome", default=0) or 0)
