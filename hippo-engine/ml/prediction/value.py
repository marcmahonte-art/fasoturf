"""
VALUE ENGINE (#16).

Transforme une cote en probabilité implicite, compare au modèle, et détecte
la value. Le seuil est **configurable**, jamais figé (#16).

Cote décimale   : implied = 1 / odds
Cote fractionnelle (15/1) : implied = 1 / (fraction + 1)

    value_edge  = model_probability - implied_probability
    value_ratio = model_probability / implied_probability
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ValueResult:
    number: int
    odds: float | None
    implied_probability: float
    model_probability: float
    value_edge: float
    value_ratio: float
    is_value: bool
    value_score: float  # normalisé 0..100


def implied_probability(odds: float | None) -> float:
    """Probabilité implicite d'une cote décimale."""
    if not odds or odds <= 0:
        return 0.0
    return 1.0 / float(odds)


def fractional_to_decimal(text: str | float | int | None) -> float | None:
    """Convertit une cote fractionnelle ("15/1") en décimale (16.0)."""
    if text is None:
        return None
    if isinstance(text, (int, float)):
        return float(text)
    raw = str(text).strip()
    if "/" not in raw:
        try:
            return float(raw)
        except ValueError:
            return None
    try:
        num, den = raw.split("/", 1)
        return float(num) / float(den) + 1.0
    except (ValueError, ZeroDivisionError):
        return None


def compute_value(
    number: int,
    model_probability: float,
    odds: float | None,
    *,
    value_threshold: float = 0.03,
    value_ratio_threshold: float = 1.10,
) -> ValueResult:
    """Calcule l'edge d'un partant."""
    implied = implied_probability(odds)
    edge = round(model_probability - implied, 6)
    ratio = round(model_probability / implied, 4) if implied > 0 else 0.0
    is_value = implied > 0 and edge >= value_threshold and ratio >= value_ratio_threshold

    # value_score 0..100 : met l'edge à l'échelle, borné.
    score = 0.0
    if implied > 0:
        score = round(min(max(edge / 0.20, 0.0), 1.0) * 100.0, 2)

    return ValueResult(
        number=number,
        odds=odds,
        implied_probability=round(implied, 6),
        model_probability=round(model_probability, 6),
        value_edge=edge,
        value_ratio=ratio,
        is_value=is_value,
        value_score=score,
    )


def compute_value_all(
    probabilities: dict[int, float],
    odds: dict[int, float | None],
    *,
    value_threshold: float = 0.03,
    value_ratio_threshold: float = 1.10,
) -> dict[int, ValueResult]:
    return {
        num: compute_value(
            num, prob, odds.get(num),
            value_threshold=value_threshold,
            value_ratio_threshold=value_ratio_threshold,
        )
        for num, prob in probabilities.items()
    }
