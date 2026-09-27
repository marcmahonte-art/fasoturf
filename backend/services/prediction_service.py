#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service « prédictions ».

Le moteur **Hippo Engine** est la seule source de probabilités : le backend
l'invoque en sous-processus

    python -m ml.scripts.run_prediction --race <document_id> --json

et ne recalcule jamais une probabilité lui-même (spec §44).

Règle d'honnêteté : si le moteur est indisponible ou échoue, la réponse est un
`PredictionUnavailable` **explicite avec sa raison**. Aucune probabilité n'est
jamais inventée ni extrapolée.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time

from ..config import (
    HIPPO_ENGINE_DIR,
    HIPPO_ENGINE_ENABLED,
    HIPPO_ENGINE_TIMEOUT_S,
    ORIGIN_PREDICTION,
    PREDICTION_CACHE_TTL_S,
)
from ..db.repositories import race_repository as race_repo
from ..schemas.prediction import Prediction, PredictionUnavailable, RacePrediction

#: Cache mémoire (course → (horodatage, charge utile)). Le moteur est coûteux.
_CACHE: dict[str, tuple[float, dict[str, object]]] = {}
_CACHE_LOCK = threading.Lock()

#: Cache de l'ensemble des identifiants supportés par le moteur.
_SUPPORTED: tuple[float, set[int]] | None = None
_SUPPORTED_LOCK = threading.Lock()

#: Durée de validité de la liste des courses supportées (le socle bouge peu).
SUPPORTED_TTL_S = 3600.0


class PredictionError(RuntimeError):
    """Le moteur n'a pas pu produire de pronostic."""


# --------------------------------------------------------------------------
# Appel du moteur
# --------------------------------------------------------------------------


def engine_available() -> bool:
    """Vrai si le moteur est activé et présent sur le disque."""
    return HIPPO_ENGINE_ENABLED and (HIPPO_ENGINE_DIR / "ml" / "scripts" / "run_prediction.py").is_file()


def _cache_get(document_id: str) -> dict[str, object] | None:
    with _CACHE_LOCK:
        entry = _CACHE.get(document_id)
    if entry is None:
        return None
    stored_at, payload = entry
    if time.time() - stored_at > PREDICTION_CACHE_TTL_S:
        return None
    return payload


def _cache_put(document_id: str, payload: dict[str, object]) -> None:
    with _CACHE_LOCK:
        _CACHE[document_id] = (time.time(), payload)


def invalidate_cache(document_id: str | None = None) -> None:
    """Vide le cache (une course, ou tout si `document_id` est None)."""
    with _CACHE_LOCK:
        if document_id is None:
            _CACHE.clear()
        else:
            _CACHE.pop(document_id, None)


