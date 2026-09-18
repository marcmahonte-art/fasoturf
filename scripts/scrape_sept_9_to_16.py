#!/usr/bin/env python3
"""
Scrape et intègre les courses PMU du 9 au 16 septembre 2026
via l'API officielle PMU, directement dans pmu_master.db.

Usage: python scrape_sept_9_to_16.py

NOTE : ce script ingère le programme + les partants. Le MARQUAGE LONAB
(`is_lonab` / `lonab_bet`) et la consolidation des ARRIVÉES officielles sont
assurés par `scripts/rebuild_sept_lonab.py`, qui est idempotent et rejouable.
Enchaîner les deux, ou lancer directement le second (il fait tout).
"""

import sys
import os
import sqlite3
import json
import uuid
import time
import math
import re
from datetime import date, timedelta
from pathlib import Path

# Ajouter le répertoire du scraper au path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(ROOT / "pmu-lonab-scraper"))

from app.enrichment.pmu_client import PMUApiClient

# Chemins
MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
FASOTURF_DIR = ROOT / "fasoturf"
# ATTENTION : le front importe `src/data/realRaces.json` (cf. src/data/races.ts et
# src/services/api.ts). Écrire dans `public/` ne met PAS à jour l'application.
REAL_RACES_JSON = FASOTURF_DIR / "src" / "data" / "realRaces.json"

# Dates à scraper
START_DATE = date(2026, 9, 9)
END_DATE = date(2026, 9, 16)

# API PMU Client
client = PMUApiClient(timeout=15, delay=0.5)


def get_dates_to_scrape():
    dates = []
    current = START_DATE
    while current <= END_DATE:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def norm_name(name):
    if not name:
        return ""
    return re.sub(r'[^A-Z\s]', '', name.upper()).strip()


def get_or_create_horse(conn, nom, sexe=None, age=None, pere=None, mere=None, 
                         robe=None, race_str=None, race_date=None):
    name_normalized = norm_name(nom)
    name_key = re.sub(r'\s+', '', name_normalized)
    
    c = conn.cursor()
    c.execute("SELECT horse_id FROM master_horse WHERE name_key = ?", (name_key,))
    row = c.fetchone()
    if row:
        c.execute("""
            UPDATE master_horse SET 
                last_seen_date = MAX(COALESCE(last_seen_date, ''), ?),
                n_starts = n_starts + 1,
                pedigree_pere = COALESCE(pedigree_pere, ?),
                pedigree_mere = COALESCE(pedigree_mere, ?),
                robe = COALESCE(robe, ?),
                race = COALESCE(race, ?)
            WHERE horse_id = ?
        """, (race_date or '', pere, mere, robe, race_str, row[0]))
        return row[0]
    
    horse_id = str(uuid.uuid4())
    sex_byr = f"{sexe or '?'}_{age or '?'}" if sexe or age else None
    c.execute("""
        INSERT INTO master_horse (
            horse_id, name_normalized, name_key,
            resolution_method, resolution_confidence, homonym_risk,
            n_sex_birthyear_variants, sex_birthyear_variants,
            n_starts, first_seen_date, last_seen_date,
            pedigree_pere, pedigree_mere, robe, race
        ) VALUES (?, ?, ?, 'api_pmu', 1.0, 'none', ?, ?, 1, ?, ?, ?, ?, ?, ?)
    """, (
        horse_id, name_normalized, name_key,
        1 if sex_byr else 0, sex_byr,
        race_date, race_date,
        pere, mere, robe, race_str
    ))
    return horse_id


def get_or_create_person(conn, nom, role):
    if not nom:
        return None
    name_normalized = norm_name(nom)
    name_key = re.sub(r'\s+', '', name_normalized)
    
    c = conn.cursor()
    c.execute("SELECT person_id FROM master_person WHERE name_key = ? AND role = ?", (name_key, role))
    row = c.fetchone()
    if row:
        c.execute("UPDATE master_person SET n_appearances = n_appearances + 1 WHERE person_id = ?", (row[0],))
        return row[0]
    
    person_id = str(uuid.uuid4())
    c.execute("""
        INSERT INTO master_person (
            person_id, name_normalized, name_key,
            role, resolution_method, resolution_confidence,
            n_appearances
        ) VALUES (?, ?, ?, ?, 'api_pmu', 1.0, 1)
    """, (person_id, name_normalized, name_key, role))
    return person_id


