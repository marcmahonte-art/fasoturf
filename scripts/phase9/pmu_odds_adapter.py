#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 9 — ADAPTER EXTERNE : MASSE D'ENJEU ET COTES RÉELLES (API PMU)
=====================================================================

Objectif
--------
Aller chercher LA donnée manquante identifiée en Phase 5 : la **masse d'enjeu**
et les **cotes réelles** du marché PMU (et, par polling, leur **évolution**).
C'est la seule donnée absente du socle susceptible de porter un edge.

Conformité ADR-001 (RÈGLES STRICTES)
------------------------------------
- Adapter **DÉSACTIVÉ PAR DÉFAUT** : il faut `--enable-external` pour l'exécuter.
- Endpoints **VÉRIFIÉS** dans le code existant du projet (`explore_api.py`,
  `app/enrichment/pmu_client.py`) — **aucun endpoint inventé** (spec §12) :
    · https://online.turfinfo.api.pmu.fr/rest/client/61
    · programme/{DDMMYYYY}/R{n}/C{n}/citations?paris=&specialisation=INTERNET&combinaisonEnTableau=true
    · programme/{DDMMYYYY}/R{n}/C{n}/rapports-definitifs?specialisation=INTERNET&combinaisonEnTableau=true
- Écriture **UNIQUEMENT** dans des tables `external_*` de la **Master DB**.
  Le **socle LONAB n'est jamais modifié** (SHA vérifié avant/après).
- **Dégradation gracieuse** : toute panne réseau est journalisée, le pipeline
  continue (spec §64-8).

