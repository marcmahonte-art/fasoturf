#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repository « personnes » (jockeys et entraîneurs). SQL uniquement."""

from __future__ import annotations

import sqlite3

from ..client import query_all, query_one, query_scalar

#: Rôles réellement présents en base.
ROLE_JOCKEY = "jockey"
ROLE_TRAINER = "trainer"


def search_persons(
    role: str | None = None,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[sqlite3.Row]:
    """Recherche des personnes, filtrables par rôle."""
    where: list[str] = []
    params: list[object] = []

    if role:
        where.append("lower(role) = ?")
        params.append(role)
    if query:
        where.append("name_normalized LIKE ?")
        params.append(f"%{query.upper()}%")

    sql = f"""
        SELECT person_id, name_normalized, role, n_appearances,
               resolution_method, resolution_confidence
        FROM master_person
        {'WHERE ' + ' AND '.join(where) if where else ''}
        ORDER BY COALESCE(n_appearances, 0) DESC, name_normalized
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    return query_all(sql, params)


def get_person(person_id: str) -> sqlite3.Row | None:
    """Fiche d'une personne."""
    return query_one(
        """
        SELECT person_id, name_normalized, name_key, role, n_appearances,
               resolution_method, resolution_confidence
        FROM master_person
        WHERE person_id = ?
        """,
        (person_id,),
    )


def person_statistics(person_id: str, role: str) -> dict[str, object]:
    """
    Statistiques réelles d'un jockey ou d'un entraîneur.

    Le taux de victoire est calculé sur les participations dont le résultat
    est connu (les positions nulles sont exclues du dénominateur).
    """
    column = "jockey_id" if role == ROLE_JOCKEY else "trainer_id"
    row = query_one(
        f"""
        SELECT
            count(*)                                              AS mounts,
            sum(CASE WHEN r.result_position = 1 THEN 1 ELSE 0 END) AS wins,
            sum(CASE WHEN r.result_position <= 3 THEN 1 ELSE 0 END) AS top3,
            sum(CASE WHEN r.result_position IS NULL THEN 1 ELSE 0 END) AS unknown
        FROM master_runner r
        JOIN master_race mr ON mr.race_id = r.race_id
        WHERE r.{column} = ? AND COALESCE(mr.date_is_sentinel, 0) = 0
        """,
        (person_id,),
    )
    if row is None:
        return {"mounts": 0, "wins": 0, "top3": 0, "unknown": 0, "winRate": None, "top3Rate": None}

    mounts = int(row["mounts"] or 0)
    known = mounts - int(row["unknown"] or 0)
    return {
        "mounts": mounts,
        "wins": int(row["wins"] or 0),
        "top3": int(row["top3"] or 0),
        "unknown": int(row["unknown"] or 0),
        "winRate": (int(row["wins"] or 0) / known) if known else None,
        "top3Rate": (int(row["top3"] or 0) / known) if known else None,
    }


def person_recent_races(person_id: str, role: str, limit: int = 15) -> list[sqlite3.Row]:
    """Dernières courses d'un jockey ou d'un entraîneur."""
    column = "jockey_id" if role == ROLE_JOCKEY else "trainer_id"
    return query_all(
        f"""
        SELECT
            mr.race_id,
            mr.date,
            COALESCE(h.label_canonical, mr.hippodrome_label_raw) AS hippodrome,
            mr.discipline,
            mr.distance_m,
            mr.titre,
            r.numero,
            r.result_position,
            r.cote_decimale,
            ho.name_normalized AS horse_name
        FROM master_runner r
        JOIN master_race mr ON mr.race_id = r.race_id
        LEFT JOIN master_hippodrome h ON h.hippodrome_id = mr.hippodrome_id
        LEFT JOIN master_horse ho ON ho.horse_id = r.horse_id
        WHERE r.{column} = ? AND COALESCE(mr.date_is_sentinel, 0) = 0
        ORDER BY mr.date DESC
        LIMIT ?
        """,
        (person_id, limit),
    )


def count_persons(role: str | None = None) -> int:
    """Nombre de personnes référencées, éventuellement filtrées par rôle."""
    if role:
        return int(
            query_scalar("SELECT count(*) FROM master_person WHERE lower(role) = ?", (role,), default=0) or 0
        )
    return int(query_scalar("SELECT count(*) FROM master_person", default=0) or 0)
