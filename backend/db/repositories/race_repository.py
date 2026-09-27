#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repository « courses ».

Contient uniquement du SQL. Aucune logique métier, aucune mise en forme :
c'est le rôle des services.

Toutes les requêtes excluent la **date sentinelle** (`date_is_sentinel = 1`),
valeur par défaut du parseur qui ne correspond à aucune course réelle.
"""

from __future__ import annotations

import sqlite3

from ..client import query_all, query_one, query_scalar

#: Seuil d'exploitabilité retenu par le projet (aligné sur le moteur).
MIN_RUNNERS = 8

_RACE_COLUMNS = """
    mr.race_id,
    mr.source_document_id,
    mr.date,
    mr.date_is_sentinel,
    mr.reunion_num,
    mr.course_num,
    mr.heure_depart,
    mr.hippodrome_label_raw,
    h.label_canonical,
    mr.discipline,
    mr.distance_m,
    mr.montant_euros,
    mr.type_course,
    mr.titre,
    mr.partants_declares,
    mr.partants_effectifs,
    mr.n_runners_linked,
    mr.result_status,
    mr.is_lonab,
    mr.lonab_bet,
    mr.lonab_journal_bet,
    mr.lonab_journal_venue,
    mr.arrivee_officielle,
    mr.quinte_dividende,
    mr.nb_gagnants_quinte,
    mr.meteo_temperature,
    mr.meteo_nebulosite,
    mr.meteo_vent_force,
    mr.meteo_vent_direction
"""

_BASE_FROM = """
    FROM master_race mr
    LEFT JOIN master_hippodrome h ON h.hippodrome_id = mr.hippodrome_id
"""

#: Tri : réunion/course numérotées d'abord, puis par heure de départ.
_ORDER = """
    ORDER BY
        mr.date DESC,
        CASE WHEN mr.reunion_num IS NULL THEN 1 ELSE 0 END,
        mr.reunion_num,
        mr.course_num,
        mr.heure_depart
"""


def list_races(
    *,
    date: str | None = None,
    hippodrome: str | None = None,
    discipline: str | None = None,
    only_lonab: bool = False,
    analysable: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[sqlite3.Row]:
    """Liste les courses exploitables, filtrables par date, hippodrome, discipline."""
    where = ["mr.n_runners_linked >= ?", "COALESCE(mr.date_is_sentinel, 0) = 0"]
    params: list[object] = [MIN_RUNNERS]

    if date:
        where.append("mr.date = ?")
        params.append(date)
    if hippodrome:
        where.append("(h.label_canonical = ? OR mr.hippodrome_label_raw = ?)")
        params.extend([hippodrome, hippodrome])
    if discipline:
        where.append("mr.discipline = ?")
        params.append(discipline)
    if only_lonab:
        where.append("mr.is_lonab = 1")
    if analysable:
        # Précondition documentée du moteur : il raisonne sur l'identifiant de
        # document source. La liste réellement acceptée reste déterminée par le
        # moteur lui-même au moment du pronostic (voir `prediction_service`).
        where.append("mr.source_document_id IS NOT NULL AND mr.source_document_id > 0")

    params.extend([limit, offset])

    sql = f"""
        SELECT {_RACE_COLUMNS}
        {_BASE_FROM}
        WHERE {' AND '.join(where)}
        {_ORDER}
        LIMIT ? OFFSET ?
    """
    return query_all(sql, params)


def get_race(race_id: str) -> sqlite3.Row | None:
    """Retourne une course par son identifiant interne."""
    sql = f"""
        SELECT {_RACE_COLUMNS}
        {_BASE_FROM}
        WHERE mr.race_id = ?
    """
    return query_one(sql, (race_id,))


def get_race_by_document_id(document_id: int) -> sqlite3.Row | None:
    """Retourne une course à partir de son identifiant de document source."""
    sql = f"""
        SELECT {_RACE_COLUMNS}
        {_BASE_FROM}
        WHERE mr.source_document_id = ?
        LIMIT 1
    """
    return query_one(sql, (document_id,))


def list_runners(race_id: str) -> list[sqlite3.Row]:
    """Partants d'une course, enrichis du marché et des libellés normalisés."""
    sql = """
        SELECT
            r.runner_id,
            r.numero,
            r.cote_decimale,
            r.gains_euros,
            r.performances_structured,
            r.sexe_raw,
            r.age_raw,
            r.poids_raw,
            r.corde_raw,
            r.result_position,
            r.result_status,
            h.horse_id,
            h.name_normalized AS horse_name,
            pj.person_id AS jockey_id,
            pj.name_normalized AS jockey_name,
            pt.person_id AS trainer_id,
            pt.name_normalized AS trainer_name,
            m.m_prob_norm,
            m.m_implied,
            m.m_rank,
            m.m_is_fav,
            m.f_age,
            m.f_sex,
            m.f_musique_winrate,
            m.f_musique_top3rate,
            m.c_horse_winrate,
            m.c_horse_top3rate,
            m.c_jockey_winrate,
            m.c_trainer_winrate,
            m.label_win,
            m.label_top3
        FROM master_runner r
        LEFT JOIN master_horse h ON h.horse_id = r.horse_id
        LEFT JOIN master_person pj ON pj.person_id = r.jockey_id
        LEFT JOIN master_person pt ON pt.person_id = r.trainer_id
        LEFT JOIN market_runner_features m ON m.runner_id = r.runner_id
        WHERE r.race_id = ?
        ORDER BY r.numero
    """
    return query_all(sql, (race_id,))


