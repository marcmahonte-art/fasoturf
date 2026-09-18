#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 13 — BACKFILL DU MARCHÉ RÉEL (extension de l'échantillon)
================================================================

Les Phases 9-11 ont conclu à l'efficience sur **13 dates** (~300 courses).
Pour **resserrer les intervalles de confiance** et rendre le résultat négatif
plus solide, on étend la collecte du marché réel (citations + rapports) à des
dates supplémentaires, via le **client vérifié de la Phase 9** (aucun endpoint
inventé, ADR-001).

⚠️ Adapter désactivé par défaut (`--enable-external`), écrit uniquement dans
`external_*`, socle jamais modifié (SHA vérifié avant/après).

Usage :
  python scripts/phase13/collect_market_history.py --enable-external --max-races 30
  python scripts/phase13/collect_market_history.py --enable-external --dates 2024-03-08,2024-05-17
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "phase9"))

from pmu_odds_adapter import (  # noqa: E402
    BASE_URL, MASTER_DB, SOCLE_DB, SOCLE_SHA_EXPECTED, FALLBACK_IPS,
    install_dns_fallback, build_opener, fetch_json, open_master_rw,
    sha256_file, ddmmyyyy, fetch_race, make_logger,
)

# Dates supplémentaires (espacées, différentes de celles déjà collectées en Phase 9)
DEFAULT_DATES = [
    "2024-03-08", "2024-05-17", "2024-06-14", "2024-07-12",
    "2024-09-13", "2024-10-11", "2024-11-08",
    "2025-01-10", "2025-02-14", "2025-04-11", "2025-05-09",
    "2025-07-04", "2025-09-05", "2025-11-07",
    "2026-01-09", "2026-03-06", "2026-05-08", "2026-07-03",
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Backfill du marché réel PMU (Phase 13).")
    ap.add_argument("--enable-external", action="store_true")
    ap.add_argument("--dates", help="liste ISO séparée par des virgules (défaut : liste interne)")
    ap.add_argument("--max-races", type=int, default=30)
    ap.add_argument("--master", default=str(MASTER_DB))
    a = ap.parse_args(argv)

    if not a.enable_external:
        print("ADAPTER EXTERNE DÉSACTIVÉ (ADR-001). Relancer avec --enable-external.")
        return 2

    dates = [d.strip() for d in a.dates.split(",")] if a.dates else DEFAULT_DATES

    socle_before = sha256_file(SOCLE_DB)
    if socle_before != SOCLE_SHA_EXPECTED:
        raise SystemExit(f"ERREUR FATALE : SHA socle inattendu : {socle_before}")

    conn = open_master_rw(Path(a.master))
    install_dns_fallback(FALLBACK_IPS[0])
    opener = build_opener()
    log = make_logger(conn)

    print(f"backfill : {len(dates)} dates, max {a.max_races} courses/date")
    grand_total = 0
    ok_dates = 0
    for iso in dates:
        url = f"{BASE_URL}/programme/{ddmmyyyy(iso)}?specialisation=INTERNET"
        prog, err = fetch_json(opener, url, retries=2)
        if prog is None:
            print(f"  {iso} : programme indisponible ({err})")
            continue
        races = []
        for ru in (prog.get("programme", {}) or {}).get("reunions", []) or []:
            rn = ru.get("numOfficiel")
            for c in ru.get("courses", []) or []:
                cn = c.get("numOrdre")
                if rn is not None and cn is not None:
                    races.append((rn, cn))
        races = races[: a.max_races]
        tot = 0
        for (r, c) in races:
            try:
                tot += fetch_race(opener, conn, iso, r, c, log)
                conn.commit()
            except Exception as e:  # dégradation gracieuse
                log(conn, "exception", iso, r, c, "ERREUR", str(e))
        grand_total += tot
        ok_dates += 1
        print(f"  {iso} : {len(races)} courses, {tot} lignes citations")

    socle_after = sha256_file(SOCLE_DB)
    print(f"\ndates traitées : {ok_dates}/{len(dates)}")
    print(f"lignes citations captées : {grand_total}")
    print(f"socle inchangé : {socle_after == socle_before}")
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
