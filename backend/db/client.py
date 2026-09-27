#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Client d'accès à la base SQLite.

Point d'entrée unique de la couche données : aucun repository, service ou
routeur n'ouvre de connexion lui-même.

La connexion est **strictement en lecture seule** (`mode=ro`) : l'API ne peut
pas altérer le socle LONAB (ADR-001).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

from ..config import database_path


@contextmanager
def read_connection() -> Iterator[sqlite3.Connection]:
    """
    Ouvre une connexion SQLite en lecture seule et la referme systématiquement.

    Usage :
        with read_connection() as conn:
            rows = conn.execute("SELECT ...").fetchall()
    """
    uri = f"file:{database_path().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    # Requêtes analytiques : on privilégie la lecture séquentielle.
    try:
        conn.execute("PRAGMA query_only = ON")
        yield conn
    finally:
        conn.close()


def query_all(sql: str, params: Sequence[object] = ()) -> list[sqlite3.Row]:
    """Exécute une requête et retourne toutes les lignes."""
    with read_connection() as conn:
        return conn.execute(sql, params).fetchall()


def query_one(sql: str, params: Sequence[object] = ()) -> sqlite3.Row | None:
    """Exécute une requête et retourne la première ligne (ou None)."""
    with read_connection() as conn:
        return conn.execute(sql, params).fetchone()


def query_scalar(sql: str, params: Sequence[object] = (), default: object = None) -> object:
    """Exécute une requête et retourne la première colonne de la première ligne."""
    row = query_one(sql, params)
    if row is None:
        return default
    return row[0]


def table_exists(name: str) -> bool:
    """Vrai si la table (ou vue) existe dans la base courante."""
    row = query_one(
        "SELECT 1 FROM sqlite_master WHERE (type='table' OR type='view') AND name = ?",
        (name,),
    )
    return row is not None


def database_info() -> dict[str, object]:
    """Métadonnées de la base utilisée (pour /api/health)."""
    path = database_path()
    stat = path.stat()
    return {
        "path": str(path),
        "name": path.name,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
    }
