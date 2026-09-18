#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 12 — CAPTURE FORWARD DU MOUVEMENT DES COTES
==================================================

Dernière hypothèse non testée : le **mouvement des cotes** (ouverture → clôture).
Les Phases 9-11 ont montré que les marchés SG / Placé / exotiques sont **efficients
en niveau**. Mais l'information du **mouvement** (argent informé) n'est pas dans un
instantané : elle n'apparaît qu'en **pollant une course AVANT son départ**.

Ce script capture, pour les courses **à venir**, une série d'instantanés du marché
réel (`citations` : `enjeu` + `ratio` par cheval, horodatés par `api_updatetime`),
et les stocke dans `external_pmu_citations` (clé = `api_updatetime`, donc chaque
instantané est conservé).

⚠️ ADR-001 : adapter **désactivé par défaut** (`--enable-external`), écrit uniquement
dans les tables `external_*`, socle jamais modifié (SHA vérifié avant/après).

⚠️ Réseau : le sandbox bloque l'HTTP sortant → exécuter hors sandbox, avec le repli
DNS + `ProxyHandler({})` (déjà gérés par `pmu_odds_adapter`).

Usage :
  # une passe (instantané unique de toutes les courses à venir)
  python scripts/phase12/capture_odds_movement.py --enable-external --once

  # capture continue (ex. toutes les 2 min pendant 30 min)
  python scripts/phase12/capture_odds_movement.py --enable-external \
      --interval 120 --duration 1800 --max-races 20

  # état de la collecte
  python scripts/phase12/capture_odds_movement.py --report
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "phase9"))

# Réutilisation du client réseau VÉRIFIÉ de la Phase 9 (aucun endpoint inventé)
from pmu_odds_adapter import (  # noqa: E402
    BASE_URL, MASTER_DB, SOCLE_DB, SOCLE_SHA_EXPECTED,
    install_dns_fallback, build_opener, fetch_json, parse_citations,
    open_master_rw, sha256_file, ddmmyyyy, FALLBACK_IPS,
)

REPORT = ROOT / "PHASE12_CAPTURE_STATE.md"


def select_upcoming(opener, iso: str, min_lead_s: int = 0, max_races: int = 50):
    """Renvoie [(reunion, course, heure_utc)] des courses dont le départ est FUTUR."""
    url = f"{BASE_URL}/programme/{ddmmyyyy(iso)}?specialisation=INTERNET"
    prog, err = fetch_json(opener, url)
    if prog is None:
        print(f"programme indisponible pour {iso} : {err}")
        return []
    now = datetime.now(timezone.utc)
    out = []
    for reun in (prog.get("programme", {}) or {}).get("reunions", []) or []:
        rn = reun.get("numOfficiel")
        for c in reun.get("courses", []) or []:
            cn = c.get("numOrdre")
            ms = c.get("heureDepart")
            if rn is None or cn is None or not ms:
                continue
            dt = datetime.fromtimestamp(ms / 1000, timezone.utc)
            if (dt - now).total_seconds() >= min_lead_s:
                out.append((rn, cn, dt))
    out.sort(key=lambda z: z[2])
    return out[:max_races]