def list_dates(limit: int = 30) -> list[sqlite3.Row]:
    """Dates de courses disponibles, de la plus récente à la plus ancienne."""
    sql = """
        SELECT date, count(*) AS n_races
        FROM master_race
        WHERE n_runners_linked >= ?
          AND COALESCE(date_is_sentinel, 0) = 0
        GROUP BY date
        ORDER BY date DESC
        LIMIT ?
    """
    return query_all(sql, (MIN_RUNNERS, limit))


def latest_date() -> str | None:
    """Date la plus récente contenant au moins une course exploitable."""
    return query_scalar(
        """
        SELECT max(date) FROM master_race
        WHERE n_runners_linked >= ? AND COALESCE(date_is_sentinel, 0) = 0
        """,
        (MIN_RUNNERS,),
    )


def count_races_for_date(date: str) -> int:
    """Nombre de courses exploitables pour une date donnée."""
    value = query_scalar(
        """
        SELECT count(*) FROM master_race
        WHERE date = ? AND n_runners_linked >= ? AND COALESCE(date_is_sentinel, 0) = 0
        """,
        (date, MIN_RUNNERS),
        default=0,
    )
    return int(value or 0)


def list_disciplines() -> list[str]:
    """Disciplines réellement présentes en base."""
    rows = query_all(
        """
        SELECT DISTINCT discipline FROM master_race
        WHERE discipline IS NOT NULL AND trim(discipline) <> ''
        ORDER BY discipline
        """
    )
    return [row[0] for row in rows]


def recent_races_with_document(limit: int = 200) -> list[sqlite3.Row]:
    """
    Courses récentes rattachées à un document source.

    `source_document_id` vaut 0 pour les courses injectées par les adapters
    externes (aucun document LONAB d'origine) : elles sont exclues, car le
    moteur de pronostics raisonne sur l'identifiant de document.
    """
    return query_all(
        """
        SELECT race_id, source_document_id, date, hippodrome_label_raw, n_runners_linked
        FROM master_race
        WHERE source_document_id IS NOT NULL
          AND source_document_id > 0
          AND n_runners_linked >= ?
          AND COALESCE(date_is_sentinel, 0) = 0
        ORDER BY date DESC, reunion_num, course_num
        LIMIT ?
        """,
        (MIN_RUNNERS, limit),
    )
