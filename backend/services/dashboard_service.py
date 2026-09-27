#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service « Dashboard ».

Assemble la charge utile de la page `/dashboard` à partir des services métier.
C'est le **seul** endroit où les blocs sont réunis.

Règle d'honnêteté (spec §2.3) : ce qui n'existe pas encore est déclaré
indisponible avec une raison explicite. Aucun bloc n'est rempli avec une
donnée de démonstration présentée comme réelle.
"""

from __future__ import annotations

import datetime

from ..config import (
    DASHBOARD_PREDICTION_BUDGET_S,
    FOLLOWED_RACES_LIMIT,
    ORIGIN_REAL,
)
from ..db.client import database_info
from ..schemas.dashboard import (
    DashboardResponse,
    DataStatus,
    NotificationSummary,
    SubscriptionSummary,
)
from ..schemas.race import RaceSummary
from . import prediction_service, race_service, statistics_service

#: Raisons explicites d'indisponibilité (jamais un substitut inventé).
NO_ACCOUNT_REASON = (
    "Aucun compte utilisateur n'est connecté : l'application n'expose pas encore "
    "d'authentification. Les blocs personnels restent vides plutôt que remplis "
    "par des valeurs de démonstration."
)
NO_PERFORMANCE_REASON = (
    "Les performances personnelles exigent un historique de paris lié à un compte "
    "utilisateur. Cette donnée n'existe pas dans la base : aucune statistique "
    "personnelle n'est affichée."
)
NO_NOTIFICATION_REASON = (
    "Les notifications sont rattachées à un compte utilisateur, qui n'existe pas encore."
)


def _today() -> str:
    return datetime.date.today().strftime("%Y-%m-%d")


def _pick_next_race(races: list[RaceSummary]) -> RaceSummary | None:
    """Première course non terminée ; à défaut, la première disponible."""
    for race in races:
        if race.status != "finished":
            return race
    return races[0] if races else None


def _pick_followed(races: list[RaceSummary], exclude: RaceSummary | None) -> list[RaceSummary]:
    """
    Sélection des « courses à suivre ».

    Priorité aux courses marquées LONAB (couverture éditoriale réelle), puis
    aux courses non terminées, puis au reste. L'ordre reste déterministe.
    """
    candidates = [race for race in races if exclude is None or race.id != exclude.id]

    def sort_key(race: RaceSummary) -> tuple[int, int, str]:
        return (
            0 if race.isLonab else 1,
            0 if race.status != "finished" else 1,
            race.startTime or "99:99",
        )

    return sorted(candidates, key=sort_key)[:FOLLOWED_RACES_LIMIT]


def _data_status(target_date: str | None, race_count: int) -> DataStatus:
    """État de la donnée : source réelle, date de dernière consolidation connue."""
    info = database_info()

    last_updated = target_date or ""
    versions = statistics_service.data_versions()
    if versions and versions[0].createdAt:
        last_updated = versions[0].createdAt

    return DataStatus(
        status="CURRENT",
        lastUpdatedAt=last_updated,
        source=str(info.get("name") or "base locale"),
        raceCount=race_count,
        origin=ORIGIN_REAL,
    )


def _pick_prediction_race(
    next_race: RaceSummary | None,
) -> tuple[str | None, int | None, bool]:
    """
    Choisit la course sur laquelle porter le pronostic.

    Délègue au service de pronostics, qui est seul juge des courses que le
    moteur sait traiter. Retourne `(race_id, document_id, is_next_race)`.
    """
    return prediction_service.resolve_target_race(next_race.id if next_race else None)


def build_dashboard(target_date: str | None = None) -> DashboardResponse:
    """
    Construit la charge utile complète du Dashboard.

    `target_date` permet de forcer une journée ; sinon le backend résout la
    date de travail (jour même → prochaine journée à venir → plus récente).
    """
    resolved_date = target_date or race_service.resolve_target_date()
    today = _today()

    summaries: list[RaceSummary] = (
        race_service.list_race_summaries(date=resolved_date, limit=60)
        if resolved_date
        else []
    )

    next_race = _pick_next_race(summaries)
    followed = _pick_followed(summaries, next_race)

    predictions: list = []
    prediction_context: str | None = None
    prediction_reason: str | None = None

    if next_race is None:
        prediction_reason = (
            "Aucune course exploitable pour la journée affichée : le moteur de "
            "pronostics ne peut pas être exécuté."
        )
    else:
        race_id, document_id, is_next = _pick_prediction_race(next_race)
        if document_id is None or race_id is None:
            prediction_reason = (
                "Aucune course analysable par le moteur n'est disponible dans la base."
            )
        else:
            predictions, prediction_context, prediction_reason = (
                prediction_service.top_predictions(
                    document_id,
                    race_id,
                    limit=5,
                    timeout_s=DASHBOARD_PREDICTION_BUDGET_S,
                )
            )
            if prediction_context and not is_next:
                prediction_context = (
                    "Dernière course analysable par le moteur — "
                    f"{prediction_context}"
                )

    return DashboardResponse(
        targetDate=resolved_date,
        user=None,
        subscription=SubscriptionSummary(plan="NONE", status="NONE", configured=False),
        nextRace=next_race,
        followedRaces=followed,
        topPredictions=predictions,
        predictionContext=prediction_context,
        predictionUnavailableReason=prediction_reason,
        performance=None,
        performanceUnavailableReason=NO_PERFORMANCE_REASON,
        coverage=statistics_service.coverage(),
        notifications=NotificationSummary(
            unreadCount=0, items=[], configured=False, origin=ORIGIN_REAL
        ),
        dataStatus=_data_status(resolved_date, len(summaries)),
        isLive=bool(resolved_date and resolved_date == today),
    )