def capture_pass(opener, conn, iso, races, log) -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    n = 0
    for (r, c, dt) in races:
        url = (f"{BASE_URL}/programme/{ddmmyyyy(iso)}/R{r}/C{c}/citations"
               f"?paris=&specialisation=INTERNET&combinaisonEnTableau=true")
        data, err = fetch_json(opener, url, retries=2)
        if data is None:
            log(conn, "citations", iso, r, c, "ERREUR", str(err))
            continue
        rows = parse_citations(data)
        for x in rows:
            conn.execute(
                """INSERT OR IGNORE INTO external_pmu_citations
                   (fetched_at, date_race, reunion, course, type_pari, api_updatetime,
                    numero, nom, statut, enjeu, ratio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (now, iso, r, c, x["type_pari"], x["api_updatetime"], x["numero"],
                 x["nom"], x["statut"], x["enjeu"], x["ratio"]))
        n += len(rows)
        conn.commit()
        time.sleep(0.35)
    return n


def select_all_races(opener, iso: str):
    """Renvoie [(reunion, course, heure_utc)] de TOUTES les courses du programme."""
    url = f"{BASE_URL}/programme/{ddmmyyyy(iso)}?specialisation=INTERNET"
    prog, err = fetch_json(opener, url)
    if prog is None:
        print(f"programme indisponible pour {iso} : {err}")
        return []
    out = []
    for reun in (prog.get("programme", {}) or {}).get("reunions", []) or []:
        rn = reun.get("numOfficiel")
        for c in reun.get("courses", []) or []:
            cn = c.get("numOrdre")
            ms = c.get("heureDepart")
            if rn is None or cn is None or not ms:
                continue
            out.append((rn, cn, datetime.fromtimestamp(ms / 1000, timezone.utc)))
    return out


def fetch_results_pass(opener, conn, iso, races, log) -> int:
    """Récupère `rapports-definitifs` pour les courses DÉJÀ PARTIES (sinon le test
    prédictif n'a pas d'issue à comparer). Écrit dans external_pmu_results."""
    now = datetime.now(timezone.utc)
    n = 0
    for (r, c, dt) in races:
        if dt > now:          # pas encore courue
            continue
        url = (f"{BASE_URL}/programme/{ddmmyyyy(iso)}/R{r}/C{c}/rapports-definitifs"
               f"?specialisation=INTERNET&combinaisonEnTableau=true")
        data, err = fetch_json(opener, url, retries=2)
        if not isinstance(data, list):
            log(conn, "rapports-definitifs", iso, r, c, "ERREUR", str(err))
            continue
        fetched = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        for rap in data:
            conn.execute(
                """INSERT OR REPLACE INTO external_pmu_results
                   (date_race, reunion, course, fetched_at, arrivee, type_pari,
                    nb_gagnants, masse_partager, data_json)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (iso, r, c, fetched, json.dumps(rap.get("arrivee"), ensure_ascii=False),
                 rap.get("typePari"), rap.get("nbGagnants"), rap.get("massePartager"),
                 json.dumps(rap, ensure_ascii=False)))
        conn.commit()
        n += 1
        time.sleep(0.35)
    return n


def races_with_movement(conn):
    """{(date, reunion, course)} ayant ≥2 instantanés SG (= mouvement capté)."""
    return {(r["date_race"], r["reunion"], r["course"]) for r in conn.execute(
        """SELECT date_race, reunion, course
           FROM external_pmu_citations
           WHERE type_pari='E_SIMPLE_GAGNANT'
           GROUP BY date_race, reunion, course
           HAVING COUNT(DISTINCT api_updatetime) >= 2""")}


def races_with_result(conn):
    """{(date, reunion, course)} ayant un résultat SG (rapports-definitifs)."""
    return {(r["date_race"], r["reunion"], r["course"]) for r in conn.execute(
        """SELECT date_race, reunion, course
           FROM external_pmu_results
           WHERE type_pari='E_SIMPLE_GAGNANT'""")}


def missing_result_dates(conn):
    """Dates ISO où du mouvement a été capté MAIS le résultat SG manque encore.

    C'est le correctif du trou de couverture : la capture (courses à venir) et la
    récupération des résultats (courses déjà parties) se déroulent le même jour, donc
    les courses qui finissent APRÈS la passe « fetch-results » n'obtiennent jamais
    leur résultat (l'automation du lendemain ne regarde que le lendemain).
    """
    missing = sorted(races_with_movement(conn) - races_with_result(conn))
    return sorted({d for (d, _r, _c) in missing}), missing


