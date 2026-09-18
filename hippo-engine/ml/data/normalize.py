"""
Normalisation multi-fournisseurs (#6).

Les fournisseurs exposent des formats différents :

    Fournisseur A :  {"horse_name": "..."}
    Fournisseur B :  {"runner": {"name": "..."}}

Le format interne est toujours ``runner.horse.name``.

Chaque fonction ``normalize_*`` accepte un dict brut hétérogène et retourne
l'entité interne correspondante, validée. C'est le seul point d'entrée des
données externes vers le moteur.
"""
from __future__ import annotations

from typing import Any

from .schema import (
    HistoricalRun,
    Horse,
    OddsPoint,
    Person,
    Race,
    RaceResult,
    Runner,
    validate_horse,
    validate_person,
    validate_race,
    validate_result,
    validate_runner,
)

# Chemins connus vers le nom du cheval selon le fournisseur.
HORSE_NAME_PATHS: tuple[tuple[str, ...], ...] = (
    ("horse", "name"),
    ("runner", "horse", "name"),
    ("runner", "name"),
    ("horse_name",),
    ("nom_cheval_normalized",),
    ("nom_cheval",),
    ("nom",),
    ("name",),
)


def _dig(raw: dict[str, Any], path: tuple[str, ...]) -> Any:
    node: Any = raw
    for part in path:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def extract_horse_name(raw: dict[str, Any]) -> str | None:
    """Cherche le nom du cheval dans tous les emplacements connus."""
    for path in HORSE_NAME_PATHS:
        value = _dig(raw, path)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def normalize_horse(raw: dict[str, Any]) -> Horse:
    name = extract_horse_name(raw)
    return validate_horse({**raw, "name": name})


def normalize_jockey(raw: dict[str, Any] | None) -> Person | None:
    if not raw:
        return None
    if isinstance(raw, str):
        return validate_person({"name": raw})
    name = (
        raw.get("name")
        or raw.get("nom")
        or raw.get("driver_normalized")
        or raw.get("jockey_name")
        or raw.get("driver")
    )
    return validate_person({**raw, "name": name})


def normalize_trainer(raw: dict[str, Any] | None) -> Person | None:
    if not raw:
        return None
    if isinstance(raw, str):
        return validate_person({"name": raw})
    name = (
        raw.get("name")
        or raw.get("nom")
        or raw.get("entraineur_normalized")
        or raw.get("trainer_name")
        or raw.get("entraineur")
    )
    return validate_person({**raw, "name": name})


def normalize_odds(raw: Any) -> float | None:
    """Accepte une cote décimale, une cote fractionnaire ("15/1") ou un dict."""
    if raw is None:
        return None
    if isinstance(raw, dict):
        raw = raw.get("rapport") or raw.get("odds") or raw.get("cote")
    if isinstance(raw, (int, float)):
        return float(raw) if raw else None
    text = str(raw).strip().replace(",", ".")
    if not text:
        return None
    if "/" in text:
        try:
            num, den = text.split("/", 1)
            fraction = float(num) / float(den)
            return round(fraction + 1.0, 4)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(text)
    except ValueError:
        return None


def normalize_runner(raw: dict[str, Any]) -> Runner:
    payload = dict(raw)
    # Numéro : peut être imbriqué selon le fournisseur.
    if "number" not in payload and "numero" not in payload:
        for path in (("runner", "number"), ("runner", "numero"),
                     ("participant", "numPmu"), ("numPmu",), ("number",)):
            value = _dig(raw, path)
            if value is not None:
                payload["number"] = value
                break
    if "horse" not in payload:
        payload["horse"] = {"name": extract_horse_name(raw), **(raw.get("horse") or {})}
    if "current_odds" not in payload:
        payload["current_odds"] = normalize_odds(
            raw.get("cote_decimale") or raw.get("cote") or raw.get("morning_odds")
        )
    if "jockey" not in payload:
        payload["jockey"] = raw.get("driver") or raw.get("jockey") or raw.get("jockey_name")
    if "trainer" not in payload:
        payload["trainer"] = raw.get("entraineur") or raw.get("trainer")
    runner = validate_runner(payload)
    runner.history = normalize_history(raw.get("history") or raw.get("performances") or [])
    runner.odds_history = [
        OddsPoint(odds=o["odds"], timestamp=o.get("timestamp", ""), source=o.get("source", "pmu"))
        for o in (raw.get("odds_history") or [])
        if o.get("odds")
    ]
    return runner


def normalize_history(raw_history: Any) -> list[HistoricalRun]:
    """Normalise l'historique d'un cheval (liste de sorties passées)."""
    if not raw_history or not isinstance(raw_history, (list, tuple)):
        return []
    runs: list[HistoricalRun] = []
    for item in raw_history:
        if isinstance(item, (int, float)):
            runs.append(HistoricalRun(date="", finish_position=int(item)))
            continue
        if not isinstance(item, dict):
            continue
        pos = item.get("finish_position", item.get("place", item.get("position")))
        try:
            pos_int = int(pos) if pos is not None and str(pos).strip() != "" else None
        except (TypeError, ValueError):
            pos_int = None
        runs.append(HistoricalRun(
            date=str(item.get("date", ""))[:10],
            finish_position=pos_int,
            distance=item.get("distance"),
            terrain=str(item.get("terrain", "")).upper(),
            hippodrome=str(item.get("hippodrome", "")).upper(),
            weight=item.get("weight") or item.get("poids"),
            draw=item.get("draw") or item.get("corde"),
            official_rating=item.get("official_rating") or item.get("valeur"),
            jockey=str(item.get("jockey", "")).upper(),
            trainer=str(item.get("trainer", "")).upper(),
            odds=item.get("odds"),
        ))
    return runs


def normalize_race(raw: dict[str, Any]) -> Race:
    payload = dict(raw)
    if "date" not in payload:
        payload["date"] = str(raw.get("date_course") or raw.get("date_publication") or "")[:10]
    payload["runners"] = [normalize_runner(r) for r in (raw.get("runners") or raw.get("partants") or [])]
    return validate_race(payload)


def normalize_result(raw: dict[str, Any]) -> RaceResult:
    payload = dict(raw)
    if "finish_order" not in payload:
        payload["finish_order"] = raw.get("arrivee") or raw.get("ordre_arrivee") or []
    return validate_result(payload)
