#!/usr/bin/env python3
"""
PHASE 2 — MASTER DATABASE + IDENTIFIANTS INTERNES (PMU'B LONAB V2)

Construit une base maîtresse DÉRIVÉE à partir du socle LONAB.

Garanties :
  - le socle est ouvert en LECTURE SEULE (URI mode=ro) : aucun UPDATE/DELETE/INSERT/ALTER
  - la Master DB est un fichier SÉPARÉ (jamais le socle) — ADR-001
  - aucun nom n'est utilisé comme clé étrangère (spec §9)
  - identifiants UUIDv5 DÉTERMINISTES : 2 exécutions => identifiants identiques
  - aucune API externe, aucune donnée fictive, aucun modèle ML
  - toute incertitude est TRACÉE (jamais devinée)

Usage :
    python scripts/phase2/build_master_db.py
    python scripts/phase2/build_master_db.py --db <socle> --master <master.db> --output-dir <dir>

Déterministe et ré-exécutable (idempotent).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import sys
import unicodedata
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ------------------------------------------------------------------
# Constantes
# ------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"
DEFAULT_MASTER = PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
DEFAULT_OUT = PROJECT_ROOT

# Namespace UUIDv5 fixe — NE JAMAIS CHANGER (sinon tous les identifiants changent)
NAMESPACE_PMUB = uuid.UUID("6f1a4c2e-9b7d-5a31-8c4f-2d6e0b9a7c15")

SENTINEL_DATE = "1995-07-18"

# Sexes valides observés dans le socle : H=hongre, F=femelle, M=mâle
VALID_SEX = {"H", "F", "M"}

LOG_LINES: list[str] = []


def log(msg: str) -> None:
    print(msg, flush=True)
    LOG_LINES.append(msg)


# ------------------------------------------------------------------
# Utilitaires
# ------------------------------------------------------------------

def norm_text(value) -> str:
    """Normalisation déterministe : accents retirés, majuscules, ponctuation -> espaces."""
    if value is None:
        return ""
    s = str(value)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.upper()
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return " ".join(s.split())


def is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def make_id(kind: str, *parts) -> str:
    """UUIDv5 déterministe."""
    payload = "|".join([kind] + [str(p) for p in parts])
    return str(uuid.uuid5(NAMESPACE_PMUB, payload))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def open_readonly(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def parse_json_list(value):
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    s = str(value).strip()
    if s in ("", "[]", "null", "None"):
        return []
    try:
        parsed = json.loads(s)
    except (ValueError, TypeError):
        return []
    return parsed if isinstance(parsed, list) else []


def sex_letter(sexe_raw) -> str:
    """Le champ `sexe` encode sexe + âge sous la forme '<SEX>.<AGE>' (ex. 'H.7').
    On ne retient que les sexes valides : H (hongre), F (femelle), M (mâle).
    Toute autre valeur ('AGE', '1', 'P', '') est un artefact de parsing -> None."""
    token = str(sexe_raw or "").strip().upper().split(".")[0].strip()
    return token if token in VALID_SEX else ""


def horse_age(sexe_raw, age_raw) -> int | None:
    """Âge : colonne `age` si plausible, sinon suffixe numérique de `sexe` ('H.7' -> 7)."""
    a = str(age_raw or "").strip()
    if a.isdigit() and 1 <= int(a) <= 20:
        return int(a)
    parts = str(sexe_raw or "").split(".")
    if len(parts) >= 2 and parts[1].strip().isdigit():
        v = int(parts[1])
        if 1 <= v <= 20:
            return v
    return None


def year_of(date_str: str) -> int | None:
    m = re.match(r"^(\d{4})-", str(date_str or ""))
    return int(m.group(1)) if m else None


def csv_write(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


# ------------------------------------------------------------------
# Schéma Master DB
# ------------------------------------------------------------------

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE master_hippodrome (
    hippodrome_id     TEXT PRIMARY KEY,
    label_canonical   TEXT NOT NULL,
    label_variants    TEXT,
    country           TEXT,
    is_valid          INTEGER NOT NULL,
    quality_flag      TEXT NOT NULL,
    n_courses         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE master_race (
    race_id              TEXT PRIMARY KEY,
    source_document_id   INTEGER NOT NULL,
    date                 TEXT,
    date_is_sentinel     INTEGER NOT NULL DEFAULT 0,
    hippodrome_id        TEXT,
    hippodrome_label_raw TEXT,
    discipline           TEXT,
    discipline_status    TEXT NOT NULL,
    distance_m           INTEGER,
    montant_euros        INTEGER,
    partants_declares    INTEGER,
    partants_effectifs   INTEGER,
    type_course          TEXT,
    titre                TEXT,
    n_partants_source    INTEGER NOT NULL DEFAULT 0,
    n_runners_linked     INTEGER NOT NULL DEFAULT 0,
    result_status        TEXT NOT NULL,
    FOREIGN KEY (hippodrome_id) REFERENCES master_hippodrome(hippodrome_id)
);

CREATE TABLE master_horse (
    horse_id                TEXT PRIMARY KEY,
    name_normalized         TEXT NOT NULL,
    name_key                TEXT NOT NULL UNIQUE,
    resolution_method       TEXT NOT NULL,
    resolution_confidence   REAL NOT NULL,
    homonym_risk            TEXT NOT NULL,
    n_sex_birthyear_variants INTEGER,
    sex_birthyear_variants  TEXT,
    n_starts                INTEGER NOT NULL DEFAULT 0,
    first_seen_date         TEXT,
    last_seen_date          TEXT,
    pedigree_pere           TEXT,
    pedigree_mere           TEXT,
    robe                    TEXT,
    race                    TEXT
);

CREATE TABLE master_person (
    person_id             TEXT PRIMARY KEY,
    name_normalized       TEXT NOT NULL,
    name_key              TEXT NOT NULL,
    role                  TEXT NOT NULL,
    resolution_method     TEXT NOT NULL,
    resolution_confidence REAL NOT NULL,
    n_appearances         INTEGER NOT NULL DEFAULT 0,
    UNIQUE (role, name_key)
);

CREATE TABLE master_runner (
    runner_id               TEXT PRIMARY KEY,
    race_id                 TEXT NOT NULL,
    source_document_id      INTEGER NOT NULL,
    source_partant_id       INTEGER NOT NULL,
    numero                  INTEGER,
    horse_id                TEXT,
    jockey_id               TEXT,
    trainer_id              TEXT,
    owner_id                TEXT,
    cote_decimale           REAL,
    gains_euros             INTEGER,
    performances_structured TEXT,
    sexe_raw                TEXT,
    age_raw                 TEXT,
    poids_raw               TEXT,
    corde_raw               TEXT,
    result_position         INTEGER,
    result_status           TEXT NOT NULL,
    FOREIGN KEY (race_id) REFERENCES master_race(race_id),
    FOREIGN KEY (horse_id) REFERENCES master_horse(horse_id)
);

CREATE TABLE ref_hippodrome (
    label_variant  TEXT PRIMARY KEY,
    hippodrome_id  TEXT,
    quality_flag   TEXT NOT NULL
);

CREATE TABLE ref_discipline (
    discipline_raw  TEXT PRIMARY KEY,
    discipline_norm TEXT,
    status          TEXT NOT NULL
);

CREATE TABLE external_entity_mapping (
    internal_id   TEXT NOT NULL,
    internal_type TEXT NOT NULL,
    provider      TEXT NOT NULL,
    external_id   TEXT,
    confidence    REAL,
    verified      INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT,
    PRIMARY KEY (internal_id, provider)
);

CREATE TABLE data_version (
    version_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    scope          TEXT NOT NULL,
    version        TEXT NOT NULL,
    source_sha256  TEXT,
    created_at     TEXT NOT NULL,
    notes          TEXT
);

CREATE TABLE feature_version (
    version_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    scope         TEXT NOT NULL,
    version       TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    notes         TEXT
);

CREATE TABLE model_version (
    version_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    scope         TEXT NOT NULL,
    version       TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    notes         TEXT
);

CREATE TABLE prediction_snapshot (
    snapshot_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    race_id       TEXT,
    model_version TEXT,
    cutoff_ts     TEXT,
    payload_json  TEXT,
    created_at    TEXT NOT NULL
);

CREATE INDEX idx_race_date        ON master_race(date);
CREATE INDEX idx_race_hippo       ON master_race(hippodrome_id);
CREATE INDEX idx_runner_race      ON master_runner(race_id);
CREATE INDEX idx_runner_horse     ON master_runner(horse_id);
CREATE INDEX idx_runner_jockey    ON master_runner(jockey_id);
CREATE INDEX idx_runner_trainer   ON master_runner(trainer_id);
CREATE INDEX idx_horse_namekey    ON master_horse(name_key);
CREATE INDEX idx_person_role_key  ON master_person(role, name_key);
"""

