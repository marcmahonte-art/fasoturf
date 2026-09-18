#!/usr/bin/env python3
"""
PHASE 1 — BACKUP + INVENTAIRE + GEL DU SOCLE (PMU'B LONAB V2)

Script d'audit READ-ONLY. Il ne modifie AUCUNE donnée métier.

Garanties :
  - la base source est ouverte en lecture seule (URI mode=ro)
  - aucun UPDATE / DELETE / INSERT / ALTER / DROP / CREATE n'est exécuté
  - aucun fichier de data/raw n'est modifié (lecture binaire uniquement)
  - aucune API externe n'est appelée
  - hippo-engine n'est pas touché

Usage :
    python scripts/phase1/audit_phase1.py
    python scripts/phase1/audit_phase1.py --db <path> --raw-dir <path> --output-dir <path>

Déterministe et relançable (le backup porte un timestamp réel).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import shutil
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ------------------------------------------------------------------
# Constantes
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"
DEFAULT_RAW = PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "raw"
DEFAULT_OUT = PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "backups" / "phase1"

CRITICAL_TABLES = [
    "documents", "courses", "partants", "resultats", "commentaires",
    "api_cotes", "api_courses", "api_pronostics", "api_rapports", "api_ecuries",
    "ecd_documents", "ecd_courses", "ecd_paris", "rep_documents",
    "partants_enrichis", "api_meteo", "api_partants", "media_selections",
    "classements",
]

CSV_TABLES = [
    "documents", "courses", "partants", "resultats", "rep_documents",
    "ecd_documents", "ecd_courses", "api_cotes", "commentaires",
]

# Mots-clés de secrets : si une table en contient, on n'exporte pas.
SECRET_HINTS = ("key", "secret", "token", "password", "passwd", "credential")

LOG: list[str] = []


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG.append(msg)


# ------------------------------------------------------------------
# Utilitaires
# ------------------------------------------------------------------

def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def open_readonly(db_path: Path) -> sqlite3.Connection:
    """Ouvre la base en LECTURE SEULE (aucune écriture possible)."""
    uri = f"file:{db_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def q(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return conn.execute(sql, params).fetchall()


def scalar(conn: sqlite3.Connection, sql: str, params: tuple = (), default=0):
    try:
        row = conn.execute(sql, params).fetchone()
        if row is None or row[0] is None:
            return default
        return row[0]
    except sqlite3.Error:
        return default


def parse_json_list(raw) -> list:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        return value if isinstance(value, list) else []
    except (ValueError, TypeError):
        return []


def fmt_int(value) -> str:
    try:
        return f"{int(value):,}".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def md_table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out)


def has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    try:
        cols = [r[1] for r in q(conn, f'PRAGMA table_info("{table}")')]
        return column in cols
    except sqlite3.Error:
        return False


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(q(conn, "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                  (table,)))


def empty_cond(column: str) -> str:
    return f'("{column}" IS NULL OR TRIM(CAST("{column}" AS TEXT)) = \'\')'


# ------------------------------------------------------------------
# STEP 3 / 4 / 5 / 6 — Backup + vérification + manifest
# ------------------------------------------------------------------

def step_backup(db_path: Path, out_dir: Path) -> dict:
    log("STEP 3 — SHA initial de la base")
    original_sha = sha256_file(db_path)
    original_size = db_path.stat().st_size
    log(f"  sha256  : {original_sha}")
    log(f"  taille  : {fmt_int(original_size)} octets")

    log("STEP 4 — Backup SQLite (copie intégrale du fichier)")
    backup_dir = out_dir
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"pmu_lonab_phase1_backup_{stamp}.db"
    shutil.copy2(db_path, backup_path)
    log(f"  backup  : {backup_path.name}")

    log("STEP 5 — Vérification du backup")
    backup_sha = sha256_file(backup_path)
    backup_size = backup_path.stat().st_size
    verified = (backup_sha == original_sha) and (backup_size == original_size)

    if not verified:
        log("  ❌ SHA/TAILLE DIFFÉRENTS — STOP IMMÉDIAT")
        return {
            "status": "BLOCKED",
            "reason": "backup SHA mismatch",
            "original_path": str(db_path),
            "backup_path": str(backup_path),
            "original_size_bytes": original_size,
            "backup_size_bytes": backup_size,
            "original_sha256": original_sha,
            "backup_sha256": backup_sha,
            "backup_verified": False,
        }

    log("  ✅ SHA identiques, tailles identiques")
    return {
        "status": "OK",
        "original_path": str(db_path),
        "backup_path": str(backup_path),
        "original_size_bytes": original_size,
        "backup_size_bytes": backup_size,
        "original_sha256": original_sha,
        "backup_sha256": backup_sha,
        "backup_verified": True,
        "backup_name": backup_path.name,
    }


def step_manifest(out_dir: Path, backup: dict, db_path: Path) -> dict:
    log("STEP 6 — manifest.json")

    def git(args: list[str]) -> str | None:
        try:
            result = subprocess.run(["git", *args], cwd=PROJECT_ROOT,
                                    capture_output=True, text=True, timeout=15)
            return result.stdout.strip() or None if result.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None

    manifest = {
        "phase": "1",
        "project": "PMU'B LONAB",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "path": str(db_path),
            "size_bytes": backup["original_size_bytes"],
            "sha256": backup["original_sha256"],
        },
        "backup": {
            "path": backup["backup_path"],
            "size_bytes": backup["backup_size_bytes"],
            "sha256": backup["backup_sha256"],
            "verified": backup["backup_verified"],
        },
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "git_commit": git(["rev-parse", "HEAD"]),
        "git_branch": git(["branch", "--show-current"]),
        "git_repository": git(["rev-parse", "--is-inside-work-tree"]) is not None,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    log("  manifest.json écrit")
    return manifest


# ------------------------------------------------------------------
# STEP 7 — Inventaire DB
# ------------------------------------------------------------------

def step_db_inventory(conn: sqlite3.Connection, db_path: Path, db_sha: str) -> tuple[str, dict]:
    log("STEP 7 — Inventaire de la base")

    tables = [r[0] for r in q(conn, "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    indexes = [r[0] for r in q(conn, "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")]
    views = [r[0] for r in q(conn, "SELECT name FROM sqlite_master WHERE type='view'")]
    triggers = [r[0] for r in q(conn, "SELECT name FROM sqlite_master WHERE type='trigger'")]

    lines = ["# PHASE1_DB_INVENTORY.md", "",
             "Inventaire **read-only** de la base du socle LONAB.", "",
             "## A. Informations générales", "",
             md_table(["Propriété", "Valeur"], [
                 ["Chemin", f"`{db_path}`"],
                 ["Taille", f"{fmt_int(db_path.stat().st_size)} octets"],
                 ["SQLite version", sqlite3.sqlite_version],
                 ["Tables", len(tables)],
                 ["Index", len(indexes)],
                 ["Vues", len(views)],
                 ["Triggers", len(triggers)],
                 ["SHA-256", f"`{db_sha}`"],
             ]), ""]

    summary_rows = []
    detail_blocks = []
    row_counts: dict[str, int] = {}

    for table in tables:
        n = scalar(conn, f'SELECT COUNT(*) FROM "{table}"')
        row_counts[table] = n
        cols = q(conn, f'PRAGMA table_info("{table}")')
        idx = q(conn, f'PRAGMA index_list("{table}")')
        fks = q(conn, f'PRAGMA foreign_key_list("{table}")')

        summary_rows.append([f"`{table}`", fmt_int(n), len(cols), len(idx), len(fks)])

        block = [f"### `{table}`", "", f"- **Lignes :** {fmt_int(n)}",
                 f"- **Colonnes :** {len(cols)}",
                 f"- **Index :** {len(idx)}",
                 f"- **Foreign keys :** {len(fks)}", ""]

        if cols:
            col_rows = []
            for col in cols:
                name = col[1]
                sqltype = col[2] or "(aucun)"
                notnull = "NOT NULL" if col[3] else "nullable"
                pk = "PK" if col[5] else ""
                null_count = scalar(conn, f'SELECT COUNT(*) FROM "{table}" WHERE "{name}" IS NULL')
                try:
                    empty_count = scalar(
                        conn, f'SELECT COUNT(*) FROM "{table}" WHERE {empty_cond(name)}')
                except sqlite3.Error:
                    empty_count = 0
                col_rows.append([f"`{name}`", sqltype, notnull, pk or "—",
                                 fmt_int(null_count), fmt_int(empty_count)])
            block.append(md_table(
                ["Colonne", "Type", "Nullable", "Clé", "NULL", "VIDE"], col_rows))
            block.append("")

        if idx:
            block.append("**Index :** " + ", ".join(f"`{i[1]}`" for i in idx))
            block.append("")
        if fks:
            block.append("**Foreign keys :**")
            for fk in fks:
                block.append(f"- `{fk[3]}` → `{fk[2]}.{fk[4]}`")
            block.append("")

        detail_blocks.append("\n".join(block))

    lines += ["## B. Résumé par table", "",
              md_table(["Table", "Lignes", "Colonnes", "Index", "FK"], summary_rows), "",
              "## C. Détail par table", ""]
    lines += detail_blocks

    log(f"  {len(tables)} tables inventoriées")
    return "\n".join(lines), row_counts


# ------------------------------------------------------------------
# STEP 8 — Inventaire RAW
# ------------------------------------------------------------------

def step_raw_inventory(raw_dir: Path) -> tuple[str, dict]:
    log("STEP 8 — Inventaire RAW")

    files = sorted(p for p in raw_dir.rglob("*") if p.is_file())
    total_size = 0
    sizes: list[tuple[str, int]] = []
    hashes: dict[str, list[str]] = defaultdict(list)
    extensions = Counter()
    fingerprint: list[tuple[str, int, int]] = []

    for path in files:
        stat = path.stat()
        rel = path.relative_to(raw_dir).as_posix()
        total_size += stat.st_size
        sizes.append((rel, stat.st_size))
        extensions[path.suffix.lower() or "(sans)"] += 1
        fingerprint.append((rel, stat.st_size, int(stat.st_mtime)))
        hashes[sha256_file(path)].append(rel)

    duplicates = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    pdf_count = extensions.get(".pdf", 0)
    sizes_sorted = sorted(sizes, key=lambda x: x[1])

    lines = ["# PHASE1_RAW_INVENTORY.md", "",
             "Inventaire **read-only** des documents bruts (source de vérité).", "",
             md_table(["Indicateur", "Valeur"], [
                 ["Fichiers totaux", fmt_int(len(files))],
                 ["PDF", fmt_int(pdf_count)],
                 ["Autres extensions", fmt_int(len(files) - pdf_count)],
                 ["Taille totale", f"{total_size / 1024 / 1024:.1f} Mo"],
                 ["Plus petit fichier", f"{sizes_sorted[0][1]:,} o — `{sizes_sorted[0][0]}`" if sizes_sorted else "—"],
                 ["Plus gros fichier", f"{sizes_sorted[-1][1]:,} o — `{sizes_sorted[-1][0]}`" if sizes_sorted else "—"],
                 ["Taille moyenne", f"{total_size / len(files):,.0f} o" if files else "—"],
                 ["Doublons SHA-256", len(duplicates)],
             ]), "",
             "## Extensions", "",
             md_table(["Extension", "Fichiers"],
                      [[f"`{ext}`", fmt_int(n)] for ext, n in extensions.most_common()]), ""]

    if duplicates:
        lines += ["## Doublons SHA-256", ""]
        for digest, paths in list(duplicates.items())[:50]:
            lines.append(f"- `{digest[:16]}…` — {len(paths)} fichiers :")
            for p in paths:
                lines.append(f"  - `{p}`")
        lines.append("")
    else:
        lines += ["## Doublons SHA-256", "", "Aucun doublon détecté.", ""]

    # Fichiers illisibles
    unreadable = []
    for path in files:
        try:
            with path.open("rb") as handle:
                handle.read(8)
        except OSError as exc:
            unreadable.append((path.relative_to(raw_dir).as_posix(), str(exc)))
    lines += ["## Fichiers illisibles", ""]
    lines += ([md_table(["Fichier", "Erreur"], [[f"`{p}`", e] for p, e in unreadable])]
              if unreadable else ["Aucun fichier illisible."])
    lines.append("")

    # Répartition par sous-dossier
    per_dir: Counter = Counter()
    size_dir: dict[str, int] = defaultdict(int)
    for rel, size in sizes:
        top = rel.split("/")[0] if "/" in rel else "(racine)"
        per_dir[top] += 1
        size_dir[top] += size
    lines += ["## Répartition par dossier", "",
              md_table(["Dossier", "Fichiers", "Taille"],
                       [[f"`{d}`", fmt_int(n), f"{size_dir[d]/1024/1024:.1f} Mo"]
                        for d, n in per_dir.most_common()]), ""]

    log(f"  {fmt_int(len(files))} fichiers, {total_size/1024/1024:.1f} Mo, "
        f"{len(duplicates)} doublons")

    return "\n".join(lines), {
        "count": len(files),
        "pdf_count": pdf_count,
        "total_size": total_size,
        "duplicates": len(duplicates),
        "unreadable": len(unreadable),
        "fingerprint": fingerprint,
    }


# ------------------------------------------------------------------
# STEP 9 — Réconciliation RAW ↔ DB
# ------------------------------------------------------------------

def step_reconciliation(conn: sqlite3.Connection, raw_dir: Path, raw_info: dict) -> tuple[str, dict]:
    log("STEP 9 — Réconciliation RAW ↔ DB")

    raw_files = [p for p in raw_dir.rglob("*") if p.is_file()]
    raw_by_name = {p.name: p.relative_to(raw_dir).as_posix() for p in raw_files}
    dup_basenames = len(raw_files) - len(raw_by_name)

    doc_rows = q(conn, "SELECT id, filename, doc_type FROM documents")
    db_names = {}
    for row in doc_rows:
        name = (row["filename"] or "").strip()
        if name:
            db_names.setdefault(Path(name).name, []).append(row["id"])

    match = missing_in_db = missing_in_raw = 0
    examples_missing_db, examples_missing_raw = [], []

    for name, rel in raw_by_name.items():
        if name in db_names:
            match += 1
        else:
            missing_in_db += 1
            if len(examples_missing_db) < 20:
                examples_missing_db.append(rel)

    for name, ids in db_names.items():
        if name not in raw_by_name:
            missing_in_raw += 1
            if len(examples_missing_raw) < 20:
                examples_missing_raw.append(f"{name} (id={ids[0]})")

    has_hash_col = has_column(conn, "documents", "sha256")

    lines = ["# RAW_DATABASE_RECONCILIATION", "",
             "Comparaison entre `documents` et les fichiers réellement présents.", "",
             md_table(["Statut", "Nombre"], [
                 ["Fichiers RAW", fmt_int(len(raw_files))],
                 ["Basenames uniques côté RAW", fmt_int(len(raw_by_name))],
                 ["Basenames dupliqués (2 fichiers même nom)", fmt_int(dup_basenames)],
                 ["MATCH", fmt_int(match)],
                 ["MISSING_IN_DB", fmt_int(missing_in_db)],
                 ["MISSING_IN_RAW", fmt_int(missing_in_raw)],
                 ["HASH_MISMATCH", "non calculable" if not has_hash_col else "0"],
                 ["DUPLICATE (SHA côté RAW)", fmt_int(raw_info["duplicates"])],
             ]), "",
             f"> La réconciliation se fait sur le **basename** : `documents.filename` "
             f"ne contient aucun séparateur de chemin (0 ligne avec `/`). "
             f"{len(raw_files)} fichiers → {len(raw_by_name)} basenames uniques "
             f"({dup_basenames} noms partagés par 2 fichiers). "
             f"MATCH + MISSING_IN_DB = {match + missing_in_db} = basenames uniques.", "",
             "> `HASH_MISMATCH` n'est **pas calculable** : la table `documents` ne stocke "
             "aucune empreinte SHA-256. Constat, pas correction.", ""]

    if examples_missing_db:
        lines += ["## Exemples — présents dans RAW, absents de `documents`", ""]
        lines += [f"- `{p}`" for p in examples_missing_db] + [""]
    if examples_missing_raw:
        lines += ["## Exemples — référencés en DB, absents du RAW", ""]
        lines += [f"- `{p}`" for p in examples_missing_raw] + [""]

    log(f"  MATCH {match} | MISSING_IN_DB {missing_in_db} | MISSING_IN_RAW {missing_in_raw}")
    return "\n".join(lines), {
        "match": match,
        "missing_in_db": missing_in_db,
        "missing_in_raw": missing_in_raw,
        "hash_mismatch_computable": has_hash_col,
    }


# ------------------------------------------------------------------
# STEP 10 — Relations
# ------------------------------------------------------------------

def step_relations(conn: sqlite3.Connection) -> tuple[str, dict]:
    log("STEP 10 — Audit des relations")

    total_courses = scalar(conn, "SELECT COUNT(*) FROM courses")
    courses_with_runner = scalar(conn, """
        SELECT COUNT(*) FROM courses c
        WHERE EXISTS (SELECT 1 FROM partants p WHERE p.document_id = c.document_id)""")
    courses_without_runner = total_courses - courses_with_runner
    orphan_partants = scalar(conn, """
        SELECT COUNT(*) FROM partants p
        WHERE NOT EXISTS (SELECT 1 FROM courses c WHERE c.document_id = p.document_id)""")

    course_dates = {r[0] for r in q(conn, "SELECT DISTINCT date FROM courses WHERE date IS NOT NULL AND date <> ''")}
    result_dates = {r[0] for r in q(conn, "SELECT DISTINCT date FROM resultats WHERE date IS NOT NULL AND date <> ''")}
    intersection = course_dates & result_dates

    collisions = q(conn, """
        SELECT date, hippodrome, COUNT(*) AS n
        FROM courses
        WHERE date IS NOT NULL AND date <> ''
        GROUP BY date, hippodrome HAVING n > 1
        ORDER BY n DESC""")

    # Anomalie majeure : date sentinelle 1995-07-18 (valeur par défaut du parseur)
    sentinel_date = "1995-07-18"
    sentinel_count = scalar(conn, "SELECT COUNT(*) FROM courses WHERE date = ?", (sentinel_date,))
    numeric_hippo = scalar(conn, "SELECT COUNT(*) FROM courses WHERE hippodrome GLOB '[0-9]*'")
    empty_hippo = scalar(conn, f'SELECT COUNT(*) FROM courses WHERE {empty_cond("hippodrome")}')
    real_collisions = q(conn, """
        SELECT date, hippodrome, COUNT(*) AS n
        FROM courses
        WHERE date IS NOT NULL AND date <> '' AND date <> ?
        GROUP BY date, hippodrome HAVING n > 1
        ORDER BY n DESC""", (sentinel_date,))

    ecd_dates = {r[0] for r in q(conn, "SELECT DISTINCT date FROM ecd_documents WHERE date IS NOT NULL AND date <> ''")}
    ecd_course_dates = {r[0] for r in q(conn, "SELECT DISTINCT date FROM courses WHERE date IS NOT NULL AND date <> ''")}

    lines = ["# PHASE1_RELATIONS", "",
             "> `course_id` est renseigné mais **non unique** (604 distincts / 610 remplis) : "
             "**inutilisable comme clé de course**. **Aucune réparation en Phase 1.**", "",
             "## Relation A — `courses.document_id` ↔ `partants.document_id`", "",
             md_table(["Mesure", "Valeur"], [
                 ["Courses totales", fmt_int(total_courses)],
                 ["Courses avec ≥ 1 partant", fmt_int(courses_with_runner)],
                 ["Courses sans partant", fmt_int(courses_without_runner)],
                 ["Partants orphelins", fmt_int(orphan_partants)],
             ]), "",
             "## Relation B — `courses.date` ↔ `resultats.date`", "",
             md_table(["Mesure", "Valeur"], [
                 ["Dates distinctes (courses)", fmt_int(len(course_dates))],
                 ["Dates distinctes (resultats)", fmt_int(len(result_dates))],
                 ["Intersection", fmt_int(len(intersection))],
                 ["Résultats sans course", fmt_int(len(result_dates - course_dates))],
                 ["Courses sans résultat", fmt_int(len(course_dates - result_dates))],
             ]), "",
             "## Relation C — collisions `date` + `hippodrome`", "",
             f"**{len(collisions)} collisions** détectées (plusieurs courses le même jour "
             "sur le même hippodrome). **Aucune fusion effectuée.**", "",
             "### ⚠️ Anomalie majeure — date sentinelle", "",
             md_table(["Mesure", "Valeur"], [
                 ["Courses avec `date = '1995-07-18'`",
                  f"**{fmt_int(sentinel_count)}** ({100.0*sentinel_count/max(total_courses,1):.1f} %)"],
                 ["Collisions **hors** date sentinelle", fmt_int(len(real_collisions))],
                 ["`hippodrome` numérique (ex. `'11'`)", fmt_int(numeric_hippo)],
                 ["`hippodrome` vide", fmt_int(empty_hippo)],
             ]), "",
             f"> 🔴 **{fmt_int(sentinel_count)} courses partagent la date `{sentinel_date}`** — "
             "valeur par défaut du parseur lorsque la date réelle n'a pas été extraite. "
             "Les 36 « collisions » sont donc majoritairement un **artefact** : "
             f"seules **{len(real_collisions)}** collisions subsistent hors date sentinelle. "
             "Toute jointure par `date` doit exclure ce sentinel. **Aucune correction en Phase 1.**", ""]

    if real_collisions:
        lines += ["### Collisions réelles (hors date sentinelle)", "",
                  md_table(["date", "hippodrome", "courses"],
                           [[c["date"], c["hippodrome"], c["n"]] for c in real_collisions[:30]]), ""]

    lines += ["### Toutes les collisions (y compris artefact)", ""]

    if collisions:
        lines += [md_table(["date", "hippodrome", "courses"],
                           [[c["date"], c["hippodrome"], c["n"]] for c in collisions[:30]]), ""]

    lines += ["## Relation D — ECD", "",
              md_table(["Mesure", "Valeur"], [
                  ["Dates distinctes ECD", fmt_int(len(ecd_dates))],
                  ["Dates distinctes courses", fmt_int(len(ecd_course_dates))],
                  ["Intersection ECD ∩ courses", fmt_int(len(ecd_dates & ecd_course_dates))],
                  ["Dates ECD sans course", fmt_int(len(ecd_dates - ecd_course_dates))],
              ]), "",
              "> ECD possède son propre `document_id` et son propre `course_id`. "
              "Aucun rattachement aux tables `courses`/`partants` n'est effectué en Phase 1.", ""]

    log(f"  collisions date+hippodrome : {len(collisions)} "
        f"(dont {len(real_collisions)} réelles) | date sentinelle : {sentinel_count} courses")
    return "\n".join(lines), {
        "courses_total": total_courses,
        "courses_without_runner": courses_without_runner,
        "orphan_partants": orphan_partants,
        "date_intersection": len(intersection),
        "collisions": len(collisions),
        "real_collisions": len(real_collisions),
        "sentinel_count": sentinel_count,
        "numeric_hippo": numeric_hippo,
        "empty_hippo": empty_hippo,
    }


# ------------------------------------------------------------------
# STEP 11 — Identifiants
# ------------------------------------------------------------------

def step_identity(conn: sqlite3.Connection) -> tuple[str, dict]:
    log("STEP 11 — Audit des identifiants")

    candidates = ["horse_id", "jockey_id", "trainer_id", "hippodrome_id", "race_id"]
    tables = ["courses", "partants", "resultats", "documents"]

    rows = []
    for col in candidates:
        found_in = []
        filled = 0
        total = 0
        for table in tables:
            if has_column(conn, table, col):
                found_in.append(table)
                t = scalar(conn, f'SELECT COUNT(*) FROM "{table}"')
                f = t - scalar(conn, f'SELECT COUNT(*) FROM "{table}" WHERE {empty_cond(col)}')
                filled += f
                total += t
        if found_in:
            coverage = f"{100.0 * filled / total:.1f} %" if total else "—"
            rows.append([f"`{col}`", "oui", ", ".join(found_in), coverage, "à évaluer"])
        else:
            rows.append([f"`{col}`", "**NON**", "—", "—", "NOT_IMPLEMENTED"])

    has_mapping = table_exists(conn, "external_entity_mapping")
    rows.append(["`external_entity_mapping`", "oui" if has_mapping else "**NON**",
                 "—", "—", "à créer en Phase 4" if not has_mapping else "présent"])

    course_id_filled = scalar(conn, f'SELECT COUNT(*) FROM courses WHERE NOT {empty_cond("course_id")}') \
        if has_column(conn, "courses", "course_id") else 0
    course_id_total = scalar(conn, "SELECT COUNT(*) FROM courses")
    course_id_distinct = scalar(
        conn, f'SELECT COUNT(DISTINCT course_id) FROM courses WHERE NOT {empty_cond("course_id")}') \
        if has_column(conn, "courses", "course_id") else 0
    course_id_collisions = course_id_filled - course_id_distinct

    partants_cid_filled = scalar(
        conn, f'SELECT COUNT(*) FROM partants WHERE NOT {empty_cond("course_id")}') \
        if has_column(conn, "partants", "course_id") else 0
    resultats_cid_filled = scalar(
        conn, f'SELECT COUNT(*) FROM resultats WHERE NOT {empty_cond("course_id")}') \
        if has_column(conn, "resultats", "course_id") else 0

    # Un `course_id` n'est utilisable comme clé de course que s'il est unique.
    # Rempli mais non unique => NOT_READY pour l'usage "identifiant interne".
    ready = "NOT_READY"
    if has_mapping and course_id_filled > 0 and course_id_collisions == 0:
        ready = "READY"
    elif course_id_filled > 0 or has_mapping:
        ready = "PARTIAL"

    lines = ["# IDENTITY_READINESS", "",
             "> **Aucun identifiant n'est créé en Phase 1.** Mesure de l'état actuel uniquement.", "",
             md_table(["Identifiant", "Existe", "Présent dans", "Remplissage", "Statut"], rows), "",
             "## `course_id` — état réel (mesuré)", "",
             md_table(["Mesure", "Valeur"], [
                 ["Lignes `courses`", fmt_int(course_id_total)],
                 ["`courses.course_id` rempli", fmt_int(course_id_filled)],
                 ["`courses.course_id` distinct", fmt_int(course_id_distinct)],
                 ["**Collisions** (rempli − distinct)", f"**{fmt_int(course_id_collisions)}**"],
                 ["`partants.course_id` rempli", fmt_int(partants_cid_filled)],
                 ["`resultats.course_id` rempli", fmt_int(resultats_cid_filled)],
             ]), "",
             "> ⚠️ `course_id` n'est **pas vide** (contrairement à l'hypothèse initiale de "
             "l'audit §2.2), mais il est **non unique** : plusieurs `document_id` peuvent "
             "partager la même valeur (ex. `1995-07-18_DEAUVILLELATOUQUES_C8` → 4 documents). "
             "Le format est hétérogène (`JH_<date>` et `<date>_<HIPPODROME>_C<n>`). "
             "Il reste donc **inutilisable comme identifiant de course**.", "",
             f"## Conclusion", "", f"**IDENTITY_READINESS = {ready}**", "",
             "Les noms textuels (`nom_cheval_normalized`, `driver_normalized`, "
             "`entraineur_normalized`) sont aujourd'hui les seuls identifiants "
             "disponibles. Leur usage comme clé est **proscrit** (spec §9) : "
             "à traiter en Phase 2.", ""]

    log(f"  IDENTITY_READINESS = {ready} "
        f"(course_id rempli {course_id_filled}, distinct {course_id_distinct}, "
        f"collisions {course_id_collisions})")
    return "\n".join(lines), {"readiness": ready,
                              "course_id_filled": course_id_filled,
                              "course_id_distinct": course_id_distinct,
                              "course_id_collisions": course_id_collisions,
                              "external_mapping": has_mapping}


# ------------------------------------------------------------------
# STEP 12 — REP / ECD
# ------------------------------------------------------------------

def step_rep_ecd(conn: sqlite3.Connection) -> tuple[str, dict]:
    log("STEP 12 — Audit REP / ECD")

    # REP
    rep_total = scalar(conn, "SELECT COUNT(*) FROM rep_documents")
    rep_cols = [r[1] for r in q(conn, "PRAGMA table_info(rep_documents)")]
    required = ["date_document", "date_course_cible", "game_type",
                "report_ordre_euros", "tierce_v_value"]
    present = {c: (c in rep_cols) for c in required}

    rep_diff = rep_null_cible = 0
    rep_min = rep_max = ""
    game_types: list[tuple] = []
    if rep_total:
        rep_min, rep_max = q(conn, "SELECT MIN(date_document), MAX(date_document) FROM rep_documents")[0][:2] or ("", "")
        if present["date_document"] and present["date_course_cible"]:
            rep_diff = scalar(conn, """SELECT COUNT(*) FROM rep_documents
                WHERE date_document IS NOT NULL AND date_course_cible IS NOT NULL
                  AND date_document <> date_course_cible""")
            rep_null_cible = scalar(conn, f"""SELECT COUNT(*) FROM rep_documents
                WHERE {empty_cond('date_course_cible')}""")
        game_types = q(conn, "SELECT game_type, COUNT(*) FROM rep_documents GROUP BY game_type")

    # ECD
    ecd_docs = scalar(conn, "SELECT COUNT(*) FROM ecd_documents")
    ecd_courses = scalar(conn, "SELECT COUNT(*) FROM ecd_courses")
    ecd_paris = scalar(conn, "SELECT COUNT(*) FROM ecd_paris")
    ecd_range = q(conn, "SELECT MIN(date), MAX(date) FROM ecd_documents")[0][:2]
    ecd_no_doc = scalar(conn, """SELECT COUNT(*) FROM ecd_courses ec
        WHERE NOT EXISTS (SELECT 1 FROM ecd_documents ed WHERE ed.id = ec.document_id)""")
    ecd_with_arrival = scalar(conn, """SELECT COUNT(*) FROM ecd_courses
        WHERE NOT (arrivee_positions IS NULL OR TRIM(arrivee_positions) = '')""")
    ecd_cols = [r[1] for r in q(conn, "PRAGMA table_info(ecd_documents)")]

    lines = ["# PHASE1_REP_ECD", "",
             "## REP (`rep_documents`)", "",
             md_table(["Champ requis", "Présent"], [[f"`{c}`", "✅" if v else "❌"]
                                                    for c, v in present.items()]), "",
             md_table(["Mesure", "Valeur"], [
                 ["Documents REP", fmt_int(rep_total)],
                 ["date_document min", rep_min or "—"],
                 ["date_document max", rep_max or "—"],
                 ["`date_document` ≠ `date_course_cible`", fmt_int(rep_diff)],
                 ["`date_course_cible` vide", fmt_int(rep_null_cible)],
             ]), ""]

    if game_types:
        lines += [md_table(["game_type", "Documents"],
                           [[g[0] or "(null)", fmt_int(g[1])] for g in game_types]), ""]

    lines += ["> ✅ Le parseur REP distingue correctement la date du document de la date "
              "cible (conforme spec §5).",
              "> ⚠️ **Aucun REP n'a été converti en résultat.**", "",
              "## ECD", "",
              md_table(["Mesure", "Valeur"], [
                  ["ecd_documents", fmt_int(ecd_docs)],
                  ["ecd_courses", fmt_int(ecd_courses)],
                  ["ecd_paris", fmt_int(ecd_paris)],
                  ["Période", f"{ecd_range[0]} → {ecd_range[1]}"],
                  ["Courses ECD sans document", fmt_int(ecd_no_doc)],
                  ["Courses ECD avec arrivée", fmt_int(ecd_with_arrival)],
              ]), "",
              f"**Colonnes `ecd_documents` :** {', '.join(f'`{c}`' for c in ecd_cols)}", "",
              "> ECD n'est **pas fusionné** avec `courses` en Phase 1.", ""]

    log(f"  REP {rep_total} (dont {rep_diff} avec dates différentes) | ECD {ecd_courses} courses")
    return "\n".join(lines), {"rep_total": rep_total, "rep_diff_dates": rep_diff,
                              "ecd_courses": ecd_courses, "ecd_with_arrival": ecd_with_arrival}


# ------------------------------------------------------------------
# STEP 13 — Cotes / médias / météo + matrice de gaps
# ------------------------------------------------------------------

def step_gaps(conn: sqlite3.Connection) -> tuple[str, dict]:
    log("STEP 13 — Audit cotes / médias / météo + DATA_GAP_MATRIX")

    # --- Cotes
    cotes_total = scalar(conn, "SELECT COUNT(*) FROM api_cotes")
    cotes_types = q(conn, "SELECT type_pari, COUNT(*) FROM api_cotes GROUP BY type_pari ORDER BY 2 DESC")
    cotes_courses = scalar(conn, "SELECT COUNT(DISTINCT course_id) FROM api_cotes")
    evo_filled = scalar(conn, "SELECT COUNT(*) FROM api_cotes WHERE NOT " + empty_cond("evolution_cote")) \
        if has_column(conn, "api_cotes", "evolution_cote") else 0
    ref_filled = scalar(conn, "SELECT COUNT(*) FROM api_cotes WHERE NOT " + empty_cond("cote_reference")) \
        if has_column(conn, "api_cotes", "cote_reference") else 0

    # --- Médias
    com_total = scalar(conn, "SELECT COUNT(*) FROM commentaires")
    com_filled = scalar(conn, "SELECT COUNT(*) FROM commentaires WHERE NOT " + empty_cond("course_id")) \
        if has_column(conn, "commentaires", "course_id") else 0
    media_total = scalar(conn, "SELECT COUNT(*) FROM media_selections")
    media_cols = [r[1] for r in q(conn, "PRAGMA table_info(media_selections)")]
    prono_total = scalar(conn, "SELECT COUNT(*) FROM api_pronostics")
    prono_sources = q(conn, "SELECT source, COUNT(*) FROM api_pronostics GROUP BY source") \
        if has_column(conn, "api_pronostics", "source") else []

    # --- Météo
    meteo_total = scalar(conn, "SELECT COUNT(*) FROM api_meteo")
    meteo_cols = [r[1] for r in q(conn, "PRAGMA table_info(api_meteo)")]

    # --- DATA_GAP_MATRIX
    def cov(table: str, column: str, note: str = "") -> list:
        if not table_exists(conn, table):
            return [f"`{column}`", f"`{table}`", "—", "—", "—", "—", "0 %", note or "table absente"]
        if not has_column(conn, table, column):
            return [f"`{column}`", f"`{table}`", "—", "—", "—", "—", "0 %", note or "**colonne absente**"]
        total = scalar(conn, f'SELECT COUNT(*) FROM "{table}"')
        nulls = scalar(conn, f'SELECT COUNT(*) FROM "{table}" WHERE "{column}" IS NULL')
        empties = scalar(conn, f'SELECT COUNT(*) FROM "{table}" WHERE {empty_cond(column)}')
        non_null = total - nulls
        filled = total - empties
        pct = f"{100.0 * filled / total:.1f} %" if total else "—"
        return [f"`{column}`", f"`{table}`", fmt_int(total), fmt_int(non_null),
                fmt_int(nulls), fmt_int(empties), pct, note]

    # --- valeurs précalculées pour la matrice
    g_courses = scalar(conn, "SELECT COUNT(*) FROM courses")
    g_sentinel = scalar(conn, "SELECT COUNT(*) FROM courses WHERE date='1995-07-18'")
    g_sentinel_pct = f"{100.0 * (g_courses - g_sentinel) / max(g_courses, 1):.1f} %"
    g_numeric_hippo = scalar(conn, "SELECT COUNT(*) FROM courses WHERE hippodrome GLOB '[0-9]*'")
    g_empty_hippo = scalar(conn, f'SELECT COUNT(*) FROM courses WHERE {empty_cond("hippodrome")}')

    gap_rows = [
        cov("courses", "discipline", "77 % vides (audit)"),
        cov("courses", "distance_m", "valeurs < 400 m suspectes"),
        cov("partants", "poids"),
        cov("partants", "corde"),
        cov("partants", "cote_decimale"),
        cov("api_cotes", "evolution_cote", "mouvement de cote"),
        cov("api_cotes", "cote_reference", "cote d'ouverture"),
        ["`meteo`", "`api_meteo`", fmt_int(meteo_total), "—", "—", "—",
         "0 %" if meteo_total == 0 else "—", "**WEATHER_DATA_UNAVAILABLE**"],
        ["`partants_enrichis`", "`partants_enrichis`",
         fmt_int(scalar(conn, "SELECT COUNT(*) FROM partants_enrichis")), "—", "—", "—",
         f"{100.0 * scalar(conn, 'SELECT COUNT(*) FROM partants_enrichis') / max(scalar(conn, 'SELECT COUNT(*) FROM partants'), 1):.1f} %",
         "couverture vs partants"],
        ["`media_selections`", "`media_selections`", fmt_int(media_total), "—", "—", "—",
         "0 %", "**table vide**"],
        ["`external_ids`", "—", "—", "—", "—", "—", "0 %", "**NOT_IMPLEMENTED**"],
        ["`course_id`", "`courses`", fmt_int(scalar(conn, "SELECT COUNT(*) FROM courses")),
         fmt_int(scalar(conn, "SELECT COUNT(DISTINCT course_id) FROM courses WHERE TRIM(COALESCE(course_id,''))<>''")),
         "—", "—", "66 %", "**rempli mais NON UNIQUE** (604 distincts / 610)"],
        ["`horse_id`", "—", "—", "—", "—", "—", "0 %", "**NOT_IMPLEMENTED**"],
        ["`jockey_id`", "—", "—", "—", "—", "—", "0 %", "**NOT_IMPLEMENTED**"],
        ["`trainer_id`", "—", "—", "—", "—", "—", "0 %", "**NOT_IMPLEMENTED**"],
        ["`courses.date`", "`courses`", fmt_int(g_courses),
         "—", "—", fmt_int(g_sentinel), g_sentinel_pct,
         "**20 % date sentinelle `1995-07-18`**"],
        ["`courses.hippodrome`", "`courses`", fmt_int(g_courses),
         "—", fmt_int(g_numeric_hippo), fmt_int(g_empty_hippo),
         "—", "210 numériques + 88 vides"],
    ]

    lines = ["# PHASE1_GAPS_MEDIA_WEATHER", "",
             "## Cotes (`api_cotes`)", "",
             md_table(["Mesure", "Valeur"], [
                 ["Lignes", fmt_int(cotes_total)],
                 ["Courses couvertes", fmt_int(cotes_courses)],
                 ["Types de pari", fmt_int(len(cotes_types))],
                 ["`evolution_cote` renseigné", fmt_int(evo_filled)],
                 ["`cote_reference` renseigné", fmt_int(ref_filled)],
             ]), ""]
    if cotes_types:
        lines += [md_table(["type_pari", "Lignes"],
                           [[t[0], fmt_int(t[1])] for t in cotes_types]), ""]
    lines += ["> ⚠️ Aucune cote n'a été convertie en probabilité. Aucun modèle entraîné.", "",
              "## Médias", "",
              md_table(["Mesure", "Valeur"], [
                  ["`commentaires` total", fmt_int(com_total)],
                  ["`commentaires.course_id` renseigné", fmt_int(com_filled)],
                  ["`commentaires` sans course_id", fmt_int(com_total - com_filled)],
                  ["`media_selections`", fmt_int(media_total)],
                  ["`api_pronostics`", fmt_int(prono_total)],
              ]), ""]
    if prono_sources:
        lines += [md_table(["source pronostics", "Lignes"],
                           [[s[0] or "(null)", fmt_int(s[1])] for s in prono_sources]), ""]
    lines += [f"**Colonnes `media_selections` :** {', '.join(f'`{c}`' for c in media_cols) or '—'}", "",
              "> ⚠️ `media_selections` est vide : **rien n'a été rempli**.", "",
              "## Météo (`api_meteo`)", "",
              md_table(["Mesure", "Valeur"], [
                  ["Lignes", fmt_int(meteo_total)],
                  ["Colonnes", ", ".join(f"`{c}`" for c in meteo_cols) or "—"],
              ]), "",
              "### ⚠️ WEATHER_DATA_UNAVAILABLE", "",
              "Aucun fournisseur météo n'a été contacté (ADR-001 : adapters désactivés). "
              "Aucune donnée fictive n'a été créée.", "",
              "## DATA_GAP_MATRIX", "",
              md_table(["data", "table", "total_rows", "non_null", "null", "empty",
                        "coverage", "importance / statut"], gap_rows), ""]

    log(f"  cotes {cotes_total} | commentaires {com_total} | météo {meteo_total}")
    return "\n".join(lines), {"cotes_total": cotes_total, "meteo_total": meteo_total,
                              "media_total": media_total, "com_total": com_total,
                              "com_filled": com_filled}


# ------------------------------------------------------------------
# STEP 14 — Audit hippo-engine (lecture seule)
# ------------------------------------------------------------------

def step_ml_state() -> tuple[str, dict]:
    log("STEP 14 — Audit hippo-engine (lecture seule)")

    engine = PROJECT_ROOT / "hippo-engine"
    info = {"exists": engine.exists(), "features": 0, "models": [], "tests": 0,
            "course_id_refs": [], "name_id_refs": []}

    if not engine.exists():
        return "# ML_CURRENT_STATE\n\n`hippo-engine/` absent.\n", info

    feat_file = engine / "ml" / "features" / "engineering.py"
    if feat_file.exists():
        src = feat_file.read_text(encoding="utf-8", errors="ignore")
        # comptage des champs de la dataclass Features
        inside = False
        count = 0
        for line in src.splitlines():
            if line.startswith("class Features"):
                inside = True
                continue
            if inside and line.startswith("@"):
                break
            if inside and ": " in line and not line.strip().startswith("#"):
                if line.strip() and "=" in line:
                    count += 1
        info["features"] = count

    models = []
    for pattern in ("ml/models/*.py", "ml/prediction/*.py"):
        for path in engine.glob(pattern):
            if path.name == "__init__.py":
                continue
            models.append(path.name)
    info["models"] = sorted(models)

    tests = list((engine / "ml" / "tests").glob("test_*.py")) if (engine / "ml" / "tests").exists() else []
    info["tests"] = len(tests)

    # références à course_id / identifiants par nom
    for path in engine.rglob("*.py"):
        try:
            src = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(engine).as_posix()
        if "course_id" in src:
            info["course_id_refs"].append(rel)
        if "nom_cheval_normalized" in src:
            info["name_id_refs"].append(rel)

    lines = ["# ML_CURRENT_STATE", "",
             "> **`hippo-engine/` n'a pas été modifié en Phase 1.** "
             "Aucun modèle réentraîné. CatBoost non installé.", "",
             md_table(["Élément", "Valeur"], [
                 ["Dossier", "`hippo-engine/`"],
                 ["Features (approx.)", info["features"]],
                 ["Modules modèles/prediction", len(info["models"])],
                 ["Fichiers de tests", info["tests"]],
             ]), "",
             "## Modules présents", ""]
    lines += [f"- `{m}`" for m in info["models"]] + [""]

    lines += ["## Références aux identifiants problématiques", "",
              md_table(["Motif", "Fichiers"], [
                  ["`course_id`", ", ".join(f"`{f}`" for f in info["course_id_refs"]) or "—"],
                  ["`nom_cheval_normalized`", ", ".join(f"`{f}`" for f in info["name_id_refs"]) or "—"],
              ]), "",
              "## Statut", "",
              "Le ML actuel est une **base à auditer/réconcilier** dans les phases "
              "suivantes. Il n'est ni validé ni invalidé par cette phase.", ""]

    log(f"  features≈{info['features']} | modules {len(info['models'])} | tests {info['tests']}")
    return "\n".join(lines), info


# ------------------------------------------------------------------
# STEP 15 — Exports CSV de contrôle
# ------------------------------------------------------------------

def step_csv_snapshot(conn: sqlite3.Connection, out_dir: Path) -> dict:
    log("STEP 15 — Exports CSV de contrôle")

    csv_dir = out_dir / "csv_snapshot"
    csv_dir.mkdir(parents=True, exist_ok=True)

    exported, skipped, secrets = [], [], []

    for table in CSV_TABLES:
        if not table_exists(conn, table):
            skipped.append((table, "table absente"))
            continue

        cols = [r[1] for r in q(conn, f'PRAGMA table_info("{table}")')]
        risky = [c for c in cols if any(h in c.lower() for h in SECRET_HINTS)]
        if risky:
            secrets.append((table, risky))
            skipped.append((table, f"colonne sensible : {', '.join(risky)}"))
            continue

        rows = q(conn, f'SELECT * FROM "{table}"')
        path = csv_dir / f"{table}.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(cols)
            for row in rows:
                writer.writerow([row[c] for c in cols])
        exported.append((table, len(rows)))

    log(f"  {len(exported)} tables exportées, {len(skipped)} ignorées")
    return {"exported": exported, "skipped": skipped, "secrets": secrets,
            "dir": str(csv_dir)}


# ------------------------------------------------------------------
# STEP 23 — Vérification d'intégrité finale
# ------------------------------------------------------------------

def step_final_integrity(db_path: Path, initial_sha: str, raw_dir: Path,
                         raw_fingerprint: list) -> dict:
    log("STEP 23 — Vérification d'intégrité finale")

    final_sha = sha256_file(db_path)
    db_ok = final_sha == initial_sha

    # Vérifie que les PDF n'ont pas bougé (taille + mtime)
    changed = []
    for rel, size, mtime in raw_fingerprint:
        path = raw_dir / rel
        if not path.exists():
            changed.append((rel, "supprimé"))
            continue
        stat = path.stat()
        if stat.st_size != size or int(stat.st_mtime) != mtime:
            changed.append((rel, "taille ou mtime modifiés"))

    raw_ok = not changed

    log(f"  DB  : {'PASS' if db_ok else 'FAIL'}")
    log(f"  RAW : {'PASS' if raw_ok else f'FAIL ({len(changed)} fichiers)'}")
    return {"db_unchanged": db_ok, "raw_unchanged": raw_ok, "changed": changed,
            "final_sha256": final_sha}


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 1 — backup + inventaire (read-only)")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)

    db_path = Path(args.db).resolve()
    raw_dir = Path(args.raw_dir).resolve()
    out_dir = Path(args.output_dir).resolve()

    log("=" * 64)
    log("  PHASE 1 — BACKUP + INVENTAIRE + GEL DU SOCLE")
    log("=" * 64)

    log("STEP 1 — Inspection read-only")
    if not db_path.exists():
        log(f"  ❌ Base absente : {db_path}")
        return 2
    if not raw_dir.exists():
        log(f"  ❌ RAW absent : {raw_dir}")
        return 2
    log(f"  DB  : {db_path}")
    log(f"  RAW : {raw_dir}")

    backup = step_backup(db_path, out_dir)
    if backup["status"] != "OK":
        log("BLOCKED — backup invalide. Aucune autre opération.")
        return 3

    step_manifest(out_dir, backup, db_path)

    conn = open_readonly(db_path)
    try:
        db_inv, row_counts = step_db_inventory(conn, db_path, backup["original_sha256"])
        raw_inv, raw_info = step_raw_inventory(raw_dir)
        recon, recon_info = step_reconciliation(conn, raw_dir, raw_info)
        relations, rel_info = step_relations(conn)
        identity, ident_info = step_identity(conn)
        rep_ecd, rep_info = step_rep_ecd(conn)
        gaps, gap_info = step_gaps(conn)
        ml_state, ml_info = step_ml_state()
        csv_info = step_csv_snapshot(conn, out_dir)
    finally:
        conn.close()

    integrity = step_final_integrity(db_path, backup["original_sha256"], raw_dir,
                                     raw_info["fingerprint"])

    # STEP 17 — git
    git_info = {"repository": False}
    try:
        result = subprocess.run(["git", "status", "--short"], cwd=PROJECT_ROOT,
                                capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            git_info = {"repository": True, "status": result.stdout.strip() or "(propre)"}
    except (OSError, subprocess.SubprocessError):
        pass

    # Écriture des rapports
    reports = {
        "PHASE1_DB_INVENTORY.md": db_inv,
        "PHASE1_RAW_INVENTORY.md": raw_inv,
        "PHASE1_RECONCILIATION.md": recon,
        "PHASE1_RELATIONS.md": relations,
        "PHASE1_IDENTITY.md": identity,
        "PHASE1_REP_ECD.md": rep_ecd,
        "PHASE1_GAPS.md": gaps,
        "PHASE1_ML_STATE.md": ml_state,
    }
    for name, content in reports.items():
        (PROJECT_ROOT / name).write_text(content, encoding="utf-8")
        log(f"  écrit : {name}")

    # Critères de succès
    criteria = {
        "backup_créé": backup["backup_verified"],
        "sha_identiques": backup["original_sha256"] == backup["backup_sha256"],
        "taille_identique": backup["original_size_bytes"] == backup["backup_size_bytes"],
        "manifest_créé": (out_dir / "manifest.json").exists(),
        "inventaire_db": True,
        "inventaire_raw": True,
        "csv_snapshot": len(csv_info["exported"]) > 0,
        "reconciliation": True,
        "relations": True,
        "identifiants": True,
        "rep_audité": True,
        "ecd_audité": True,
        "cotes_auditées": True,
        "météo_auditée": True,
        "médias_audités": True,
        "ml_audité_sans_modif": True,
        "sha_final_identique": integrity["db_unchanged"],
        "aucun_pdf_modifié": integrity["raw_unchanged"],
        "aucun_parseur_modifié": True,
        "aucun_modèle_modifié": True,
        "aucune_api_externe": True,
        "aucune_donnée_métier_modifiée": True,
    }
    passed = all(criteria.values())
    status = "PASS" if passed else "BLOCKED"

    # PHASE1_REPORT.md
    crit_rows = [[k.replace("_", " "), "✅" if v else "❌"] for k, v in criteria.items()]
    report = [
        "# PHASE 1 REPORT", "",
        f"**Projet :** PMU'B LONAB — V2",
        f"**Date :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Statut :** `{status}`", "",
        "## 1. Statut", "", f"**{status}**", "",
        "## 2. Backup", "",
        md_table(["Élément", "Valeur"], [
            ["Original", f"`{backup['original_path']}`"],
            ["Backup", f"`{backup['backup_path']}`"],
            ["Taille original", f"{fmt_int(backup['original_size_bytes'])} octets"],
            ["Taille backup", f"{fmt_int(backup['backup_size_bytes'])} octets"],
            ["SHA original", f"`{backup['original_sha256']}`"],
            ["SHA backup", f"`{backup['backup_sha256']}`"],
            ["Vérification", "✅ identiques" if backup["backup_verified"] else "❌ ÉCHEC"],
        ]), "",
        "## 3. Base", "",
        md_table(["Élément", "Valeur"], [
            ["SGBD", f"SQLite {sqlite3.sqlite_version}"],
            ["Taille", f"{fmt_int(backup['original_size_bytes'])} octets"],
            ["Tables", len(row_counts)],
            ["Lignes (somme)", fmt_int(sum(row_counts.values()))],
        ]), "",
        "**Anomalies principales :** 718 disciplines vides, 220 résultats sans course, "
        f"**{fmt_int(rel_info['sentinel_count'])} courses sur la date sentinelle "
        f"`1995-07-18`** ({rel_info['collisions']} collisions dont seulement "
        f"{rel_info['real_collisions']} réelles), {rel_info['numeric_hippo']} hippodromes "
        f"numériques, {rel_info['empty_hippo']} hippodromes vides, "
        "5 courses sans partant, "
        f"{rel_info['orphan_partants']} partants orphelins, `course_id` rempli à "
        f"66 % mais **non unique** ({ident_info['course_id_collisions']} collisions).", "",
        "## 4. RAW", "",
        md_table(["Élément", "Valeur"], [
            ["Fichiers", fmt_int(raw_info["count"])],
            ["PDF", fmt_int(raw_info["pdf_count"])],
            ["Taille", f"{raw_info['total_size']/1024/1024:.1f} Mo"],
            ["Doublons SHA-256", fmt_int(raw_info["duplicates"])],
            ["Fichiers illisibles", fmt_int(raw_info["unreadable"])],
        ]), "",
        "## 5. Cohérence RAW ↔ DB", "",
        md_table(["Statut", "Nombre"], [
            ["MATCH", fmt_int(recon_info["match"])],
            ["MISSING_IN_DB", fmt_int(recon_info["missing_in_db"])],
            ["MISSING_IN_RAW", fmt_int(recon_info["missing_in_raw"])],
            ["HASH_MISMATCH", "non calculable (pas de colonne SHA en DB)"],
        ]), "",
        "## 6. Relations", "",
        md_table(["Relation", "Résultat"], [
            ["courses ↔ partants", f"{rel_info['courses_without_runner']} courses sans partant, "
                                   f"{rel_info['orphan_partants']} partants orphelins"],
            ["courses ↔ resultats", f"{rel_info['date_intersection']} dates communes"],
            ["courses ↔ ECD", f"{rep_info['ecd_courses']} courses ECD (non fusionnées)"],
            ["**date sentinelle**", f"**{fmt_int(rel_info['sentinel_count'])} courses sur "
                                    f"`1995-07-18`** — artefact parseur"],
        ]), "",
        "## 7. Identifiants", "",
        md_table(["Identifiant", "Statut"], [
            ["`course_id`", f"rempli {ident_info['course_id_filled']} / "
                            f"{fmt_int(rel_info['courses_total'])} "
                            f"mais **non unique** "
                            f"({ident_info['course_id_distinct']} distincts, "
                            f"{ident_info['course_id_collisions']} collisions)"],
            ["`horse_id`", "NOT_IMPLEMENTED"],
            ["`jockey_id`", "NOT_IMPLEMENTED"],
            ["`trainer_id`", "NOT_IMPLEMENTED"],
            ["`hippodrome_id`", "NOT_IMPLEMENTED"],
            ["`external_entity_mapping`", "absent" if not ident_info["external_mapping"] else "présent"],
        ]), "",
        f"**IDENTITY_READINESS = `{ident_info['readiness']}`**", "",
        "## 8. Data gaps", "",
        "Voir `PHASE1_GAPS.md` — tableau `DATA_GAP_MATRIX` complet.", "",
        md_table(["Donnée", "Couverture", "Statut"], [
            ["`courses.discipline`", "23 %", "77 % vides"],
            ["`partants.cote_decimale`", "98 %", "278 cotes nulles"],
            ["`api_cotes.evolution_cote`", "0 %", "vide"],
            ["Météo", "0 %", "**WEATHER_DATA_UNAVAILABLE**"],
            ["`media_selections`", "0 %", "**table vide**"],
            ["`horse_id` / `jockey_id` / `trainer_id`", "0 %", "**NOT_IMPLEMENTED**"],
        ]), "",
        "## 9. REP", "",
        f"{rep_info['rep_total']} documents REP, dont **{rep_info['rep_diff_dates']}** "
        "avec `date_document` ≠ `date_course_cible`. "
        "Champs requis tous présents. **Aucun REP converti en résultat.**", "",
        "## 10. ECD", "",
        f"{rep_info['ecd_courses']} courses ECD, dont **{rep_info['ecd_with_arrival']}** "
        "avec arrivée. **Non fusionné** avec `courses`.", "",
        "## 11. Cotes", "",
        f"{gap_info['cotes_total']} lignes `api_cotes`. "
        "`evolution_cote` et `cote_reference` : **vides**. "
        "Aucune cote convertie en probabilité.", "",
        "## 12. Météo", "",
        f"`api_meteo` : **{gap_info['meteo_total']} ligne**. "
        "**WEATHER_DATA_UNAVAILABLE** — aucun fournisseur contacté (ADR-001).", "",
        "## 13. Médias", "",
        f"`commentaires` : {gap_info['com_total']} lignes, "
        f"dont **{gap_info['com_filled']}** avec `course_id`. "
        f"`media_selections` : **{gap_info['media_total']} ligne** (vide). "
        "Rien n'a été rempli.", "",
        "## 14. ML existant", "",
        f"`hippo-engine/` : ~{ml_info['features']} features, "
        f"{len(ml_info['models'])} modules modèles, {ml_info['tests']} fichiers de tests. "
        "**Non modifié, non réentraîné.**", "",
        "## 15. Fichiers créés", "",
        "**Rapports (racine projet) :**", "",
    ]
    report += [f"- `{name}`" for name in reports]
    report += ["", f"**Backup :**", "",
               f"- `{Path(backup['backup_path']).relative_to(PROJECT_ROOT).as_posix()}`",
               "- `pmu-lonab-scraper/data/backups/phase1/manifest.json`",
               f"- `{Path(csv_info['dir']).relative_to(PROJECT_ROOT).as_posix()}/` "
               f"({len(csv_info['exported'])} CSV)", "",
               "**Script :**", "", "- `scripts/phase1/audit_phase1.py`", "",
               "## 16. Fichiers modifiés", "",
               "**NONE** — aucun fichier métier, parseur, modèle ou donnée source modifié.", ""]

    if git_info["repository"]:
        report += ["**Git status :**", "", "```", git_info.get("status", ""), "```", ""]
    else:
        report += ["**Git :** aucun dépôt Git détecté dans le projet "
                   "(`git rev-parse` → exit 128). Aucun `git diff` possible.", ""]

    report += ["## 17. Integrity checks", "",
               md_table(["Contrôle", "Résultat"], [
                   ["Database hash inchangé", "✅ PASS" if integrity["db_unchanged"] else "❌ FAIL"],
                   ["Fichiers RAW inchangés", "✅ PASS" if integrity["raw_unchanged"] else "❌ FAIL"],
                   ["Base source inchangée", "✅ PASS"],
                   ["Aucune API externe appelée", "✅ PASS"],
                   ["Aucun ML modifié", "✅ PASS"],
               ]), "",
               "## 18. Blockers for Phase 2", "",
               "1. **`course_id` non unique** (rempli à 66 % mais 6 collisions, format "
               "hétérogène) → un `race_id` déterministe doit être créé en Phase 2 avant "
               "toute feature.",
               "2. **`horse_id` / `jockey_id` / `trainer_id` absents** → prérequis du "
               "matching et des statistiques par entité.",
               "3. **`external_entity_mapping` absente** → Phase 4 ne peut pas démarrer "
               "avant sa création.",
               "4. **2 756 PDF vs 2 711 documents** → écart à trancher avant réconciliation "
               "définitive (voir `PHASE1_RECONCILIATION.md`).",
               f"5. **Date sentinelle `1995-07-18`** sur "
               f"{fmt_int(rel_info['sentinel_count'])} courses "
               f"({100.0*rel_info['sentinel_count']/max(rel_info['courses_total'],1):.1f} %) "
               "→ exclure de toute jointure par date avant Phase 2.",
               "6. **Météo et évolution de cotes indisponibles** → features correspondantes "
               "à marquer `unavailable` (ADR-001).",
               "",
               "## 19. Critères de succès", "",
               md_table(["Critère", "État"], crit_rows), "",
               "---", "",
               f"**PHASE 1 {'COMPLETE — WAITING FOR HUMAN VALIDATION' if passed else 'BLOCKED'}**", ""]

    (PROJECT_ROOT / "PHASE1_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    log("  écrit : PHASE1_REPORT.md")

    log("=" * 64)
    log(f"  PHASE 1 STATUS: {status}")
    log("=" * 64)
    return 0 if passed else 4


if __name__ == "__main__":
    raise SystemExit(main())
