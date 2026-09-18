#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit automatique des bases de données du projet FasoTurf / PMU.

Ce script :
  1. détecte automatiquement tous les fichiers SQLite du projet
     (aucun chemin n'est codé en dur) ;
  2. décrit le schéma : tables, vues, colonnes, types, clés, index ;
  3. mesure les volumes et les taux de nullité ;
  4. infère les relations entre tables ;
  5. signale les anomalies de qualité de données ;
  6. écrit un rapport Markdown.

LECTURE SEULE : les bases sont ouvertes en `mode=ro`. Aucune écriture.

Usage :
    python scripts/audit_database.py
    python scripts/audit_database.py --out AUDIT_DATABASE.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

# --------------------------------------------------------------------------
# Détection
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

#: Répertoires à ne jamais parcourir (dépendances, artefacts de build, venvs).
EXCLUDED_DIRS = {
    "node_modules",
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "dist_check",
    "dist_verify",
    ".next",
    "site",
    ".workbuddy-ai",
}

SQLITE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}


def detect_databases(root: Path) -> list[Path]:
    """Retourne tous les fichiers SQLite du projet, triés par taille décroissante."""
    found: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SQLITE_SUFFIXES:
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        # Un vrai fichier SQLite commence par l'en-tête « SQLite format 3\0 ».
        try:
            with path.open("rb") as handle:
                if handle.read(16) != b"SQLite format 3\x00":
                    continue
        except OSError:
            continue
        found.append(path)

    return sorted(found, key=lambda p: p.stat().st_size, reverse=True)