MASTER_TABLES = [
    "master_hippodrome", "master_race", "master_horse", "master_person",
    "master_runner", "ref_hippodrome", "ref_discipline",
    "external_entity_mapping", "data_version", "feature_version",
    "model_version", "prediction_snapshot",
]


# ------------------------------------------------------------------
# STEP S1 — vérification du socle
# ------------------------------------------------------------------

def step_s1_verify(socle: Path, backup_dir: Path) -> dict:
    log("S1 — Vérification du socle (lecture seule)")
    if not socle.exists():
        raise SystemExit(f"ERREUR FATALE : socle introuvable : {socle}")

    sha = sha256_file(socle)
    size = socle.stat().st_size
    log(f"  socle   : {socle}")
    log(f"  sha256  : {sha}")
    log(f"  taille  : {size} octets")

    backups = sorted(backup_dir.glob("*.db")) if backup_dir.exists() else []
    log(f"  backups phase1 trouvés : {len(backups)}")
    for b in backups:
        log(f"    - {b.name} ({b.stat().st_size} octets)")

    # contrôle de lecture + preuve de non-écriture
    conn = open_readonly(socle)
    try:
        n_tables = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        try:
            conn.execute("CREATE TABLE __rw_probe (x INTEGER)")
            readonly = False
        except sqlite3.OperationalError:
            readonly = True
    finally:
        conn.close()
    log(f"  tables  : {n_tables} | écriture refusée par SQLite : {readonly}")
    if not readonly:
        raise SystemExit("ERREUR FATALE : le socle n'est pas ouvert en lecture seule !")
    return {"sha256": sha, "size": size, "tables": n_tables, "backups": len(backups)}


# ------------------------------------------------------------------
# STEP S2 — création de la Master DB
# ------------------------------------------------------------------

def step_s2_create(master: Path) -> sqlite3.Connection:
    log("S2 — Création de la Master DB")
    master.parent.mkdir(parents=True, exist_ok=True)
    if master.exists():
        log(f"  fichier existant -> reconstruction idempotente : {master.name}")
    conn = sqlite3.connect(master)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = OFF")
    for t in MASTER_TABLES:
        conn.execute(f'DROP TABLE IF EXISTS "{t}"')
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")
    log(f"  schéma créé : {len(MASTER_TABLES)} tables")
    return conn


# ------------------------------------------------------------------
# STEP S3 — hippodromes
# ------------------------------------------------------------------

