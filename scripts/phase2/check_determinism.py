#!/usr/bin/env python3
"""Contrôle de déterminisme : calcule une empreinte stable des identifiants générés.

Deux exécutions de build_master_db.py doivent produire la MÊME empreinte.
Usage : python scripts/phase2/check_determinism.py [--master <path>]
"""
import argparse
import hashlib
import sqlite3
from pathlib import Path

DEFAULT_MASTER = (Path(__file__).resolve().parents[2]
                  / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db")

QUERIES = [
    "SELECT race_id, source_document_id, date, hippodrome_id, result_status "
    "FROM master_race ORDER BY race_id",
    "SELECT horse_id, name_key, resolution_method, homonym_risk FROM master_horse "
    "ORDER BY horse_id",
    "SELECT person_id, role, name_key FROM master_person ORDER BY person_id",
    "SELECT runner_id, source_partant_id, race_id, horse_id, jockey_id, trainer_id, "
    "owner_id, result_position, result_status FROM master_runner ORDER BY runner_id",
    "SELECT hippodrome_id, label_canonical FROM master_hippodrome ORDER BY hippodrome_id",
]


def digest(master: Path) -> str:
    conn = sqlite3.connect(f"file:{master.as_posix()}?mode=ro", uri=True)
    h = hashlib.sha256()
    try:
        for sql in QUERIES:
            for row in conn.execute(sql):
                h.update(("|".join("" if x is None else str(x) for x in row) + "\n")
                         .encode("utf-8"))
    finally:
        conn.close()
    return h.hexdigest()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default=str(DEFAULT_MASTER))
    a = ap.parse_args()
    print(digest(Path(a.master).resolve()))
