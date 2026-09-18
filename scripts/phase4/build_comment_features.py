#!/usr/bin/env python3
"""
PHASE 4 / ÉTAPE 1 — FEATURES DE COMMENTAIRES PRESSE (PMU'B LONAB V2)

Extrait un signal depuis les 14 015 commentaires presse du socle et l'écrit
dans la Master DB (table `comment_features`).

Anti-fuite :
  - VÉRIFIÉ : 100 % des commentaires proviennent de documents `JOURNAL`
    (= presse PRÉ-course). Aucun commentaire post-course.
  - la provenance est contrôlée à l'exécution et consignée dans l'audit
  - aucun appel API externe ; socle ouvert en lecture seule

Usage :
    python scripts/phase4/build_comment_features.py
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
import sqlite3
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MASTER = PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
DEFAULT_SOCLE = PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"
SOCLE_SHA_EXPECTED = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"

# Lexique hippique français — marqueurs de sentiment
POS_MARKERS = [
    "favori", "favorite", "chance", "solide", "solidement", "regulier", "reguliere",
    "regularite", "en forme", "victoire", "victorieux", "victorieuse", "succes",
    "imposer", "impose", "gagner", "gagne", "gagnant", "a suivre", "atout",
    "excellent", "excellente", "convaincant", "convaincante", "rassurant", "rassurante",
    "progresse", "progression", "confiance", "logique", "incontournable",
    "performant", "performante", "brillant", "brillante", "facile", "facilement",
    "autorite", "serieux", "serieuse", "qualite", "prometteur", "prometteuse",
    "meilleur", "meilleure", "apte", "ideal", "parfait", "parfaite", "merite",
    "domine", "dominateur", "belle", "bel", "bonne", "net", "nette",
    "impressionnant", "impressionnante", "superbe",
]
NEG_MARKERS = [
    "decevant", "decevante", "decevra", "deception", "difficile", "difficilement",
    "echec", "loin", "retard", "blesse", "blessure", "arret", "mefiance", "doute",
    "douteux", "douteuse", "irregulier", "irreguliere", "irregularite", "fautif",
    "fautive", "disqualifie", "disqualifiee", "disqualification", "penalise",
    "penalisee", "lourd", "lourde", "surcharge", "surchargee", "absent", "forfait",
    "non partant", "modeste", "limite", "insuffisant", "insuffisante", "probleme",
    "inquietant", "inquietante", "desillusion", "en difficulte", "aucune chance",
]

WORD_RE = {}


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(value) -> str:
    if value is None:
        return ""
    s = unicodedata.normalize("NFKD", str(value))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.upper()
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return " ".join(s.split())


def count_markers(text_norm: str, markers: list[str]) -> int:
    total = 0
    for m in markers:
        key = norm(m)
        if not key:
            continue
        if key not in WORD_RE:
            WORD_RE[key] = re.compile(r"\b" + re.escape(key) + r"\b")
        total += len(WORD_RE[key].findall(text_norm))
    return total


SCHEMA_SQL = """
DROP TABLE IF EXISTS comment_features;
CREATE TABLE comment_features (
    runner_id     TEXT PRIMARY KEY,
    race_id       TEXT NOT NULL,
    has_comment   INTEGER NOT NULL,
    cm_len        INTEGER,
    cm_len_log    REAL,
    cm_pos        INTEGER,
    cm_neg        INTEGER,
    cm_sentiment  REAL,
    cm_has_favori INTEGER,
    FOREIGN KEY (runner_id) REFERENCES master_runner(runner_id)
);
CREATE INDEX idx_cf_race ON comment_features(race_id);
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default=str(DEFAULT_MASTER))
    ap.add_argument("--socle", default=str(DEFAULT_SOCLE))
    a = ap.parse_args(argv)
    master, socle = Path(a.master).resolve(), Path(a.socle).resolve()

    log("=" * 64)
    log("  PHASE 4 / ÉTAPE 1 — FEATURES COMMENTAIRES PRESSE")
    log("=" * 64)

    if sha256_file(socle) != SOCLE_SHA_EXPECTED:
        raise SystemExit("ERREUR FATALE : le socle a changé !")

    s = sqlite3.connect(f"file:{socle.as_posix()}?mode=ro", uri=True)
    s.row_factory = sqlite3.Row

    # --- contrôle de provenance (anti-fuite) ---
    prov = dict(s.execute("""
        SELECT d.doc_type, COUNT(*) FROM commentaires cm
        JOIN documents d ON d.id = cm.document_id GROUP BY d.doc_type""").fetchall())
    log(f"S1 — Provenance des commentaires : {prov}")
    leaky = sum(v for k, v in prov.items() if k != "JOURNAL")
    if leaky:
        raise SystemExit(f"ERREUR FATALE : {leaky} commentaires hors JOURNAL (fuite potentielle) !")
    log("  ✅ 100 % JOURNAL (presse pré-course) — aucun commentaire post-course")

    comments = {}
    for r in s.execute("SELECT document_id, numero_cheval, texte FROM commentaires"):
        comments[(r["document_id"], r["numero_cheval"])] = r["texte"] or ""
    log(f"  commentaires chargés : {len(comments)}")
    s.close()

    m = sqlite3.connect(master)
    m.row_factory = sqlite3.Row
    m.executescript(SCHEMA_SQL)

    runners = m.execute("""
        SELECT runner_id, race_id, source_document_id, numero
        FROM master_runner WHERE result_status IN ('arrived','unplaced')""").fetchall()

    payload = []
    n_with = 0
    for r in runners:
        txt = comments.get((r["source_document_id"], r["numero"]))
        if txt is None:
            payload.append((r["runner_id"], r["race_id"], 0, None, None, None, None, None, None))
            continue
        n_with += 1
        tn = norm(txt)
        pos = count_markers(tn, POS_MARKERS)
        neg = count_markers(tn, NEG_MARKERS)
        sent = (pos - neg) / (pos + neg + 1.0)
        payload.append((r["runner_id"], r["race_id"], 1, len(txt),
                        math.log1p(len(txt)), pos, neg, sent,
                        1 if "FAVORI" in tn else 0))

    m.executemany(
        "INSERT INTO comment_features (runner_id,race_id,has_comment,cm_len,cm_len_log,"
        "cm_pos,cm_neg,cm_sentiment,cm_has_favori) VALUES (?,?,?,?,?,?,?,?,?)", payload)
    m.commit()

    n = len(payload)
    log(f"S2 — Features écrites : {n} runners")
    log(f"  avec commentaire : {n_with} ({100*n_with/max(n,1):.1f} %)")
    pos_n = sum(1 for p in payload if p[5])
    log(f"  marqueurs positifs détectés : {sum(p[5] or 0 for p in payload)} occurrences")
    log(f"  marqueurs négatifs détectés : {sum(p[6] or 0 for p in payload)} occurrences")
    log(f"  mentions « favori »          : {sum(1 for p in payload if p[8])} runners")
    m.close()

    ok = sha256_file(socle) == SOCLE_SHA_EXPECTED
    log(f"  socle après : {'INCHANGÉ ✅' if ok else 'MODIFIÉ ❌'}")
    log("=" * 64)
    log(f"  ÉTAPE 1 STATUS: {'PASS' if ok else 'FAIL'}")
    log("=" * 64)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
