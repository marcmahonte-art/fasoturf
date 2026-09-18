"""
Modèles CatBoost (#13) — Win / Top3 / Top5.

Trois modèles, versionnés :

    catboost_win_v1
    catboost_top3_v1
    catboost_top5_v1

Ordre de préférence des backends :
    1. CatBoost      (si ``catboost`` est installé)
    2. scikit-learn  (HistGradientBoosting / LogisticRegression)
    3. régression logistique Python pur (aucune dépendance)

Le backend utilisé est enregistré dans les métadonnées du modèle, de sorte
qu'aucune métrique ne puisse être confondue avec celle d'un autre backend.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from ..config import ARTIFACTS_DIR

TARGETS = ("win", "top3", "top5")


def _try_import(name: str):
    try:
        return __import__(name)
    except ImportError:
        return None


# ------------------------------------------------------------------
# Backend 3 : régression logistique Python pur (repli sans dépendance)
# ------------------------------------------------------------------

class PureLogisticRegression:
    """Régression logistique minimale (descente de gradient), sans dépendance."""

    def __init__(self, lr: float = 0.5, epochs: int = 150, l2: float = 1e-3) -> None:
        self.lr = lr
        self.epochs = epochs
        self.l2 = l2
        self.weights: list[float] = []
        self.bias: float = 0.0
        self.feature_names: list[str] = []
        self.mean: list[float] = []
        self.std: list[float] = []

    def _standardise(self, X: list[list[float]]) -> list[list[float]]:
        return [
            [(x - m) / s for x, m, s in zip(row, self.mean, self.std)]
            for row in X
        ]

    def fit(self, X: list[list[float]], y: list[int], feature_names: list[str]) -> "PureLogisticRegression":
        n = len(X)
        if n == 0:
            raise ValueError("Jeu d'entraînement vide")
        d = len(X[0])
        self.feature_names = list(feature_names)

        # Standardisation (indispensable pour la convergence)
        self.mean = [sum(row[j] for row in X) / n for j in range(d)]
        self.std = []
        for j in range(d):
            var = sum((row[j] - self.mean[j]) ** 2 for row in X) / n
            self.std.append(var ** 0.5 or 1.0)

        Xs = self._standardise(X)
        self.weights = [0.0] * d
        self.bias = 0.0

        for _ in range(self.epochs):
            grad_w = [0.0] * d
            grad_b = 0.0
            for row, label in zip(Xs, y):
                z = self.bias + sum(w * x for w, x in zip(self.weights, row))
                pred = 1.0 / (1.0 + math.exp(-max(min(z, 35), -35)))
                error = pred - label
                for j in range(d):
                    grad_w[j] += error * row[j]
                grad_b += error
            for j in range(d):
                self.weights[j] -= self.lr * (grad_w[j] / n + self.l2 * self.weights[j])
            self.bias -= self.lr * (grad_b / n)
        return self

    def predict_proba(self, X: list[list[float]]) -> list[float]:
        Xs = self._standardise(X) if self.mean else X
        out = []
        for row in Xs:
            z = self.bias + sum(w * x for w, x in zip(self.weights, row))
            out.append(1.0 / (1.0 + math.exp(-max(min(z, 35), -35))))
        return out

    def to_dict(self) -> dict:
        return {
            "weights": self.weights,
            "bias": self.bias,
            "feature_names": self.feature_names,
            "mean": self.mean,
            "std": self.std,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "PureLogisticRegression":
        model = cls()
        model.weights = payload["weights"]
        model.bias = payload["bias"]
        model.feature_names = payload.get("feature_names", [])
        model.mean = payload.get("mean", [])
        model.std = payload.get("std", [])
        return model


# ------------------------------------------------------------------
# Modèle unifié
# ------------------------------------------------------------------

@dataclass
class ProbabilityModel:
    """Modèle probabiliste pour une cible (win / top3 / top5)."""
    target: str
    version: str = "v1"
    backend: str = "pure"
    model: object | None = None
    feature_names: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return f"catboost_{self.target}_{self.version}"

    # -- Entraînement ------------------------------------------------

    def fit(self, X: list[list[float]], y: list[int], feature_names: list[str],
            *, prefer: str | None = None) -> "ProbabilityModel":
        self.feature_names = list(feature_names)
        backend = prefer or self._pick_backend()

        if backend == "catboost":
            from catboost import CatBoostClassifier  # type: ignore
            model = CatBoostClassifier(iterations=400, depth=6, learning_rate=0.05,
                                       verbose=False, random_seed=42)
            model.fit(X, y)
            self.model = model
        elif backend == "sklearn":
            from sklearn.ensemble import HistGradientBoostingClassifier  # type: ignore
            model = HistGradientBoostingClassifier(max_iter=300, random_state=42)
            model.fit(X, y)
            self.model = model
        else:
            backend = "pure"
            self.model = PureLogisticRegression().fit(X, y, feature_names)

        self.backend = backend
        return self

    @staticmethod
    def _pick_backend() -> str:
        if _try_import("catboost") is not None:
            return "catboost"
        if _try_import("sklearn") is not None:
            return "sklearn"
        return "pure"

    # -- Prédiction --------------------------------------------------

    def predict_proba(self, X: list[list[float]]) -> list[float]:
        if self.model is None:
            raise RuntimeError("Modèle non entraîné")
        if self.backend == "pure":
            return self.model.predict_proba(X)
        proba = self.model.predict_proba(X)
        return [float(row[1]) for row in proba]

    def predict_one(self, vector: dict[str, float]) -> float:
        row = [[float(vector.get(name, 0.0)) for name in self.feature_names]]
        return round(self.predict_proba(row)[0], 6)

    # -- Sérialisation -----------------------------------------------

    def save(self, directory: Path | None = None) -> Path:
        directory = directory or ARTIFACTS_DIR
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.name}.json"
        payload = {
            "name": self.name,
            "target": self.target,
            "version": self.version,
            "backend": self.backend,
            "feature_names": self.feature_names,
            "metrics": self.metrics,
            "model": self.model.to_dict() if self.backend == "pure" else None,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: Path) -> "ProbabilityModel":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        model = cls(
            target=payload["target"],
            version=payload["version"],
            backend=payload["backend"],
            feature_names=payload["feature_names"],
            metrics=payload.get("metrics", {}),
        )
        if payload["backend"] == "pure" and payload.get("model"):
            model.model = PureLogisticRegression.from_dict(payload["model"])
        else:
            raise RuntimeError(
                f"Le modèle {payload['name']} utilise le backend '{payload['backend']}' : "
                "rechargez-le avec la librairie correspondante installée."
            )
        return model


def train_all_targets(
    X: list[list[float]],
    labels: dict[str, list[int]],
    feature_names: list[str],
    *,
    version: str = "v1",
) -> dict[str, ProbabilityModel]:
    """
    Entraîne les trois modèles (win / top3 / top5).

    Les lignes dont le label vaut -1 (cible inconnue, ex. top5 non renseigné
    parce que l'arrivée ne listait que 4 chevaux) sont exclues.
    """
    models: dict[str, ProbabilityModel] = {}
    for target in TARGETS:
        y_all = labels[target]
        rows = [(x, y) for x, y in zip(X, y_all) if y != -1]
        X_t = [x for x, _ in rows]
        y_t = [y for _, y in rows]
        if not X_t:
            continue
        model = ProbabilityModel(target=target, version=version)
        model.fit(X_t, y_t, feature_names)
        models[target] = model
    return models
