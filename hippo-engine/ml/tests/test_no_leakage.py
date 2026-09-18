"""
TEST CRITIQUE (#43) — absence de data leakage.

Garantit qu'aucune feature utilisée pour prédire une course ne contient
d'information postérieure à cette course (position d'arrivée, résultat, etc.).

Ce test est bloquant : s'il échoue, le moteur est invalide.
"""
from __future__ import annotations

import inspect

from ml.data.providers.mock import MockDataProvider
from ml.features import engineering
from ml.features.engineering import FORBIDDEN_FEATURE_NAMES, compute_features


class TestFeatureNamesClean:
    def test_no_forbidden_feature_names(self):
        provider = MockDataProvider(seed=7)
        race = provider.get_race(provider.all_race_ids()[0])
        features = compute_features(race)
        for feat in features.values():
            for name in feat.to_vector():
                assert name not in FORBIDDEN_FEATURE_NAMES, (
                    f"Feature interdite détectée : {name} (fuite de la cible)"
                )

    def test_feature_vector_is_numeric_only(self):
        provider = MockDataProvider(seed=11)
        race = provider.get_race(provider.all_race_ids()[0])
        features = compute_features(race)
        for feat in features.values():
            for name, value in feat.to_vector().items():
                assert isinstance(value, (int, float)), f"{name} n'est pas numérique"


class TestNoTargetInInput:
    def test_result_not_read_during_feature_computation(self):
        """``compute_features`` ne doit jamais appeler ``get_results``."""
        provider = MockDataProvider(seed=3)
        race = provider.get_race(provider.all_race_ids()[0])

        called = {"results": False}
        original = provider.get_results

        def spy(race_id):
            called["results"] = True
            return original(race_id)

        provider.get_results = spy  # type: ignore[assignment]
        compute_features(race)
        assert called["results"] is False, (
            "compute_features a lu les résultats : fuite de données"
        )

    def test_history_used_is_strictly_prior(self):
        """
        L'historique d'un partant ne doit contenir que des sorties
        STRICTEMENT antérieures à la course (donc jamais sa propre ligne).
        """
        provider = MockDataProvider(seed=5)
        race = provider.get_race(provider.all_race_ids()[1])
        for runner in race.runners:
            for run in runner.history:
                if run.date:
                    assert run.date < race.date, (
                        f"Historique non antérieur pour le n°{runner.number} : "
                        f"{run.date} >= {race.date}"
                    )


class TestSourceOfFeatures:
    def test_engineering_module_has_no_result_access(self):
        """
        Le module de features ne doit contenir aucun ACCÈS aux résultats.

        On cherche des appels/attributs, pas les mots présents dans la liste
        de constantes ``FORBIDDEN_FEATURE_NAMES`` (qui les cite par nature).
        """
        source = inspect.getsource(engineering)
        for token in ("get_results(", ".finish_order", "get_results)"):
            assert token not in source, (
                f"Le module de features accède aux résultats via '{token}' : fuite"
            )