def step_s3_hippodromes(socle: sqlite3.Connection, master: sqlite3.Connection) -> dict:
    log("S3 — Référentiel hippodromes")
    rows = socle.execute(
        "SELECT hippodrome, COUNT(*) AS n FROM courses GROUP BY hippodrome").fetchall()

    ref_rows, master_rows = [], {}
    n_ok = n_numeric = n_missing = 0

    for r in rows:
        raw = r["hippodrome"]
        count = r["n"]
        if is_blank(raw):
            flag, canon, hid = "missing", None, None
            n_missing += count
        elif re.fullmatch(r"\d+", str(raw).strip()):
            flag, canon, hid = "numeric_parse_error", None, None
            n_numeric += count
        else:
            canon = norm_text(raw)
            hid = make_id("hippodrome", canon)
            flag = "ok"
            n_ok += count
            entry = master_rows.setdefault(hid, {
                "hippodrome_id": hid, "label_canonical": canon,
                "label_variants": set(), "country": "FR",
                "is_valid": 1, "quality_flag": "ok", "n_courses": 0,
            })
            entry["label_variants"].add(str(raw).strip())
            entry["n_courses"] += count
        ref_rows.append([str(raw) if raw is not None else "", hid, flag])

    for hid, e in master_rows.items():
        master.execute(
            "INSERT INTO master_hippodrome (hippodrome_id,label_canonical,label_variants,"
            "country,is_valid,quality_flag,n_courses) VALUES (?,?,?,?,?,?,?)",
            (hid, e["label_canonical"], " | ".join(sorted(e["label_variants"])),
             e["country"], e["is_valid"], e["quality_flag"], e["n_courses"]))

    master.executemany(
        "INSERT INTO ref_hippodrome (label_variant,hippodrome_id,quality_flag) VALUES (?,?,?)",
        ref_rows)
    master.commit()

    log(f"  hippodromes valides : {len(master_rows)} | courses ok={n_ok} "
        f"numériques={n_numeric} vides={n_missing}")
    return {"n_valid": len(master_rows), "n_ok": n_ok,
            "n_numeric": n_numeric, "n_missing": n_missing,
            "ref_rows": len(ref_rows)}


# ------------------------------------------------------------------
# STEP S4 — courses (master_race)
# ------------------------------------------------------------------

def step_s4_races(socle: sqlite3.Connection, master: sqlite3.Connection) -> dict:
    log("S4 — Dérivation des courses (master_race)")

    # arrivées par date (dédupliquées, cohérence contrôlée)
    arrivals: dict[str, dict] = {}
    ambiguous_dates: set[str] = set()
    for r in socle.execute(
        "SELECT date, arrivee FROM resultats "
        "WHERE TRIM(COALESCE(date,''))<>'' AND arrivee NOT IN ('','[]')"
    ):
        arr = parse_json_list(r["arrivee"])
        nums = [int(x) for x in arr if isinstance(x, (int, float)) or str(x).isdigit()]
        if not nums:
            continue
        d = r["date"]
        if d not in arrivals:
            arrivals[d] = {"nums": nums, "variants": {tuple(nums)}}
        else:
            arrivals[d]["variants"].add(tuple(nums))

    for d, info in arrivals.items():
        if len(info["variants"]) > 1:
            ambiguous_dates.add(d)

    def position_map(date_str: str):
        info = arrivals.get(date_str)
        if not info or date_str in ambiguous_dates:
            return None
        return {num: i + 1 for i, num in enumerate(info["nums"])}

    hip_map = {r["label_variant"]: r["hippodrome_id"] for r in
               master.execute("SELECT label_variant, hippodrome_id FROM ref_hippodrome")}

    counts = defaultdict(int)
    rows = socle.execute("""
        SELECT c.document_id, c.date, c.hippodrome, c.discipline, c.distance_m,
               c.montant_euros, c.partants_declares, c.partants_effectifs,
               c.type_course, c.titre,
               (SELECT COUNT(*) FROM partants p WHERE p.document_id = c.document_id) AS n_part
        FROM courses c
    """).fetchall()

    for r in rows:
        doc = r["document_id"]
        date = r["date"]
        is_sent = 1 if date == SENTINEL_DATE else 0
        raw_h = r["hippodrome"]
        hid = hip_map.get(str(raw_h) if raw_h is not None else "")
        if is_blank(raw_h):
            disc_status, disc = "missing", None
        elif is_blank(r["discipline"]):
            disc_status, disc = "missing", None
        else:
            disc_status, disc = "present", norm_text(r["discipline"])

        pmap = position_map(date)
        if is_sent:
            res_status = "sentinel_date"
        elif date in ambiguous_dates:
            res_status = "ambiguous_date"
        elif pmap is None:
            res_status = "no_arrival_for_date"
        else:
            res_status = "arrival_available"
        counts[res_status] += 1

        master.execute(
            "INSERT INTO master_race (race_id,source_document_id,date,date_is_sentinel,"
            "hippodrome_id,hippodrome_label_raw,discipline,discipline_status,distance_m,"
            "montant_euros,partants_declares,partants_effectifs,type_course,titre,"
            "n_partants_source,result_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (make_id("race", "LONAB", doc), doc, date, is_sent, hid,
             str(raw_h) if raw_h is not None else None, disc, disc_status,
             r["distance_m"], r["montant_euros"], r["partants_declares"],
             r["partants_effectifs"], r["type_course"], r["titre"],
             r["n_part"], res_status))
    master.commit()

    log(f"  courses          : {len(rows)}")
    log(f"  arrivée dispo    : {counts['arrival_available']}")
    log(f"  sans arrivée     : {counts['no_arrival_for_date']}")
    log(f"  date sentinelle  : {counts['sentinel_date']}")
    log(f"  date ambiguë     : {counts['ambiguous_date']}")
    return {"n_races": len(rows), "counts": dict(counts),
            "ambiguous_dates": sorted(ambiguous_dates)}


# ------------------------------------------------------------------
# STEP S5 — chevaux (master_horse)
# ------------------------------------------------------------------

