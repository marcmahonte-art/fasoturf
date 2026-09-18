"""
Modèle RANK (#9) — score statistique transparent et explicable.

RANK_SCORE = 25 % forme + 20 % classe/rating + 10 % distance + 10 % terrain
           + 10 % jockey + 10 % entraîneur + 5 % poids + 5 % corde
           + 5 % régularité

Chaque sous-score est normalisé 0..100. Le score est **entièrement
explicable** : on peut afficher la contribution de chaque composante.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import load_config
from ..features.engineering import Features

DEFAULT_WEIGHTS = {
    "form": 0.25,
    "rating": 0.20,
    "distance": 0.10,
    "terrain": 0.10,
    "jockey": 0.10,
    "trainer": 0.10,
    "weight": 0.05,
    "draw": 0.05,
    "regularity": 0.05,
}


@dataclass(slots=True)
class RankResult:
    number: int
    rank_score: float
    components: dict[str, float] = field(default_factory=dict)
    contributions: dict[str, float] = field(default_factory=dict)


def _pct(value: float) -> float:
    """0..1 -> 0..100, borné."""
    return round(min(max(value, 0.0), 1.0) * 100.0, 2)


def compute_rank(features: Features, weights: dict[str, float] | None = None) -> RankResult:
    """Calcule le RANK_SCORE d'un partant à partir de ses features."""
    w = weights or load_config().rank_weights

    # Sous-scores 0..100
    form = _pct(0.5 * features.form_5 + 0.3 * features.form_3 + 0.2 * features.form_10)
    rating = _pct(0.6 * features.rating_score + 0.4 * features.horse_rating_percentile)
    distance = _pct(features.distance_score)
    terrain = _pct(features.terrain_score)
    jockey = _pct(0.6 * min(features.jockey_win_rate * 5, 1.0) + 0.4 * features.horse_jockey_percentile)
    trainer = _pct(0.6 * min(features.trainer_win_rate * 5, 1.0) + 0.4 * features.horse_trainer_percentile)
    weight = _pct(features.weight_score)
    draw = _pct(features.draw_score)
    regularity = _pct(features.regularity)

    components = {
        "form": form,
        "rating": rating,
        "distance": distance,
        "terrain": terrain,
        "jockey": jockey,
        "trainer": trainer,
        "weight": weight,
        "draw": draw,
        "regularity": regularity,
    }

    contributions = {key: round(components[key] * w.get(key, 0.0), 3) for key in components}
    score = round(sum(contributions.values()), 2)

    return RankResult(
        number=features.number,
        rank_score=score,
        components=components,
        contributions=contributions,
    )


def compute_rank_all(
    features: dict[int, Features],
    weights: dict[str, float] | None = None,
) -> dict[int, RankResult]:
    return {num: compute_rank(f, weights) for num, f in features.items()}


def explain(result: RankResult, top: int = 3) -> list[str]:
    """Retourne les composantes qui pèsent le plus dans le score."""
    ordered = sorted(result.contributions.items(), key=lambda kv: kv[1], reverse=True)
    return [f"{name} : +{value:.2f} pts (sous-score {result.components[name]:.1f}/100)"
            for name, value in ordered[:top]]
