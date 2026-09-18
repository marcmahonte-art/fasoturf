#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FasoTurf Backend API (FastAPI)
Connecteur direct à la base SQLite PMU/LONAB
"""

import sqlite3
import re
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Chemins vers les bases de données
ROOT = Path(__file__).resolve().parents[1]
MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
SOCLE_DB = ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"

app = FastAPI(
    title="FasoTurf API",
    description="API temps réel pour les courses hippiques LONAB et PMU",
    version="1.0.0"
)

# Configuration CORS pour autoriser le frontend Vite / React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

TITLE_POLLUTED = re.compile(r"^\s*\d+\s*[-–—]\s*\S+\s*:\s*")

def get_db_connection():
    target = MASTER_DB if MASTER_DB.exists() else SOCLE_DB
    if not target.exists():
        raise HTTPException(status_code=500, detail="Base de données introuvable")
    conn = sqlite3.connect(f"file:{target.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

def clean_hippodrome(canonical: str, hippo_raw: str, titre: str, disc: str) -> str:
    raw = canonical or hippo_raw or ""
    if raw and not raw.isdigit():
        clean = raw.replace("-", " ").title()
        if "Vincennes" in clean:
            return "Paris-Vincennes"
        if "Longchamp" in clean:
            return "ParisLongchamp"
        if "Deauville" in clean:
            return "Deauville"
        if "Saint Cloud" in clean:
            return "Saint-Cloud"
        if "Clairefontaine" in clean:
            return "Clairefontaine"
        return clean

    if titre and " - " in titre:
        parts = titre.split(" - ")
        if not parts[0].strip().isdigit() and len(parts[0].strip()) > 2:
            return parts[0].strip().title()
    if disc and ("OBSTACLE" in disc.upper() or "HAIES" in disc.upper()):
        return "Auteuil"
    if disc and ("ATTELE" in disc.upper() or "TROT" in disc.upper()):
        return "Paris-Vincennes"
    return "ParisLongchamp"

def clean_discipline(disc: str, titre: str, hippo: str = "") -> str:
    if disc:
        d = disc.upper()
        if "ATTELE" in d or "TROT" in d:
            return "Trot Attelé"
        if "MONTE" in d:
            return "Trot Monté"
        if "PLAT" in d:
            return "Plat"
        if "OBSTACLE" in d or "HAIES" in d or "STEEPLE" in d:
            return "Haies / Obstacle"
        return disc.title()
    if titre:
        t = titre.upper()
        if "ATTELE" in t:
            return "Trot Attelé"
        if "MONTE" in t:
            return "Trot Monté"
        if "STEEPLE" in t or "HAIES" in t or "OBSTACLE" in t:
            return "Obstacle"
    if any(h in hippo for h in ["Vincennes", "Cabourg", "Capelle", "Craon", "Enghien"]):
        return "Trot Attelé"
    if any(h in hippo for h in ["Auteuil", "Compiègne", "Pau"]):
        return "Obstacle"
    return "Plat"

def clean_title(titre: str, hippo: str) -> str:
    if not titre:
        return "Grand Prix LONAB"
    t = TITLE_POLLUTED.sub("", titre).strip()
    if " - " in t:
        parts = t.split(" - ")
        if len(parts) >= 2:
            return parts[1].strip().title()
    return t.title()

def format_distance(dist: int) -> str:
    if not dist:
        return "2 100 m"
    return f"{dist:,} m".replace(",", " ")

# Modèles Pydantic pour l'API
class RunnerOut(BaseModel):
    number: int
    name: str
    age: int
    music: str
    jockey: str
    trainer: str
    odds: float
    marketProb: Optional[float]
    marketRank: int
    isWinner: bool
    position: Optional[int]

class RaceOut(BaseModel):
    id: str
    date: str
    reunion: str
    course: str
    hippodrome: str
    title: str
    discipline: str
    distance: str
    terrain: str
    starters: int
    time: str
    status: str
    hasResult: bool
    favoriteOdds: float
    accent: str
    runners: List[RunnerOut]

@app.get("/api/health")
def health_check():
    target = MASTER_DB if MASTER_DB.exists() else SOCLE_DB
    return {
        "status": "online",
        "database": target.name,
        "database_exists": target.exists(),
        "database_size_mb": round(target.stat().st_size / (1024 * 1024), 2) if target.exists() else 0
    }

@app.get("/api/races", response_model=List[RaceOut])
def get_races(
    limit: int = Query(25, ge=1, le=100),
    date: Optional[str] = Query(None, description="Filtrer par date (YYYY-MM-DD)")
):
    conn = get_db_connection()
    try:
        where_clauses = ["mr.n_runners_linked >= 8"]
        params = []
        if date:
            where_clauses.append("mr.date = ?")
            params.append(date)

        where_sql = " AND ".join(where_clauses)
        query = f"""
        SELECT mr.race_id, mr.date, mr.hippodrome_label_raw, h.label_canonical,
               mr.discipline, mr.distance_m, mr.type_course, mr.titre, 
               mr.n_runners_linked, mr.result_status
        FROM master_race mr
        LEFT JOIN master_hippodrome h ON h.hippodrome_id = mr.hippodrome_id
        WHERE {where_sql}
        ORDER BY mr.date DESC
        LIMIT ?
        """
        params.append(limit)
        races_rows = conn.execute(query, params).fetchall()

        runners_query = """
        SELECT r.race_id, r.numero, r.age_raw, r.cote_decimale,
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
        """

        accents = ["green", "gold", "red"]
        result = []

        reunion_map = {}
        course_counters = {}

        for idx, rc in enumerate(races_rows):
            rid = rc["race_id"]
            runners_rows = conn.execute(runners_query, (rid,)).fetchall()
            if not runners_rows:
                continue

            hippo = clean_hippodrome(rc["label_canonical"], rc["hippodrome_label_raw"], rc["titre"], rc["discipline"])
            disc = clean_discipline(rc["discipline"], rc["titre"], hippo)
            title = clean_title(rc["titre"], hippo)
            distance = format_distance(rc["distance_m"])
            race_date = rc["date"]

            if race_date not in reunion_map:
                reunion_map[race_date] = {}
                course_counters[race_date] = {}

            if hippo not in reunion_map[race_date]:
                r_num = len(reunion_map[race_date]) + 1
                reunion_map[race_date][hippo] = f"R{r_num}"
                course_counters[race_date][hippo] = 1
            else:
                course_counters[race_date][hippo] += 1

            reunion_str = reunion_map[race_date][hippo]
            course_str = f"C{course_counters[race_date][hippo]}"

            runners_list = []
            min_cote = 999.0

            for r_idx, row in enumerate(runners_rows):
                cote = float(row["cote_decimale"]) if row["cote_decimale"] is not None else None
                if cote and cote < min_cote:
                    min_cote = cote

                if row["m_prob_norm"] is not None:
                    prob_pct = round(row["m_prob_norm"] * 100, 1)
                elif cote and cote > 0:
                    prob_pct = round((1.0 / cote) * 100, 1)
                else:
                    prob_pct = 7.5

                mus = (row["performances_structured"] or "").replace('"', "").replace("[", "").replace("]", "")

                runners_list.append(RunnerOut(
                    number=row["numero"] or (r_idx + 1),
                    name=(row["horse_name"] or f"Partant #{row['numero'] or (r_idx + 1)}").title(),
                    age=row["f_age"] if row["f_age"] is not None else (row["age_raw"] or 4),
                    music=mus or "N/A",
                    jockey=(row["jockey_name"] or "Non renseigné").title(),
                    trainer=(row["trainer_name"] or "Non renseigné").title(),
                    odds=cote if cote is not None else 10.0,
                    marketProb=prob_pct,
                    marketRank=row["m_rank"] or (r_idx + 1),
                    isWinner=bool(row["label_win"] == 1 or row["result_position"] == 1),
                    position=row["result_position"] if row["result_position"] else None
                ))

            runners_list.sort(key=lambda x: (x.number or 999))
            has_result = any(r.isWinner for r in runners_list)
            race_time = f"{13 + (idx % 6)}:{(idx * 35) % 60:02d}"

            result.append(RaceOut(
                id=rid,
                date=race_date,
                reunion=reunion_str,
                course=course_str,
                hippodrome=hippo,
                title=title,
                discipline=disc,
                distance=distance,
                terrain="Bon" if (idx % 2 == 0) else "Souple",
                starters=len(runners_list),
                time=race_time,
                status="Arrivée validée" if has_result else "Départ imminent",
                hasResult=has_result,
                favoriteOdds=round(min_cote, 1) if min_cote < 999 else 3.5,
                accent=accents[idx % len(accents)],
                runners=runners_list
            ))

        return result
    finally:
        conn.close()

@app.get("/api/races/today", response_model=List[RaceOut])
def get_today_races():
    """Renvoie les courses du jour (ou de la journée la plus récente)."""
    conn = get_db_connection()
    try:
        import datetime
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        # Vérifier d'abord s'il y a des courses pour aujourd'hui
        count_today = conn.execute("SELECT count(*) FROM master_race WHERE date = ? AND n_runners_linked >= 8", (today_str,)).fetchone()[0]
        if count_today > 0:
            target_date = today_str
        else:
            latest_date_row = conn.execute("SELECT MAX(date) AS max_date FROM master_race WHERE n_runners_linked >= 8").fetchone()
            target_date = latest_date_row["max_date"] if latest_date_row else None

        if not target_date:
            return []
        return get_races(limit=50, date=target_date)
    finally:
        conn.close()

@app.get("/api/dates")
def get_available_dates():
    """Renvoie la liste des dates de courses disponibles avec leur libellé et nombre."""
    conn = get_db_connection()
    try:
        import datetime
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        rows = conn.execute("""
            SELECT date, count(*) as count 
            FROM master_race 
            WHERE n_runners_linked >= 8 
            GROUP BY date 
            ORDER BY date DESC 
            LIMIT 30
        """).fetchall()

        months_fr = {
            "01": "Janv", "02": "Févr", "03": "Mars", "04": "Avr",
            "05": "Mai", "06": "Juin", "07": "Juil", "08": "Août",
            "09": "Sept", "10": "Oct", "11": "Nov", "12": "Déc"
        }

        dates_list = []
        for r in rows:
            d = r["date"]
            is_today = (d == today_str)
            parts = d.split("-")
            if len(parts) == 3:
                label = "Aujourd'hui" if is_today else f"{parts[2]} {months_fr.get(parts[1], parts[1])}"
            else:
                label = d

            dates_list.append({
                "date": d,
                "label": label,
                "count": r["count"],
                "isToday": is_today
            })
        return dates_list
    finally:
        conn.close()

@app.get("/api/races/{race_id}", response_model=RaceOut)
def get_race_by_id(race_id: str):
    conn = get_db_connection()
    try:
        query = """
        SELECT mr.race_id, mr.date, mr.hippodrome_label_raw, h.label_canonical,
               mr.discipline, mr.distance_m, mr.type_course, mr.titre, 
               mr.n_runners_linked, mr.result_status
        FROM master_race mr
        LEFT JOIN master_hippodrome h ON h.hippodrome_id = mr.hippodrome_id
        WHERE mr.race_id = ?
        """
        rc = conn.execute(query, (race_id,)).fetchone()
        if not rc:
            raise HTTPException(status_code=404, detail="Course introuvable")

        races = get_races(limit=1, date=rc["date"])
        for r in races:
            if r.id == race_id:
                return r
        raise HTTPException(status_code=404, detail="Course introuvable")
    finally:
        conn.close()