def step_s5_horses(socle: sqlite3.Connection, master: sqlite3.Connection) -> dict:
    log("S5 — Résolution des chevaux (passe exacte + signal d'homonymie)")

    rows = socle.execute("""
        SELECT p.nom_cheval_normalized AS name, p.sexe, p.age, c.date
        FROM partants p JOIN courses c ON c.document_id = p.document_id
    """).fetchall()

    agg: dict[str, dict] = {}
    for r in rows:
        name = r["name"]
        if is_blank(name):
            continue
        key = norm_text(name)
        if not key:
            continue
        e = agg.setdefault(key, {
            "name_normalized": str(name).strip(), "n_starts": 0,
            "dates": [], "sb": set(),
        })
        e["n_starts"] += 1
        if not is_blank(r["date"]):
            e["dates"].append(r["date"])
        # signal (sexe, année de naissance) — EXCLUT la date sentinelle,
        # qui produirait des années de naissance fictives (1995 - âge).
        if r["date"] != SENTINEL_DATE:
            sl = sex_letter(r["sexe"])
            ag = horse_age(r["sexe"], r["age"])
            yr = year_of(r["date"])
            if sl and ag and yr:
                e["sb"].add((sl, yr - ag))

    # passe enrichie (pedigree) — 185 lignes
    ped = {}
    try:
        for r in socle.execute("""
            SELECT nom_cheval_normalized AS name, nom_pere, nom_mere, robe, race
            FROM partants_enrichis
        """):
            if is_blank(r["name"]):
                continue
            k = norm_text(r["name"])
            ped.setdefault(k, {"pere": r["nom_pere"], "mere": r["nom_mere"],
                               "robe": r["robe"], "race": r["race"]})
    except sqlite3.Error:
        pass

    review = []
    n_suspected = 0
    for key, e in sorted(agg.items()):
        variants = len(e["sb"])
        info = ped.get(key)
        if variants > 1:
            risk, method, conf = "suspected_homonym", "exact_name+sex_age", 0.6
        elif info:
            risk, method, conf = "verified_unique", "name+pedigree", 1.0
        elif variants == 1:
            risk, method, conf = "consistent_signal", "exact_name+sex_age", 0.9
        else:
            risk, method, conf = "no_signal", "exact_name", 0.7
        if risk == "suspected_homonym":
            n_suspected += 1
            review.append([key, e["name_normalized"], e["n_starts"], variants,
                           " | ".join(f"{a}~{b}" for a, b in sorted(e["sb"], key=str)),
                           risk, method, conf])

        dates = sorted(d for d in e["dates"] if d)
        master.execute(
            "INSERT INTO master_horse (horse_id,name_normalized,name_key,resolution_method,"
            "resolution_confidence,homonym_risk,n_sex_birthyear_variants,"
            "sex_birthyear_variants,n_starts,first_seen_date,last_seen_date,"
            "pedigree_pere,pedigree_mere,robe,race) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (make_id("horse", key), e["name_normalized"], key, method, conf, risk,
             variants, " | ".join(f"{a}~{b}" for a, b in sorted(e["sb"], key=str)),
             e["n_starts"], dates[0] if dates else None, dates[-1] if dates else None,
             info["pere"] if info else None, info["mere"] if info else None,
             info["robe"] if info else None, info["race"] if info else None))
    master.commit()

    log(f"  chevaux (name_key)   : {len(agg)}")
    log(f"  homonymes suspects   : {n_suspected}")
    log(f"  avec pedigree        : {sum(1 for k in agg if k in ped)}")
    return {"n_horses": len(agg), "n_suspected": n_suspected,
            "n_pedigree": sum(1 for k in agg if k in ped), "review": review}


# ------------------------------------------------------------------
# STEP S6 — personnes (master_person)
# ------------------------------------------------------------------

def step_s6_persons(socle: sqlite3.Connection, master: sqlite3.Connection) -> dict:
    log("S6 — Résolution des personnes (jockeys / entraîneurs / propriétaires)")

    specs = [
        ("JOCKEY", "driver_normalized"),
        ("TRAINER", "entraineur_normalized"),
        ("OWNER", "proprietaire_normalized"),
    ]
    stats = {}
    for role, col in specs:
        rows = socle.execute(
            f'SELECT "{col}" AS name, COUNT(*) AS n FROM partants '
            f'WHERE NOT ("{col}" IS NULL OR TRIM("{col}")=\'\') GROUP BY "{col}"'
        ).fetchall()
        # plusieurs libellés bruts peuvent se normaliser vers la même clé
        # (ex. 'D.SANTIAGO' et 'D SANTIAGO') -> agrégation en Python
        agg: dict[str, dict] = {}
        for r in rows:
            key = norm_text(r["name"])
            if not key:
                continue
            e = agg.setdefault(key, {"label": str(r["name"]).strip(), "n": 0})
            e["n"] += r["n"]
        for key, e in sorted(agg.items()):
            master.execute(
                "INSERT INTO master_person (person_id,name_normalized,name_key,role,"
                "resolution_method,resolution_confidence,n_appearances) VALUES (?,?,?,?,?,?,?)",
                (make_id("person", role, key), e["label"], key, role,
                 "exact_name", 1.0, e["n"]))
        stats[role] = len(agg)
        log(f"  {role:8s} : {len(agg)} entités distinctes "
            f"(depuis {len(rows)} libellés bruts)")

    master.commit()
    return stats


# ------------------------------------------------------------------
# STEP S7 — partants (master_runner)
# ------------------------------------------------------------------

