#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository « statistiques ».

Toutes les mesures exposées ici sont **réellement calculées** sur la base du
projet, et chacune porte son volume (nombre d'observations) afin de respecter
la règle « période + volume + méthode » du moteur (spec §52).
"""

from __future__ import annotations

import sqlite3

from ..client import query_all, query_one, query_scalar, table_exists


def overview() -> dict[str, object]:
    """Volumes disponibles dans la base."""
    def count(table: str, where: str = "") -> int:
        if not table_exists(table):
            return 0
        sql = f"SELECT count(*) FROM {table}"
        if where:
            sql += f" WHERE {where}"
        return int(query_scalar(sql, default=0) or 0)

    return {
        "races": count("master_race", "COALESCE(date_is_sentinel,0) = 0"),
        "exploitableRaces": count(
            "master_race",
            "n_runners_linked >= 8 AND COALESCE(date_is_sentinel,0) = 0",
        ),
        "racesWithResult": count(
            "master_race",
            "result_status IN ('arrival_available','OFFICIAL')",
        ),
        "runners": count("master_runner"),
        "horses": count("master_horse"),
        "persons": count("master_person"),
        "jockeys": count("master_person", "lower(role) = 'jockey'"),
        "trainers": count("master_person", "lower(role) = 'trainer'"),
        "hippodromes": count("master_hippodrome"),
        "oddsSnapshots": count("external_pmu_citations"),
        "pmuResults": count("external_pmu_results"),
    }


def favourite_win_rate() -> dict[str, object]:
    """
    Taux de victoire du favori du marché.

    Mesure directe sur les partants dont la cote est connue. C'est une mesure
    de référence : elle sert de point de comparaison, pas de promesse.
    """
    if not table_exists("market_runner_features"):
        return {"favourites": 0, "wins": 0, "rate": None}

    row = query_one(
        """
        SELECT
            sum(CASE WHEN m_is_fav = 1 THEN 1 ELSE 0 END) AS favourites,
            sum(CASE WHEN m_is_fav = 1 AND label_win = 1 THEN 1 ELSE 0 END) AS wins
        FROM market_runner_features
        WHERE m_is_fav IS NOT NULL AND label_win IS NOT NULL
        """
    )
    favourites = int((row["favourites"] if row else 0) or 0)
    wins = int((row["wins"] if row else 0) or 0)
    return {
        "favourites": favourites,
        "wins": wins,
        "rate": (wins / favourites) if favourites else None,
    }


def by_discipline(limit: int = 10) -> list[dict[str, object]]:
    """Répartition des courses par discipline."""
    rows = query_all(
        """
        SELECT COALESCE(NULLIF(trim(discipline), ''), 'Non renseignée') AS discipline,
               count(*) AS races,
               avg(distance_m) AS avg_distance
        FROM master_race
        WHERE COALESCE(date_is_sentinel, 0) = 0
        GROUP BY 1
        ORDER BY races DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [
        {
            "discipline": row["discipline"],
            "races": int(row["races"] or 0),
            "avgDistance": round(float(row["avg_distance"]), 0) if row["avg_distance"] else None,
        }
        for row in rows
    ]


def by_hippodrome(limit: int = 10) -> list[dict[str, object]]:
    """Hippodromes les plus actifs."""
    rows = query_all(
        """
        SELECT COALESCE(h.label_canonical, mr.hippodrome_label_raw, 'Inconnu') AS hippodrome,
               count(*) AS races,
               count(DISTINCT mr.date) AS days
        FROM master_race mr
        LEFT JOIN master_hippodrome h ON h.hippodrome_id = mr.hippodrome_id
        WHERE COALESCE(mr.date_is_sentinel, 0) = 0
        GROUP BY 1
        ORDER BY races DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [
        {
            "hippodrome": row["hippodrome"],
            "races": int(row["races"] or 0),
            "days": int(row["days"] or 0),
        }
        for row in rows
    ]


def monthly_activity(limit: int = 12) -> list[dict[str, object]]:
    """Nombre de courses par mois (12 derniers mois présents en base)."""
    rows = query_all(
        """
        SELECT substr(date, 1, 7) AS month, count(*) AS races
        FROM master_race
        WHERE COALESCE(date_is_sentinel, 0) = 0
        GROUP BY 1
        ORDER BY month DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [
        {"month": row["month"], "races": int(row["races"] or 0)}
        for row in reversed(rows)
    ]


def odds_coverage() -> dict[str, object]:
    """Part des partants disposant réellement d'une cote."""
    row = query_one(
        """
        SELECT count(*) AS total,
               sum(CASE WHEN cote_decimale IS NOT NULL THEN 1 ELSE 0 END) AS with_odds
        FROM master_runner
        """
    )
    total = int((row["total"] if row else 0) or 0)
    with_odds = int((row["with_odds"] if row else 0) or 0)
    return {
        "runners": total,
        "withOdds": with_odds,
        "coverage": (with_odds / total) if total else None,
    }


def result_coverage() -> dict[str, object]:
    """Part des courses disposant d'une arrivée exploitable."""
    row = query_one(
        """
        SELECT count(*) AS total,
               sum(CASE WHEN result_status IN ('arrival_available','OFFICIAL') THEN 1 ELSE 0 END) AS with_result
        FROM master_race
        WHERE COALESCE(date_is_sentinel, 0) = 0
        """
    )
    total = int((row["total"] if row else 0) or 0)
    with_result = int((row["with_result"] if row else 0) or 0)
    return {
        "races": total,
        "withResult": with_result,
        "coverage": (with_result / total) if total else None,
    }


def data_versions() -> list[sqlite3.Row]:
    """Versions de données enregistrées (traçabilité)."""
    if not table_exists("data_version"):
        return []
    return query_all(
        "SELECT version_id, scope, version, source_sha256, created_at, notes "
        "FROM data_version ORDER BY created_at DESC"
    )


def external_fetch_summary(limit: int = 5) -> list[sqlite3.Row]:
    """Dernières collectes externes enregistrées."""
    if not table_exists("external_fetch_log"):
        return []
    return query_all(
        "SELECT * FROM external_fetch_log ORDER BY rowid DESC LIMIT ?",
        (limit,),
    )
