#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration du backend FasoTurf.

La base de données n'est **jamais** codée en dur : elle est détectée au
démarrage parmi des emplacements candidats, puis validée (en-tête SQLite +
présence des tables attendues). `FASOTURF_DB` permet de forcer un chemin.

Règle ADR-001 : la base du socle LONAB est ouverte en **lecture seule**.
"""

from __future__ import annotations

import os
import sqlite3
from functools import lru_cache
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
FASOTURF_DIR = BACKEND_DIR.parent
PROJECT_ROOT = FASOTURF_DIR.parent

#: Emplacements candidats, par ordre de préférence.
CANDIDATE_PATHS: tuple[Path, ...] = (
    PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db",
    PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db",
)

#: Tables minimales attendues pour considérer une base comme exploitable.
REQUIRED_TABLES = {"master_race", "master_runner"}

#: Dossiers exclus lors du balayage de secours.
EXCLUDED_DIRS = {"node_modules", ".git", ".venv", "__pycache__", "dist", "dist_check", "dist_verify"}

SQLITE_HEADER = b"SQLite format 3\x00"


def _is_usable_sqlite(path: Path) -> bool:
    """Vrai si le fichier est une base SQLite contenant les tables attendues."""
    if not path.is_file():
        return False
    try:
        with path.open("rb") as handle:
            if handle.read(16) != SQLITE_HEADER:
                return False
        conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        try:
            names = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        finally:
            conn.close()
    except (OSError, sqlite3.Error):
        return False
    return REQUIRED_TABLES.issubset(names)


def _scan_for_database() -> Path | None:
    """Balayage de secours : première base exploitable trouvée dans le projet."""
    for suffix in ("*.db", "*.sqlite", "*.sqlite3"):
        for path in sorted(PROJECT_ROOT.rglob(suffix)):
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            if _is_usable_sqlite(path):
                return path
    return None


@lru_cache(maxsize=1)
def database_path() -> Path:
    """
    Retourne le chemin de la base exploitée par l'API.

    Ordre : `FASOTURF_DB` → candidats connus → balayage du projet.
    Lève `RuntimeError` si aucune base exploitable n'est trouvée.
    """
    override = os.environ.get("FASOTURF_DB")
    if override:
        path = Path(override).expanduser().resolve()
        if not _is_usable_sqlite(path):
            raise RuntimeError(
                f"FASOTURF_DB pointe vers une base inexploitable : {path}"
            )
        return path

    for candidate in CANDIDATE_PATHS:
        if _is_usable_sqlite(candidate):
            return candidate

    found = _scan_for_database()
    if found is not None:
        return found

    raise RuntimeError(
        "Aucune base SQLite exploitable détectée. "
        "Définissez FASOTURF_DB ou vérifiez pmu-lonab-scraper/data/."
    )


#: Moteur Hippo Engine (prédictions réelles).
HIPPO_ENGINE_DIR = PROJECT_ROOT / "hippo-engine"
HIPPO_ENGINE_TIMEOUT_S = float(os.environ.get("FASOTURF_ENGINE_TIMEOUT", "90"))
HIPPO_ENGINE_ENABLED = os.environ.get("FASOTURF_ENGINE_DISABLED") != "1"

#: Cache mémoire des prédictions (le moteur est coûteux à exécuter).
PREDICTION_CACHE_TTL_S = float(os.environ.get("FASOTURF_PREDICTION_TTL", "900"))

#: Budget accordé au moteur lors de l'appel agrégé du Dashboard : celui-ci ne
#: doit jamais bloquer l'affichage de la page entière.
DASHBOARD_PREDICTION_BUDGET_S = float(os.environ.get("FASOTURF_DASHBOARD_BUDGET", "25"))

#: Nombre de courses affichées dans « Courses à suivre ».
FOLLOWED_RACES_LIMIT = 4

#: Origines de données exposées au frontend (spec §2.3).
ORIGIN_REAL = "real"
ORIGIN_PREDICTION = "prediction"
ORIGIN_OFFICIAL = "official"
ORIGIN_DEMO = "demo"
