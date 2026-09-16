#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Intégration du Journal Hippique PMU'B officiel du Jeudi 17 Septembre 2026
Prix de Mehun-sur-Yèvre (Paris-Vincennes)
"""

import sqlite3
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / "pmu-lonab-scraper").exists():
    ROOT = Path(__file__).resolve().parents[1]
MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"

def ingest_journal_17_sept():
    conn = sqlite3.connect(MASTER_DB)
    c = conn.cursor()

    # 1. Vérifier si la course existe déjà
    c.execute("SELECT race_id FROM master_race WHERE date = '2026-09-17'")
    existing = c.fetchall()
    for row in existing:
        c.execute("DELETE FROM master_runner WHERE race_id = ?", (row[0],))
        c.execute("DELETE FROM master_race WHERE race_id = ?", (row[0],))

    race_id = str(uuid.uuid4())
    doc_id = 44471  # AN XXV - N° 44 471

    # Insertion de la course principale Quarté+ LONAB
    c.execute("""
        INSERT INTO master_race (
            race_id, source_document_id, date, date_is_sentinel,
            hippodrome_label_raw, discipline, discipline_status, distance_m,
            titre, n_partants_source, n_runners_linked, result_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        race_id,
        doc_id,
        "2026-09-17",
        0,
        "Paris-Vincennes",
        "Trot Attelé",
        "OK",
        2100,
        "Prix de Mehun-sur-Yèvre (Quarté+ LONAB)",
        15,
        15,
        "SCHEDULED"
    ))

    # Les 15 partants officiels issus du tableau du journal
    partants = [
        {
            "num": 1, "nom": "LE GRAAL", "sexe_age": "H.5", "dist": 2100, "chrono": "1.10.40",
            "perf": "1.D.1.1.2", "gains": 145515, "driver": "CL. DUVALDESTIN", "entr": "TH. DUVALDESTIN",
            "prop": "Ph. BEAUVISAGE", "cote_pt": 4.0, "cote_tm": 2.0, "prob": 28.5, "rank": 1
        },
        {
            "num": 2, "nom": "FERAHAN AS", "sexe_age": "M.5", "dist": 2100, "chrono": "1.10.90",
            "perf": "D.9.9.4.A", "gains": 127854, "driver": "G. GELORMINI", "entr": "H.E. BONDO",
            "prop": "Sc. ERCA", "cote_pt": 36.0, "cote_tm": 38.0, "prob": 2.7, "rank": 10
        },
        {
            "num": 3, "nom": "LAMONT DU DOUET", "sexe_age": "H.5", "dist": 2100, "chrono": "1.11.60",
            "perf": "4.3.3.5.7", "gains": 142410, "driver": "F. LAGADEUC", "entr": "N. BRIDAULT",
            "prop": "EC. BCC RACING", "cote_pt": 23.0, "cote_tm": 22.0, "prob": 4.5, "rank": 8
        },
        {
            "num": 4, "nom": "EMPIRE AS", "sexe_age": "M.6", "dist": 2100, "chrono": "1.11.90",
            "perf": "D.D.0.7.D", "gains": 127556, "driver": "J.M. BAZIRE", "entr": "N. BAZIRE",
            "prop": "IL MIGLIO VERDE", "cote_pt": 19.0, "cote_tm": 18.0, "prob": 5.4, "rank": 7
        },
        {
            "num": 5, "nom": "ALADIN", "sexe_age": "M.5", "dist": 2100, "chrono": "0.00.00",
            "perf": "3.3.2.1.D", "gains": 145299, "driver": "M. ABRIVARD", "entr": "W. NIMCZYK",
            "prop": "GESTUT IDEE", "cote_pt": 12.0, "cote_tm": 10.0, "prob": 9.5, "rank": 4
        },
        {
            "num": 6, "nom": "LOVEBIRD", "sexe_age": "M.5", "dist": 2100, "chrono": "1.10.90",
            "perf": "D.D.2.2.4", "gains": 134200, "driver": "E. RAFFIN", "entr": "J.PH. DUBOIS",
            "prop": "EC. VICT. DREAMS", "cote_pt": 11.0, "cote_tm": 9.0, "prob": 10.5, "rank": 3
        },
        {
            "num": 7, "nom": "FAWAZ MIL", "sexe_age": "H.5", "dist": 2100, "chrono": "1.11.40",
            "perf": "2.2.1.4.2", "gains": 122093, "driver": "M. MOTTIER", "entr": "Maria TORNQVIST",
            "prop": "EC. HAZELAAR", "cote_pt": 7.0, "cote_tm": 5.0, "prob": 17.5, "rank": 2
        },
        {
            "num": 8, "nom": "PURE STEEL", "sexe_age": "M.6", "dist": 2100, "chrono": "1.10.60",
            "perf": "2.4.1.D.6", "gains": 136126, "driver": "B. ROCHARD", "entr": "H.E. BONDO",
            "prop": "ENGHA. AALBORG APS", "cote_pt": 16.0, "cote_tm": 14.0, "prob": 6.8, "rank": 5
        },
        {
            "num": 9, "nom": "LOULOU DAB", "sexe_age": "H.5", "dist": 2100, "chrono": "1.12.90",
            "perf": "D.D.1.1.1", "gains": 118700, "driver": "D. BONNE", "entr": "D. BONNE",
            "prop": "EC. Damien BONNE", "cote_pt": 73.0, "cote_tm": 75.0, "prob": 1.3, "rank": 13
        },
        {
            "num": 10, "nom": "QUINTUS TOOMA", "sexe_age": "H.6", "dist": 2100, "chrono": "1.14.60",
            "perf": "1.6.2.D.0", "gains": 75140, "driver": "A. COLLETTE", "entr": "Vitale CIOTOLA",
            "prop": "K. M. HASTFARM I HOLM", "cote_pt": 67.0, "cote_tm": 70.0, "prob": 1.4, "rank": 12
        },
        {
            "num": 11, "nom": "TROGIR", "sexe_age": "H.6", "dist": 2100, "chrono": "1.11.70",
            "perf": "D.2.D.1.D", "gains": 108877, "driver": "M. NIMCZYK", "entr": "W. NIMCZYK",
            "prop": "U. MOMMERT", "cote_pt": 17.0, "cote_tm": 15.0, "prob": 6.2, "rank": 6
        },
        {
            "num": 12, "nom": "FABIUS ORS", "sexe_age": "M.5", "dist": 2100, "chrono": "0.00.00",
            "perf": "D.3.8.1.8", "gains": 30596, "driver": "G. PORZIO", "entr": "C. GODARD",
            "prop": "F. SORRENTINO", "cote_pt": 107.0, "cote_tm": 110.0, "prob": 0.9, "rank": 15
        },
        {
            "num": 13, "nom": "ELFO BREED", "sexe_age": "H.6", "dist": 2100, "chrono": "1.11.90",
            "perf": "7.1.1.1.1", "gains": 52431, "driver": "A. LAMY", "entr": "Vitale CIOTOLA",
            "prop": "Pietro GRANATA", "cote_pt": 78.0, "cote_tm": 80.0, "prob": 1.2, "rank": 14
        },
        {
            "num": 14, "nom": "L'AMOUR MEARAS", "sexe_age": "M.5", "dist": 2100, "chrono": "1.13.30",
            "perf": "3.8.6.2.2", "gains": 30580, "driver": "CH. MARTENS", "entr": "V. MARTENS",
            "prop": "Kjell JOHANSSON", "cote_pt": 47.0, "cote_tm": 50.0, "prob": 2.1, "rank": 11
        },
        {
            "num": 15, "nom": "LE RETOUR VRIE", "sexe_age": "M.5", "dist": 2100, "chrono": "1.11.40",
            "perf": "2.9.2.1.4", "gains": 116245, "driver": "A. ABRIVARD", "entr": "L.CL. ABRIVARD",
            "prop": "EC. ELEVAGE DU ROY", "cote_pt": 20.0, "cote_tm": 17.0, "prob": 5.2, "rank": 9
        }
    ]

    for p in partants:
        runner_id = str(uuid.uuid4())
        horse_id = str(uuid.uuid4())
        jockey_id = str(uuid.uuid4())
        trainer_id = str(uuid.uuid4())

        import re
        name_key = re.sub(r"[^A-Z0-9 ]", "", p["nom"].upper()).strip()
        h_row = c.execute("SELECT horse_id FROM master_horse WHERE name_key = ?", (name_key,)).fetchone()
        if h_row:
            horse_id = h_row[0]
        else:
            horse_id = str(uuid.uuid4())
            c.execute("""
                INSERT INTO master_horse (
                    horse_id, name_normalized, name_key, resolution_method,
                    resolution_confidence, homonym_risk, n_starts
                ) VALUES (?, ?, ?, 'EXACT', 1.0, 0, 1)
            """, (horse_id, p["nom"], name_key))

        driver_key = re.sub(r"[^A-Z0-9 ]", "", p["driver"].upper()).strip()
        d_row = c.execute("SELECT person_id FROM master_person WHERE name_key = ?", (driver_key,)).fetchone()
        if d_row:
            jockey_id = d_row[0]
        else:
            jockey_id = str(uuid.uuid4())
            c.execute("""
                INSERT INTO master_person (
                    person_id, name_normalized, name_key, role, resolution_method,
                    resolution_confidence, n_appearances
                ) VALUES (?, ?, ?, 'JOCKEY', 'EXACT', 1.0, 1)
            """, (jockey_id, p["driver"], driver_key))

        trainer_key = re.sub(r"[^A-Z0-9 ]", "", p["entr"].upper()).strip()
        t_row = c.execute("SELECT person_id FROM master_person WHERE name_key = ?", (trainer_key,)).fetchone()
        if t_row:
            trainer_id = t_row[0]
        else:
            trainer_id = str(uuid.uuid4())
            c.execute("""
                INSERT INTO master_person (
                    person_id, name_normalized, name_key, role, resolution_method,
                    resolution_confidence, n_appearances
                ) VALUES (?, ?, ?, 'TRAINER', 'EXACT', 1.0, 1)
            """, (trainer_id, p["entr"], trainer_key))

        age = int(p["sexe_age"].split(".")[1]) if "." in p["sexe_age"] else 5

        c.execute("""
            INSERT INTO master_runner (
                runner_id, race_id, source_document_id, source_partant_id,
                numero, horse_id, jockey_id, trainer_id,
                cote_decimale, gains_euros, performances_structured, age_raw, result_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            runner_id,
            race_id,
            doc_id,
            doc_id * 100 + p["num"],
            p["num"],
            horse_id,
            jockey_id,
            trainer_id,
            p["cote_pt"],
            p["gains"],
            p["perf"],
            age,
            "DECLARED"
        ))

        # Enregistrer les métriques marché
        c.execute("""
            INSERT OR REPLACE INTO market_runner_features (
                runner_id, race_id, m_prob_norm, m_rank, f_age, split
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            runner_id,
            race_id,
            round(p["prob"] / 100.0, 4),
            p["rank"],
            age,
            "inference"
        ))

    conn.commit()
    conn.close()
    print("Journal du 17 Septembre 2026 intégrant les 15 partants réels ingéré avec succès dans pmu_master.db !")

if __name__ == "__main__":
    ingest_journal_17_sept()
