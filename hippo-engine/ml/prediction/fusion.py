"""
FUSION ENGINE (#18).

    FINAL_SCORE = 30 % CatBoost + 25 % Top3 + 20 % RANK + 15 % Forme + 10 % Value

Les coefficients sont **configurables** (admin / env). Tous les sous-scores
sont ramenés sur 0..100 avant fusion.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import load_config
from ..features.engineering import Features
from ..models.rank import RankResult
from .value import ValueResult

DEFAULT_WEIGHTS = {
    "catboost": 0.30,
    "top3": 0.25,
    "rank": 0.20,
    "form": 0.15,
    "value": 0.10,
}


@dataclass(slots=True)
class FusionResult:
    number: int
    final_score: float
    components: dict[str, float] = field(default_factory=dict)
    contributions: dict[str, float] = field(default_factory=dict)


def compute_fusion(
    number: int,
    *,
    rank: RankResult,
    features: Features,
    catboost_probability: float,
    top3_probability: float,
    value: ValueResult,
    weights: dict[str, float] | None = None,
) -> FusionResult:
    """Fusionne les scores hétérogènes en un score final 0..100."""
    w = weights or load_config().weights

    # Toutes les composantes ramenées sur 0..100.
    # Les probabilités sont mises à l'échelle par rapport à une proba "forte"
    # observée sur un peloton de 15 partants (~1/3 pour Top3, ~1/6 pour gagner).
    catboost_score = round(min(catboost_probability / 0.35, 1.0) * 100.0, 2)
    top3_score = round(min(top3_probability / 0.60, 1.0) * 100.0, 2)
    rank_score = rank.rank_score
    form_score = round((0.5 * features.form_5 + 0.3 * features.form_3 + 0.2 * features.form_10) * 100.0, 2)
    value_score = value.value_score

    components = {
        "catboost": catboost_score,
        "top3": top3_score,
        "rank": rank_score,
        "form": form_score,
        "value": value_score,
    }
    contributions = {k: round(v * w.get(k, 0.0), 3) for k, v in components.items()}
    final = round(sum(contributions.values()), 2)

    return FusionResult(number=number, final_score=final,
                        components=components, contributions=contributions)
