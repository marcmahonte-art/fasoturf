"""Tests du Value engine (#16)."""
from __future__ import annotations

import pytest

from ml.prediction.value import (
    compute_value,
    fractional_to_decimal,
    implied_probability,
)


class TestImpliedProbability:
    def test_decimal_odds(self):
        assert implied_probability(4.0) == pytest.approx(0.25)

    def test_invalid_odds(self):
        assert implied_probability(0) == 0.0
        assert implied_probability(None) == 0.0
        assert implied_probability(-3) == 0.0


class TestFractionalOdds:
    def test_fifteen_to_one(self):
        # 15/1 -> 1/16 = 6.25 %
        assert fractional_to_decimal("15/1") == pytest.approx(16.0)
        assert implied_probability(fractional_to_decimal("15/1")) == pytest.approx(0.0625)

    def test_five_to_two(self):
        assert fractional_to_decimal("5/2") == pytest.approx(3.5)

    def test_decimal_passthrough(self):
        assert fractional_to_decimal(6.9) == pytest.approx(6.9)


class TestValueEdge:
    def test_positive_edge_detected(self):
        # Modèle 12 %, cote 15/1 (6.25 %) -> edge positif
        result = compute_value(1, model_probability=0.12, odds=16.0)
        assert result.value_edge == pytest.approx(0.0575, abs=1e-4)
        assert result.is_value is True

    def test_negative_edge(self):
        result = compute_value(2, model_probability=0.05, odds=2.0)
        assert result.value_edge < 0
        assert result.is_value is False

    def test_threshold_is_configurable(self):
        # Modèle 25 %, cote 5.0 (implicite 20 %) -> edge de 5 %
        # value si seuil 3 %, pas value si seuil 10 %
        low = compute_value(3, 0.25, 5.0, value_threshold=0.03)
        high = compute_value(3, 0.25, 5.0, value_threshold=0.10)
        assert low.is_value is True
        assert high.is_value is False

    def test_value_ratio(self):
        result = compute_value(4, model_probability=0.12, odds=16.0)
        assert result.value_ratio == pytest.approx(0.12 / 0.0625, abs=1e-3)
