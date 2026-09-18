"""
Factory de fournisseurs (#4).

    DATA_PROVIDER=mock      -> MockDataProvider      (aucune dépendance externe)
    DATA_PROVIDER=sqlite    -> SqliteDataProvider    (base réelle du projet)
    DATA_PROVIDER=pmu       -> PmUProvider           (API PMU en direct)
    DATA_PROVIDER=external  -> PmUProvider           (API tierce via EXTERNAL_API_URL)

Le moteur ne connaît jamais le fournisseur concret.
"""
from __future__ import annotations

from ...config import Config, load_config
from .base import DataProvider
from .mock import MockDataProvider
from .pmu import ProviderUnavailable, PmUProvider
from .sqlite_provider import SqliteDataProvider


def build_provider(config: Config | None = None, *, allow_fallback: bool = True) -> DataProvider:
    cfg = config or load_config()
    kind = cfg.data_provider

    if kind == "mock":
        return MockDataProvider()

    if kind == "sqlite":
        return SqliteDataProvider(cfg.sqlite_path)

    if kind in {"pmu", "external"}:
        base = cfg.external_api_url if kind == "external" else "https://www.pmu.fr/services/racing"
        provider = PmUProvider(base_url=base or "https://www.pmu.fr/services/racing")
        if not allow_fallback:
            return provider
        # Sonde : si le réseau est indisponible, on retombe sur le réel local.
        try:
            provider.get_meetings("2026-09-13")
            return provider
        except ProviderUnavailable:
            if cfg.sqlite_path.exists():
                return SqliteDataProvider(cfg.sqlite_path)
            return MockDataProvider()

    raise ValueError(f"DATA_PROVIDER inconnu : {kind}")