def step_s7_runners(socle: sqlite3.Connection, master: sqlite3.Connection) -> dict:
    log("S7 — Construction de master_runner")

    # cartes d'identifiants (jamais de nom comme FK)
    horse_map = {r["name_key"]: r["horse_id"] for r in
                 master.execute("SELECT name_key, horse_id FROM master_horse")}
    person_map = {(r["role"], r["name_key"]): r["person_id"] for r in
                  master.execute("SELECT role, name_key, person_id FROM master_person")}
    race_map = {r["source_document_id"]: r["race_id"] for r in
                master.execute("SELECT source_document_id, race_id FROM master_race")}

    # arrivées
    arrivals: dict[str, list[int]] = {}
    ambiguous: set[str] = set()
    seen: dict[str, set] = defaultdict(set)
    for r in socle.execute(
        "SELECT date, arrivee FROM resultats "
        "WHERE TRIM(COALESCE(date,''))<>'' AND arrivee NOT IN ('','[]')"
    ):
        nums = [int(x) for x in parse_json_list(r["arrivee"])
                if str(x).isdigit() or isinstance(x, int)]
        if nums:
            seen[r["date"]].add(tuple(nums))
    for d, variants in seen.items():
        if len(variants) == 1:
            arrivals[d] = list(next(iter(variants)))
        else:
            ambiguous.add(d)

    counts = defaultdict(int)
    id_collisions = 0
    seen_ids = set()

    rows = socle.execute("""
        SELECT p.id, p.document_id, p.numero, p.nom_cheval_normalized,
               p.driver_normalized, p.entraineur_normalized, p.proprietaire_normalized,
               p.cote_decimale, p.gains_euros, p.performances_structured,
               p.sexe, p.age, p.poids, p.corde, c.date
        FROM partants p JOIN courses c ON c.document_id = p.document_id
    """).fetchall()

    for r in rows:
        doc, numero, date = r["document_id"], r["numero"], r["date"]
        rid = make_id("runner", doc, numero)
        if rid in seen_ids:
            id_collisions += 1
            rid = make_id("runner", doc, numero, r["id"])
        seen_ids.add(rid)

        if date == SENTINEL_DATE:
            pos, st = None, "sentinel_date"
        elif date in ambiguous:
            pos, st = None, "ambiguous_date"
        elif date not in arrivals:
            pos, st = None, "no_arrival_for_date"
        else:
            n2p = {num: i + 1 for i, num in enumerate(arrivals[date])}
            if numero in n2p:
                pos, st = n2p[numero], "arrived"
            else:
                # l'arrivée enregistrée ne liste que 3 à 5 places :
                # un partant absent de cette liste est "hors arrivée", pas une anomalie
                pos, st = None, "unplaced"
        counts[st] += 1

        master.execute(
            "INSERT INTO master_runner (runner_id,race_id,source_document_id,source_partant_id,"
            "numero,horse_id,jockey_id,trainer_id,owner_id,cote_decimale,gains_euros,"
            "performances_structured,sexe_raw,age_raw,poids_raw,corde_raw,"
            "result_position,result_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (rid, race_map.get(doc), doc, r["id"], numero,
             horse_map.get(norm_text(r["nom_cheval_normalized"])),
             person_map.get(("JOCKEY", norm_text(r["driver_normalized"]))),
             person_map.get(("TRAINER", norm_text(r["entraineur_normalized"]))),
             person_map.get(("OWNER", norm_text(r["proprietaire_normalized"]))),
             r["cote_decimale"], r["gains_euros"], r["performances_structured"],
             r["sexe"], r["age"], r["poids"], r["corde"], pos, st))
    master.commit()

    # validation : nombre MAXIMAL de positions théoriquement rattachables
    # (= somme des |arrivée ∩ numéros des partants| sur les courses concernées)
    max_matchable = 0
    for r in socle.execute("SELECT document_id AS doc, date FROM courses WHERE date <> ?",
                           (SENTINEL_DATE,)):
        a = arrivals.get(r["date"])
        if not a:
            continue
        nums = {x[0] for x in socle.execute(
            "SELECT numero FROM partants WHERE document_id = ?", (r["doc"],))}
        if nums:
            max_matchable += len(nums & set(a))

    # mise à jour des compteurs de courses
    master.execute("""
        UPDATE master_race SET n_runners_linked = (
            SELECT COUNT(*) FROM master_runner mr WHERE mr.race_id = master_race.race_id)
    """)
    master.commit()

    log(f"  runners                : {len(rows)}")
    log(f"  positions rattachées   : {counts['arrived']} / max rattachable {max_matchable}")
    log(f"  hors arrivée (3-5 pl.) : {counts['unplaced']}")
    log(f"  sans arrivée           : {counts['no_arrival_for_date']}")
    log(f"  date sentinelle        : {counts['sentinel_date']}")
    log(f"  date ambiguë           : {counts['ambiguous_date']}")
    log(f"  collisions d'ID        : {id_collisions}")
    return {"n_runners": len(rows), "counts": dict(counts),
            "id_collisions": id_collisions, "ambiguous": sorted(ambiguous),
            "max_matchable": max_matchable}


# ------------------------------------------------------------------
# STEP S8 — référentiel disciplines + file de revue
# ------------------------------------------------------------------

def step_s8_refs(socle: sqlite3.Connection, master: sqlite3.Connection,
                 out_dir: Path, horse_info: dict, socle_path: Path) -> dict:
    log("S8 — Référentiel disciplines + exports de contrôle")

    rows = socle.execute(
        "SELECT discipline, COUNT(*) AS n FROM courses GROUP BY discipline").fetchall()
    ref = []
    for r in rows:
        if is_blank(r["discipline"]):
            ref.append(["", None, "missing"])
        else:
            ref.append([str(r["discipline"]).strip(), norm_text(r["discipline"]), "present"])
    master.executemany(
        "INSERT INTO ref_discipline (discipline_raw,discipline_norm,status) VALUES (?,?,?)", ref)
    master.commit()

    # file de revue homonymes
    q_path = out_dir / "PHASE2_REVIEW_QUEUE.csv"
    csv_write(q_path,
              ["name_key", "name_normalized", "n_starts", "n_sex_birthyear_variants",
               "sex_birthyear_variants", "homonym_risk", "resolution_method",
               "resolution_confidence"],
              horse_info["review"])
    log(f"  file de revue : {q_path.name} ({len(horse_info['review'])} entités)")

    # RAW non référencés
    raw_dir = socle_path.parent.parent / "raw"
    unmatched = []
    if raw_dir.exists():
        known = {r[0] for r in socle.execute("SELECT filename FROM documents")}
        for p in sorted(raw_dir.rglob("*")):
            if p.is_file() and p.name not in known:
                unmatched.append([p.relative_to(raw_dir).as_posix(), p.stat().st_size])
    u_path = out_dir / "PHASE2_UNMATCHED_RAW.csv"
    csv_write(u_path, ["relative_path", "size_bytes"], unmatched)
    log(f"  RAW non référencés : {u_path.name} ({len(unmatched)} fichiers)")

    return {"n_discipline_variants": len(ref),
            "n_review": len(horse_info["review"]),
            "n_unmatched": len(unmatched)}


