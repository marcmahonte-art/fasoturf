"""Tests de la normalisation multi-fournisseurs (#6)."""
from __future__ import annotations

import pytest

from ml.data.normalize import (
    extract_horse_name,
    normalize_jockey,
    normalize_odds,
    normalize_race,
    normalize_result,
    normalize_runner,
)
from ml.data.schema import ValidationError


class TestHorseNameExtraction:
    def test_provider_a_flat(self):
        assert extract_horse_name({"horse_name": "BIG LOG"}) == "BIG LOG"

    def test_provider_b_nested(self):
        assert extract_horse_name({"runner": {"horse": {"name": "BIG LOG"}}}) == "BIG LOG"

    def test_internal_format(self):
        assert extract_horse_name({"horse": {"name": "BIG LOG"}}) == "BIG LOG"

    def test_legacy_column(self):
        assert extract_horse_name({"nom_cheval_normalized": "big log"}) == "big log"

    def test_missing(self):
        assert extract_horse_name({"foo": "bar"}) is None


class TestNormalizeRunner:
    def test_unifies_to_internal_schema(self):
        runner = normalize_runner({
            "runner": {"horse": {"name": "Aminaco"}, "number": 12},
            "jockey_name": "T.BLANCHOUIN",
            "cote_decimale": 7.0,
        })
        assert runner.horse.name == "AMINACO"
        assert runner.number == 12
        assert runner.jockey.name == "T.BLANCHOUIN"
        assert runner.current_odds == 7.0

    def test_rejects_runner_without_number(self):
        with pytest.raises(ValidationError):
            normalize_runner({"horse": {"name": "X"}})


class TestNormalizeOdds:
    def test_fractional(self):
        assert normalize_odds("15/1") == pytest.approx(16.0)

    def test_decimal_string(self):
        assert normalize_odds("6,9") == pytest.approx(6.9)

    def test_dict(self):
        assert normalize_odds({"rapport": 4.5}) == pytest.approx(4.5)

    def test_none(self):
        assert normalize_odds(None) is None


class TestNormalizeJockey:
    def test_from_string(self):
        assert normalize_jockey("D.SANTIAGO").name == "D.SANTIAGO"

    def test_from_dict(self):
        assert normalize_jockey({"driver_normalized": "T.PICCONE"}).name == "T.PICCONE"

    def test_none(self):
        assert normalize_jockey(None) is None


class TestNormalizeRace:
    def test_full_race(self):
        race = normalize_race({
            "date": "2026-09-13",
            "hippodrome": "strasbourg",
            "discipline": "plat",
            "distance_m": 2000,
            "partants": [
                {"numero": 1, "nom_cheval_normalized": "ALPHA", "cote_decimale": 3.2},
                {"numero": 2, "nom_cheval_normalized": "BETA", "cote_decimale": 12.0},
            ],
        })
        assert race.hippodrome == "STRASBOURG"
        assert race.discipline == "PLAT"
        assert race.distance == 2000
        assert len(race.runners) == 2

    def test_rejects_race_without_date(self):
        with pytest.raises(ValidationError):
            normalize_race({"hippodrome": "X", "partants": []})


class TestNormalizeResult:
    def test_result_order(self):
        result = normalize_result({"race_id": "1", "arrivee": ["4", 12, "7"]})
        assert result.finish_order == [4, 12, 7]

    def test_empty(self):
        assert normalize_result({"race_id": "1"}).finish_order == []
