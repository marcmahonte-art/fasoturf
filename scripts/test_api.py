#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test automatisé de bout en bout de l'API FasoTurf.

Le script :
  1. démarre le serveur `uvicorn` sur un port libre ;
  2. attend que `/api/health` réponde ;
  3. exerce **chaque** endpoint et vérifie le code HTTP + la forme de la réponse ;
  4. contrôle la non-régression du socle LONAB (SHA-256 inchangé) ;
  5. arrête le serveur et affiche un rapport.

Aucune dépendance externe : uniquement la bibliothèque standard.

Usage :
    python scripts/test_api.py
    python scripts/test_api.py --port 8077 --verbose
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

FASOTURF_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = FASOTURF_DIR.parent

#: Empreinte gelée du socle LONAB : elle ne doit jamais changer.
SOCLE_PATH = PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"
SOCLE_SHA256 = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


class Report:
    """Collecte des résultats du test."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.rows: list[tuple[str, str, str]] = []

    def add(self, name: str, status: str, detail: str = "") -> None:
        self.rows.append((name, status, detail))
        icon = {PASS: "  OK ", FAIL: "FAIL ", SKIP: "SKIP "}[status]
        line = f"[{icon}] {name}"
        if detail:
            line += f" — {detail}"
        print(line)

    @property
    def failures(self) -> int:
        return sum(1 for _, status, _ in self.rows if status == FAIL)

    def summary(self) -> str:
        passed = sum(1 for _, s, _ in self.rows if s == PASS)
        skipped = sum(1 for _, s, _ in self.rows if s == SKIP)
        return (
            f"{len(self.rows)} vérifications — {passed} réussies, "
            f"{self.failures} échouées, {skipped} ignorées"
        )


# --------------------------------------------------------------------------
# Utilitaires HTTP
# --------------------------------------------------------------------------


def _get(base: str, path: str, timeout: float = 180.0) -> tuple[int, object]:
    """GET JSON. Retourne (code HTTP, corps décodé ou message d'erreur)."""
    url = f"{base}{path}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                return response.status, json.loads(raw)
            except json.JSONDecodeError:
                return response.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw
    except (urllib.error.URLError, socket.timeout, OSError) as exc:
        return 0, f"connexion impossible : {exc}"


def _post(base: str, path: str, timeout: float = 60.0) -> tuple[int, object]:
    """POST JSON sans corps."""
    request = urllib.request.Request(f"{base}{path}", method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError) as exc:
        return 0, f"connexion impossible : {exc}"


def _free_port(preferred: int) -> int:
    """Retourne `preferred` s'il est libre, sinon un port attribué par l'OS."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(base: str, process: subprocess.Popen, deadline_s: float = 60.0) -> bool:
    """Attend que le serveur réponde, ou s'arrête si le processus meurt."""
    start = time.time()
    while time.time() - start < deadline_s:
        if process.poll() is not None:
            return False
        code, _ = _get(base, "/api/health", timeout=3.0)
        if code == 200:
            return True
        time.sleep(0.4)
    return False


# --------------------------------------------------------------------------
# Vérifications
# --------------------------------------------------------------------------


def check_health(base: str, report: Report) -> str | None:
    """Vérifie /api/health et retourne le chemin de la base détectée."""
    code, body = _get(base, "/api/health")
    if code != 200 or not isinstance(body, dict):
        report.add("GET /api/health", FAIL, f"code {code}")
        return None

    coverage = body.get("coverage") or {}
    report.add(
        "GET /api/health",
        PASS,
        f"base={body.get('database')} · {coverage.get('exploitableRaces')} courses exploitables",
    )

    if body.get("database_path"):
        report.add("auto-détection de la base", PASS, str(body["database_path"]))
    else:
        report.add("auto-détection de la base", FAIL, "chemin absent de la réponse")

    engine = body.get("engine") or {}
    report.add(
        "moteur de pronostics",
        PASS if engine.get("enabled") else SKIP,
        f"enabled={engine.get('enabled')}",
    )
    return str(body.get("database_path") or "")


def check_races(base: str, report: Report) -> dict | None:
    """Vérifie les endpoints de courses et retourne la première course."""
    code, races = _get(base, "/api/races?limit=5")
    if code != 200 or not isinstance(races, list):
        report.add("GET /api/races", FAIL, f"code {code}")
        return None

    if not races:
        report.add("GET /api/races", FAIL, "aucune course retournée")
        return None

    first = races[0]
    required = {
        "id", "date", "reunion", "course", "hippodrome", "title", "discipline",
        "distance", "starters", "time", "status", "hasResult", "favoriteOdds",
        "accent", "runners",
    }
    missing = required - set(first)
    if missing:
        report.add("GET /api/races", FAIL, f"champs manquants : {sorted(missing)}")
        return None

    with_runners = sum(1 for race in races if race.get("runners"))
    report.add(
        "GET /api/races",
        PASS if with_runners else FAIL,
        f"{len(races)} courses, {with_runners} avec partants, contrat historique respecté",
    )

    runner = first["runners"][0]
    runner_fields = {"number", "name", "age", "music", "jockey", "trainer", "odds",
                     "marketProb", "marketRank", "isWinner", "position"}
    missing = runner_fields - set(runner)
    report.add(
        "contrat partant (/api/races)",
        PASS if not missing else FAIL,
        f"champs manquants : {sorted(missing)}" if missing else f"{len(first['runners'])} partants",
    )
    return first


def check_races_extra(base: str, report: Report, race: dict) -> None:
    """Vérifie /api/races/today, /summary, /dates, /disciplines et le détail."""
    code, today = _get(base, "/api/races/today")
    report.add(
        "GET /api/races/today",
        PASS if code == 200 and isinstance(today, list) else FAIL,
        f"code {code}, {len(today) if isinstance(today, list) else '?'} courses",
    )

    code, summary = _get(base, "/api/races/summary?limit=5")
    ok = code == 200 and isinstance(summary, list) and (
        not summary or "meetingNumber" in summary[0]
    )
    report.add(
        "GET /api/races/summary",
        PASS if ok else FAIL,
        f"code {code}, {len(summary) if isinstance(summary, list) else '?'} entrées",
    )

    code, dates = _get(base, "/api/dates?limit=5")
    ok = code == 200 and isinstance(dates, list) and (
        not dates or {"date", "label", "count", "isToday"} <= set(dates[0])
    )
    report.add(
        "GET /api/dates",
        PASS if ok else FAIL,
        f"code {code}, {len(dates) if isinstance(dates, list) else '?'} dates",
    )

    code, disciplines = _get(base, "/api/disciplines")
    report.add(
        "GET /api/disciplines",
        PASS if code == 200 and isinstance(disciplines, list) else FAIL,
        f"code {code}, {len(disciplines) if isinstance(disciplines, list) else '?'} disciplines",
    )

    code, detail = _get(base, f"/api/races/{race['id']}")
    ok = code == 200 and isinstance(detail, dict) and detail.get("id") == race["id"]
    report.add(
        "GET /api/races/{id}",
        PASS if ok else FAIL,
        f"code {code}",
    )

    code, _ = _get(base, "/api/races/inexistant-000")
    report.add("GET /api/races/{id} inconnu → 404", PASS if code == 404 else FAIL, f"code {code}")


def check_entities(base: str, report: Report) -> None:
    """Vérifie chevaux, jockeys, entraîneurs et hippodromes."""
    code, horses = _get(base, "/api/horses?limit=3")
    if code == 200 and isinstance(horses, list) and horses:
        code2, detail = _get(base, f"/api/horses/{horses[0]['id']}")
        ok = code2 == 200 and isinstance(detail, dict) and "statistics" in detail
        report.add(
            "GET /api/horses + détail",
            PASS if ok else FAIL,
            f"{len(horses)} résultats, détail code {code2}",
        )
    else:
        report.add("GET /api/horses + détail", FAIL, f"code {code}")

    code, jockeys = _get(base, "/api/jockeys?limit=3")
    if code == 200 and isinstance(jockeys, list) and jockeys:
        code2, detail = _get(base, f"/api/jockeys/{jockeys[0]['id']}")
        ok = code2 == 200 and isinstance(detail, dict) and detail.get("person", {}).get("role") == "jockey"
        report.add(
            "GET /api/jockeys + détail",
            PASS if ok else FAIL,
            f"{len(jockeys)} résultats, détail code {code2}",
        )
    else:
        report.add("GET /api/jockeys + détail", FAIL, f"code {code}")

    code, trainers = _get(base, "/api/trainers?limit=3")
    report.add(
        "GET /api/trainers",
        PASS if code == 200 and isinstance(trainers, list) else FAIL,
        f"code {code}, {len(trainers) if isinstance(trainers, list) else '?'} résultats",
    )

    code, hippos = _get(base, "/api/hippodromes?limit=3")
    if code == 200 and isinstance(hippos, list) and hippos:
        code2, detail = _get(base, f"/api/hippodromes/{hippos[0]['id']}")
        ok = code2 == 200 and isinstance(detail, dict) and "statistics" in detail
        report.add(
            "GET /api/hippodromes + détail",
            PASS if ok else FAIL,
            f"{len(hippos)} résultats, détail code {code2}",
        )
    else:
        report.add("GET /api/hippodromes + détail", FAIL, f"code {code}")


def check_page_endpoints(base: str, report: Report) -> None:
    """
    Vérifie les endpoints consommés par les pages `/courses`, `/chevaux`,
    `/analyses` et `/pronostics`.

    Ces vérifications couvrent le contrat réellement utilisé par l'interface :
    filtres du programme, recherche d'entités et pronostics mis en avant.
    """
    # --- Programme complet vs programme analysable -------------------------
    code_all, all_races = _get(base, "/api/races/summary?limit=200")
    code_an, analysable = _get(base, "/api/races/summary?analysable=true&limit=200")

    ok = (
        code_all == 200
        and code_an == 200
        and isinstance(all_races, list)
        and isinstance(analysable, list)
        and bool(analysable)
        and len(analysable) <= len(all_races)
    )
    report.add(
        "GET /api/races/summary?analysable=true",
        PASS if ok else FAIL,
        f"{len(analysable) if isinstance(analysable, list) else '?'} analysables sur "
        f"{len(all_races) if isinstance(all_races, list) else '?'} exploitables (plafond de page)",
    )

    # --- Filtre par date : toutes les courses doivent porter la date demandée
    if isinstance(all_races, list) and all_races:
        target = str(all_races[0].get("date") or "")
        code_day, same_day = _get(base, f"/api/races/summary?date={target}&limit=200")
        ok_day = (
            code_day == 200
            and isinstance(same_day, list)
            and bool(same_day)
            and all(str(item.get("date")) == target for item in same_day)
        )
        report.add(
            "filtre date du programme",
            PASS if ok_day else FAIL,
            f"{target} → {len(same_day) if isinstance(same_day, list) else '?'} courses, "
            "aucune hors journée",
        )
    else:
        report.add("filtre date du programme", SKIP, "aucune course en base")

    # --- Filtre par discipline --------------------------------------------
    # Attention : `/api/disciplines` renvoie la valeur **brute** du socle
    # (« ATTELE »), alors que la liste des courses expose un libellé lisible
    # (« Trot Attelé »). On vérifie donc que le filtre discrimine bien : les
    # courses retournées partagent un libellé unique, et sont moins nombreuses
    # que le programme complet.
    code_disc, disciplines = _get(base, "/api/disciplines")
    if code_disc == 200 and isinstance(disciplines, list) and disciplines:
        discipline = disciplines[0]
        code_f, filtered = _get(
            base, f"/api/races/summary?discipline={urllib.parse.quote(discipline)}&limit=100"
        )
        labels = {
            str(item.get("discipline"))
            for item in (filtered if isinstance(filtered, list) else [])
        }
        ok_f = (
            code_f == 200
            and isinstance(filtered, list)
            and bool(filtered)
            and len(labels) == 1
            and len(filtered) < len(all_races)
        )
        report.add(
            "filtre discipline du programme",
            PASS if ok_f else FAIL,
            f"{discipline} → {len(filtered) if isinstance(filtered, list) else '?'} courses, "
            f"libellés distincts : {sorted(labels)}",
        )
    else:
        report.add("filtre discipline du programme", FAIL, f"code {code_disc}")

    # --- Recherche de chevaux (insensible aux accents et à la casse) --------
    code_h, horses = _get(base, "/api/horses?q=ganass&limit=5")
    ok_h = (
        code_h == 200
        and isinstance(horses, list)
        and bool(horses)
        and all("ganass" in str(item.get("name", "")).lower() for item in horses)
    )
    report.add(
        "recherche de chevaux (q=)",
        PASS if ok_h else FAIL,
        f"{len(horses) if isinstance(horses, list) else '?'} résultats pour « ganass »",
    )

    # --- Recherche de personnes --------------------------------------------
    code_j, jockeys = _get(base, "/api/jockeys?q=raffin&limit=5")
    ok_j = (
        code_j == 200
        and isinstance(jockeys, list)
        and bool(jockeys)
        and all(str(item.get("role")) == "jockey" for item in jockeys)
    )
    report.add(
        "recherche de jockeys (q=)",
        PASS if ok_j else FAIL,
        f"{len(jockeys) if isinstance(jockeys, list) else '?'} résultats pour « raffin »",
    )

    # --- Détail d'un entraîneur --------------------------------------------
    code_t, trainers = _get(base, "/api/trainers?limit=3")
    if code_t == 200 and isinstance(trainers, list) and trainers:
        code_td, detail = _get(base, f"/api/trainers/{trainers[0]['id']}")
        ok_td = (
            code_td == 200
            and isinstance(detail, dict)
            and str(detail.get("person", {}).get("role")) == "trainer"
            and "statistics" in detail
        )
        report.add(
            "GET /api/trainers/{id}",
            PASS if ok_td else FAIL,
            f"code {code_td}, statistiques présentes={isinstance(detail, dict) and 'statistics' in detail}",
        )
    else:
        report.add("GET /api/trainers/{id}", FAIL, f"code {code_t}")

    # --- Pronostics mis en avant (page /pronostics) -------------------------
    code_fp, featured = _get(base, "/api/predictions/featured?limit=5", timeout=240.0)
    required = {"raceId", "context", "predictions", "unavailableReason"}
    ok_fp = code_fp == 200 and isinstance(featured, dict) and required <= set(featured)
    if ok_fp:
        items = featured.get("predictions") or []
        # Honnêteté : soit des pronostics accompagnés d'un contexte, soit une
        # raison d'indisponibilité — jamais l'un sans l'autre.
        coherent = (bool(items) and bool(featured.get("context"))) or (
            not items and bool(featured.get("unavailableReason"))
        )
        ok_fp = coherent
        detail = (
            f"{len(items)} pronostics · contexte présent={bool(featured.get('context'))}"
            if items
            else f"indisponible : {str(featured.get('unavailableReason'))[:60]}"
        )
    else:
        detail = f"code {code_fp}"
    report.add("GET /api/predictions/featured", PASS if ok_fp else FAIL, detail)


def check_spa(base: str, report: Report) -> None:
    """
    Vérifie que le serveur expose l'interface compilée sur le même port.

    Deux invariants importants :
      * une route d'interface (`/courses`, `/chevaux/...`) doit renvoyer
        `index.html` — sinon un rechargement de page casserait la navigation ;
      * un chemin `/api/...` inconnu doit rester un **404 d'API**, et ne jamais
        être avalé par la route attrape-tout du frontend.
    """
    code, body = _get(base, "/")
    if code == 200 and isinstance(body, str) and "<div id=\"root\">" in body:
        report.add("interface servie sur /", PASS, "index.html de l'application")
    else:
        report.add(
            "interface servie sur /",
            SKIP,
            "interface non compilée (lancer `npm run build` pour la servir)",
        )
        return

    # Toutes les routes de l'interface doivent retomber sur index.html.
    routes_ok = True
    for route in ("/dashboard", "/courses", "/pronostics", "/chevaux", "/jockeys"):
        code_route, page = _get(base, route)
        if code_route != 200 or not isinstance(page, str) or "<div id=\"root\">" not in page:
            routes_ok = False
            report.add(f"route d'interface {route}", FAIL, f"code {code_route}")
            break
    if routes_ok:
        report.add("routes d'interface rechargées", PASS, "/dashboard, /courses, /pronostics, /chevaux, /jockeys")

    # Les actifs compilés doivent être joignables.
    assets = re.findall(r'/assets/[A-Za-z0-9._-]+', body)
    if assets:
        code_asset, _ = _get(base, assets[0])
        report.add(
            "actifs compilés servis",
            PASS if code_asset == 200 else FAIL,
            f"{len(assets)} référence(s), {assets[0]} → {code_asset}",
        )
    else:
        report.add("actifs compilés servis", FAIL, "aucune référence /assets/ dans index.html")

    # Un chemin d'API inconnu ne doit pas devenir une page HTML.
    code_404, api_body = _get(base, "/api/chemin-inexistant")
    report.add(
        "API inconnue → 404 (non avalée par le SPA)",
        PASS if code_404 == 404 and not (isinstance(api_body, str) and "<div id=\"root\">" in api_body) else FAIL,
        f"code {code_404}",
    )


def check_statistics(base: str, report: Report) -> None:
    """Vérifie les statistiques et la présence de la méthode de calcul."""
    code, stats = _get(base, "/api/statistics")
    if code != 200 or not isinstance(stats, dict):
        report.add("GET /api/statistics", FAIL, f"code {code}")
        return

    favourite = stats.get("favouriteWinRate") or {}
    has_method = bool(favourite.get("method")) and favourite.get("denominator") is not None
    report.add(
        "GET /api/statistics",
        PASS if has_method else FAIL,
        f"favori={favourite.get('value')} ({favourite.get('numerator')}/"
        f"{favourite.get('denominator')}) · méthode publiée={has_method}",
    )

    code, coverage = _get(base, "/api/statistics/coverage")
    report.add(
        "GET /api/statistics/coverage",
        PASS if code == 200 and isinstance(coverage, dict) else FAIL,
        f"code {code}",
    )


def check_predictions(base: str, report: Report, race: dict) -> None:
    """Vérifie le pont vers le moteur Hippo Engine."""
    code, status = _get(base, "/api/predictions/status", timeout=30)
    if code != 200 or not isinstance(status, dict):
        report.add("GET /api/predictions/status", FAIL, f"code {code}")
        return

    if not status.get("available"):
        report.add("GET /api/predictions/status", SKIP, str(status.get("reason")))
        return
    report.add("GET /api/predictions/status", PASS, "moteur disponible")

    # On interroge la course de référence connue du moteur (document 927).
    code, prediction = _get(base, "/api/predictions/document/927?limit=5")
    if code != 200 or not isinstance(prediction, dict):
        report.add("GET /api/predictions/document/927", FAIL, f"code {code}")
        return

    if prediction.get("available") is False:
        report.add("GET /api/predictions/document/927", FAIL, str(prediction.get("reason")))
        return

    runners = prediction.get("runners") or []
    ok = bool(runners) and all(
        {"horseName", "horseNumber", "winProbability", "rank", "modelVersion"} <= set(item)
        for item in runners
    )
    report.add(
        "GET /api/predictions/document/927",
        PASS if ok else FAIL,
        f"{len(runners)} partants · modèle {prediction.get('modelVersion')} · "
        f"confiance {prediction.get('confidence')}",
    )

    if ok:
        top = runners[0]
        report.add(
            "probabilités issues du moteur",
            PASS,
            f"n°{top['horseNumber']} {top['horseName']} — win {top['winProbability']:.3f}, "
            f"valueEdge {top.get('valueEdge')}",
        )

    code, _ = _get(base, "/api/predictions/race/inexistant-000")
    report.add("GET /api/predictions/race/{id} inconnu → 404", PASS if code == 404 else FAIL, f"code {code}")

    code, body = _post(base, "/api/predictions/cache/invalidate")
    report.add(
        "POST /api/predictions/cache/invalidate",
        PASS if code == 200 and isinstance(body, dict) else FAIL,
        f"code {code}",
    )


def check_dashboard(base: str, report: Report) -> dict | None:
    """Vérifie l'endpoint agrégé du Dashboard."""
    code, body = _get(base, "/api/dashboard")
    if code != 200 or not isinstance(body, dict):
        report.add("GET /api/dashboard", FAIL, f"code {code}")
        return None

    required = {
        "targetDate", "subscription", "nextRace", "followedRaces", "topPredictions",
        "predictionUnavailableReason", "performanceUnavailableReason", "coverage",
        "notifications", "dataStatus", "isLive",
    }
    missing = required - set(body)
    if missing:
        report.add("GET /api/dashboard", FAIL, f"champs manquants : {sorted(missing)}")
        return body

    report.add(
        "GET /api/dashboard",
        PASS,
        f"journée={body['targetDate']} · {len(body['followedRaces'])} courses à suivre · "
        f"{len(body['topPredictions'])} pronostics",
    )

    # Honnêteté : tout bloc non configuré doit être déclaré comme tel.
    subscription = body.get("subscription") or {}
    report.add(
        "abonnement déclaré non configuré",
        PASS if subscription.get("configured") is False else FAIL,
        f"plan={subscription.get('plan')}, configured={subscription.get('configured')}",
    )

    notifications = body.get("notifications") or {}
    report.add(
        "notifications déclarées non configurées",
        PASS if notifications.get("configured") is False else FAIL,
        f"configured={notifications.get('configured')}",
    )

    report.add(
        "performances personnelles déclarées indisponibles",
        PASS if body.get("performanceUnavailableReason") else FAIL,
        str(body.get("performanceUnavailableReason"))[:70],
    )

    if body["topPredictions"] and not body.get("predictionContext"):
        report.add("contexte du pronostic", FAIL, "pronostics présents sans contexte")
    elif body["topPredictions"]:
        report.add("contexte du pronostic", PASS, str(body["predictionContext"])[:80])
    else:
        report.add(
            "contexte du pronostic",
            SKIP,
            str(body.get("predictionUnavailableReason"))[:80],
        )
    return body


def check_socle(report: Report) -> None:
    """Contrôle que le socle LONAB n'a pas été modifié."""
    if not SOCLE_PATH.is_file():
        report.add("socle LONAB (SHA-256)", SKIP, "fichier absent")
        return

    digest = hashlib.sha256()
    with SOCLE_PATH.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest()

    if actual == SOCLE_SHA256:
        report.add("socle LONAB (SHA-256)", PASS, "empreinte gelée inchangée")
    else:
        report.add(
            "socle LONAB (SHA-256)",
            FAIL,
            f"empreinte modifiée ! attendu {SOCLE_SHA256[:12]}…, obtenu {actual[:12]}…",
        )


# --------------------------------------------------------------------------
# Point d'entrée
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Test de bout en bout de l'API FasoTurf.")
    parser.add_argument("--port", type=int, default=8077, help="port d'écoute du serveur de test")
    parser.add_argument("--verbose", action="store_true", help="afficher la sortie du serveur")
    args = parser.parse_args(argv)

    report = Report(verbose=args.verbose)
    port = _free_port(args.port)
    base = f"http://127.0.0.1:{port}"

    print("=" * 74)
    print("  TEST DE BOUT EN BOUT — API FasoTurf")
    print("=" * 74)

    check_socle(report)
    print()

    stdout = None if args.verbose else subprocess.DEVNULL
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1",
         "--port", str(port), "--log-level", "warning"],
        cwd=str(FASOTURF_DIR),
        stdout=stdout,
        stderr=stdout,
    )

    try:
        if not _wait_for_server(base, process):
            report.add("démarrage du serveur", FAIL, f"aucune réponse sur {base}")
            return 1
        report.add("démarrage du serveur", PASS, base)
        print()

        check_health(base, report)
        print()

        check_spa(base, report)
        print()

        race = check_races(base, report)
        if race is not None:
            check_races_extra(base, report, race)
        print()

        check_entities(base, report)
        print()

        check_page_endpoints(base, report)
        print()

        check_statistics(base, report)
        print()

        check_predictions(base, report, race or {})
        print()

        check_dashboard(base, report)
        print()

        # Le socle est revérifié après les appels : l'API ne doit rien écrire.
        check_socle(report)
    finally:
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()

    print("=" * 74)
    print(f"  {report.summary()}")
    print("=" * 74)
    return 1 if report.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
