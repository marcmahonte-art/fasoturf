"""Tests du modèle RANK (#9) et du Fusion engine (#18)."""
from __future__ import annotations

from ml.features.engineering import Features
from ml.models.rank import compute_rank
from ml.prediction.fusion import compute_fusion
from ml.prediction.value import compute_value


def _features(**kwargs) -> Features:
    feat = Features(number=kwargs.pop("number", 1))
    for key, value in kwargs.items():
        setattr(feat, key, value)
    return feat


class TestRankScore:
    def test_score_bounded_0_100(self):
        feat = _features(form_3=1, form_5=1, form_10=1, rating_score=1,
                         horse_rating_percentile=1, distance_score=1, terrain_score=1,
                         jockey_win_rate=1, horse_jockey_percentile=1,
                         trainer_win_rate=1, horse_trainer_percentile=1,
                         weight_score=1, draw_score=1, regularity=1)
        result = compute_rank(feat)
        assert 0.0 <= result.rank_score <= 100.0

    def test_weights_sum_to_one(self):
        feat = _features(form_5=0.5)
        result = compute_rank(feat)
        assert sum(result.contributions.values()) == result.rank_score

    def test_better_form_gives_higher_rank(self):
        good = compute_rank(_features(form_3=0.9, form_5=0.9, form_10=0.9, rating_score=0.9))
        bad = compute_rank(_features(form_3=0.1, form_5=0.1, form_10=0.1, rating_score=0.1))
        assert good.rank_score > bad.rank_score

    def test_explainability(self):
        from ml.models.rank import explain
        result = compute_rank(_features(form_5=0.9, rating_score=0.8))
        lines = explain(result, top=2)
        assert len(lines) == 2
        assert all("pts" in line for line in lines)


class TestFusion:
    def test_fusion_bounded(self):
        feat = _features(form_5=0.8, form_3=0.8, form_10=0.8)
        rank = compute_rank(feat)
        value = compute_value(1, 0.2, 5.0)
        fusion = compute_fusion(1, rank=rank, features=feat,
                                catboost_probability=0.2, top3_probability=0.45, value=value)
        assert 0.0 <= fusion.final_score <= 100.0

    def test_weights_are_configurable(self):
        feat = _features(form_5=0.5, form_3=0.5, form_10=0.5)
        rank = compute_rank(feat)
        value = compute_value(1, 0.1, 5.0)
        default = compute_fusion(1, rank=rank, features=feat,
                                 catboost_probability=0.1, top3_probability=0.3, value=value)
        catboost_only = compute_fusion(1, rank=rank, features=feat,
                                       catboost_probability=0.1, top3_probability=0.3, value=value,
                                       weights={"catboost": 1.0, "top3": 0.0, "rank": 0.0,
                                                "form": 0.0, "value": 0.0})
        assert default.final_score != catboost_only.final_score