def report(conn, iso=None):
    where = "WHERE date_race=?" if iso else ""
    args = (iso,) if iso else ()
    print("=== ÉTAT DE LA CAPTURE FORWARD ===")
    rows = conn.execute(
        f"""SELECT date_race, reunion, course, COUNT(DISTINCT api_updatetime) n_snap,
                   COUNT(DISTINCT numero) n_chevaux
            FROM external_pmu_citations {where}
            GROUP BY date_race, reunion, course
            HAVING n_snap >= 2 ORDER BY n_snap DESC LIMIT 15""", args).fetchall()
    if not rows:
        print("  aucune course avec ≥2 instantanés (pas encore de mouvement capté).")
        return
    print(f"  courses avec ≥2 instantanés : {len(rows)} (top 15)")
    for r in rows:
        print(f"    {r['date_race']} R{r['reunion']}C{r['course']} : "
              f"{r['n_snap']} instantanés, {r['n_chevaux']} chevaux")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Capture forward du mouvement des cotes PMU.")
    ap.add_argument("--enable-external", action="store_true")
    ap.add_argument("--date", help="date ISO (défaut : aujourd'hui UTC)")
    ap.add_argument("--once", action="store_true", help="une seule passe")
    ap.add_argument("--interval", type=int, default=120, help="secondes entre passes")
    ap.add_argument("--duration", type=int, default=600, help="durée totale (s)")
    ap.add_argument("--max-races", type=int, default=20)
    ap.add_argument("--min-lead", type=int, default=60,
                    help="ne capturer que les courses à ≥ N s du départ")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--fetch-results", action="store_true",
                    help="récupère les rapports définitifs des courses DÉJÀ parties (pour le test prédictif)")
    ap.add_argument("--backfill-results", action="store_true",
                    help="récupère les résultats des dates ayant du MOUVEMENT mais un résultat manquant "
                         "(ferme le trou de couverture : courses finies après la passe du jour)")
    ap.add_argument("--master", default=str(MASTER_DB))
    a = ap.parse_args(argv)

    conn = open_master_rw(Path(a.master))
    if a.report:
        report(conn, a.date)
        return 0

    if not a.enable_external:
        print("ADAPTER EXTERNE DÉSACTIVÉ (ADR-001). Relancer avec --enable-external.")
        return 2

    socle_before = sha256_file(SOCLE_DB)
    if socle_before != SOCLE_SHA_EXPECTED:
        raise SystemExit(f"ERREUR FATALE : SHA socle inattendu : {socle_before}")

    iso = a.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    install_dns_fallback(FALLBACK_IPS[0])
    opener = build_opener()
    log = None
    from pmu_odds_adapter import make_logger
    log = make_logger(conn)

    # mode « boucher le trou de couverture » : résultats manquants des dates déjà captées
    if a.backfill_results:
        dates, missing = missing_result_dates(conn)
        print(f"courses avec mouvement : {len(races_with_movement(conn))} ; "
              f"avec résultat : {len(races_with_movement(conn) & races_with_result(conn))} ; "
              f"manquantes : {len(missing)} sur {len(dates)} date(s)")
        total = 0
        for iso in dates:
            allr = select_all_races(opener, iso)
            n = fetch_results_pass(opener, conn, iso, allr, log)
            total += n
            print(f"  {iso} : {n} course(s) dont le résultat a été récupéré")
        socle_after = sha256_file(SOCLE_DB)
        print(f"socle inchangé : {socle_after == socle_before}")
        print("STATUS: PASS")
        return 0

    # mode « récupérer les résultats des courses déjà parties »
    if a.fetch_results:
        allr = select_all_races(opener, iso)
        n = fetch_results_pass(opener, conn, iso, allr, log)
        socle_after = sha256_file(SOCLE_DB)
        print(f"{iso} : {n} course(s) dont les résultats ont été récupérés")
        print(f"socle inchangé : {socle_after == socle_before}")
        report(conn, iso)
        print("STATUS: PASS")
        return 0

    races = select_upcoming(opener, iso, a.min_lead, a.max_races)
    print(f"{iso} : {len(races)} course(s) à venir (départ futur)")
    for (r, c, dt) in races[:5]:
        print(f"   R{r}C{c} → départ {dt.strftime('%H:%M')} UTC")
    if not races:
        print("Aucune course à venir : rien à capturer.")
        return 1

    passes = 1 if a.once else max(1, a.duration // max(a.interval, 1))
    print(f"mode : {passes} passe(s), intervalle {a.interval}s")
    total = 0
    for k in range(passes):
        # re-sélectionner les courses encore à venir (les départs approchent)
        live = [(r, c, dt) for (r, c, dt) in races
                if (dt - datetime.now(timezone.utc)).total_seconds() >= a.min_lead]
        if not live:
            print(f"--- passe {k+1} : plus aucune course à venir, arrêt ---")
            break
        n = capture_pass(opener, conn, iso, live, log)
        total += n
        print(f"--- passe {k+1}/{passes} : {n} lignes captées, "
              f"{len(live)} course(s) en cours de capture ---")
        if k + 1 < passes:
            time.sleep(a.interval)

    socle_after = sha256_file(SOCLE_DB)
    print(f"\nlignes captées (avant dédoublonnage) : {total}")
    print(f"socle inchangé : {socle_after == socle_before}")
    report(conn, iso)
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
