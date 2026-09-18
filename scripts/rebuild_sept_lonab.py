#!/usr/bin/env python3
"""
REBUILD SEPT 2026 (09 -> 16) — Programme officiel + Arrivées en direct + marquage LONAB
======================================================================================

Corrige 3 défauts constatés après le run de `scrape_sept_9_to_16.py` :

  D1. `rapports-definitifs` renvoie une **liste**, pas un dict -> `has_result` était
      toujours False -> `master_race.result_status` restait 'SCHEDULED' et les
      arrivées n'étaient jamais consolidées.
  D2. Le run avait sauté le 2026-09-16 (garde `existing >= 5`) et la base ne
      contenait que 8 lignes *fabriquées* par `populate_today_programme.py`
      (source_document_id 99000+, uuid4 aléatoires, `random`). Elles sont purgées.
  D3. L'export écrivait dans `fasoturf/public/realRaces.json` alors que le front
      importe `fasoturf/src/data/realRaces.json` -> le front voyait des données figées.

Ajoute aussi le **marquage LONAB** demandé :
  La course LONAB du jour est *la* course qui porte le QUINTE+ / QUARTE+ / TIERCÉ
  (vérifié 1:1 contre le journal officiel `JH_PMUB_DU_DD-MM-YYYY.pdf`, qui titre
  « "QUARTE" DU <jour> ... »). Elle est marquée `is_lonab=1` + `lonab_bet`.

GARANTIES
  - Le socle gelé `data/processed/pmu_lonab.db` (SHA d71f6a01...) n'est JAMAIS touché.
  - Écriture uniquement dans la base dérivée `data/master/pmu_master.db`.
  - Idempotent : upsert par `race_id` (uuid5 déterministe).

Usage:
    python scripts/rebuild_sept_lonab.py
"""

from __future__ import annotations

import json
import math
import re
import sqlite3
import sys
import time
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT / "pmu-lonab-scraper"))

from app.enrichment.pmu_client import PMUApiClient  # noqa: E402

MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
SOCLE_DB = ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"
SOCLE_SHA_EXPECTED = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"
REAL_RACES_JSON = ROOT / "fasoturf" / "src" / "data" / "realRaces.json"

START_DATE = date(2026, 9, 9)
END_DATE = date(2026, 9, 16)

# Paris qui désignent la course « nationale » du jour (celle publiée par la LONAB)
#
# ATTENTION au piège de nommage de l'API PMU :
#   - l'endpoint `programme`  expose  QUINTPLUS  / QUARTPLUS   (sans underscore)
#   - l'endpoint `rapports`   expose  QUINTE_PLUS / QUARTE_PLUS (avec underscore)
# On normalise donc en retirant « E_ » et « _ » avant toute comparaison.
LONAB_BET_TYPES = ("QUINTPLUS", "QUARTPLUS", "TIERCE")
FABRICATED_DOC_ID_MIN = 99000

ACCENTS = ["green", "gold", "red"]


def log(msg: str) -> None:
    print(msg, flush=True)


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
def make_client() -> PMUApiClient:
    cl = PMUApiClient(timeout=25, delay=0.15)
    # Le proxy de l'environnement casse l'accès à online.turfinfo.api.pmu.fr
    cl.session.trust_env = False
    cl.session.proxies = {}
    return cl


# --------------------------------------------------------------------------- #
# Helpers d'identité
# --------------------------------------------------------------------------- #
def norm_name(name: str | None) -> str:
    if not name:
        return ""
    return re.sub(r"[^A-Z\s]", "", name.upper()).strip()


def name_key(name: str) -> str:
    return re.sub(r"\s+", "", norm_name(name))


def race_id_for(date_str: str, r_num: int, c_num: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"pmu:{date_str}:R{r_num}:C{c_num}"))