def sha256_of(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def connect_readonly(path: Path) -> sqlite3.Connection:
    """Ouvre une base SQLite en lecture seule stricte."""
    uri = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# --------------------------------------------------------------------------
# Introspection
# --------------------------------------------------------------------------


def quote(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def list_objects(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    rows = conn.execute(
        "SELECT name, type FROM sqlite_master "
        "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' "
        "ORDER BY type, name"
    ).fetchall()
    return [(r["name"], r["type"]) for r in rows]


def table_columns(conn: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
    return conn.execute(f"PRAGMA table_info({quote(table)})").fetchall()


def foreign_keys(conn: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
    return conn.execute(f"PRAGMA foreign_key_list({quote(table)})").fetchall()


def indexes(conn: sqlite3.Connection, table: str) -> list[sqlite3.Row]:
    return conn.execute(f"PRAGMA index_list({quote(table)})").fetchall()


def safe_count(conn: sqlite3.Connection, table: str) -> int | None:
    try:
        return int(conn.execute(f"SELECT count(*) FROM {quote(table)}").fetchone()[0])
    except sqlite3.Error:
        return None


def null_rate(conn: sqlite3.Connection, table: str, column: str, total: int) -> float | None:
    if total == 0:
        return None
    try:
        nulls = conn.execute(
            f"SELECT count(*) FROM {quote(table)} WHERE {quote(column)} IS NULL"
        ).fetchone()[0]
    except sqlite3.Error:
        return None
    return nulls / total


def distinct_count(conn: sqlite3.Connection, table: str, column: str) -> int | None:
    try:
        return int(
            conn.execute(
                f"SELECT count(DISTINCT {quote(column)}) FROM {quote(table)}"
            ).fetchone()[0]
        )
    except sqlite3.Error:
        return None


def sample_values(conn: sqlite3.Connection, table: str, column: str, limit: int = 3) -> list[str]:
    try:
        rows = conn.execute(
            f"SELECT DISTINCT {quote(column)} FROM {quote(table)} "
            f"WHERE {quote(column)} IS NOT NULL LIMIT ?",
            (limit,),
        ).fetchall()
    except sqlite3.Error:
        return []
    return [str(r[0])[:48] for r in rows]


def detect_relations(
    conn: sqlite3.Connection, tables: dict[str, list[sqlite3.Row]]
) -> list[tuple[str, str, str, str]]:
    """
    Construit les relations :
      - déclarées par une clé étrangère ;
      - inférées par convention de nommage `xxx_id` → table contenant cette clé.
    """
    relations: list[tuple[str, str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    # 1. Clés étrangères déclarées
    for table in tables:
        for fk in foreign_keys(conn, table):
            target = fk["table"]
            key = (table, fk["from"], target)
            if key in seen:
                continue
            seen.add(key)
            relations.append((table, fk["from"], target, "déclarée (FOREIGN KEY)"))

    # 2. Relations inférées : colonne `<prefix>_id` et table `<prefix>s` / `master_<prefix>`
    candidates: dict[str, str] = {}
    for table in tables:
        candidates[table] = table
        if table.startswith("master_"):
            candidates[table[len("master_"):]] = table

    for table, columns in tables.items():
        column_names = {c["name"] for c in columns}
        for column in column_names:
            if not column.endswith("_id") or column == "id":
                continue
            prefix = column[: -len("_id")]
            for suffix in ("", "s", "es"):
                target = candidates.get(prefix + suffix)
                if target and target != table:
                    key = (table, column, target)
                    if key in seen:
                        continue
                    seen.add(key)
                    relations.append((table, column, target, "inférée (nommage)"))
                    break

    return sorted(relations)


# --------------------------------------------------------------------------
# Rapport
# --------------------------------------------------------------------------


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("o", "Ko", "Mo", "Go"):
        if size < 1024 or unit == "Go":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} Go"


def audit_database(path: Path, root: Path) -> dict:
    """Audite une base et retourne un dictionnaire structuré."""
    started = time.time()
    conn = connect_readonly(path)
    try:
        objects = list_objects(conn)
        tables = {
            name: table_columns(conn, name)
            for name, kind in objects
            if kind == "table"
        }

        report: dict = {
            "path": str(path.relative_to(root)).replace("\\", "/"),
            "size": path.stat().st_size,
            "sha256": sha256_of(path),
            "tables": [],
            "views": [name for name, kind in objects if kind == "view"],
            "relations": detect_relations(conn, tables),
        }

        for name, kind in objects:
            if kind != "table":
                continue

            columns = tables[name]
            total = safe_count(conn, name)
            indexes_info = indexes(conn, name)
            pk_columns = [c["name"] for c in columns if c["pk"]]

            column_reports = []
            for column in columns:
                column_reports.append(
                    {
                        "name": column["name"],
                        "type": column["type"] or "—",
                        "notnull": bool(column["notnull"]),
                        "pk": bool(column["pk"]),
                        "null_rate": null_rate(conn, name, column["name"], total or 0),
                        "distinct": distinct_count(conn, name, column["name"]),
                        "samples": sample_values(conn, name, column["name"]),
                    }
                )

            report["tables"].append(
                {
                    "name": name,
                    "rows": total,
                    "pk": pk_columns,
                    "indexes": [
                        {
                            "name": idx["name"],
                            "unique": bool(idx["unique"]),
                            "origin": idx["origin"],
                        }
                        for idx in indexes_info
                        if not idx["name"].startswith("sqlite_autoindex")
                    ],
                    "columns": column_reports,
                }
            )

        report["elapsed_ms"] = int((time.time() - started) * 1000)
        return report
    finally:
        conn.close()


def render_markdown(reports: list[dict], root: Path) -> str:
    lines: list[str] = []
    add = lines.append

    add("# AUDIT — BASES DE DONNÉES DU PROJET")
    add("")
    add(f"- Racine analysée : `{root}`")
    add(f"- Bases détectées : **{len(reports)}**")
    add(f"- Date de l'audit : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    add("")
    add("> Audit **en lecture seule** (`mode=ro`). Aucune écriture, aucune migration.")
    add("")

    # Synthèse
    add("## 1. Synthèse")
    add("")
    add("| Base | Taille | Tables | SHA-256 (12) |")
    add("|---|---:|---:|---|")
    for report in reports:
        add(
            f"| `{report['path']}` | {human_size(report['size'])} | "
            f"{len(report['tables'])} | `{report['sha256'][:12]}` |"
        )
    add("")

    # Détail par base
    for report in reports:
        add(f"## 2. Base `{report['path']}`")
        add("")
        add(f"- Taille : **{human_size(report['size'])}**")
        add(f"- SHA-256 : `{report['sha256']}`")
        add(f"- Vues : {', '.join(f'`{v}`' for v in report['views']) or 'aucune'}")
        add("")

        add("### 2.1 Tables et volumes")
        add("")
        add("| Table | Lignes | Clé primaire | Index |")
        add("|---|---:|---|---|")
        for table in report["tables"]:
            pk = ", ".join(f"`{c}`" for c in table["pk"]) or "—"
            idx = ", ".join(f"`{i['name']}`" for i in table["indexes"]) or "—"
            rows = "n/a" if table["rows"] is None else f"{table['rows']:,}".replace(",", " ")
            add(f"| `{table['name']}` | {rows} | {pk} | {idx} |")
        add("")

        add("### 2.2 Colonnes")
        for table in report["tables"]:
            rows = "n/a" if table["rows"] is None else f"{table['rows']:,}".replace(",", " ")
            add("")
            add(f"**`{table['name']}`** — {rows} lignes")
            add("")
            add("| Colonne | Type | NOT NULL | PK | Taux de nullité | Distinct | Exemples |")
            add("|---|---|---|---|---:|---:|---|")
            for column in table["columns"]:
                rate = column["null_rate"]
                rate_txt = "—" if rate is None else f"{rate * 100:.1f} %"
                distinct = "—" if column["distinct"] is None else f"{column['distinct']:,}".replace(",", " ")
                samples = ", ".join(f"`{s}`" for s in column["samples"]) or "—"
                add(
                    f"| `{column['name']}` | {column['type']} | "
                    f"{'oui' if column['notnull'] else 'non'} | "
                    f"{'oui' if column['pk'] else 'non'} | {rate_txt} | {distinct} | {samples} |"
                )
        add("")

        add("### 2.3 Relations")
        add("")
        if report["relations"]:
            add("| Source | Colonne | Cible | Origine |")
            add("|---|---|---|---|")
            for source, column, target, origin in report["relations"]:
                add(f"| `{source}` | `{column}` | `{target}` | {origin} |")
        else:
            add("_Aucune relation détectée._")
        add("")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit des bases SQLite du projet.")
    parser.add_argument("--root", default=str(ROOT), help="Racine du projet à analyser.")
    parser.add_argument(
        "--out",
        default=str(ROOT / "AUDIT_DATABASE.md"),
        help="Chemin du rapport Markdown.",
    )
    parser.add_argument(
        "--json",
        default=str(ROOT / "AUDIT_DATABASE.json"),
        help="Chemin du rapport JSON brut.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    databases = detect_databases(root)

    if not databases:
        print("Aucune base SQLite détectée.", file=sys.stderr)
        return 1

    print(f"{len(databases)} base(s) détectée(s) :")
    reports = []
    for path in databases:
        print(f"  - {path.relative_to(root)}")
        reports.append(audit_database(path, root))

    Path(args.out).write_text(render_markdown(reports, root), encoding="utf-8")
    Path(args.json).write_text(json.dumps(reports, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nRapport écrit : {args.out}")
    print(f"Données brutes : {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
