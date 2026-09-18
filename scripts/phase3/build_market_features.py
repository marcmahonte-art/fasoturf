#!/usr/bin/env python3
"""
PHASE 3 / ÉTAPE 1 — FEATURES DE MARCHÉ + FORM + AUDIT ANTI-FUITE (PMU'B LONAB V2)

Construit la couche `market_*` dans la Master DB, à partir de la Master DB uniquement.
Le socle LONAB n'est PAS lu ici (et jamais modifié).

Garanties :
  - Master DB ouverte en écriture (c'est NOTRE base dérivée), socle jamais touché
  - AUCUNE fuite temporelle : les features cumulatives n'utilisent que des courses
    STRICTEMENT antérieures (regroupement par date, mise à jour des stats APRÈS)
  - aucun appel API externe
  - déterministe : aucun aléatoire

Usage :
    python scripts/phase3/build_market_features.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MASTER = (PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db")
DEFAULT_SOCLE = (PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db")
DEFAULT_OUT = PROJECT_ROOT

SOCLE_SHA_EXPECTED = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"

TRAIN_FRAC, VAL_FRAC = 0.60, 0.20   # le reste = test


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_ranks(value) -> list[int]:
    """`performances_structured` = musique pré-course, ex. '[2, 2, 9, 5, 4]'."""
    if value is None:
        return []
    try:
        arr = json.loads(value) if isinstance(value, str) else value
    except (ValueError, TypeError):
        return []
    if not isinstance(arr, list):
        return []
    out = []
    for x in arr:
        try:
            out.append(int(x))
        except (TypeError, ValueError):
            continue
    return out


def sex_code(sexe_raw) -> int:
    """H -> 0 (hongre), F -> 1 (femelle), M -> 2 (mâle), inconnu -> -1."""
    t = str(sexe_raw or "").strip().upper().split(".")[0].strip()
    return {"H": 0, "F": 1, "M": 2}.get(t, -1)


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


SCHEMA_SQL = """
DROP TABLE IF EXISTS market_runner_features;
DROP TABLE IF EXISTS market_race_meta;
DROP TABLE IF EXISTS phase3_leakage_audit;

CREATE TABLE market_runner_features (
    runner_id            TEXT PRIMARY KEY,
    race_id              TEXT NOT NULL,
    date                 TEXT,
    split                TEXT NOT NULL,

    -- --- marché (connu AVANT le départ : cotes du socle) ---
    m_implied            REAL,
    m_prob_norm          REAL,
    m_rank               INTEGER,
    m_log_odds           REAL,
    m_rel_median         REAL,
    m_is_fav             INTEGER,

    -- --- forme intrinsèque (pré-course, même ligne) ---
    f_musique_n          INTEGER,
    f_musique_avg        REAL,
    f_musique_best       REAL,
    f_musique_winrate    REAL,
    f_musique_top3rate   REAL,
    f_gains_log          REAL,
    f_age                INTEGER,
    f_sex                INTEGER,
    f_field_size         INTEGER,

    -- --- cumulatif STRICTEMENT antérieur (pas de fuite) ---
    c_horse_starts       INTEGER,
    c_horse_winrate      REAL,
    c_horse_top3rate     REAL,
    c_jockey_winrate     REAL,
    c_trainer_winrate    REAL,

    -- --- cibles ---
    label_win            INTEGER,
    label_top3           INTEGER,

    FOREIGN KEY (runner_id) REFERENCES master_runner(runner_id)
);

CREATE TABLE market_race_meta (
    race_id      TEXT PRIMARY KEY,
    date         TEXT,
    split        TEXT NOT NULL,
    n_runners    INTEGER NOT NULL,
    n_with_odds  INTEGER NOT NULL
);

CREATE TABLE phase3_leakage_audit (
    check_name  TEXT PRIMARY KEY,
    result      TEXT NOT NULL,
    detail      TEXT
);