def get_or_create_horse(conn, nom, sexe, age, pere, mere, robe, race_str, race_date):
    nk = name_key(nom)
    if not nk:
        return None
    row = conn.execute("SELECT horse_id FROM master_horse WHERE name_key = ?", (nk,)).fetchone()
    if row:
        conn.execute(
            """UPDATE master_horse SET
                   last_seen_date = MAX(COALESCE(last_seen_date,''), ?),
                   n_starts = n_starts + 1,
                   pedigree_pere = COALESCE(pedigree_pere, ?),
                   pedigree_mere = COALESCE(pedigree_mere, ?),
                   robe = COALESCE(robe, ?),
                   race = COALESCE(race, ?)
               WHERE horse_id = ?""",
            (race_date or "", pere, mere, robe, race_str, row[0]),
        )
        return row[0]

    hid = str(uuid.uuid4())
    sex_byr = f"{sexe or '?'}_{age or '?'}" if (sexe or age) else None
    conn.execute(
        """INSERT INTO master_horse (
               horse_id, name_normalized, name_key,
               resolution_method, resolution_confidence, homonym_risk,
               n_sex_birthyear_variants, sex_birthyear_variants,
               n_starts, first_seen_date, last_seen_date,
               pedigree_pere, pedigree_mere, robe, race
           ) VALUES (?, ?, ?, 'api_pmu', 1.0, 'none', ?, ?, 1, ?, ?, ?, ?, ?, ?)""",
        (hid, norm_name(nom), nk, 1 if sex_byr else 0, sex_byr,
         race_date, race_date, pere, mere, robe, race_str),
    )
    return hid


def get_or_create_person(conn, nom, role):
    if not nom:
        return None
    nk = name_key(nom)
    if not nk:
        return None
    row = conn.execute(
        "SELECT person_id FROM master_person WHERE name_key = ? AND role = ?", (nk, role)
    ).fetchone()
    if row:
        conn.execute("UPDATE master_person SET n_appearances = n_appearances + 1 WHERE person_id = ?", (row[0],))
        return row[0]
    pid = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO master_person (
               person_id, name_normalized, name_key, role,
               resolution_method, resolution_confidence, n_appearances
           ) VALUES (?, ?, ?, ?, 'api_pmu', 1.0, 1)""",
        (pid, norm_name(nom), nk, role),
    )
    return pid


def get_or_create_hippodrome(conn, label):
    if not label:
        return None
    row = conn.execute("SELECT hippodrome_id FROM master_hippodrome WHERE label_canonical = ?", (label,)).fetchone()
    if row:
        conn.execute("UPDATE master_hippodrome SET n_courses = n_courses + 1 WHERE hippodrome_id = ?", (row[0],))
        return row[0]
    hid = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO master_hippodrome (
               hippodrome_id, label_canonical, label_variants,
               country, is_valid, quality_flag, n_courses
           ) VALUES (?, ?, ?, 'FR', 1, 'ok', 1)""",
        (hid, label, label),
    )
    return hid


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #
def unwrap(val):
    """Les champs PMU sont tantôt scalaires, tantôt {'nom': ...}."""
    if isinstance(val, dict):
        return val.get("nom") or val.get("libelleCourt") or val.get("libelle") or ""
    return val or ""


def extract_cote(p):
    """Cote décimale du partant.

    Pour une course DÉJÀ COURUE, `participants` n'expose plus `coteDirect`
    (qui n'est rempli qu'en direct). Le dernier rapport connu est alors dans
    `dernierRapportDirect` ({typePari, rapport, ...}). Sans cette branche,
    toutes les cotes retombaient sur le fallback 15.0 — ce qui rendait les
    features de marché (m_prob_norm, m_rank, favori) totalement fausses.
    """
    drd = p.get("dernierRapportDirect")
    if isinstance(drd, dict) and drd.get("typePari") == "SIMPLE_GAGNANT":
        r = drd.get("rapport")
        if isinstance(r, (int, float)) and r > 0:
            return float(r)

    cd = p.get("coteDirect")
    if isinstance(cd, dict):
        c = cd.get("coteDirect")
        if isinstance(c, (int, float)) and c > 0:
            return float(c)

    c = p.get("rapport")
    if isinstance(c, (int, float)) and c > 0:
        return float(c)
    return None


def canon_bet(tp: str | None) -> str:
    """Normalise un typePari : 'E_QUINTE_PLUS' -> 'QUINTPLUS'."""
    return (tp or "").replace("E_", "").replace("_", "")


def bet_types(course) -> set[str]:
    return {canon_bet(x.get("typePari")) for x in (course.get("paris") or [])}


def lonab_label(types: set[str]) -> str | None:
    has_q5 = "QUINTPLUS" in types
    has_q4 = "QUARTPLUS" in types
    has_t3 = "TIERCE" in types
    if has_q5 and has_q4:
        return "Quinté+ / Quarté+ / Tiercé"
    if has_q5:
        return "Quinté+ / Tiercé"
    if has_q4 and has_t3:
        return "Quarté+ / Tiercé"
    if has_q4:
        return "Quarté+"
    return None


