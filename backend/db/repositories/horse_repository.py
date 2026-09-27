#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repository « chevaux ». SQL uniquement."""

from __future__ import annotations

import sqlite3

from ..client import query_all, query_one, query_scalar


def search_horses(query: str | None = None, limit: int = 50, offset: int = 0) -> list[sqlite3.Row]:
    """
    Recherche des chevaux par nom normalisé.

    Le tri privilégie les chevaux ayant le plus de courses connues.
    """
    where: list[str] = []
    params: list[object] = []

    if query:
        where.append("name_normalized LIKE ?")
        params.append(f"%{query.upper()}%")

    sql = f"""
        SELECT horse_id, name_normalized, n_starts, first_seen_date, last_seen_date,
               sex_birthyear_variants, pedigree_pere, pedigree_mere, robe, race,
               homonym_risk, resolution_confidence
        FROM master_horse
        {'WHERE ' + ' AND '.join(where) if where else ''}
        ORDER BY COALESCE(n_starts, 0) DESC, name_normalized
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    return query_all(sql, params)


def get_horse(horse_id: str) -> sqlite3.Row | None:
    """Fiche d'un cheval."""
    return query_one(
        """
        SELECT horse_id, name_normalized, name_key, n_starts, first_seen_date, last_seen_date,
               sex_birthyear_variants, n_sex_birthyear_variants,
               pedigree_pere, pedigree_mere, robe, race,
               resolution_method, resolution_confidence, homonym_risk
        FROM master_horse
        WHERE horse_id = ?
        """,
        (horse_id,),
    )


def horse_results(horse_id: str, limit: int = 20) -> list[sqlite3.Row]:
    """Dernières participations d'un cheval, avec la course associée."""
    return query_all(
        """
        SELECT
            r.race_id,
            r.numero,
            r.cote_decimale,
            r.result_position,
            r.result_status,
            r.gains_euros,
            mr.date,
            COALESCE(h.label_canonical, mr.hippodrome_label_raw) AS hippodrome,
            mr.discipline,
            mr.distance_m,
            mr.titre,
            mr.reunion_num,
            mr.course_num
        FROM master_runner r
        JOIN master_race mr ON mr.race_id = r.race_id
        LEFT JOIN master_hippodrome h ON h.hippodrome_id = mr.hippodrome_id
        WHERE r.horse_id = ?
          AND COALESCE(mr.date_is_sentinel, 0) = 0
        ORDER BY mr.date DESC
        LIMIT ?
        """,
        (horse_id, limit),
    )


def horse_statistics(horse_id: str) -> dict[str, object]:
    """Statistiques réelles calculées sur les participations connues."""
    row = query_one(
        """
        SELECT
            count(*)                                            AS starts,
            sum(CASE WHEN r.result_position = 1 THEN 1 ELSE 0 END) AS wins,
            sum(CASE WHEN r.result_position <= 3 THEN 1 ELSE 0 END) AS top3,
            sum(CASE WHEN r.result_position <= 5 THEN 1 ELSE 0 END) AS top5,
            sum(CASE WHEN r.result_position IS NULL THEN 1 ELSE 0 END) AS unknown
        FROM master_runner r
        JOIN master_race mr ON mr.race_id = r.race_id
        WHERE r.horse_id = ? AND COALESCE(mr.date_is_sentinel, 0) = 0
        """,
        (horse_id,),
    )
    if row is None:
        return {"starts": 0, "wins": 0, "top3": 0, "top5": 0, "unknown": 0,
                "winRate": None, "top3Rate": None}

    starts = int(row["starts"] or 0)
    known = starts - int(row["unknown"] or 0)
    return {
        "starts": starts,
        "wins": int(row["wins"] or 0),
        "top3": int(row["top3"] or 0),
        "top5": int(row["top5"] or 0),
        "unknown": int(row["unknown"] or 0),
        "winRate": (int(row["wins"] or 0) / known) if known else None,
        "top3Rate": (int(row["top3"] or 0) / known) if known else None,
    }


def count_horses() -> int:
    """Nombre total de chevaux référencés."""
    return int(query_scalar("SELECT count(*) FROM master_horse", default=0) or 0)