CREATE INDEX idx_mrf_race   ON market_runner_features(race_id);
CREATE INDEX idx_mrf_split  ON market_runner_features(split);
"""


# ------------------------------------------------------------------

def step_s1_verify(socle: Path, master: Path) -> dict:
    log("S1 — Vérification socle + Master DB")
    if not socle.exists():
        raise SystemExit(f"socle introuvable : {socle}")
    if not master.exists():
        raise SystemExit(f"Master DB introuvable : {master} (lancer la Phase 2 d'abord)")

    socle_sha = sha256_file(socle)
    master_sha = sha256_file(master)
    log(f"  socle sha   : {socle_sha}")
    log(f"  master sha  : {master_sha}")
    if socle_sha != SOCLE_SHA_EXPECTED:
        raise SystemExit("ERREUR FATALE : le socle a changé depuis la Phase 1 !")

    conn = sqlite3.connect(f"file:{socle.as_posix()}?mode=ro", uri=True)
    try:
        try:
            conn.execute("CREATE TABLE __probe (x INTEGER)")
            raise SystemExit("ERREUR FATALE : le socle n'est pas en lecture seule !")
        except sqlite3.OperationalError:
            pass
    finally:
        conn.close()
    log("  socle : lecture seule confirmée (écriture refusée)")
    return {"socle_sha": socle_sha, "master_sha": master_sha}


def step_s2_schema(master: Path) -> sqlite3.Connection:
    log("S2 — Création des tables market_*")
    conn = sqlite3.connect(master)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    log("  tables créées : market_runner_features, market_race_meta, phase3_leakage_audit")
    return conn


def step_s3_features(conn: sqlite3.Connection) -> dict:
    log("S3 — Construction des features (cutoff temporel strict)")

    rows = conn.execute("""
        SELECT r.runner_id, r.race_id, r.horse_id, r.jockey_id, r.trainer_id,
               r.cote_decimale, r.gains_euros, r.performances_structured,
               r.age_raw, r.sexe_raw, r.result_position, r.result_status,
               ra.date
        FROM master_runner r
        JOIN master_race ra ON ra.race_id = r.race_id
        WHERE r.result_status IN ('arrived', 'unplaced')
          AND ra.date IS NOT NULL AND ra.date <> ''
        ORDER BY ra.date, r.race_id, r.numero
    """).fetchall()
    log(f"  runners éligibles : {len(rows)}")

    by_race: dict[str, list] = defaultdict(list)
    race_date: dict[str, str] = {}
    for r in rows:
        by_race[r["race_id"]].append(r)
        race_date[r["race_id"]] = r["date"]

    # split chronologique par dates distinctes
    dates = sorted(set(race_date.values()))
    n = len(dates)
    n_train, n_val = int(n * TRAIN_FRAC), int(n * VAL_FRAC)
    split_of_date = {}
    for i, d in enumerate(dates):
        split_of_date[d] = "train" if i < n_train else ("val" if i < n_train + n_val else "test")
    log(f"  dates : {n} -> train {n_train} | val {n_val} | test {n - n_train - n_val}")

    # stats cumulatives (mises à jour APRÈS chaque date, jamais avant)
    horse = defaultdict(lambda: [0, 0, 0])   # starts, wins, top3
    jockey = defaultdict(lambda: [0, 0])
    trainer = defaultdict(lambda: [0, 0])

    def rate(pair, idx=0):
        starts = pair[0]
        return (pair[idx + 1] / starts) if starts else 0.0

    payload = []
    race_meta = []
    order = sorted(by_race.keys(), key=lambda rid: (race_date[rid], rid))

    # regroupement par date : on calcule TOUTES les features d'une date
    # avant de mettre à jour les statistiques (anti-fuite intra-journée)
    i = 0
    while i < len(order):
        d = race_date[order[i]]
        group = []
        while i < len(order) and race_date[order[i]] == d:
            group.append(order[i])
            i += 1

        for rid in group:
            runners = by_race[rid]
            odds = [r["cote_decimale"] for r in runners
                    if r["cote_decimale"] is not None and r["cote_decimale"] > 0]
            implied_sum = sum(1.0 / o for o in odds) or 1.0
            med = median(odds) if odds else 0.0
            field = len(runners)
            split = split_of_date[d]

            ranked = sorted(
                [r for r in runners if r["cote_decimale"] and r["cote_decimale"] > 0],
                key=lambda r: r["cote_decimale"])
            rank_of = {r["runner_id"]: k + 1 for k, r in enumerate(ranked)}

            for r in runners:
                o = r["cote_decimale"] if (r["cote_decimale"] or 0) > 0 else None
                if o:
                    implied = 1.0 / o
                    prob_norm = implied / implied_sum
                    log_odds = math.log(o)
                    rel_med = (o / med) if med else 0.0
                    m_rank = rank_of.get(r["runner_id"])
                else:
                    implied = prob_norm = log_odds = rel_med = None
                    m_rank = None

                mus = parse_ranks(r["performances_structured"])
                valid = [x for x in mus if x > 0]
                f_n = len(mus)
                f_avg = (sum(valid) / len(valid)) if valid else None
                f_best = float(min(valid)) if valid else None
                f_wr = (mus.count(1) / f_n) if f_n else 0.0
                f_t3 = (sum(1 for x in mus if 1 <= x <= 3) / f_n) if f_n else 0.0

                age = None
                a = str(r["age_raw"] or "").strip()
                if a.isdigit() and 1 <= int(a) <= 25:
                    age = int(a)
                else:
                    p = str(r["sexe_raw"] or "").split(".")
                    if len(p) >= 2 and p[1].strip().isdigit() and 1 <= int(p[1]) <= 25:
                        age = int(p[1])

                hs = horse[r["horse_id"]] if r["horse_id"] else [0, 0, 0]
                js = jockey[r["jockey_id"]] if r["jockey_id"] else [0, 0]
                ts = trainer[r["trainer_id"]] if r["trainer_id"] else [0, 0]

                pos = r["result_position"]
                label_win = 1 if pos == 1 else 0
                label_top3 = 1 if (pos is not None and pos <= 3) else 0

                payload.append((
                    r["runner_id"], rid, d, split,
                    implied, prob_norm, m_rank, log_odds, rel_med,
                    1 if m_rank == 1 else 0,
                    f_n, f_avg, f_best, f_wr, f_t3,
                    math.log1p(r["gains_euros"]) if (r["gains_euros"] or 0) > 0 else 0.0,
                    age if age is not None else -1,
                    sex_code(r["sexe_raw"]),
                    field,
                    hs[0], (hs[1] / hs[0]) if hs[0] else 0.0, (hs[2] / hs[0]) if hs[0] else 0.0,
                    (js[1] / js[0]) if js[0] else 0.0,
                    (ts[1] / ts[0]) if ts[0] else 0.0,
                    label_win, label_top3,
                ))
            race_meta.append((rid, d, split, field, len(odds)))

        # mise à jour APRÈS la date complète
        for rid in group:
            for r in by_race[rid]:
                pos = r["result_position"]
                if r["horse_id"]:
                    s = horse[r["horse_id"]]
                    s[0] += 1
                    s[1] += 1 if pos == 1 else 0
                    s[2] += 1 if (pos is not None and pos <= 3) else 0
                if r["jockey_id"]:
                    s = jockey[r["jockey_id"]]
                    s[0] += 1
                    s[1] += 1 if pos == 1 else 0
                if r["trainer_id"]:
                    s = trainer[r["trainer_id"]]
                    s[0] += 1
                    s[1] += 1 if pos == 1 else 0

    conn.executemany("""
        INSERT INTO market_runner_features (
            runner_id, race_id, date, split,
            m_implied, m_prob_norm, m_rank, m_log_odds, m_rel_median, m_is_fav,
            f_musique_n, f_musique_avg, f_musique_best, f_musique_winrate,
            f_musique_top3rate, f_gains_log, f_age, f_sex, f_field_size,
            c_horse_starts, c_horse_winrate, c_horse_top3rate,
            c_jockey_winrate, c_trainer_winrate,
            label_win, label_top3
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, payload)
    conn.executemany(
        "INSERT INTO market_race_meta (race_id,date,split,n_runners,n_with_odds) "
        "VALUES (?,?,?,?,?)", race_meta)
    conn.commit()

    counts = defaultdict(int)
    for p in payload:
        counts[p[3]] += 1
    log(f"  features écrites : {len(payload)} lignes "
        f"(train {counts['train']} | val {counts['val']} | test {counts['test']})")
    log(f"  courses          : {len(race_meta)}")
    return {"n_features": len(payload), "n_races": len(race_meta),
            "counts": dict(counts), "n_dates": n,
            "dates": {"train": n_train, "val": n_val, "test": n - n_train - n_val}}