def parse_arrivee(rapports):
    """Retourne (arrivee_str, dividends) depuis la liste rapports-definitifs."""
    if not isinstance(rapports, list):
        return None, {}
    div = {}
    for e in rapports:
        tp = canon_bet(e.get("typePari"))
        rr = e.get("rapports") or []
        if rr:
            combos = [x.get("combinaison") for x in rr if x.get("combinaison")]
            if combos:
                div[tp] = {
                    "combinaison": combos[0],
                    "dividendePourUnEuro": rr[0].get("dividendePourUnEuro"),
                    "nombreGagnants": rr[0].get("nombreGagnants"),
                }
    for key in ("QUINTPLUS", "QUARTPLUS", "TIERCE"):
        if key in div:
            return div[key]["combinaison"], div
    return None, div


# --------------------------------------------------------------------------- #
# Features de marché (identiques à scrape_sept_9_to_16.py)
# --------------------------------------------------------------------------- #
def compute_market_features(participants, n_runners):
    """Features de marché, **dans l'ordre de `participants`**.

    BUG CORRIGÉ : la version d'origine triait la liste retournée par probabilité
    décroissante puis l'appelant l'indexait positionnellement contre la liste
    `participants` NON triée. Résultat : cotes et rangs étaient attribués aux
    mauvais chevaux. Le tri n'est désormais utilisé que pour calculer m_rank /
    m_is_fav ; la liste renvoyée reste alignée sur `participants`.
    """
    cotes = [extract_cote(p) for p in participants]
    valid = [c for c in cotes if c]
    total_implied = sum(1.0 / c for c in valid) if valid else 1.0
    median_cote = sorted(valid)[len(valid) // 2] if valid else 10.0

    feats = []
    for p, cote in zip(participants, cotes):
        cote_eff = cote if cote else 15.0          # valeur de calcul
        implied = 1.0 / cote_eff
        musique = p.get("musique") or ""
        pos = [int(x) for x in re.findall(r"(\d)", musique[:20])] if musique else []
        gains = (p.get("gainsParticipant") or {}).get("gainsCarriere", 0) or 0
        if gains > 1000:
            gains = gains // 100
        sexe = (p.get("sexe") or "").upper()
        feats.append({
            "cote": cote,                          # cote réelle (None si inconnue)
            "m_implied": round(implied, 6),
            "m_prob_norm": round(implied / total_implied if total_implied else 0.0, 6),
            "m_log_odds": round(math.log(cote_eff), 4),
            "m_rel_median": round(cote_eff / median_cote if median_cote else 1.0, 4),
            "f_musique_n": len(pos),
            "f_musique_avg": round(sum(pos) / len(pos), 2) if pos else 5.0,
            "f_musique_best": min(pos) if pos else 5.0,
            "f_musique_winrate": round(sum(1 for x in pos if x == 1) / max(len(pos), 1), 4),
            "f_musique_top3rate": round(sum(1 for x in pos if x <= 3) / max(len(pos), 1), 4),
            "f_gains_log": round(math.log1p(gains), 4),
            "f_age": p.get("age", 4) or 4,
            "f_sex": 1 if sexe in ("M", "H") else 0,
            "f_field_size": n_runners,
            "m_rank": 0,
            "m_is_fav": 0,
        })

    # Le classement de marché se calcule par index, sans réordonner la liste.
    order = sorted(range(len(feats)), key=lambda i: -feats[i]["m_prob_norm"])
    for rank, i in enumerate(order, 1):
        feats[i]["m_rank"] = rank
        feats[i]["m_is_fav"] = 1 if rank == 1 else 0

    return feats


# --------------------------------------------------------------------------- #
# Schéma
# --------------------------------------------------------------------------- #
def ensure_schema(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info('master_race')")}
    added = []
    for name, ddl in (
        ("is_lonab", "INTEGER DEFAULT 0"),
        ("lonab_bet", "TEXT"),
        ("arrivee_officielle", "TEXT"),
        ("reunion_num", "INTEGER"),
        ("course_num", "INTEGER"),
        ("heure_depart", "TEXT"),
        ("quinte_dividende", "REAL"),
        ("nb_gagnants_quinte", "REAL"),
        ("lonab_journal_bet", "TEXT"),
        ("lonab_journal_venue", "TEXT"),
        ("lonab_source_url", "TEXT"),
        # Météo réelle (objet `meteo` de la réunion) — le terrain, lui, n'est
        # exposé par AUCUN endpoint PMU : `api_meteo` du socle est vide et
        # l'audit Phase 1 l'a classé WEATHER_DATA_UNAVAILABLE.
        ("meteo_temperature", "INTEGER"),
        ("meteo_nebulosite", "TEXT"),
        ("meteo_vent_force", "INTEGER"),
        ("meteo_vent_direction", "TEXT"),
    ):
        if name not in cols:
            conn.execute(f"ALTER TABLE master_race ADD COLUMN {name} {ddl}")
            added.append(name)
    conn.commit()
    log(f"  schema master_race : +{added if added else 'aucune colonne manquante'}")


def purge_fabricated(conn):
    rows = conn.execute(
        "SELECT race_id, titre FROM master_race WHERE COALESCE(source_document_id,0) >= ?",
        (FABRICATED_DOC_ID_MIN,),
    ).fetchall()
    if not rows:
        log("  purge : aucune ligne fabriquée trouvée")
        return 0
    for rid, titre in rows:
        conn.execute("DELETE FROM market_runner_features WHERE race_id = ?", (rid,))
        conn.execute("DELETE FROM master_runner WHERE race_id = ?", (rid,))
        conn.execute("DELETE FROM master_race WHERE race_id = ?", (rid,))
        log(f"    - purge {titre[:52]}")
    conn.commit()
    log(f"  purge : {len(rows)} courses fabriquées supprimées")
    return len(rows)


# --------------------------------------------------------------------------- #
# Ingestion
# --------------------------------------------------------------------------- #
def ingest_date(conn, cl, target: date) -> dict:
    dstr = target.isoformat()
    stats = {"races": 0, "runners": 0, "arrivees": 0, "lonab": 0}

    prog = cl.get_programme(dstr)
    if not prog or "programme" not in prog:
        log(f"  {dstr} : AUCUN PROGRAMME")
        return stats

    reunions = prog["programme"].get("reunions", [])
    log(f"  {dstr} : {len(reunions)} réunions")

    for reu in reunions:
        r_num = reu.get("numOfficiel") or 0
        hippo_label = ((reu.get("hippodrome") or {}).get("libelleCourt") or "").upper()
        hippo_id = get_or_create_hippodrome(conn, hippo_label)
        meteo = reu.get("meteo") or {}

        for course in reu.get("courses", []):
            c_num = course.get("numOrdre") or 0
            nb_decl = course.get("nombreDeclaresPartants") or 0
            if nb_decl < 5:
                continue

            parts = cl.get_participants(dstr, r_num, c_num)
            if not parts or "participants" not in parts:
                continue
            participants = parts["participants"]
            n_runners = len(participants)
            if n_runners < 5:
                continue

            rapports = cl.get_rapports(dstr, r_num, c_num)
            arrivee, div = parse_arrivee(rapports)
            types = bet_types(course)
            lonab_bet = lonab_label(types)

            rid = race_id_for(dstr, r_num, c_num)
            libelle = course.get("libelle") or f"Course {c_num}"
            titre = f"{hippo_label} - {libelle}"
            if lonab_bet:
                # convention historique du projet : suffixe lisible dans le titre
                titre = f"{titre} ({lonab_bet.split(' / ')[0]} LONAB)"

            hd = course.get("heureDepart")
            heure = datetime.fromtimestamp(hd / 1000).strftime("%H:%M") if hd else None
            montant = course.get("montantPrix")
            if montant and montant > 10000:
                montant = montant // 100

            result_status = "OFFICIAL" if arrivee else "SCHEDULED"

            conn.execute(
                """INSERT INTO master_race (
                       race_id, source_document_id, date, date_is_sentinel,
                       hippodrome_id, hippodrome_label_raw, discipline, discipline_status,
                       distance_m, montant_euros, partants_declares, partants_effectifs,
                       type_course, titre, n_partants_source, n_runners_linked, result_status,
                       is_lonab, lonab_bet, arrivee_officielle,
                       reunion_num, course_num, heure_depart,
                       quinte_dividende, nb_gagnants_quinte,
                       meteo_temperature, meteo_nebulosite,
                       meteo_vent_force, meteo_vent_direction
                   ) VALUES (?, 0, ?, 0, ?, ?, ?, 'resolved', ?, ?, ?, ?, ?, ?, ?, ?, ?,
                             ?, ?, ?, ?, ?, ?, ?, ?,
                             ?, ?, ?, ?)
                   ON CONFLICT(race_id) DO UPDATE SET
                       hippodrome_id=excluded.hippodrome_id,
                       hippodrome_label_raw=excluded.hippodrome_label_raw,
                       discipline=excluded.discipline,
                       distance_m=excluded.distance_m,
                       montant_euros=excluded.montant_euros,
                       partants_declares=excluded.partants_declares,
                       partants_effectifs=excluded.partants_effectifs,
                       type_course=excluded.type_course,
                       titre=excluded.titre,
                       n_partants_source=excluded.n_partants_source,
                       n_runners_linked=excluded.n_runners_linked,
                       result_status=excluded.result_status,
                       is_lonab=excluded.is_lonab,
                       lonab_bet=excluded.lonab_bet,
                       arrivee_officielle=excluded.arrivee_officielle,
                       reunion_num=excluded.reunion_num,
                       course_num=excluded.course_num,
                       heure_depart=excluded.heure_depart,
                       quinte_dividende=excluded.quinte_dividende,
                       nb_gagnants_quinte=excluded.nb_gagnants_quinte,
                       meteo_temperature=excluded.meteo_temperature,
                       meteo_nebulosite=excluded.meteo_nebulosite,
                       meteo_vent_force=excluded.meteo_vent_force,
                       meteo_vent_direction=excluded.meteo_vent_direction""",
                (rid, dstr, hippo_id, hippo_label, course.get("discipline"), course.get("distance"),
                 montant, nb_decl, n_runners, course.get("specialite") or course.get("discipline"),
                 titre, n_runners, n_runners, result_status,
                 1 if lonab_bet else 0, lonab_bet, arrivee,
                 r_num, c_num, heure,
                 (div.get("QUINTPLUS") or {}).get("dividendePourUnEuro"),
                 (div.get("QUINTPLUS") or {}).get("nombreGagnants"),
                 meteo.get("temperature"), meteo.get("nebulositeLibelleCourt"),
                 meteo.get("forceVent"), meteo.get("directionVent")),
            )

            # --- arrivée de référence : top 5 du Quinté+, sinon Tiercé
            ordered = []
            if arrivee:
                ordered = [int(x) for x in re.findall(r"\d+", arrivee)]
            for p in participants:
                oa = p.get("ordreArrivee")
                if isinstance(oa, int) and oa > 0 and oa not in ordered:
                    ordered.append(oa)

            feats = compute_market_features(participants, n_runners)

            # purge des partants précédents de cette course (ré-ingestion propre)
            conn.execute("DELETE FROM market_runner_features WHERE race_id = ?", (rid,))
            conn.execute("DELETE FROM master_runner WHERE race_id = ?", (rid,))

            for idx, (p, feat) in enumerate(zip(participants, feats)):
                nom = (p.get("nom") or f"Partant {idx+1}").upper()
                numero = p.get("numPmu") or (idx + 1)
                oa = p.get("ordreArrivee")
                result_pos = oa if isinstance(oa, int) and oa > 0 else None
                if result_pos is None and numero in ordered:
                    result_pos = ordered.index(numero) + 1

                hid = get_or_create_horse(
                    conn, nom, p.get("sexe"), p.get("age"),
                    unwrap(p.get("nomPere")), unwrap(p.get("nomMere")),
                    unwrap(p.get("robe")), p.get("race"), dstr,
                )
                jid = get_or_create_person(conn, unwrap(p.get("driver") or p.get("jockey")), "jockey")
                tid = get_or_create_person(conn, unwrap(p.get("entraineur")), "trainer")
                oid = get_or_create_person(conn, unwrap(p.get("proprietaire")), "owner")

                gains_val = (p.get("gainsParticipant") or {}).get("gainsCarriere", 0) or 0
                if gains_val > 10000:
                    gains_val = gains_val // 100

                runner_id = str(uuid.uuid4())
                conn.execute(
                    """INSERT INTO master_runner (
                           runner_id, race_id, source_document_id, source_partant_id,
                           numero, horse_id, jockey_id, trainer_id, owner_id,
                           cote_decimale, gains_euros, performances_structured,
                           sexe_raw, age_raw, poids_raw, corde_raw,
                           result_position, result_status
                       ) VALUES (?, ?, 0, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (runner_id, rid, numero, hid, jid, tid, oid,
                     feat["cote"], gains_val, p.get("musique"),
                     p.get("sexe"), str(p.get("age")) if p.get("age") else None, None, None,
                     result_pos, "official" if result_pos else "pending"),
                )
                conn.execute(
                    """INSERT OR REPLACE INTO market_runner_features (
                           runner_id, race_id, date, split,
                           m_implied, m_prob_norm, m_rank, m_log_odds, m_rel_median, m_is_fav,
                           f_musique_n, f_musique_avg, f_musique_best,
                           f_musique_winrate, f_musique_top3rate,
                           f_gains_log, f_age, f_sex, f_field_size,
                           c_horse_starts, c_horse_winrate, c_horse_top3rate,
                           c_jockey_winrate, c_trainer_winrate, label_win, label_top3
                       ) VALUES (?, ?, ?, 'api_pmu', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                 0, 0.0, 0.0, 0.0, 0.0, ?, ?)""",
                    (runner_id, rid, dstr,
                     feat["m_implied"], feat["m_prob_norm"], feat["m_rank"], feat["m_log_odds"],
                     feat["m_rel_median"], feat["m_is_fav"],
                     feat["f_musique_n"], feat["f_musique_avg"], feat["f_musique_best"],
                     feat["f_musique_winrate"], feat["f_musique_top3rate"],
                     feat["f_gains_log"], feat["f_age"], feat["f_sex"], feat["f_field_size"],
                     1 if result_pos == 1 else 0,
                     1 if result_pos and result_pos <= 3 else 0),
                )
                stats["runners"] += 1

            stats["races"] += 1
            if arrivee:
                stats["arrivees"] += 1
            if lonab_bet:
                stats["lonab"] += 1
                log(f"      >> LONAB  R{r_num}C{c_num} {hippo_label} / {libelle[:38]}  arrivée={arrivee}")

    conn.commit()
    return stats


def backfill_meteo(conn, cl) -> int:
    """Récupère la météo réelle de chaque réunion (8 appels API au total)."""
    total = 0
    d = START_DATE
    while d <= END_DATE:
        dstr = d.isoformat()
        prog = cl.get_programme(dstr)
        if prog and "programme" in prog:
            for reu in prog["programme"].get("reunions", []):
                r_num = reu.get("numOfficiel") or 0
                m = reu.get("meteo") or {}
                if not m:
                    continue
                cur = conn.execute(
                    """UPDATE master_race
                       SET meteo_temperature = ?, meteo_nebulosite = ?,
                           meteo_vent_force = ?, meteo_vent_direction = ?
                       WHERE date = ? AND reunion_num = ?""",
                    (m.get("temperature"), m.get("nebulositeLibelleCourt"),
                     m.get("forceVent"), m.get("directionVent"), dstr, r_num),
                )
                total += cur.rowcount
        conn.commit()
        d += timedelta(days=1)
    return total


# --------------------------------------------------------------------------- #
# Export front
# --------------------------------------------------------------------------- #
_LOWER_WORDS = {"de", "du", "des", "la", "le", "les", "l", "d", "et", "en",
                "sur", "au", "aux", "a", "un", "une", "par", "sous"}


def _pretty_fr(txt: str) -> str:
    """'PRIX DE LA PLACE DE LA CONCORDE' -> 'Prix de la Place de la Concorde'."""
    if not txt:
        return txt
    words = []
    for i, w in enumerate(txt.split()):
        low = w.lower()
        if low in _LOWER_WORDS and i > 0:
            words.append(low)
        elif len(w) <= 2 and low not in ("ok",):
            words.append(w.upper() if w.isupper() and w.isalpha() else low)
        else:
            words.append(w.capitalize() if w.isupper() else w)
    return " ".join(words)


def _clean_title(titre: str) -> str:
    """Sépare l'hippodrome du libellé et remet le libellé en casse normale.

    Conserve le suffixe LONAB tel quel : '... (Quinté+ LONAB)'.
    """
    suffix = ""
    m = re.search(r"\s*\(([^)]*LONAB[^)]*)\)\s*$", titre or "")
    if m:
        suffix = f" ({m.group(1)})"
        titre = titre[: m.start()]
    if " - " in titre:
        left, right = titre.split(" - ", 1)
        if right.strip():
            titre = right.strip()
    return _pretty_fr(titre.strip()) + suffix


def export_json(conn):
    rows = conn.execute(
        """SELECT race_id, date, reunion_num, course_num, hippodrome_label_raw,
                  discipline, distance_m, titre, n_runners_linked, result_status,
                  is_lonab, lonab_bet, arrivee_officielle, heure_depart,
                  quinte_dividende, nb_gagnants_quinte,
                  lonab_journal_bet, lonab_journal_venue,
                  meteo_temperature, meteo_nebulosite,
                  meteo_vent_force, meteo_vent_direction
           FROM master_race
           WHERE date BETWEEN ? AND ? AND n_runners_linked >= 5
           ORDER BY date DESC, reunion_num ASC, course_num ASC""",
        (START_DATE.isoformat(), END_DATE.isoformat()),
    ).fetchall()

    out = []
    for idx, r in enumerate(rows):
        (rid, rdate, rn, cn, hippo_raw, disc_raw, dist, titre, n_runners,
         rstatus, is_lonab, lonab_bet, arrivee, heure, q5div, q5win,
         jbet, jvenue, mtemp, mneb, mvent, mdir) = r

        hippo = (hippo_raw or "Hippodrome").replace("-", " ").title()
        if "Vincennes" in hippo:
            hippo = "Paris-Vincennes"
        if "Longchamp" in hippo:
            hippo = "ParisLongchamp"

        d = (disc_raw or "").upper()
        if "ATTELE" in d or "TROT" in d:
            disc = "Trot Attelé"
        elif "MONTE" in d:
            disc = "Trot Monté"
        elif "PLAT" in d:
            disc = "Plat"
        elif any(k in d for k in ("OBSTACLE", "HAIES", "STEEPLE")):
            disc = "Haies / Obstacle"
        else:
            disc = (disc_raw or "Plat").title()

        dist_str = f"{dist:,} m".replace(",", " ") if dist else "—"

        runners_rows = conn.execute(
            """SELECT r.numero, r.age_raw, r.cote_decimale, r.performances_structured,
                      r.result_position, h.name_normalized,
                      pj.name_normalized, pt.name_normalized,
                      m.m_prob_norm, m.m_rank, m.label_win
               FROM master_runner r
               LEFT JOIN master_horse h ON h.horse_id = r.horse_id
               LEFT JOIN master_person pj ON pj.person_id = r.jockey_id
               LEFT JOIN master_person pt ON pt.person_id = r.trainer_id
               LEFT JOIN market_runner_features m ON m.runner_id = r.runner_id
               WHERE r.race_id = ?
               ORDER BY r.numero ASC""",
            (rid,),
        ).fetchall()

        runners = []
        min_cote = None
        for i, rr in enumerate(runners_rows):
            numero, age_raw, cote, musique, pos, hname, jname, tname, prob, mrank, win = rr
            cote = float(cote) if cote is not None else None
            if cote:
                min_cote = cote if min_cote is None else min(min_cote, cote)
            pct = round(prob * 100, 1) if prob is not None else (
                round((1.0 / cote) * 100, 1) if cote else None)
            runners.append({
                "number": numero or (i + 1),
                "name": (hname or f"Partant {numero or i+1}").title(),
                "age": int(age_raw) if age_raw and str(age_raw).isdigit() else 4,
                "music": (musique or "N/A").replace('"', "").replace("[", "").replace("]", ""),
                "jockey": (jname or "Non renseigné").title(),
                "trainer": (tname or "Non renseigné").title(),
                "odds": cote if cote is not None else 10.0,
                "marketProb": pct,
                "marketRank": mrank or (i + 1),
                "isWinner": bool(win == 1 or pos == 1),
                "position": pos,
            })

        runners.sort(key=lambda x: x["number"])

        # --- Arrivée : provenance explicite (ADR-001) --------------------------
        # 1) `arrivee_officielle` = socle LONAB, source de vérité, jamais écrasée.
        # 2) sinon on DÉRIVE l'ordre depuis `master_runner.result_position`, donnée
        #    déjà présente au socle : aucun appel externe, aucune écriture en base.
        arrivee_source = None
        if arrivee:
            arrivee_source = "lonab"
        else:
            placed = sorted(
                (x for x in runners
                 if isinstance(x["position"], int) and x["position"] > 0),
                key=lambda x: x["position"],
            )
            if len(placed) >= 3:
                arrivee = "-".join(str(x["number"]) for x in placed[:5])
                arrivee_source = "positions"

        # `hasResult` signifie désormais strictement « un ordre d'arrivée est
        # affichable ». Auparavant il valait true dès qu'UN partant avait une
        # position, si bien que 431 cartes annonçaient « Arrivée validée » alors
        # que 415 d'entre elles n'avaient aucun arrivage à montrer.
        has_result = bool(arrivee)

        out.append({
            "id": rid,
            "date": rdate,
            "reunion": f"R{rn}" if rn else "R1",
            "course": f"C{cn}" if cn else "C1",
            "hippodrome": hippo,
            "title": _clean_title(titre or "")[:70],
            "discipline": disc,
            "distance": dist_str,
            # Le terrain n'est exposé par AUCUN endpoint PMU : on ne l'invente pas.
            # La météo réelle de la réunion est fournie à la place.
            "terrain": None,
            "meteo": (
                {
                    "temperature": mtemp,
                    "nebulosite": mneb,
                    "ventForce": mvent,
                    "ventDirection": mdir,
                }
                if (mtemp is not None or mneb)
                else None
            ),
            "starters": len(runners),
            "time": heure or "—",
            "status": "Arrivée validée" if has_result else "Programmée",
            "hasResult": has_result,
            "favoriteOdds": round(min_cote, 1) if min_cote else 0,
            "accent": ACCENTS[idx % len(ACCENTS)],
            # --- marquage LONAB demandé ---
            "isLonab": bool(is_lonab),
            "lonabBet": lonab_bet,
            "lonabJournalBet": jbet,
            "lonabJournalVenue": jvenue,
            "arrivee": arrivee,
            # "lonab" = socle ; "positions" = dérivé des positions au socle
            "arriveeSource": arrivee_source,
            "quinteDividende": q5div,
            "quinteGagnants": q5win,
            "runners": runners,
        })

    REAL_RACES_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(REAL_RACES_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    nb_lonab = sum(1 for r in out if r["isLonab"])
    nb_arr = sum(1 for r in out if r["hasResult"])
    nb_socle = sum(1 for r in out if r.get("arriveeSource") == "lonab")
    nb_derive = sum(1 for r in out if r.get("arriveeSource") == "positions")
    log(f"\n  export -> {REAL_RACES_JSON}")
    log(f"  {len(out)} courses | {nb_lonab} marquées LONAB | {nb_arr} avec arrivée "
        f"({nb_socle} socle LONAB + {nb_derive} dérivées des positions)")
    return len(out)


# --------------------------------------------------------------------------- #
def main() -> int:
    log("=" * 74)
    log("  REBUILD SEPT 09->16 : Programme officiel + Arrivées + marquage LONAB")
    log("=" * 74)

    # Garde-fou ADR-001 : le socle gelé ne doit pas bouger
    import hashlib
    if SOCLE_DB.exists():
        h = hashlib.sha256(SOCLE_DB.read_bytes()).hexdigest()
        ok = h == SOCLE_SHA_EXPECTED
        log(f"  socle SHA-256 {'OK' if ok else 'MODIFIÉ !!'}  {h[:16]}…")
        if not ok:
            log("  ABORT : le socle gelé a changé.")
            return 2

    if not MASTER_DB.exists():
        log(f"  ABORT : {MASTER_DB} introuvable")
        return 1

    conn = sqlite3.connect(str(MASTER_DB), timeout=60)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.row_factory = sqlite3.Row

    export_only = "--export-only" in sys.argv
    meteo_only = "--meteo-only" in sys.argv

    try:
        if export_only:
            log("\n[export seul] aucune requête réseau")
            export_json(conn)
            log("\n  TERMINÉ")
            return 0

        if meteo_only:
            log("\n[météo seule] 8 requêtes programme")
            ensure_schema(conn)
            n = backfill_meteo(conn, make_client())
            log(f"  {n} courses mises à jour")
            export_json(conn)
            log("\n  TERMINÉ")
            return 0

        log("\n[1/4] Schéma")
        ensure_schema(conn)

        log("\n[2/4] Purge des lignes fabriquées (populate_today_programme)")
        purge_fabricated(conn)

        log("\n[3/4] Ingestion API PMU 09/09 -> 16/09")
        cl = make_client()
        total = {"races": 0, "runners": 0, "arrivees": 0, "lonab": 0}
        d = START_DATE
        while d <= END_DATE:
            st = ingest_date(conn, cl, d)
            for k in total:
                total[k] += st[k]
            d += timedelta(days=1)
            time.sleep(0.1)
        log(f"\n  TOTAL : {total['races']} courses, {total['runners']} partants, "
            f"{total['arrivees']} arrivées, {total['lonab']} LONAB")

        log("\n[4/4] Export front")
        export_json(conn)

        log("\n  Bilan par date :")
        for r in conn.execute(
            """SELECT date, COUNT(*) n, SUM(is_lonab) lon,
                      SUM(CASE WHEN result_status='OFFICIAL' THEN 1 ELSE 0 END) off
               FROM master_race WHERE date BETWEEN ? AND ?
               GROUP BY date ORDER BY date""",
            (START_DATE.isoformat(), END_DATE.isoformat()),
        ):
            log(f"    {r[0]}  courses={r[1]:3d}  LONAB={r[2]:2d}  arrivées={r[3]:3d}")
    finally:
        conn.close()

    log("\n  TERMINÉ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
