"""
Configuration centralisée du moteur.

Toutes les valeurs sont surchargeables par variables d'environnement (#41).
Aucune clé n'est jamais lue depuis le frontend.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "ml" / "models" / "artifacts"
DEMO_DATA_DIR = PROJECT_ROOT / "ml" / "data" / "demo"

# Base SQLite réelle existante (actif réutilisable du repo).
DEFAULT_SQLITE_PATH = Path(
    r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db"
)


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Config:
    """Paramètres du moteur. Instancier via :func:`load_config`."""

    data_provider: str = "sqlite"          # mock | sqlite | pmu | external
    sqlite_path: Path = DEFAULT_SQLITE_PATH
    database_url: str | None = None

    external_api_url: str | None = None
    external_api_key: str | None = None

    ml_service_url: str | None = None
    redis_url: str | None = None

    # Seuil de détection VALUE (#16). Configurable en admin, jamais figé.
    value_threshold: float = 0.03
    value_ratio_threshold: float = 1.10

    model_version: str = "catboost_v1"
    prediction_version: str = "v1"

    # Pondérations du Fusion Engine (#18). Configurables.
    weights: dict[str, float] = field(default_factory=lambda: {
        "catboost": 0.30,
        "top3": 0.25,
        "rank": 0.20,
        "form": 0.15,
        "value": 0.10,
    })

    # Pondérations du modèle RANK (#9).
    rank_weights: dict[str, float] = field(default_factory=lambda: {
        "form": 0.25,
        "rating": 0.20,
        "distance": 0.10,
        "terrain": 0.10,
        "jockey": 0.10,
        "trainer": 0.10,
        "weight": 0.05,
        "draw": 0.05,
        "regularity": 0.05,
    })

    # Découpage temporel train/valid/test (#14).
    train_until: str = "2023-12-31"
    valid_until: str = "2024-12-31"

    def validate(self) -> None:
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Les pondérations du Fusion Engine doivent sommer à 1.0 (actuel : {total})"
            )
        rank_total = sum(self.rank_weights.values())
        if abs(rank_total - 1.0) > 1e-6:
            raise ValueError(
                f"Les pondérations RANK doivent sommer à 1.0 (actuel : {rank_total})"
            )
        if self.data_provider not in {"mock", "sqlite", "pmu", "external"}:
            raise ValueError(f"DATA_PROVIDER inconnu : {self.data_provider}")


def load_config(**overrides) -> Config:
    cfg = Config(
        data_provider=os.environ.get("DATA_PROVIDER", "sqlite"),
        sqlite_path=Path(os.environ.get("SQLITE_PATH", str(DEFAULT_SQLITE_PATH))),
        database_url=os.environ.get("DATABASE_URL"),
        external_api_url=os.environ.get("EXTERNAL_API_URL"),
        external_api_key=os.environ.get("EXTERNAL_API_KEY"),
        ml_service_url=os.environ.get("ML_SERVICE_URL"),
        redis_url=os.environ.get("REDIS_URL"),
        value_threshold=_env_float("VALUE_THRESHOLD", 0.03),
        value_ratio_threshold=_env_float("VALUE_RATIO_THRESHOLD", 1.10),
        model_version=os.environ.get("MODEL_VERSION", "catboost_v1"),
    )
    for key, value in overrides.items():
        if not hasattr(cfg, key):
            raise AttributeError(f"Config inconnue : {key}")
        setattr(cfg, key, value)
    cfg.validate()
    return cfg
