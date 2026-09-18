#!/usr/bin/env python3
"""
ENRICHISSEMENT LONAB — libellé du pari officiel du jour
=======================================================

La course LONAB du jour est identifiée par `rebuild_sept_lonab.py` via l'API PMU
(la course qui porte QUINTPLUS / QUARTPLUS / TIERCE).

Ce script confronte cette identification au **journal officiel LONAB**
(`JH_PMUB_DU_DD-MM-YYYY.pdf`, page 1) et récupère le pari que la LONAB met en
avant ce jour-là — « 4+1 », « QUARTE » ou « TIERCE » — ainsi que l'hippodrome.

Validation constatée sur 09→16/09/2026 : 8/8 concordances.

Usage:
    python scripts/lonab_journal_enrich.py
"""

from __future__ import annotations

import importlib.util
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote

import requests
import urllib3

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent

MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
JOURNAL_BASE = "https://lonab.bf/sites/default/files"

START_DATE = date(2026, 9, 9)
END_DATE = date(2026, 9, 16)

# Le nom du fichier du 09/09 contient une apostrophe (JH_PMU'B_...) et un suffixe _0.
JOURNAL_OVERRIDES = {
    date(2026, 9, 9): "JH_PMU'B_DU_09-09-2026_0.pdf",
}


def load_rebuild_module():
    spec = importlib.util.spec_from_file_location("rebuild_sept_lonab", SCRIPT_DIR / "rebuild_sept_lonab.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def journal_url(d: date) -> str:
    name = JOURNAL_OVERRIDES.get(d) or f"JH_PMUB_DU_{d.day:02d}-{d.month:02d}-{d.year}.pdf"
    return f"{JOURNAL_BASE}/{d.year}-{d.month:02d}/{quote(name)}"


def fetch_headline(session, url: str):
    """Retourne (bet, venue, nb_pages) depuis la page 1 du journal LONAB."""
    r = session.get(url, timeout=90, verify=False)
    if r.status_code != 200:
        return None, None, r.status_code
    import pymupdf

    doc = pymupdf.open(stream=r.content, filetype="pdf")
    lines = [l.strip() for l in doc[0].get_text().splitlines() if l.strip()]
    hi = None
    for i, l in enumerate(lines):
        u = l.upper()
        if "2026" in u and " DU " in u:
            hi = i
            break
    if hi is None:
        return None, None, doc.page_count
    bet = lines[hi].split(" DU ")[0].strip().strip('"').strip()
    venue = lines[hi + 1] if hi + 1 < len(lines) else ""
    return bet, venue, doc.page_count


def main() -> int:
    rb = load_rebuild_module()

    print("=" * 74)
    print("  ENRICHISSEMENT LONAB — pari officiel du jour (journaux PDF)")
    print("=" * 74)

    conn = sqlite3.connect(str(MASTER_DB), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.row_factory = sqlite3.Row

    cols = {r[1] for r in conn.execute("PRAGMA table_info('master_race')")}
    for name, ddl in (("lonab_journal_bet", "TEXT"),
                      ("lonab_journal_venue", "TEXT"),
                      ("lonab_source_url", "TEXT")):
        if name not in cols:
            conn.execute(f"ALTER TABLE master_race ADD COLUMN {name} {ddl}")
    conn.commit()

    session = requests.Session()
    session.trust_env = False
    session.proxies = {}
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    urllib3.disable_warnings()
    ok_count = 0
    total = 0

    d = START_DATE
    while d <= END_DATE:
        dstr = d.isoformat()
        url = journal_url(d)

        # La course LONAB « principale » = celle qui porte le Quinté+
        row = conn.execute(
            """SELECT race_id, hippodrome_label_raw, titre
               FROM master_race
               WHERE date = ? AND is_lonab = 1 AND lonab_bet LIKE 'Quinté+%'
               ORDER BY reunion_num, course_num LIMIT 1""",
            (dstr,),
        ).fetchone()

        if not row:
            print(f"  {dstr} : aucune course LONAB principale en base -> ignoré")
            d += timedelta(days=1)
            continue

        total += 1
        bet, venue, pages = fetch_headline(session, url)
        if bet is None:
            print(f"  {dstr} : journal indisponible (HTTP {pages})")
            d += timedelta(days=1)
            continue

        hippo = (row["hippodrome_label_raw"] or "").upper().replace("-", "").replace(" ", "")
        venue_norm = (venue or "").upper().replace("-", "").replace(" ", "")
        match = hippo and hippo in venue_norm

        conn.execute(
            """UPDATE master_race
               SET lonab_journal_bet = ?, lonab_journal_venue = ?, lonab_source_url = ?
               WHERE race_id = ?""",
            (bet, venue, url, row["race_id"]),
        )
        conn.commit()

        flag = "OK" if match else "ECART"
        if match:
            ok_count += 1
        print(f"  {dstr} : pari LONAB = {bet:8s} | {venue[:34]:34s} | base = {row['hippodrome_label_raw'][:16]:16s} {flag}")
        d += timedelta(days=1)

    print(f"\n  Concordance journal LONAB / base : {ok_count}/{total}")

    print("\n  Ré-export du front…")
    rb.export_json(conn)
    conn.close()

    print("\n  TERMINÉ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