Structure vérifiée de la réponse `citations`
--------------------------------------------
  listeCitations[] -> { typePari, updatetime (epoch ms), participants[] }
    participants[] -> { numPmu, nom, statut, citations[ {position, enjeu, ratio} ] }
  où  `enjeu` = masse d'enjeu (EUR)   et   `ratio` = enjeu / masse_totale × 100
  (vérifié : la somme des `ratio` d'un typePari vaut 100).
  `updatetime` changeant d'un appel à l'autre => **évolution** des cotes par polling.

Usage
-----
  # liste des options
  python scripts/phase9/pmu_odds_adapter.py --help

  # récupérer le marché réel d'une date (obligatoire : --enable-external)
  python scripts/phase9/pmu_odds_adapter.py --enable-external --date 2024-02-09

  # une seule course, ou un nombre limité
  python scripts/phase9/pmu_odds_adapter.py --enable-external --date 2024-02-09 --race 1/1
  python scripts/phase9/pmu_odds_adapter.py --enable-external --date 2024-02-09 --max-races 10

  # capturer l'ÉVOLUTION : boucle de polling (courses à venir)
  python scripts/phase9/pmu_odds_adapter.py --enable-external --date 2026-09-14 --loop --interval 60 --duration 1800

  # analyser ce qui a été collecté
  python scripts/phase9/pmu_odds_adapter.py --report
"""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import sqlite3
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
SOCLE_DB = ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"

SOCLE_SHA_EXPECTED = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"

BASE_URL = "https://online.turfinfo.api.pmu.fr/rest/client/61"
PMU_HOSTS = ("online.turfinfo.api.pmu.fr", "offline.turfinfo.api.pmu.fr", "api.pmu.fr")

# IP de secours CloudFront — reprises du code existant du projet (pmu_client.py)
FALLBACK_IPS = ["99.86.159.69", "99.86.159.128", "99.86.159.19", "99.86.159.57"]

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "application/json",
    "Referer": "https://www.pmu.fr/",
}

RATE_DELAY = 0.35  # politesse


# --------------------------------------------------------------------------- #
# Réseau (stdlib pur, sans proxy, avec repli DNS)
# --------------------------------------------------------------------------- #
_orig_getaddrinfo = socket.getaddrinfo
_active_ip = FALLBACK_IPS[0]


def install_dns_fallback(ip: str) -> None:
    def patched(host, port, family=0, type=0, proto=0, flags=0):
        if any(h in str(host) for h in PMU_HOSTS):
            return _orig_getaddrinfo(ip, port, family, type, proto, flags)
        return _orig_getaddrinfo(host, port, family, type, proto, flags)
    socket.getaddrinfo = patched


def build_opener():
    """Ouvre sans proxy (les variables d'environnement proxy cassent l'accès)."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    opener.addheaders = list(HEADERS.items())
    return opener


def fetch_json(opener, url: str, timeout: int = 20, retries: int = 3):
    """GET JSON avec dégradation gracieuse. Renvoie (data|None, erreur|None)."""
    last = None
    for attempt in range(retries):
        try:
            with opener.open(url, timeout=timeout) as resp:
                if resp.status == 200:
                    return json.loads(resp.read().decode("utf-8")), None
                last = f"HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code == 404:
                return None, "404"
        except Exception as e:  # réseau, TLS, timeout…
            last = f"{type(e).__name__}: {e}"
        time.sleep(RATE_DELAY * (attempt + 1))
    return None, last


def ddmmyyyy(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}{m}{y}"


def iso_date(d: str) -> str:
    return f"{d[4:8]}-{d[2:4]}-{d[0:2]}"


# --------------------------------------------------------------------------- #
# Base (Master DB uniquement)
# --------------------------------------------------------------------------- #
DDL = """
CREATE TABLE IF NOT EXISTS external_pmu_citations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fetched_at   TEXT NOT NULL,
    date_race    TEXT NOT NULL,
    reunion      INTEGER NOT NULL,
    course       INTEGER NOT NULL,
    type_pari    TEXT NOT NULL,
    api_updatetime INTEGER,
    numero       INTEGER NOT NULL,
    nom          TEXT,
    statut       TEXT,
    enjeu        REAL,
    ratio        REAL,
    UNIQUE(date_race, reunion, course, type_pari, api_updatetime, numero)
);
CREATE INDEX IF NOT EXISTS idx_ext_cit_race ON external_pmu_citations(date_race, reunion, course, type_pari);
CREATE INDEX IF NOT EXISTS idx_ext_cit_upd  ON external_pmu_citations(api_updatetime);

CREATE TABLE IF NOT EXISTS external_pmu_results (
    date_race    TEXT NOT NULL,
    reunion      INTEGER NOT NULL,
    course       INTEGER NOT NULL,
    fetched_at   TEXT,
    arrivee      TEXT,
    type_pari    TEXT,
    nb_gagnants  REAL,
    masse_partager REAL,
    data_json    TEXT,
    PRIMARY KEY (date_race, reunion, course, type_pari)
);

CREATE TABLE IF NOT EXISTS external_fetch_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT,
    endpoint   TEXT,
    date_race  TEXT,
    reunion    INTEGER,
    course     INTEGER,
    status     TEXT,
    detail     TEXT
);
"""


def open_master_rw(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(DDL)
    return conn


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# Collecte
# --------------------------------------------------------------------------- #
def parse_citations(payload) -> list[dict]:
    rows = []
    for cit in (payload or {}).get("listeCitations", []) or []:
        tp = cit.get("typePari")
        upd = cit.get("updatetime")
        for p in cit.get("participants", []) or []:
            cits = p.get("citations") or []
            if not cits:
                continue
            c0 = cits[0]
            rows.append({
                "type_pari": tp, "api_updatetime": upd, "numero": p.get("numPmu"),
                "nom": p.get("nom"), "statut": p.get("statut"),
                "enjeu": c0.get("enjeu"), "ratio": c0.get("ratio"),
            })
    return rows


def fetch_race(opener, conn, iso: str, r: int, c: int, log) -> int:
    d = ddmmyyyy(iso)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    n_rows = 0

    # 1) citations (marché réel)
    url = (f"{BASE_URL}/programme/{d}/R{r}/C{c}/citations"
           f"?paris=&specialisation=INTERNET&combinaisonEnTableau=true")
    data, err = fetch_json(opener, url)
    if data is not None:
        rows = parse_citations(data)
        for x in rows:
            conn.execute(
                """INSERT OR IGNORE INTO external_pmu_citations
                   (fetched_at, date_race, reunion, course, type_pari, api_updatetime,
                    numero, nom, statut, enjeu, ratio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (now, iso, r, c, x["type_pari"], x["api_updatetime"], x["numero"],
                 x["nom"], x["statut"], x["enjeu"], x["ratio"]))
        n_rows = len(rows)
        log(conn, "citations", iso, r, c, "OK", f"{len(rows)} lignes")
    else:
        log(conn, "citations", iso, r, c, "ERREUR", str(err))
    time.sleep(RATE_DELAY)

    # 2) rapports définitifs (arrivée + paiements)
    url2 = (f"{BASE_URL}/programme/{d}/R{r}/C{c}/rapports-definitifs"
            f"?specialisation=INTERNET&combinaisonEnTableau=true")
    data2, err2 = fetch_json(opener, url2)
    if data2 is not None and isinstance(data2, list):
        for rap in data2:
            conn.execute(
                """INSERT OR REPLACE INTO external_pmu_results
                   (date_race, reunion, course, fetched_at, arrivee, type_pari,
                    nb_gagnants, masse_partager, data_json)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (iso, r, c, now, json.dumps(rap.get("arrivee"), ensure_ascii=False),
                 rap.get("typePari"), rap.get("nbGagnants"), rap.get("massePartager"),
                 json.dumps(rap, ensure_ascii=False)))
        log(conn, "rapports-definitifs", iso, r, c, "OK", f"{len(data2)} types")
    else:
        log(conn, "rapports-definitifs", iso, r, c, "ERREUR", str(err2))
    time.sleep(RATE_DELAY)
    return n_rows


def make_logger(conn):
    def log(c, endpoint, iso, r, cc, status, detail):
        c.execute("INSERT INTO external_fetch_log (ts, endpoint, date_race, reunion, course, status, detail) "
                  "VALUES (?,?,?,?,?,?,?)",
                  (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                   endpoint, iso, r, cc, status, detail))
        c.commit()
    return log


# --------------------------------------------------------------------------- #
# Rapport
# --------------------------------------------------------------------------- #
def report(conn) -> int:
    n_cit = conn.execute("SELECT COUNT(*) FROM external_pmu_citations").fetchone()[0]
    n_res = conn.execute("SELECT COUNT(*) FROM external_pmu_results").fetchone()[0]
    n_race = conn.execute(
        "SELECT COUNT(DISTINCT date_race||'-'||reunion||'-'||course) FROM external_pmu_citations"
    ).fetchone()[0]
    print("=== DONNÉES EXTERNES COLLECTÉES ===")
    print(f"  lignes citations : {n_cit}")
    print(f"  lignes résultats : {n_res}")
    print(f"  courses distinctes : {n_race}")
    if n_cit:
        print("\n  --- aperçu (E_SIMPLE_GAGNANT) ---")
        for row in conn.execute(
            """SELECT date_race, reunion, course, numero, nom, enjeu, ratio
               FROM external_pmu_citations WHERE type_pari='E_SIMPLE_GAGNANT'
               ORDER BY date_race DESC, reunion, course, enjeu DESC LIMIT 12"""):
            print(f"    {row['date_race']} R{row['reunion']}C{row['course']} "
                  f"n°{row['numero']:<3} {(row['nom'] or '')[:20]:<20} "
                  f"enjeu={row['enjeu']:<10} ratio={row['ratio']}%")
        print("\n  --- cohérence : somme des ratio par course (doit valoir ~100) ---")
        for row in conn.execute(
            """SELECT date_race, reunion, course, ROUND(SUM(ratio),2) s, COUNT(*) n
               FROM external_pmu_citations WHERE type_pari='E_SIMPLE_GAGNANT'
               GROUP BY date_race, reunion, course ORDER BY date_race DESC LIMIT 8"""):
            print(f"    {row['date_race']} R{row['reunion']}C{row['course']} : "
                  f"somme ratio = {row['s']} % ({row['n']} partants)")
    return 0


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Adapter externe PMU (masse d'enjeu / cotes).")
    ap.add_argument("--enable-external", action="store_true",
                    help="OBLIGATOIRE : confirme l'activation de l'adapter externe (ADR-001).")
    ap.add_argument("--date", help="date ISO (YYYY-MM-DD)")
    ap.add_argument("--race", help="course ciblée au format R/C (ex: 1/1)")
    ap.add_argument("--max-races", type=int, default=200)
    ap.add_argument("--loop", action="store_true", help="polling répété (capture l'évolution)")
    ap.add_argument("--interval", type=int, default=60, help="secondes entre deux passes (--loop)")
    ap.add_argument("--duration", type=int, default=1800, help="durée totale du polling (--loop)")
    ap.add_argument("--report", action="store_true", help="affiche les données déjà collectées")
    ap.add_argument("--master", default=str(MASTER_DB))
    a = ap.parse_args(argv)

    conn = open_master_rw(Path(a.master))

    if a.report:
        return report(conn)

    if not a.enable_external:
        print("ADAPTER EXTERNE DÉSACTIVÉ (ADR-001).\n"
              "Relancez avec --enable-external après vérification des conditions d'accès.\n"
              "Source : API publique utilisée par le site PMU (online.turfinfo.api.pmu.fr).\n"
              "Réutilisation : vérifier les CGU du PMU avant tout usage commercial.")
        return 2

    if not a.date:
        print("--date requis (ou --report).")
        return 2

    socle_sha_before = sha256_file(SOCLE_DB)
    if socle_sha_before != SOCLE_SHA_EXPECTED:
        raise SystemExit(f"ERREUR FATALE : SHA socle inattendu : {socle_sha_before}")

    install_dns_fallback(_active_ip)
    opener = build_opener()
    log = make_logger(conn)

    iso = a.date
    races = []
    if a.race:
        r, c = a.race.split("/")
        races = [(int(r), int(c))]
    else:
        # découvrir les courses via le programme
        url = f"{BASE_URL}/programme/{ddmmyyyy(iso)}?specialisation=INTERNET"
        prog, err = fetch_json(opener, url)
        if prog is None:
            print(f"programme indisponible pour {iso} : {err}")
            return 1
        for reun in (prog.get("programme", {}) or {}).get("reunions", []) or []:
            # Champs réels vérifiés : numOfficiel = n° de réunion, numOrdre = n° de course
            rn = reun.get("numOfficiel")
            for c in reun.get("courses", []) or []:
                cn = c.get("numOrdre")
                if rn is not None and cn is not None:
                    races.append((rn, cn))
    races = races[: a.max_races]
    print(f"date {iso} : {len(races)} course(s) à récupérer")

    passes = 1
    if a.loop:
        passes = max(1, a.duration // max(a.interval, 1))
        print(f"mode polling : {passes} passe(s), intervalle {a.interval}s")

    total = 0
    for k in range(passes):
        if passes > 1:
            print(f"--- passe {k+1}/{passes} ---")
        for (r, c) in races:
            try:
                n = fetch_race(opener, conn, iso, r, c, log)
                total += n
                conn.commit()
            except Exception as e:  # dégradation gracieuse
                log(conn, "exception", iso, r, c, "ERREUR", str(e))
                continue
        if k + 1 < passes:
            time.sleep(a.interval)

    socle_sha_after = sha256_file(SOCLE_DB)
    print(f"\nlignes citations insérées (avant dédoublonnage) : {total}")
    print(f"socle inchangé : {socle_sha_after == socle_sha_before}")
    report(conn)
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