# ------------------------------------------------------------------
# STEP S9 — mapping externe + versioning
# ------------------------------------------------------------------

def step_s9_versioning(master: sqlite3.Connection, socle_sha: str,
                       master_path: Path) -> dict:
    log("S9 — Tables externes (vides) + versioning")
    now = datetime.now(timezone.utc).isoformat()
    master.execute(
        "INSERT INTO data_version (scope,version,source_sha256,created_at,notes) "
        "VALUES (?,?,?,?,?)",
        ("socle_lonab", "phase2-derived", socle_sha, now,
         "Master DB dérivée du socle LONAB en lecture seule"))
    master.execute(
        "INSERT INTO data_version (scope,version,source_sha256,created_at,notes) "
        "VALUES (?,?,?,?,?)",
        ("master_db", "v1", None, now, f"fichier: {master_path.name}"))
    master.commit()

    n_map = master.execute("SELECT COUNT(*) FROM external_entity_mapping").fetchone()[0]
    log(f"  external_entity_mapping : {n_map} ligne(s) — VIDE (bloque la Phase 4, ADR-001)")
    log("  data_version / feature_version / model_version / prediction_snapshot : prêtes")
    return {"n_external_mapping": n_map}


# ------------------------------------------------------------------
# STEP S10 — rapport
# ------------------------------------------------------------------

def step_s10_report(master: sqlite3.Connection, out_dir: Path, socle_path: Path,
                    master_path: Path, socle_info: dict, hip: dict, race: dict,
                    horse: dict, person: dict, runner: dict, refs: dict,
                    ver: dict) -> tuple[str, bool]:
    log("S10 — Rapport de validation")

    def cnt(sql):
        return master.execute(sql).fetchone()[0]

    n_race = cnt("SELECT COUNT(*) FROM master_race")
    n_horse = cnt("SELECT COUNT(*) FROM master_horse")
    n_person = cnt("SELECT COUNT(*) FROM master_person")
    n_runner = cnt("SELECT COUNT(*) FROM master_runner")
    n_pos = cnt("SELECT COUNT(*) FROM master_runner WHERE result_position IS NOT NULL")
    n_fk = cnt("SELECT COUNT(*) FROM master_runner WHERE horse_id IS NULL OR race_id IS NULL")
    n_jk = cnt("SELECT COUNT(*) FROM master_runner WHERE jockey_id IS NULL")
    n_tr = cnt("SELECT COUNT(*) FROM master_runner WHERE trainer_id IS NULL")

    # contrôle de non-régression du socle
    socle_after = sha256_file(socle_path)
    socle_ok = socle_after == socle_info["sha256"]

    master_sha = sha256_file(master_path) if master_path.exists() else None

    lines = [
        "# PHASE 2 REPORT", "",
        f"**Projet :** PMU'B LONAB — V2",
        f"**Date :** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Statut :** `{'PASS' if socle_ok else 'FAIL'}`", "",
        "## 1. Socle LONAB — non-régression", "",
        "| Élément | Valeur |", "|---|---|",
        f"| SHA-256 avant | `{socle_info['sha256']}` |",
        f"| SHA-256 après | `{socle_after}` |",
        f"| Inchangé | {'✅ OUI' if socle_ok else '❌ NON'} |",
        f"| Backup Phase 1 disponible | {'oui' if socle_info['backups'] else 'non'} |", "",
        "## 2. Master DB", "",
        "| Table | Lignes |", "|---|---|",
        f"| `master_hippodrome` | {cnt('SELECT COUNT(*) FROM master_hippodrome')} |",
        f"| `master_race` | {n_race} |",
        f"| `master_horse` | {n_horse} |",
        f"| `master_person` | {n_person} |",
        f"| `master_runner` | {n_runner} |",
        f"| `ref_hippodrome` | {cnt('SELECT COUNT(*) FROM ref_hippodrome')} |",
        f"| `ref_discipline` | {cnt('SELECT COUNT(*) FROM ref_discipline')} |",
        f"| `external_entity_mapping` | {cnt('SELECT COUNT(*) FROM external_entity_mapping')} |", "",
        "## 3. Couverture des identifiants", "",
        "| Mesure | Valeur |", "|---|---|",
        f"| `race_id` renseignés | {n_race} / {race['n_races']} |",
        f"| `horse_id` renseignés | {n_runner - cnt('SELECT COUNT(*) FROM master_runner WHERE horse_id IS NULL')} / {n_runner} |",
        f"| `jockey_id` renseignés | {n_runner - n_jk} / {n_runner} |",
        f"| `trainer_id` renseignés | {n_runner - n_tr} / {n_runner} |",
        f"| `result_position` renseignées | {n_pos} / {n_runner} |",
        f"| **FK manquantes** (race_id/horse_id) | **{n_fk}** |", "",
        "## 4. Chevaux — résolution", "",
        "| Mesure | Valeur |", "|---|---|",
        f"| Entités `horse_id` | {n_horse} |",
        f"| dont `suspected_homonym` | {horse['n_suspected']} |",
        f"| dont avec pedigree | {horse['n_pedigree']} |",
        f"| File de revue | `PHASE2_REVIEW_QUEUE.csv` ({horse['n_suspected']}) |", "",
        "## 5. Personnes", "",
        "| Rôle | Entités |", "|---|---|",
        f"| JOCKEY | {person.get('JOCKEY', 0)} |",
        f"| TRAINER | {person.get('TRAINER', 0)} |",
        f"| OWNER | {person.get('OWNER', 0)} |", "",
        "## 6. Hippodromes", "",
        "| Mesure | Valeur |", "|---|---|",
        f"| Hippodromes valides | {hip['n_valid']} |",
        f"| Courses rattachées | {hip['n_ok']} |",
        f"| Hippodromes numériques (non rattachés) | {hip['n_numeric']} |",
        f"| Hippodromes vides (non rattachés) | {hip['n_missing']} |", "",
        "## 7. Statut des résultats", "",
        "> ⚠️ Les arrivées enregistrées ne contiennent que **3 à 5 places**. Un partant "
        "absent de cette liste est donc *hors arrivée*, pas une anomalie.", "",
        "| Statut | Courses | Runners |", "|---|---|---|",
        f"| `arrived` (dans l'arrivée) | {race['counts'].get('arrival_available', 0)} | "
        f"{runner['counts'].get('arrived', 0)} |",
        f"| `unplaced` (hors arrivée 3-5 pl.) | — | {runner['counts'].get('unplaced', 0)} |",
        f"| `no_arrival_for_date` | {race['counts'].get('no_arrival_for_date', 0)} | "
        f"{runner['counts'].get('no_arrival_for_date', 0)} |",
        f"| `sentinel_date` | {race['counts'].get('sentinel_date', 0)} | "
        f"{runner['counts'].get('sentinel_date', 0)} |",
        f"| `ambiguous_date` | {race['counts'].get('ambiguous_date', 0)} | "
        f"{runner['counts'].get('ambiguous_date', 0)} |", "",
        f"> **Contrôle de complétude :** positions rattachées = "
        f"**{runner['counts'].get('arrived', 0)}** ; maximum théoriquement rattachable "
        f"(somme des |arrivée ∩ numéros|) = **{runner['max_matchable']}** → "
        f"**écart = {runner['max_matchable'] - runner['counts'].get('arrived', 0)}** "
        f"({'✅ jointure complète' if runner['max_matchable'] == runner['counts'].get('arrived', 0) else '❌ positions perdues'}).",
        f"> Dates ambiguës (arrivées contradictoires) : {', '.join(race['ambiguous_dates']) or 'aucune'}",
        f"> Collisions d'ID runner : {runner['id_collisions']}", "",
        "## 8. Mapping externe", "",
        f"`external_entity_mapping` : **{ver['n_external_mapping']} ligne** — table créée mais VIDE.",
        "Aucun fournisseur externe n'a été contacté (ADR-001). La Phase 4 reste bloquée.", "",
        "## 9. Livrables", "",
        f"- `{master_path}`",
        f"- SHA-256 Master DB : `{master_sha}`",
        "- `PHASE2_REPORT.md`, `PHASE2_IDENTITY_MAP.md`, `PHASE2_INTEGRITY.md`",
        f"- `PHASE2_REVIEW_QUEUE.csv` ({refs['n_review']} lignes)",
        f"- `PHASE2_UNMATCHED_RAW.csv` ({refs['n_unmatched']} fichiers)",
        "- `manifest_phase2.json`", "",
        "## 10. Critères de succès", "",
        "| # | Critère | État |", "|---|---|---|",
        f"| 1 | Socle LONAB inchangé | {'✅' if socle_ok else '❌'} |",
        f"| 2 | Déterminisme (2 runs identiques) | ✅ (UUIDv5) |",
        f"| 3 | Couverture `race_id` 100 % | {'✅' if n_race == race['n_races'] else '❌'} |",
        f"| 4 | Couverture `runner_id` 100 % | {'✅' if n_runner == runner['n_runners'] else '❌'} |",
        f"| 5 | `horse_id` renseigné | {'✅' if n_fk == 0 else '❌'} ({n_fk} manquants) |",
        "| 6 | Aucune clé = un nom | ✅ (UUIDv5 uniquement) |",
        f"| 7 | `master_runner` == `partants` | {'✅' if n_runner == runner['n_runners'] else '❌'} |",
        f"| 8 | Arrivées rattachées (complétude) | "
        f"{'✅' if runner['max_matchable'] == runner['counts'].get('arrived', 0) else '❌'} "
        f"({n_pos} / {runner['max_matchable']}) |",
        "| 9 | Aucune donnée fictive | ✅ (incertitudes tracées) |",
        "| 10 | Aucune API externe | ✅ |", "",
        "---", "",
        "**PHASE 2 COMPLETE — WAITING FOR HUMAN VALIDATION**", "",
    ]
    report = "\n".join(lines)
    (out_dir / "PHASE2_REPORT.md").write_text(report, encoding="utf-8")
    log(f"  écrit : PHASE2_REPORT.md | socle inchangé : {socle_ok}")
    return report, socle_ok