def step_s4_leakage(conn: sqlite3.Connection) -> dict:
    log("S4 — Audit anti-fuite")

    checks = []

    # 1. toute date de train <= toute date de val <= toute date de test
    mx = {r["split"]: r["m"] for r in conn.execute(
        "SELECT split, MAX(date) m FROM market_runner_features GROUP BY split")}
    mn = {r["split"]: r["m"] for r in conn.execute(
        "SELECT split, MIN(date) m FROM market_runner_features GROUP BY split")}
    ok1 = (mx.get("train", "") <= mn.get("val", "zzz")) and (mx.get("val", "") <= mn.get("test", "zzz"))
    checks.append(("split_chronologique", "PASS" if ok1 else "FAIL",
                   f"train≤{mx.get('train')} < val≤{mx.get('val')} < test≤{mx.get('test')}"))

    # 2. aucune feature de marché n'est NULL alors que la cote existe (cohérence)
    n_bad = conn.execute(
        "SELECT COUNT(*) FROM market_runner_features mf JOIN master_runner r "
        "ON r.runner_id = mf.runner_id "
        "WHERE r.cote_decimale > 0 AND mf.m_prob_norm IS NULL").fetchone()[0]
    checks.append(("marche_coherent", "PASS" if n_bad == 0 else "FAIL",
                   f"{n_bad} lignes avec cote mais sans probabilité"))

    # 3. probabilités normalisées : somme ≈ 1 par course
    bad_sum = 0
    for r in conn.execute("""
        SELECT race_id, SUM(m_prob_norm) s FROM market_runner_features
        WHERE m_prob_norm IS NOT NULL GROUP BY race_id"""):
        if r["s"] is not None and abs(r["s"] - 1.0) > 1e-6:
            bad_sum += 1
    checks.append(("probas_normalisees", "PASS" if bad_sum == 0 else "FAIL",
                   f"{bad_sum} courses dont la somme ≠ 1"))

    # 4. les stats cumulatives d'un cheval ne comptent que des courses antérieures
    #    (vérification par échantillon : starts cumulés <= starts réels avant la date)
    leak = conn.execute("""
        SELECT COUNT(*) FROM market_runner_features f
        WHERE f.c_horse_starts > (
            SELECT COUNT(*) FROM master_runner r2
            JOIN master_race ra2 ON ra2.race_id = r2.race_id
            JOIN master_runner r1 ON r1.runner_id = f.runner_id
            WHERE r2.horse_id = r1.horse_id AND ra2.date < f.date
              AND r2.result_status IN ('arrived','unplaced'))
    """).fetchone()[0]
    checks.append(("cumul_strictement_anterieur", "PASS" if leak == 0 else "FAIL",
                   f"{leak} lignes où c_horse_starts dépasse les courses antérieures réelles"))

    # 5. aucune feature dérivée de la cible
    forbidden = conn.execute("""
        SELECT COUNT(*) FROM pragma_table_info('market_runner_features')
        WHERE name IN ('result_position','finish_order','arrivee')
    """).fetchone()[0]
    checks.append(("aucune_colonne_cible", "PASS" if forbidden == 0 else "FAIL",
                   f"{forbidden} colonnes interdites trouvées"))

    conn.executemany(
        "INSERT OR REPLACE INTO phase3_leakage_audit (check_name,result,detail) VALUES (?,?,?)",
        checks)
    conn.commit()

    for name, res, det in checks:
        log(f"  [{res}] {name} — {det}")
    return {"checks": checks, "all_pass": all(c[1] == "PASS" for c in checks)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default=str(DEFAULT_MASTER))
    ap.add_argument("--socle", default=str(DEFAULT_SOCLE))
    a = ap.parse_args(argv)

    master, socle = Path(a.master).resolve(), Path(a.socle).resolve()
    log("=" * 64)
    log("  PHASE 3 / ÉTAPE 1 — FEATURES MARCHÉ + FORM + AUDIT ANTI-FUITE")
    log("=" * 64)

    step_s1_verify(socle, master)
    conn = step_s2_schema(master)
    try:
        feat = step_s3_features(conn)
        leak = step_s4_leakage(conn)
    finally:
        conn.close()

    socle_after = sha256_file(socle)
    ok = socle_after == SOCLE_SHA_EXPECTED
    log(f"  socle après : {'INCHANGÉ ✅' if ok else 'MODIFIÉ ❌'}")
    log("=" * 64)
    log(f"  ÉTAPE 1 STATUS: {'PASS' if (leak['all_pass'] and ok) else 'FAIL'}")
    log("=" * 64)
    return 0 if (leak["all_pass"] and ok) else 1


if __name__ == "__main__":
    sys.exit(main())