def _run_engine(document_id: str, timeout_s: float | None = None) -> dict[str, object]:
    """
    Exécute le moteur et retourne sa charge utile JSON brute.

    `timeout_s` permet d'imposer un budget plus court que le délai nominal
    (utile pour l'endpoint agrégé du Dashboard, qui ne doit pas bloquer).

    Lève `PredictionError` avec un message lisible en cas d'échec.
    """
    if not HIPPO_ENGINE_ENABLED:
        raise PredictionError(
            "Moteur de pronostics désactivé (FASOTURF_ENGINE_DISABLED=1)."
        )
    if not engine_available():
        raise PredictionError(
            f"Moteur introuvable : {HIPPO_ENGINE_DIR / 'ml' / 'scripts' / 'run_prediction.py'}"
        )

    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")

    budget = timeout_s if timeout_s and timeout_s > 0 else HIPPO_ENGINE_TIMEOUT_S

    try:
        completed = subprocess.run(
            [sys.executable, "-m", "ml.scripts.run_prediction", "--race", document_id, "--json"],
            cwd=str(HIPPO_ENGINE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=budget,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise PredictionError(
            f"Délai dépassé ({budget:.0f} s) lors du calcul du pronostic."
        ) from exc
    except OSError as exc:
        raise PredictionError(f"Impossible de lancer le moteur : {exc}") from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()
        tail = detail[-1] if detail else f"code {completed.returncode}"
        raise PredictionError(f"Le moteur a échoué : {tail}")

    raw = (completed.stdout or "").strip()
    if not raw:
        raise PredictionError("Le moteur n'a produit aucune sortie.")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PredictionError("Sortie du moteur illisible (JSON invalide).") from exc

    if not isinstance(payload, dict) or "prediction" not in payload:
        raise PredictionError("Sortie du moteur incomplète (bloc « prediction » absent).")

    return payload


def _engine_payload(
    document_id: str, *, refresh: bool = False, timeout_s: float | None = None
) -> dict[str, object]:
    """Charge utile du moteur, servie depuis le cache quand c'est possible."""
    if not refresh:
        cached = _cache_get(document_id)
        if cached is not None:
            return cached
    payload = _run_engine(document_id, timeout_s)
    _cache_put(document_id, payload)
    return payload


def engine_supported_ids(*, refresh: bool = False) -> set[int]:
    """
    Ensemble des identifiants de course que le moteur sait traiter.

    La liste est demandée **au moteur lui-même** (`--list`) plutôt que
    reconstruite depuis le socle : c'est la seule façon de garantir qu'elle
    restera exacte si le moteur change de critère. Le résultat est mis en cache.
    """
    global _SUPPORTED

    with _SUPPORTED_LOCK:
        if not refresh and _SUPPORTED is not None:
            stored_at, ids = _SUPPORTED
            if time.time() - stored_at <= SUPPORTED_TTL_S:
                return ids

    if not engine_available():
        return set()

    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")

    try:
        completed = subprocess.run(
            [sys.executable, "-m", "ml.scripts.run_prediction", "--list", "--limit", "100000"],
            cwd=str(HIPPO_ENGINE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=HIPPO_ENGINE_TIMEOUT_S,
            env=env,
            check=False,
        )
    except (subprocess.SubprocessError, OSError):
        return set()

    if completed.returncode != 0:
        return set()

    ids: set[int] = set()
    lines = (completed.stdout or "").splitlines()
    for line in lines[1:]:  # la première ligne est un en-tête de comptage
        token = line.strip().split(" ", 1)[0]
        if token.isdigit():
            ids.add(int(token))

    with _SUPPORTED_LOCK:
        _SUPPORTED = (time.time(), ids)
    return ids


# --------------------------------------------------------------------------
# Traduction vers les modèles d'API
# --------------------------------------------------------------------------


def _as_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _as_str_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _as_int_list(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    numbers: list[int] = []
    for item in value:
        try:
            numbers.append(int(item))
        except (TypeError, ValueError):
            continue
    return numbers


def _race_label(race_id: str | None, fallback_hippodrome: str, fallback_date: str) -> str:
    """Libellé lisible « R1C3 · Paris-Vincennes » — repli sur la donnée du moteur."""
    if race_id:
        from . import race_service

        race = race_service.get_race(race_id)
        if race is not None:
            return f"{race.reunion}{race.course} · {race.hippodrome}"
    if fallback_hippodrome:
        return f"{fallback_hippodrome} · {fallback_date}".strip(" ·")
    return fallback_date or "Course"


def _runner_names(race_id: str | None) -> dict[int, tuple[str, str]]:
    """
    Table numéro → (horse_id, nom) construite depuis la base.

    Le moteur raisonne en numéros de partant ; les noms viennent du socle, qui
    est la seule source d'identité des chevaux.
    """
    if not race_id:
        return {}
    mapping: dict[int, tuple[str, str]] = {}
    for row in race_repo.list_runners(race_id):
        try:
            number = int(row["numero"])
        except (TypeError, ValueError):
            continue
        name = (row["horse_name"] or "").strip()
        mapping[number] = (row["horse_id"] or "", name.title() if name else "Partant non identifié")
    return mapping


def _to_prediction(
    raw: dict[str, object],
    *,
    rank: int,
    race_id: str | None,
    race_label: str,
    names: dict[int, tuple[str, str]],
    model_version: str,
    prediction_version: str,
    confidence: str | None,
) -> Prediction | None:
    try:
        number = int(raw.get("number"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None

    horse_id, horse_name = names.get(number, ("", f"Partant n°{number}"))

    return Prediction(
        horseId=horse_id,
        horseName=horse_name,
        horseNumber=number,
        winProbability=_as_float(raw.get("winProbability")),
        top3Probability=_as_float(raw.get("top3Probability")),
        top5Probability=_as_float(raw.get("top5Probability")),
        rank=rank,
        confidence=confidence,
        modelVersion=model_version,
        predictionVersion=prediction_version,
        raceLabel=race_label,
        raceId=race_id or "",
        odds=_as_float(raw.get("odds")),
        valueEdge=_as_float(raw.get("valueEdge")),
        factorsPositive=_as_str_list(raw.get("factorsPositive")),
        factorsNegative=_as_str_list(raw.get("factorsNegative")),
        origin=ORIGIN_PREDICTION,
    )


# --------------------------------------------------------------------------
# API du service
# --------------------------------------------------------------------------


def predict_race(
    document_id: int | str,
    *,
    race_id: str | None = None,
    limit: int | None = None,
    refresh: bool = False,
    timeout_s: float | None = None,
) -> RacePrediction | PredictionUnavailable:
    """
    Pronostic complet d'une course, ou raison explicite d'indisponibilité.

    `document_id` est l'identifiant attendu par le moteur (identifiant de
    document source). `race_id` permet de rattacher les noms de chevaux.
    """
    key = str(document_id)
    try:
        payload = _engine_payload(key, refresh=refresh, timeout_s=timeout_s)
    except PredictionError as exc:
        return PredictionUnavailable(available=False, reason=str(exc))

    block = payload.get("prediction")
    if not isinstance(block, dict):
        return PredictionUnavailable(
            available=False, reason="Sortie du moteur incomplète (bloc « prediction » absent)."
        )

    race_block = payload.get("race") if isinstance(payload.get("race"), dict) else {}
    assert isinstance(race_block, dict)

    if race_id is None:
        row = race_repo.get_race_by_document_id(int(document_id))
        race_id = row["race_id"] if row is not None else None

    hippodrome = str(race_block.get("hippodrome") or "").strip()
    date = str(race_block.get("date") or "").strip()
    label = _race_label(race_id, hippodrome, date)
    names = _runner_names(race_id)

    model_version = str(block.get("modelVersion") or "inconnu")
    prediction_version = str(block.get("predictionVersion") or "inconnu")
    confidence = str(block.get("confidence")) if block.get("confidence") else None

    raw_runners = block.get("runners")
    if not isinstance(raw_runners, list):
        return PredictionUnavailable(
            available=False, reason="Le moteur n'a renvoyé aucun partant."
        )

    predictions: list[Prediction] = []
    for index, raw in enumerate(raw_runners, start=1):
        if not isinstance(raw, dict):
            continue
        item = _to_prediction(
            raw,
            rank=index,
            race_id=race_id,
            race_label=label,
            names=names,
            model_version=model_version,
            prediction_version=prediction_version,
            confidence=confidence,
        )
        if item is not None:
            predictions.append(item)

    if not predictions:
        return PredictionUnavailable(
            available=False, reason="Aucun partant exploitable dans le pronostic."
        )

    if limit is not None:
        predictions = predictions[:limit]

    return RacePrediction(
        raceId=race_id or "",
        raceLabel=label,
        modelVersion=model_version,
        predictionVersion=prediction_version,
        dataTimestamp=str(block.get("dataTimestamp")) if block.get("dataTimestamp") else None,
        dataQuality=str(block.get("dataQuality")) if block.get("dataQuality") else None,
        confidence=confidence,
        confidenceReasons=_as_str_list(block.get("confidenceReasons")),
        bases=_as_int_list(block.get("bases")),
        chances=_as_int_list(block.get("chances")),
        outsiders=_as_int_list(block.get("outsiders")),
        quinte=_as_int_list(block.get("quinte")),
        tierce=_as_int_list(block.get("tierce")),
        quarte=_as_int_list(block.get("quarte")),
        runners=predictions,
        origin=ORIGIN_PREDICTION,
    )


def _as_int(value: object) -> int | None:
    """Conversion entière tolérante : `None` si la valeur n'est pas un entier."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def resolve_target_race(
    preferred_race_id: str | None = None,
) -> tuple[str | None, int | None, bool]:
    """
    Choisit la course sur laquelle porter le pronostic.

    Retourne `(race_id, document_id, is_preferred)`.

    Le moteur ne traite que les courses rattachées à un **document source**
    LONAB (`source_document_id > 0`) et figurant dans sa propre liste de courses
    exploitables. Si la course souhaitée ne remplit pas ces conditions, on se
    rabat sur la course analysable la plus récente : c'est un repli explicite,
    signalé à l'appelant par `is_preferred = False`.
    """
    supported = engine_supported_ids()
    if not supported:
        return None, None, False

    if preferred_race_id:
        row = race_repo.get_race(preferred_race_id)
        document_id = _as_int(row["source_document_id"]) if row is not None else None
        if document_id is not None and document_id in supported:
            return preferred_race_id, document_id, True

    for row in race_repo.recent_races_with_document(limit=200):
        document_id = _as_int(row["source_document_id"])
        if document_id is not None and document_id in supported:
            return row["race_id"], document_id, False

    return None, None, False


def featured_predictions(
    target_date: str | None = None,
    *,
    limit: int = 10,
    timeout_s: float | None = None,
) -> tuple[str | None, str | None, list[Prediction], str | None]:
    """
    Pronostics mis en avant pour une journée.

    Retourne `(race_id, contexte, predictions, raison d'indisponibilité)`.
    Le contexte et la raison sont mutuellement exclusifs.
    """
    from . import race_service

    resolved_date = target_date or race_service.resolve_target_date()

    preferred_id: str | None = None
    if resolved_date:
        summaries = race_service.list_race_summaries(date=resolved_date, limit=60)
        next_race = next(
            (race for race in summaries if race.status != "finished"),
            summaries[0] if summaries else None,
        )
        preferred_id = next_race.id if next_race is not None else None

    race_id, document_id, is_preferred = resolve_target_race(preferred_id)
    if document_id is None or race_id is None:
        return (
            None,
            None,
            [],
            "Aucune course analysable par le moteur n'est disponible dans la base.",
        )

    predictions, context, reason = top_predictions(
        document_id, race_id, limit=limit, timeout_s=timeout_s
    )
    if context and not is_preferred:
        context = f"Dernière course analysable par le moteur — {context}"

    return race_id, context, predictions, reason


def predict_race_by_race_id(
    race_id: str,
    *,
    limit: int | None = None,
    refresh: bool = False,
    timeout_s: float | None = None,
):
    """Pronostic à partir de l'identifiant interne de la course."""
    row = race_repo.get_race(race_id)
    if row is None:
        return None

    document_id = row["source_document_id"]
    # `source_document_id` vaut 0 pour les courses injectées par les adapters
    # externes : elles n'ont aucun document source, donc le moteur ne peut pas
    # les traiter. On l'annonce clairement plutôt que de laisser remonter
    # l'erreur technique du moteur.
    try:
        usable = document_id is not None and int(document_id) > 0
    except (TypeError, ValueError):
        usable = False

    if not usable:
        return PredictionUnavailable(
            available=False,
            reason=(
                "Cette course n'est pas rattachée à un document source LONAB : le moteur "
                "de pronostics ne peut pas l'analyser. C'est le cas des courses ajoutées "
                "par les collectes externes."
            ),
        )

    return predict_race(
        document_id, race_id=race_id, limit=limit, refresh=refresh, timeout_s=timeout_s
    )


def top_predictions(
    document_id: int | str,
    race_id: str | None = None,
    *,
    limit: int = 5,
    timeout_s: float | None = None,
) -> tuple[list[Prediction], str | None, str | None]:
    """
    Meilleures chances d'une course.

    Retourne `(predictions, contexte, raison d'indisponibilité)`. Les deux
    derniers sont mutuellement exclusifs : soit il y a un pronostic et son
    contexte, soit une raison explicite.
    """
    result = predict_race(document_id, race_id=race_id, limit=limit, timeout_s=timeout_s)

    if isinstance(result, PredictionUnavailable):
        return [], None, result.reason

    context_parts: list[str] = []
    if result.dataQuality:
        context_parts.append(f"qualité {result.dataQuality.lower().replace('_', ' ')}")
    if result.confidence:
        context_parts.append(f"confiance {result.confidence.lower()}")
    context_parts.append(f"modèle {result.modelVersion}")
    context = f"{result.raceLabel} — " + ", ".join(context_parts)

    return result.runners, context, None