def get_or_create_hippodrome(conn, hippo_label):
    if not hippo_label:
        return None
    c = conn.cursor()
    c.execute("SELECT hippodrome_id FROM master_hippodrome WHERE label_canonical = ?", (hippo_label,))
    row = c.fetchone()
    if row:
        c.execute("UPDATE master_hippodrome SET n_courses = n_courses + 1 WHERE hippodrome_id = ?", (row[0],))
        return row[0]
    hippo_id = str(uuid.uuid4())
    c.execute("""
        INSERT INTO master_hippodrome (
            hippodrome_id, label_canonical, label_variants,
            country, is_valid, quality_flag, n_courses
        ) VALUES (?, ?, ?, 'FR', 1, 'ok', 1)
    """, (hippo_id, hippo_label, hippo_label))
    return hippo_id


def compute_market_features(participants, race_id, race_date, n_runners):
    features = []
    cotes = []
    for p in participants:
        cote = p.get("coteDirect", {}).get("coteDirect") if isinstance(p.get("coteDirect"), dict) else None
        if cote is None:
            cote = p.get("rapport")
        if cote and isinstance(cote, (int, float)) and cote > 0:
            cotes.append(float(cote))
        else:
            cotes.append(None)
    
    valid_cotes = [c for c in cotes if c and c > 0]
    total_implied = sum(1.0 / c for c in valid_cotes) if valid_cotes else 1.0
    median_cote = sorted(valid_cotes)[len(valid_cotes) // 2] if valid_cotes else 10.0
    
    for idx, p in enumerate(participants):
        cote = cotes[idx]
        if cote and cote > 0:
            implied = 1.0 / cote
            prob_norm = implied / total_implied if total_implied > 0 else 0.0
            log_odds = math.log(cote)
            rel_median = cote / median_cote if median_cote > 0 else 1.0
        else:
            cote = 15.0
            implied = 1.0 / cote
            prob_norm = implied / total_implied if total_implied > 0 else 0.0
            log_odds = math.log(cote)
            rel_median = cote / median_cote if median_cote > 0 else 1.0
        
        musique = p.get("musique", "")
        positions = re.findall(r'(\d)', musique[:20]) if musique else []
        positions_int = [int(x) for x in positions if x.isdigit()]
        
        f_musique_n = len(positions_int)
        f_musique_avg = sum(positions_int) / len(positions_int) if positions_int else 5.0
        f_musique_best = min(positions_int) if positions_int else 5.0
        f_musique_winrate = sum(1 for x in positions_int if x == 1) / max(len(positions_int), 1)
        f_musique_top3rate = sum(1 for x in positions_int if x <= 3) / max(len(positions_int), 1)
        
        gains = p.get("gainsParticipant", {})
        gains_carriere = gains.get("gainsCarriere", 0) or 0
        if gains_carriere > 1000:
            gains_carriere = gains_carriere // 100
        f_gains_log = math.log1p(gains_carriere)
        
        f_age = p.get("age", 4)
        sexe = (p.get("sexe") or "").upper()
        f_sex = 1 if sexe in ("M", "H") else 0
        
        features.append({
            "runner_id": None,
            "race_id": race_id,
            "date": race_date,
            "split": "api_pmu",
            "m_implied": round(implied, 6),
            "m_prob_norm": round(prob_norm, 6),
            "m_rank": idx + 1,
            "m_log_odds": round(log_odds, 4),
            "m_rel_median": round(rel_median, 4),
            "m_is_fav": 0,
            "f_musique_n": f_musique_n,
            "f_musique_avg": round(f_musique_avg, 2),
            "f_musique_best": f_musique_best,
            "f_musique_winrate": round(f_musique_winrate, 4),
            "f_musique_top3rate": round(f_musique_top3rate, 4),
            "f_gains_log": round(f_gains_log, 4),
            "f_age": f_age,
            "f_sex": f_sex,
            "f_field_size": n_runners,
            "c_horse_starts": 0,
            "c_horse_winrate": 0.0,
            "c_horse_top3rate": 0.0,
            "c_jockey_winrate": 0.0,
            "c_trainer_winrate": 0.0,
            "label_win": 0,
            "label_top3": 0,
            "cote": cote,
        })
    
    # Le classement de marché se calcule par index, sans réordonner la liste.
    # (Avant : `features.sort(...)` puis indexation positionnelle contre
    #  `participants` NON trié -> cotes attribuées aux mauvais chevaux.)
    order = sorted(range(len(features)), key=lambda i: -features[i]["m_prob_norm"])
    for rank, i in enumerate(order, 1):
        features[i]["m_rank"] = rank
        features[i]["m_is_fav"] = 1 if rank == 1 else 0

    return features


def scrape_date(conn, target_date):
    date_str = target_date.isoformat()
    print(f"\n{'='*60}")
    print(f"  Scraping {date_str}...")
    print(f"{'='*60}")
    
    c = conn.cursor()
    c.execute("""SELECT count(*) FROM master_race
                 WHERE date = ? AND n_runners_linked >= 8
                   AND COALESCE(source_document_id, 0) < 99000""", (date_str,))
    existing = c.fetchone()[0]
    if existing >= 5:
        print(f"  -> Deja {existing} courses completes, skip")
        return existing
    
    try:
        prog = client.get_programme(date_str)
    except Exception as e:
        print(f"  X Erreur API programme: {e}")
        return 0
    
    if not prog or "programme" not in prog:
        print(f"  X Pas de programme disponible pour {date_str}")
        return 0
    
    reunions = prog["programme"].get("reunions", [])
    if not reunions:
        print(f"  X Aucune reunion trouvee")
        return 0
    
    print(f"  {len(reunions)} reunion(s) trouvee(s)")
    
    total_courses_added = 0
    
    for reunion in reunions:
        r_num = reunion.get("numOfficiel", 0)
        hippo_data = reunion.get("hippodrome", {})
        hippo_label = hippo_data.get("libelleCourt", "").upper() if hippo_data else ""
        
        courses = reunion.get("courses", [])
        print(f"  R{r_num} - {hippo_label} ({len(courses)} courses)")
        
        hippo_id = get_or_create_hippodrome(conn, hippo_label)
        
        for course in courses:
            c_num = course.get("numOrdre", 0)
            libelle = course.get("libelle", "")
            discipline = course.get("discipline", "")
            distance = course.get("distance")
            montant = course.get("montantPrix")
            if montant and montant > 10000:
                montant = montant // 100
            nb_partants = course.get("nombreDeclaresPartants", 0)
            
            if nb_partants < 5:
                continue
            
            try:
                parts_data = client.get_participants(date_str, r_num, c_num)
            except Exception as e:
                print(f"    C{c_num}: X Erreur participants: {e}")
                continue
            
            if not parts_data or "participants" not in parts_data:
                print(f"    C{c_num}: X Pas de participants")
                continue
            
            participants = parts_data["participants"]
            n_runners = len(participants)
            
            if n_runners < 5:
                continue
            
            has_result = False
            try:
                rapports = client.get_rapports(date_str, r_num, c_num)
                # ATTENTION : `rapports-definitifs` renvoie une LISTE de paris
                # ([{typePari, miseBase, rapports:[{combinaison, ...}]}, ...]),
                # pas un dict. L'ancien test `isinstance(rapports, dict)` était
                # toujours faux -> aucune course n'était marquée OFFICIAL.
                if isinstance(rapports, list):
                    for entree in rapports:
                        tp = (entree.get("typePari") or "").replace("E_", "").replace("_", "")
                        if tp in ("QUINTPLUS", "QUARTPLUS", "TIERCE"):
                            for rap in (entree.get("rapports") or []):
                                if rap.get("combinaison"):
                                    has_result = True
                                    break
                        if has_result:
                            break
            except Exception:
                pass
            
            race_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"pmu:{date_str}:R{r_num}:C{c_num}"))
            
            c = conn.cursor()
            c.execute("SELECT race_id FROM master_race WHERE race_id = ?", (race_id,))
            if c.fetchone():
                print(f"    C{c_num}: deja present, skip")
                continue
            
            titre = f"{hippo_label} - {libelle}" if libelle else f"{hippo_label} - Course {c_num}"
            result_status = "OFFICIAL" if has_result else "pending"
            
            c.execute("""
                INSERT INTO master_race (
                    race_id, source_document_id, date, date_is_sentinel,
                    hippodrome_id, hippodrome_label_raw,
                    discipline, discipline_status,
                    distance_m, montant_euros,
                    partants_declares, partants_effectifs,
                    type_course, titre,
                    n_partants_source, n_runners_linked,
                    result_status
                ) VALUES (?, 0, ?, 0, ?, ?, ?, 'resolved', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                race_id, date_str, hippo_id, hippo_label,
                discipline, distance, montant,
                nb_partants, n_runners,
                course.get("typePari", ""), titre,
                n_runners, n_runners,
                result_status
            ))
            
            mkt_features = compute_market_features(participants, race_id, date_str, n_runners)
            
            for p_idx, p in enumerate(participants):
                nom_cheval = (p.get("nom") or f"Partant {p_idx+1}").upper()
                sexe = p.get("sexe", "")
                age = p.get("age", 0)
                pere = p.get("nomPere")
                mere = p.get("nomMere")
                robe_data = p.get("robe")
                robe = robe_data.get("libelleCourt") if isinstance(robe_data, dict) else str(robe_data) if robe_data else None
                race_cheval = p.get("race")
                
                musique = p.get("musique", "")
                numero = p.get("numPmu", p_idx + 1)
                
                cote = p.get("coteDirect", {}).get("coteDirect") if isinstance(p.get("coteDirect"), dict) else None
                if cote is None:
                    cote = p.get("rapport")
                if cote and isinstance(cote, (int, float)):
                    cote = float(cote)
                else:
                    cote = None
                
                jockey_nom = p.get("driver") or p.get("jockey")
                if isinstance(jockey_nom, dict):
                    jockey_nom = jockey_nom.get("nom", "")
                
                trainer_nom = p.get("entraineur")
                if isinstance(trainer_nom, dict):
                    trainer_nom = trainer_nom.get("nom", "")
                
                owner_nom = p.get("proprietaire")
                if isinstance(owner_nom, dict):
                    owner_nom = owner_nom.get("nom", "")
                
                gains = p.get("gainsParticipant", {})
                gains_val = gains.get("gainsCarriere", 0) or 0
                if gains_val > 10000:
                    gains_val = gains_val // 100
                
                result_pos = p.get("ordreArrivee")
                if not (result_pos and isinstance(result_pos, int)):
                    result_pos = None
                
                horse_id = get_or_create_horse(conn, nom_cheval, sexe, age, pere, mere, robe, race_cheval, date_str)
                jockey_id = get_or_create_person(conn, jockey_nom, "jockey")
                trainer_id = get_or_create_person(conn, trainer_nom, "trainer")
                owner_id = get_or_create_person(conn, owner_nom, "owner")
                
                runner_id = str(uuid.uuid4())
                r_status = "official" if result_pos else "pending"
                
                c.execute("""
                    INSERT INTO master_runner (
                        runner_id, race_id, source_document_id, source_partant_id,
                        numero, horse_id, jockey_id, trainer_id, owner_id,
                        cote_decimale, gains_euros, performances_structured,
                        sexe_raw, age_raw, poids_raw, corde_raw,
                        result_position, result_status
                    ) VALUES (?, ?, 0, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    runner_id, race_id,
                    numero, horse_id, jockey_id, trainer_id, owner_id,
                    cote, gains_val, musique,
                    sexe, str(age) if age else None, None, None,
                    result_pos, r_status
                ))
                
                feat = mkt_features[p_idx] if p_idx < len(mkt_features) else None
                if feat:
                    feat["runner_id"] = runner_id
                    c.execute("""
                        INSERT OR REPLACE INTO market_runner_features (
                            runner_id, race_id, date, split,
                            m_implied, m_prob_norm, m_rank, m_log_odds,
                            m_rel_median, m_is_fav,
                            f_musique_n, f_musique_avg, f_musique_best,
                            f_musique_winrate, f_musique_top3rate,
                            f_gains_log, f_age, f_sex, f_field_size,
                            c_horse_starts, c_horse_winrate, c_horse_top3rate,
                            c_jockey_winrate, c_trainer_winrate,
                            label_win, label_top3
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        runner_id, race_id, date_str, "api_pmu",
                        feat["m_implied"], feat["m_prob_norm"], feat["m_rank"],
                        feat["m_log_odds"], feat["m_rel_median"], feat["m_is_fav"],
                        feat["f_musique_n"], feat["f_musique_avg"], feat["f_musique_best"],
                        feat["f_musique_winrate"], feat["f_musique_top3rate"],
                        feat["f_gains_log"], feat["f_age"], feat["f_sex"], feat["f_field_size"],
                        feat["c_horse_starts"], feat["c_horse_winrate"], feat["c_horse_top3rate"],
                        feat["c_jockey_winrate"], feat["c_trainer_winrate"],
                        1 if result_pos == 1 else 0,
                        1 if result_pos and result_pos <= 3 else 0
                    ))
            
            total_courses_added += 1
            print(f"    C{c_num}: OK {libelle[:40]} ({n_runners} partants, resultat={'oui' if has_result else 'non'})")
    
    conn.commit()
    return total_courses_added


def export_to_json(conn):
    print(f"\n{'='*60}")
    print("  Export vers realRaces.json...")
    print(f"{'='*60}")
    
    c = conn.cursor()
    accents = ["green", "gold", "red"]
    
    c.execute("""
        SELECT mr.race_id, mr.date, mr.hippodrome_label_raw, h.label_canonical,
               mr.discipline, mr.distance_m, mr.type_course, mr.titre, 
               mr.n_runners_linked, mr.result_status
        FROM master_race mr
        LEFT JOIN master_hippodrome h ON h.hippodrome_id = mr.hippodrome_id
        WHERE mr.n_runners_linked >= 8
        ORDER BY mr.date DESC
        LIMIT 100
    """)
    races_rows = c.fetchall()
    
    result = []
    reunion_map = {}
    course_counters = {}
    
    for idx, rc in enumerate(races_rows):
        rid = rc[0]
        race_date = rc[1]
        hippo_raw = rc[2] or ""
        hippo_canonical = rc[3] or ""
        discipline = rc[4] or ""
        distance_m = rc[5]
        titre = rc[7] or ""
        n_runners = rc[8]
        result_status = rc[9]
        
        hippo = hippo_canonical or hippo_raw
        if not hippo or hippo.isdigit():
            hippo = "ParisLongchamp"
        hippo = hippo.replace("-", " ").title()
        if "Vincennes" in hippo:
            hippo = "Paris-Vincennes"
        if "Longchamp" in hippo:
            hippo = "ParisLongchamp"
        
        disc = discipline
        if disc:
            d = disc.upper()
            if "ATTELE" in d or "TROT" in d:
                disc = "Trot Attele"
            elif "MONTE" in d:
                disc = "Trot Monte"
            elif "PLAT" in d:
                disc = "Plat"
            elif "OBSTACLE" in d or "HAIES" in d or "STEEPLE" in d:
                disc = "Haies / Obstacle"
            else:
                disc = disc.title()
        else:
            disc = "Plat"
        
        dist_str = f"{distance_m:,} m".replace(",", " ") if distance_m else "2 100 m"
        
        clean_titre = titre
        if " - " in clean_titre:
            parts = clean_titre.split(" - ")
            if len(parts) >= 2:
                clean_titre = parts[1].strip().title() if parts[1].strip() else parts[0].strip().title()
        if not clean_titre:
            clean_titre = "Grand Prix LONAB"
        
        if race_date not in reunion_map:
            reunion_map[race_date] = {}
            course_counters[race_date] = {}
        if hippo not in reunion_map[race_date]:
            r_n = len(reunion_map[race_date]) + 1
            reunion_map[race_date][hippo] = f"R{r_n}"
            course_counters[race_date][hippo] = 1
        else:
            course_counters[race_date][hippo] += 1
        
        reunion_str = reunion_map[race_date][hippo]
        course_str = f"C{course_counters[race_date][hippo]}"
        
        c.execute("""
            SELECT r.runner_id, r.numero, r.age_raw, r.cote_decimale,
                   r.performances_structured, r.result_position,
                   h.name_normalized AS horse_name,
                   pj.name_normalized AS jockey_name,
                   pt.name_normalized AS trainer_name,
                   m.m_prob_norm, m.m_rank, m.label_win,
                   m.f_age
            FROM master_runner r
            LEFT JOIN master_horse h ON h.horse_id = r.horse_id
            LEFT JOIN master_person pj ON pj.person_id = r.jockey_id
            LEFT JOIN master_person pt ON pt.person_id = r.trainer_id
            LEFT JOIN market_runner_features m ON m.runner_id = r.runner_id
            WHERE r.race_id = ?
            ORDER BY r.numero ASC
        """, (rid,))
        runner_rows = c.fetchall()
        
        if not runner_rows:
            continue
        
        runners = []
        min_cote = 999.0
        
        for r_idx, row in enumerate(runner_rows):
            cote = float(row[3]) if row[3] is not None else None
            if cote and cote < min_cote:
                min_cote = cote
            
            if row[9] is not None:
                prob_pct = round(row[9] * 100, 1)
            elif cote and cote > 0:
                prob_pct = round((1.0 / cote) * 100, 1)
            else:
                prob_pct = 7.5
            
            mus = (row[4] or "").replace('"', '').replace('[', '').replace(']', '')
            
            runners.append({
                "number": row[1] or (r_idx + 1),
                "name": (row[6] or f"Partant #{row[1] or (r_idx + 1)}").title(),
                "age": row[12] if row[12] is not None else (int(row[2]) if row[2] and str(row[2]).isdigit() else 4),
                "music": mus or "N/A",
                "jockey": (row[7] or "Non renseigne").title(),
                "trainer": (row[8] or "Non renseigne").title(),
                "odds": cote if cote is not None else 10.0,
                "marketProb": prob_pct,
                "marketRank": row[10] or (r_idx + 1),
                "isWinner": bool(row[11] == 1 or row[5] == 1),
                "position": row[5] if row[5] else None
            })
        
        runners.sort(key=lambda x: x["number"])
        has_result = any(r["isWinner"] for r in runners)
        race_time = f"{13 + (idx % 6)}:{(idx * 35) % 60:02d}"
        
        result.append({
            "id": rid,
            "date": race_date,
            "reunion": reunion_str,
            "course": course_str,
            "hippodrome": hippo,
            "title": clean_titre[:60],
            "discipline": disc,
            "distance": dist_str,
            "terrain": "Bon" if (idx % 2 == 0) else "Souple",
            "starters": len(runners),
            "time": race_time,
            "status": "Arrivee validee" if has_result else "Depart imminent",
            "hasResult": has_result,
            "favoriteOdds": round(min_cote, 1) if min_cote < 999 else 3.5,
            "accent": accents[idx % len(accents)],
            "runners": runners
        })
    
    REAL_RACES_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(REAL_RACES_JSON, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"  OK {len(result)} courses exportees vers {REAL_RACES_JSON}")
    return len(result)


def main():
    print("=" * 60)
    print("  FasoTurf - Scraping API PMU: 9-16 Septembre 2026")
    print("=" * 60)
    
    if not MASTER_DB.exists():
        print(f"ERREUR: Base de donnees introuvable: {MASTER_DB}")
        return 1
    
    conn = sqlite3.connect(str(MASTER_DB))
    conn.row_factory = sqlite3.Row
    
    try:
        dates = get_dates_to_scrape()
        
        c = conn.cursor()
        c.execute("""
            SELECT DISTINCT date FROM master_race 
            WHERE n_runners_linked >= 8 AND date BETWEEN ? AND ?
        """, (START_DATE.isoformat(), END_DATE.isoformat()))
        existing = {row[0] for row in c.fetchall()}
        
        print(f"\nDates a traiter: {len(dates)}")
        print(f"Dates deja couvertes: {existing}")
        
        total_added = 0
        for d in dates:
            added = scrape_date(conn, d)
            total_added += added
        
        print(f"\n{'='*60}")
        print(f"  SCRAPING TERMINE")
        print(f"  Courses ajoutees: {total_added}")
        print(f"{'='*60}")
        
        c = conn.cursor()
        c.execute("""
            SELECT date, count(*) FROM master_race 
            WHERE date BETWEEN '2026-09-09' AND '2026-09-16' AND n_runners_linked >= 8
            GROUP BY date ORDER BY date
        """)
        print(f"\n  Bilan Sept 9-16:")
        for row in c.fetchall():
            print(f"    {row[0]} -> {row[1]} courses")
        
        export_to_json(conn)
        
    finally:
        conn.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