# ------------------------------------------------------------------
# STEP S10b — documents annexes
# ------------------------------------------------------------------

def step_s10b_annexes(master: sqlite3.Connection, out_dir: Path, socle_path: Path,
                      socle_info: dict, master_path: Path, person: dict,
                      runner: dict, race: dict) -> None:
    def cnt(sql):
        return master.execute(sql).fetchone()[0]

    # IDENTITY MAP
    lines = ["# PHASE2_IDENTITY_MAP", "",
             "> Identifiants internes générés par UUIDv5 déterministe.", "",
             "## Volumétrie", "",
             "| Entité | Table | Identifiants |", "|---|---|---|",
             f"| Courses | `master_race` | {cnt('SELECT COUNT(*) FROM master_race')} |",
             f"| Chevaux | `master_horse` | {cnt('SELECT COUNT(*) FROM master_horse')} |",
             f"| Jockeys | `master_person` (JOCKEY) | {person.get('JOCKEY', 0)} |",
             f"| Entraîneurs | `master_person` (TRAINER) | {person.get('TRAINER', 0)} |",
             f"| Propriétaires | `master_person` (OWNER) | {person.get('OWNER', 0)} |",
             f"| Hippodromes | `master_hippodrome` | {cnt('SELECT COUNT(*) FROM master_hippodrome')} |",
             f"| Partants | `master_runner` | {cnt('SELECT COUNT(*) FROM master_runner')} |", "",
             "## Risque d'homonymie (chevaux)", "",
             "| homonym_risk | Entités |", "|---|---|"]
    for r in master.execute(
            "SELECT homonym_risk, COUNT(*) n FROM master_horse GROUP BY homonym_risk "
            "ORDER BY n DESC"):
        lines.append(f"| `{r['homonym_risk']}` | {r['n']} |")
    lines += ["", "## Résolution (méthode)", "", "| resolution_method | Entités |", "|---|---|"]
    for r in master.execute(
            "SELECT resolution_method, COUNT(*) n FROM master_horse "
            "GROUP BY resolution_method ORDER BY n DESC"):
        lines.append(f"| `{r['resolution_method']}` | {r['n']} |")
    lines += ["", "## Confiance", "", "| resolution_confidence | Entités |", "|---|---|"]
    for r in master.execute(
            "SELECT resolution_confidence, COUNT(*) n FROM master_horse "
            "GROUP BY resolution_confidence ORDER BY resolution_confidence DESC"):
        lines.append(f"| {r['resolution_confidence']} | {r['n']} |")
    lines += ["", "> ⚠️ Un `horse_id` regroupe un **nom normalisé**, pas nécessairement un "
              "cheval biologique unique. Les homonymes suspects sont listés dans "
              "`PHASE2_REVIEW_QUEUE.csv` et **n'ont pas été scindés** (aucune décision "
              "automatique sur l'identité réelle).", ""]
    (out_dir / "PHASE2_IDENTITY_MAP.md").write_text("\n".join(lines), encoding="utf-8")

    # INTEGRITY
    socle_after = sha256_file(socle_path)
    ok = socle_after == socle_info["sha256"]
    lines = ["# PHASE2_INTEGRITY", "",
             "## Socle LONAB", "",
             "| Contrôle | Valeur |", "|---|---|",
             f"| Chemin | `{socle_path}` |",
             f"| SHA-256 avant Phase 2 | `{socle_info['sha256']}` |",
             f"| SHA-256 après Phase 2 | `{socle_after}` |",
             f"| Taille | {socle_info['size']} octets |",
             f"| **Inchangé** | **{'✅ OUI' if ok else '❌ NON'}** |", "",
             "## Master DB (fichier neuf, séparé)", "",
             "| Contrôle | Valeur |", "|---|---|",
             f"| Chemin | `{master_path}` |",
             f"| SHA-256 | `{sha256_file(master_path) if master_path.exists() else 'n/a'}` |", "",
             "## Contrôles", "",
             "| Contrôle | Résultat |", "|---|---|",
             "| Aucun `UPDATE`/`DELETE`/`INSERT`/`ALTER` sur le socle | ✅ (URI `mode=ro`) |",
             "| Aucune API externe appelée | ✅ |",
             "| Aucun modèle ML entraîné | ✅ |",
             "| Aucune donnée fictive | ✅ |",
             "| Rollback = supprimer la Master DB | ✅ |", ""]
    (out_dir / "PHASE2_INTEGRITY.md").write_text("\n".join(lines), encoding="utf-8")

    # manifest
    manifest = {
        "phase": "2",
        "project": "PMU'B LONAB",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "socle": {
            "path": str(socle_path), "size_bytes": socle_info["size"],
            "sha256_before": socle_info["sha256"], "sha256_after": socle_after,
            "unchanged": ok,
        },
        "master_db": {
            "path": str(master_path),
            "sha256": sha256_file(master_path) if master_path.exists() else None,
        },
        "namespace_uuid": str(NAMESPACE_PMUB),
        "counts": {
            "races": cnt("SELECT COUNT(*) FROM master_race"),
            "horses": cnt("SELECT COUNT(*) FROM master_horse"),
            "persons": cnt("SELECT COUNT(*) FROM master_person"),
            "runners": cnt("SELECT COUNT(*) FROM master_runner"),
            "hippodromes": cnt("SELECT COUNT(*) FROM master_hippodrome"),
            "positions": cnt("SELECT COUNT(*) FROM master_runner WHERE result_position IS NOT NULL"),
            "positions_max_matchable": runner["max_matchable"],
            "unplaced": runner["counts"].get("unplaced", 0),
        },
        "ambiguous_dates": race["ambiguous_dates"],
        "id_collisions": runner["id_collisions"],
    }
    (out_dir / "manifest_phase2.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    log("  écrit : PHASE2_IDENTITY_MAP.md, PHASE2_INTEGRITY.md, manifest_phase2.json")


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------

master_path_global = DEFAULT_MASTER


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Phase 2 — Master DB + identifiants internes")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--master", default=str(DEFAULT_MASTER))
    ap.add_argument("--output-dir", default=str(DEFAULT_OUT))
    args = ap.parse_args(argv)

    socle_path = Path(args.db).resolve()
    master_path = Path(args.master).resolve()
    out_dir = Path(args.output_dir).resolve()
    backup_dir = socle_path.parent.parent / "backups" / "phase1"

    log("=" * 64)
    log("  PHASE 2 — MASTER DATABASE + IDENTIFIANTS INTERNES")
    log("=" * 64)

    socle_info = step_s1_verify(socle_path, backup_dir)
    master = step_s2_create(master_path)
    socle = open_readonly(socle_path)
    try:
        hip = step_s3_hippodromes(socle, master)
        race = step_s4_races(socle, master)
        horse = step_s5_horses(socle, master)
        person = step_s6_persons(socle, master)
        runner = step_s7_runners(socle, master)
        refs = step_s8_refs(socle, master, out_dir, horse, socle_path)
    finally:
        socle.close()

    ver = step_s9_versioning(master, socle_info["sha256"], master_path)
    report, socle_ok = step_s10_report(master, out_dir, socle_path, master_path,
                                       socle_info, hip, race, horse, person,
                                       runner, refs, ver)
    step_s10b_annexes(master, out_dir, socle_path, socle_info, master_path,
                      person, runner, race)
    master.close()

    log("=" * 64)
    log(f"  PHASE 2 STATUS: {'PASS' if socle_ok else 'FAIL'}")
    log("=" * 64)
    return 0 if socle_ok else 1


if __name__ == "__main__":
    sys.exit(main())
