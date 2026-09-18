"""Export toutes les courses Sept 9-17 vers realRaces.json."""
import sqlite3, json, math
from pathlib import Path

DB = Path(r"c:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\master\pmu_master.db")
OUT = Path(r"c:\Users\Lenovo\Desktop\PMU\fasoturf\public\realRaces.json")

conn = sqlite3.connect(str(DB), timeout=30)
conn.row_factory = sqlite3.Row
c = conn.cursor()

accents = ["green", "gold", "red"]

c.execute("""
    SELECT mr.race_id, mr.date, mr.hippodrome_label_raw, h.label_canonical,
           mr.discipline, mr.distance_m, mr.type_course, mr.titre, 
           mr.n_runners_linked, mr.result_status
    FROM master_race mr
    LEFT JOIN master_hippodrome h ON h.hippodrome_id = mr.hippodrome_id
    WHERE mr.n_runners_linked >= 8 AND mr.date BETWEEN '2026-09-09' AND '2026-09-17'
    ORDER BY mr.date DESC
    LIMIT 500
""")
races_rows = c.fetchall()

result = []
reunion_map = {}
course_counters = {}

for idx, rc in enumerate(races_rows):
    rid = rc["race_id"]
    race_date = rc["date"]
    hippo_raw = rc["hippodrome_label_raw"] or ""
    hippo_canonical = rc["label_canonical"] or ""
    discipline = rc["discipline"] or ""
    distance_m = rc["distance_m"]
    titre = rc["titre"] or ""
    n_runners = rc["n_runners_linked"]
    result_status = rc["result_status"]

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
            disc = "Trot Attelé"
        elif "MONTE" in d:
            disc = "Trot Monté"
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
               m.m_prob_norm, m.m_rank, m.label_win, m.f_age
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
        cote = float(row["cote_decimale"]) if row["cote_decimale"] is not None else None
        if cote and cote < min_cote:
            min_cote = cote

        if row["m_prob_norm"] is not None:
            prob_pct = round(row["m_prob_norm"] * 100, 1)
        elif cote and cote > 0:
            prob_pct = round((1.0 / cote) * 100, 1)
        else:
            prob_pct = 7.5

        mus = (row["performances_structured"] or "").replace('"', '').replace('[', '').replace(']', '')

        age_val = row["f_age"] if row["f_age"] is not None else 4
        if age_val is None and row["age_raw"]:
            try:
                age_val = int(row["age_raw"])
            except (ValueError, TypeError):
                age_val = 4

        runners.append({
            "number": row["numero"] or (r_idx + 1),
            "name": (row["horse_name"] or f"Partant #{row['numero'] or (r_idx + 1)}").title(),
            "age": age_val or 4,
            "music": mus or "N/A",
            "jockey": (row["jockey_name"] or "Non renseigné").title(),
            "trainer": (row["trainer_name"] or "Non renseigné").title(),
            "odds": cote if cote is not None else 10.0,
            "marketProb": prob_pct,
            "marketRank": row["m_rank"] or (r_idx + 1),
            "isWinner": bool(row["label_win"] == 1 or row["result_position"] == 1),
            "position": row["result_position"] if row["result_position"] else None
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
        "status": "Arrivée validée" if has_result else "Départ imminent",
        "hasResult": has_result,
        "favoriteOdds": round(min_cote, 1) if min_cote < 999 else 3.5,
        "accent": accents[idx % len(accents)],
        "runners": runners
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

dates = {}
for r in result:
    dates[r["date"]] = dates.get(r["date"], 0) + 1

print(f"Total: {len(result)} courses exportées")
for d, cnt in sorted(dates.items(), reverse=True):
    print(f"  {d} -> {cnt} courses")

conn.close()
