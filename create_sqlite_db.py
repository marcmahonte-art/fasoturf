#!/usr/bin/env python3
"""
Crée une base SQLite unifiée à partir de tous les fichiers parsés.
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

PROCESSED_DIR = Path(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed")
DB_PATH = PROCESSED_DIR / "pmu_lonab.db"

def create_schema(conn):
    """Crée le schéma de la base de données."""
    cursor = conn.cursor()
    
    # Table principale : documents
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            doc_type TEXT NOT NULL,           -- JOURNAL, RESULTAT, REP, ECD (COURSE_EN_DIRECT)
            date_publication TEXT,            -- YYYY-MM-DD
            pages INTEGER,
            quality_score INTEGER,
            quality_status TEXT,              -- SUCCESS, PARTIAL, FAILED
            parsing_errors TEXT,              -- JSON array
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table : courses (pour JOURNAL, RESULTAT, ECD)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            date TEXT,                          -- YYYY-MM-DD
            reunion TEXT,                       -- R1, R2, etc.
            course_num INTEGER,
            hippodrome TEXT,
            discipline TEXT,                    -- ATTELE, PLAT, OBSTACLE
            distance_raw TEXT,
            distance_m INTEGER,
            montant_raw TEXT,
            montant_euros INTEGER,
            partants_declares INTEGER,
            partants_effectifs INTEGER,
            type_course TEXT,                   -- AUTOSTART, HANDICAP, etc.
            titre TEXT,
            heure_depart TEXT,
            heure_arret_jeux TEXT,
            raw_text TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)
    
    # Table : partants (chevaux) - seulement JOURNAL
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS partants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            numero INTEGER NOT NULL,
            nom_cheval_raw TEXT,
            nom_cheval_normalized TEXT,
            sexe TEXT,                          -- H, F, M
            age TEXT,
            poids TEXT,
            corde TEXT,
            distance_raw TEXT,
            distance_m INTEGER,
            chrono_raw TEXT,
            chrono_normalized TEXT,             -- 1:11.60
            performances_raw TEXT,              -- D.6.2.0.0
            performances_structured TEXT,       -- JSON array
            gains_raw TEXT,
            gains_euros INTEGER,
            driver_raw TEXT,
            driver_normalized TEXT,
            entraineur_raw TEXT,
            entraineur_normalized TEXT,
            proprietaire_raw TEXT,
            proprietaire_normalized TEXT,
            cote_raw TEXT,                      -- 7/1
            cote_decimale REAL,                 -- 7.0
            commentaire TEXT,
            raw_data TEXT,                      -- JSON des colonnes brutes
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)
    
    # Table : resultats (arrivées, gains) - RESULTAT
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            date TEXT,                          -- YYYY-MM-DD
            type_pari TEXT,                     -- QUARTE, TIERCE, 4+1, etc.
            arrivee TEXT,                       -- JSON array [9,2,16,12,1]
            arrivee_complete TEXT,              -- JSON array
            npo INTEGER,
            np INTEGER,
            disqualifies TEXT,                  -- JSON array
            non_partants TEXT,                  -- JSON array
            gains_ordre_raw TEXT,
            gains_ordre_euros INTEGER,
            gains_desordre_raw TEXT,
            gains_desordre_euros INTEGER,
            gains_bonus_raw TEXT,
            gains_bonus_euros INTEGER,
            nb_gagnants_ordre INTEGER,
            nb_gagnants_desordre INTEGER,
            nb_gagnants_bonus INTEGER,
            masse_partager_raw TEXT,
            masse_partager_euros INTEGER,
            rapport_gagnant_raw TEXT,
            rapport_gagnant_euros INTEGER,
            rapport_place_a_raw TEXT,
            rapport_place_a_euros INTEGER,
            rapport_place_b_raw TEXT,
            rapport_place_b_euros INTEGER,
            map_paris_raw TEXT,
            map_paris_euros INTEGER,
            raw_text TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)
    
    # Table : media_selections (pronostics presse) - JOURNAL
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS media_selections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            source TEXT,                        -- LE PARISIEN, EQUIDIA, etc.
            selection TEXT,                     -- JSON array [6,5,7,10,1]
            rang TEXT,                          -- JSON array
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)
    
    # Table : classements (FORME, CLASSE, PROGRES, REGULARITE) - JOURNAL
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            forme TEXT,                         -- JSON array
            classe TEXT,                        -- JSON array
            progres TEXT,                       -- JSON array
            regularite TEXT,                    -- JSON array
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)
    
    # Table : commentaires - JOURNAL
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commentaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            numero_cheval INTEGER NOT NULL,
            texte TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)
    
    # Table : ecd_documents (entête Course En Direct)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ecd_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            date TEXT,                          -- YYYY-MM-DD
            reunion TEXT,                       -- R1, R3, etc.
            hippodrome TEXT,
            discipline TEXT,
            date_heure_extraction TEXT,
            raw_text TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)
    
    # Table : ecd_courses (chaque course dans ECD)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ecd_courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            course_id TEXT NOT NULL,
            numero_course INTEGER,
            arrivee_raw TEXT,
            arrivee_positions TEXT,             -- JSON array
            gains_total_raw TEXT,
            gains_total_euros INTEGER,
            page_num INTEGER,
            y_position REAL,
            raw_text TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)
    
    # Table : ecd_paris (pari/gains par course ECD)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ecd_paris (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ecd_course_id INTEGER NOT NULL,
            type_pari TEXT,                     -- SIMPLE GAGNANT, COUPLE, etc.
            combinaison_raw TEXT,
            combinaison_normalized TEXT,        -- JSON array
            montant_raw TEXT,
            montant_euros INTEGER,
            nb_paris INTEGER,
            position TEXT,                      -- GAGNANT, PLACE, etc.
            uncertain BOOLEAN,
            FOREIGN KEY (ecd_course_id) REFERENCES ecd_courses(id)
        )
    """)
    
    # Table : rep_documents (rapports PMU)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rep_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            document_type TEXT,                 -- REP
            date_document TEXT,                 -- YYYY-MM-DD
            date_document_raw TEXT,
            date_course_cible TEXT,             -- YYYY-MM-DD
            date_course_cible_raw TEXT,
            game_type TEXT,                     -- QUARTE, TIERCE, etc.
            report_ordre_raw TEXT,
            report_ordre_euros INTEGER,
            tierce_v_raw TEXT,
            tierce_v_value INTEGER,
            raw_text TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)
    
    # Index pour performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_date ON documents(date_publication)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_courses_doc ON courses(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_courses_date ON courses(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_courses_hippo ON courses(hippodrome)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_partants_doc ON partants(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_partants_course ON partants(course_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_partants_nom ON partants(nom_cheval_normalized)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resultats_doc ON resultats(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_resultats_date ON resultats(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ecd_doc ON ecd_documents(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ecd_courses_doc ON ecd_courses(document_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rep_doc ON rep_documents(document_id)")
    
    conn.commit()
    print("Schéma créé avec succès")
    
    # Debug: vérifier le schéma de la table partants
    cursor.execute("PRAGMA table_info(partants)")
    cols = cursor.fetchall()
    print(f"Table partants: {len(cols)} colonnes")
    for c in cols:
        print(f"  {c[1]} ({c[2]})")

def insert_document(cursor, doc):
    """Insère un document principal."""
    cursor.execute("""
        INSERT OR REPLACE INTO documents 
        (filename, doc_type, date_publication, pages, quality_score, quality_status, parsing_errors)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        doc.get('filename'),
        doc.get('doc_type'),
        doc.get('date_publication'),
        doc.get('pages'),
        doc.get('quality_score'),
        doc.get('quality_status'),
        json.dumps(doc.get('parsing_errors', []), ensure_ascii=False)
    ))
    return cursor.lastrowid

def load_and_insert_all():
    """Charge tous les JSON et insère dans SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    create_schema(conn)
    cursor = conn.cursor()
    
    # ========== 1. all_parsed.json (JOURNAL + RESULTAT) ==========
    print("Chargement all_parsed.json...")
    with open(PROCESSED_DIR / "all_parsed.json", 'r', encoding='utf-8') as f:
        all_parsed = json.load(f)
    
    for doc in all_parsed:
        doc_id = insert_document(cursor, doc)
        
        # Courses
        for course in doc.get('courses', []):
            cursor.execute("""
                INSERT INTO courses 
                (document_id, course_id, date, reunion, course_num, hippodrome, discipline,
                 distance_raw, distance_m, montant_raw, montant_euros,
                 partants_declares, partants_effectifs, type_course, titre,
                 heure_depart, heure_arret_jeux, raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                course.get('course_id'),
                course.get('date'),
                course.get('reunion'),
                course.get('course_num'),
                course.get('hippodrome'),
                course.get('discipline'),
                course.get('distance_raw') or (course.get('distance', {}).get('raw') if isinstance(course.get('distance'), dict) else None),
                course.get('distance_m') or (course.get('distance', {}).get('meters') if isinstance(course.get('distance'), dict) else None),
                course.get('montant_raw') or (course.get('montant', {}).get('raw') if isinstance(course.get('montant'), dict) else None),
                course.get('montant_euros') or (course.get('montant', {}).get('euros') if isinstance(course.get('montant'), dict) else None),
                course.get('partants_declares'),
                course.get('partants_effectifs'),
                course.get('type_course'),
                course.get('titre'),
                course.get('heure_depart'),
                course.get('heure_arret_jeux'),
                course.get('raw_text')
            ))
        
        # Partants
        for p in doc.get('partants', []):
            vals = (
                doc_id,
                p.get('course_id'),
                p.get('numero'),
                p.get('nom_cheval_raw') or (p.get('nom_cheval', {}).get('raw') if isinstance(p.get('nom_cheval'), dict) else None),
                p.get('nom_cheval_normalized') or (p.get('nom_cheval', {}).get('normalized') if isinstance(p.get('nom_cheval'), dict) else None),
                p.get('sexe'),
                p.get('age'),
                p.get('poids'),
                p.get('corde'),
                p.get('distance_raw') or (p.get('distance', {}).get('raw') if isinstance(p.get('distance'), dict) else None),
                p.get('distance_m') or (p.get('distance', {}).get('meters') if isinstance(p.get('distance'), dict) else None),
                p.get('chrono_raw') or (p.get('chrono', {}).get('raw') if isinstance(p.get('chrono'), dict) else None),
                p.get('chrono_normalized') or (p.get('chrono', {}).get('normalized') if isinstance(p.get('chrono'), dict) else None),
                p.get('performances_raw') or (p.get('performances', {}).get('raw') if isinstance(p.get('performances'), dict) else None),
                json.dumps(p.get('performances_structured') or (p.get('performances', {}).get('structured') if isinstance(p.get('performances'), dict) else []), ensure_ascii=False),
                p.get('gains_raw') or (p.get('gains', {}).get('raw') if isinstance(p.get('gains'), dict) else None),
                p.get('gains_euros') or (p.get('gains', {}).get('euros') if isinstance(p.get('gains'), dict) else None),
                p.get('driver_raw') or (p.get('driver', {}).get('raw') if isinstance(p.get('driver'), dict) else None),
                p.get('driver_normalized') or (p.get('driver', {}).get('normalized') if isinstance(p.get('driver'), dict) else None),
                p.get('entraineur_raw') or (p.get('entraineur', {}).get('raw') if isinstance(p.get('entraineur'), dict) else None),
                p.get('entraineur_normalized') or (p.get('entraineur', {}).get('normalized') if isinstance(p.get('entraineur'), dict) else None),
                p.get('proprietaire_raw') or (p.get('proprietaire', {}).get('raw') if isinstance(p.get('proprietaire'), dict) else None),
                p.get('proprietaire_normalized') or (p.get('proprietaire', {}).get('normalized') if isinstance(p.get('proprietaire'), dict) else None),
                p.get('cote_raw') or (p.get('cote', {}).get('raw') if isinstance(p.get('cote'), dict) else None),
                p.get('cote_decimale') or (p.get('cote', {}).get('decimale') if isinstance(p.get('cote'), dict) else None),
                p.get('commentaire'),
                json.dumps(p.get('raw_data', {}), ensure_ascii=False)
            )
            # Debug
            print(f"  vals length: {len(vals)}")
            for i, v in enumerate(vals):
                if isinstance(v, (list, tuple, dict)):
                    print(f"  [{i}] is {type(v).__name__}: {v}")
            sql = """
                INSERT INTO partants
                (document_id, course_id, numero, nom_cheval_raw, nom_cheval_normalized,
                 sexe, age, poids, corde,
                 distance_raw, distance_m,
                 chrono_raw, chrono_normalized,
                 performances_raw, performances_structured,
                 gains_raw, gains_euros,
                 driver_raw, driver_normalized,
                 entraineur_raw, entraineur_normalized,
                 proprietaire_raw, proprietaire_normalized,
                 cote_raw, cote_decimale,
                 commentaire, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            print(f"  Executing SQL with {len(vals)} params")
            try:
                cursor.execute(sql, vals)
            except Exception as e:
                print(f"  ERROR: {e}")
                print(f"  vals: {vals}")
                raise
        
        # Résultat
        r = doc.get('resultat')
        if r:
            cursor.execute("""
                INSERT INTO resultats
                (document_id, course_id, date, type_pari, arrivee, arrivee_complete,
                 npo, np, disqualifies, non_partants,
                 gains_ordre_raw, gains_ordre_euros,
                 gains_desordre_raw, gains_desordre_euros,
                 gains_bonus_raw, gains_bonus_euros,
                 nb_gagnants_ordre, nb_gagnants_desordre, nb_gagnants_bonus,
                 masse_partager_raw, masse_partager_euros,
                 rapport_gagnant_raw, rapport_gagnant_euros,
                 rapport_place_a_raw, rapport_place_a_euros,
                 rapport_place_b_raw, rapport_place_b_euros,
                 map_paris_raw, map_paris_euros,
                 raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                r.get('course_id'),
                r.get('date'),
                r.get('type_pari'),
                json.dumps(r.get('arrivee', []), ensure_ascii=False),
                json.dumps(r.get('arrivee_complete', []), ensure_ascii=False),
                r.get('npo'),
                r.get('np'),
                json.dumps(r.get('disqualifies', []), ensure_ascii=False),
                json.dumps(r.get('non_partants', []), ensure_ascii=False),
                r.get('gains_ordre_raw') or (r.get('gains_ordre', {}).get('raw') if isinstance(r.get('gains_ordre'), dict) else None),
                r.get('gains_ordre_euros') or (r.get('gains_ordre', {}).get('euros') if isinstance(r.get('gains_ordre'), dict) else None),
                r.get('gains_desordre_raw') or (r.get('gains_desordre', {}).get('raw') if isinstance(r.get('gains_desordre'), dict) else None),
                r.get('gains_desordre_euros') or (r.get('gains_desordre', {}).get('euros') if isinstance(r.get('gains_desordre'), dict) else None),
                r.get('gains_bonus_raw') or (r.get('gains_bonus', {}).get('raw') if isinstance(r.get('gains_bonus'), dict) else None),
                r.get('gains_bonus_euros') or (r.get('gains_bonus', {}).get('euros') if isinstance(r.get('gains_bonus'), dict) else None),
                r.get('nb_gagnants_ordre') or (r.get('nb_gagnants', {}).get('ordre') if isinstance(r.get('nb_gagnants'), dict) else None),
                r.get('nb_gagnants_desordre') or (r.get('nb_gagnants', {}).get('desordre') if isinstance(r.get('nb_gagnants'), dict) else None),
                r.get('nb_gagnants_bonus') or (r.get('nb_gagnants', {}).get('bonus') if isinstance(r.get('nb_gagnants'), dict) else None),
                r.get('masse_partager_raw') or (r.get('masse_partager', {}).get('raw') if isinstance(r.get('masse_partager'), dict) else None),
                r.get('masse_partager_euros') or (r.get('masse_partager', {}).get('euros') if isinstance(r.get('masse_partager'), dict) else None),
                r.get('rapport_gagnant_raw') or (r.get('rapports', {}).get('gagnant', {}).get('raw') if isinstance(r.get('rapports'), dict) else None),
                r.get('rapport_gagnant_euros') or (r.get('rapports', {}).get('gagnant', {}).get('euros') if isinstance(r.get('rapports'), dict) else None),
                r.get('rapport_place_a_raw') or (r.get('rapports', {}).get('place_a', {}).get('raw') if isinstance(r.get('rapports'), dict) else None),
                r.get('rapport_place_a_euros') or (r.get('rapports', {}).get('place_a', {}).get('euros') if isinstance(r.get('rapports'), dict) else None),
                r.get('rapport_place_b_raw') or (r.get('rapports', {}).get('place_b', {}).get('raw') if isinstance(r.get('rapports'), dict) else None),
                r.get('rapport_place_b_euros') or (r.get('rapports', {}).get('place_b', {}).get('euros') if isinstance(r.get('rapports'), dict) else None),
                r.get('map_paris_raw') or (r.get('map_paris', {}).get('raw') if isinstance(r.get('map_paris'), dict) else None),
                r.get('map_paris_euros') or (r.get('map_paris', {}).get('euros') if isinstance(r.get('map_paris'), dict) else None),
                r.get('raw_text')
            ))
        
        # Media selections
        for ms in doc.get('media_selections', []):
            cursor.execute("""
                INSERT INTO media_selections (document_id, course_id, source, selection, rang)
                VALUES (?, ?, ?, ?, ?)
            """, (
                doc_id,
                ms.get('course_id'),
                ms.get('source'),
                json.dumps(ms.get('selection', []), ensure_ascii=False),
                json.dumps(ms.get('rang', []), ensure_ascii=False)
            ))
        
        # Classements
        for cl in doc.get('classements', []):
            cursor.execute("""
                INSERT INTO classements (document_id, course_id, forme, classe, progres, regularite)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                cl.get('course_id'),
                json.dumps(cl.get('forme', []), ensure_ascii=False),
                json.dumps(cl.get('classe', []), ensure_ascii=False),
                json.dumps(cl.get('progres', []), ensure_ascii=False),
                json.dumps(cl.get('regularite', []), ensure_ascii=False)
            ))
        
        # Commentaires
        for cm in doc.get('commentaires', []):
            cursor.execute("""
                INSERT INTO commentaires (document_id, course_id, numero_cheval, texte)
                VALUES (?, ?, ?, ?)
            """, (
                doc_id,
                cm.get('course_id'),
                cm.get('numero_cheval'),
                cm.get('texte')
            ))
    
    print(f"  Inséré {len(all_parsed)} documents (JOURNAL/RESULTAT)")
    
    # ========== 2. rep_parsed.json ==========
    print("Chargement rep_parsed.json...")
    with open(PROCESSED_DIR / "rep_parsed.json", 'r', encoding='utf-8') as f:
        rep_parsed = json.load(f)
    
    for doc in rep_parsed:
        doc_id = insert_document(cursor, doc)
        
        rd = doc.get('rep_document', {})
        cursor.execute("""
            INSERT INTO rep_documents
            (document_id, document_type, date_document, date_document_raw,
             date_course_cible, date_course_cible_raw, game_type,
             report_ordre_raw, report_ordre_euros,
             tierce_v_raw, tierce_v_value, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            rd.get('document_type'),
            rd.get('date_document'),
            rd.get('date_document_raw'),
            rd.get('date_course_cible'),
            rd.get('date_course_cible_raw'),
            rd.get('game_type'),
            rd.get('report_ordre_raw') or (rd.get('report_ordre', {}).get('raw') if isinstance(rd.get('report_ordre'), dict) else None),
            rd.get('report_ordre_euros') or (rd.get('report_ordre', {}).get('euros') if isinstance(rd.get('report_ordre'), dict) else None),
            rd.get('tierce_v_raw') or (rd.get('tierce_v', {}).get('raw') if isinstance(rd.get('tierce_v'), dict) else None),
            rd.get('tierce_v_value') or (rd.get('tierce_v', {}).get('value') if isinstance(rd.get('tierce_v'), dict) else None),
            rd.get('raw_text')
        ))
    
    print(f"  Inséré {len(rep_parsed)} documents REP")
    
    # ========== 3. ecd_parsed.json ==========
    print("Chargement ecd_parsed.json...")
    with open(PROCESSED_DIR / "ecd_parsed.json", 'r', encoding='utf-8') as f:
        ecd_parsed = json.load(f)
    
    for doc in ecd_parsed:
        doc_id = insert_document(cursor, doc)
        
        # ECD document header
        ecd = doc.get('ecd_document', {})
        cursor.execute("""
            INSERT INTO ecd_documents
            (document_id, date, reunion, hippodrome, discipline,
             date_heure_extraction, raw_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            ecd.get('date'),
            ecd.get('reunion'),
            ecd.get('hippodrome'),
            ecd.get('discipline'),
            ecd.get('date_heure_extraction'),
            ecd.get('raw_text')
        ))
        
        # ECD courses
        for course in doc.get('courses', []):
            cursor.execute("""
                INSERT INTO ecd_courses
                (document_id, course_id, numero_course,
                 arrivee_raw, arrivee_positions,
                 gains_total_raw, gains_total_euros,
                 page_num, y_position, raw_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                course.get('course_id'),
                course.get('numero_course'),
                course.get('arrivee_raw') or (course.get('arrivee', {}).get('arrivee_raw') if isinstance(course.get('arrivee'), dict) else None),
                json.dumps(course.get('arrivee_positions') or (course.get('arrivee', {}).get('positions') if isinstance(course.get('arrivee'), dict) else []), ensure_ascii=False),
                course.get('gains_total_raw') or (course.get('arrivee', {}).get('gains_total_raw') if isinstance(course.get('arrivee'), dict) else None),
                course.get('gains_total_euros') or (course.get('arrivee', {}).get('gains_total_euros') if isinstance(course.get('arrivee'), dict) else None),
                course.get('page_num'),
                course.get('y_position'),
                course.get('raw_text')
            ))
            ecd_course_id = cursor.lastrowid
            
            # ECD paris
            for pari in course.get('paris', []):
                cursor.execute("""
                    INSERT INTO ecd_paris
                    (ecd_course_id, type_pari, combinaison_raw, combinaison_normalized,
                     montant_raw, montant_euros, nb_paris, position, uncertain)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ecd_course_id,
                    pari.get('type_pari'),
                    pari.get('combinaison_raw') or (pari.get('combinaison', {}).get('raw') if isinstance(pari.get('combinaison'), dict) else None),
                    json.dumps(pari.get('combinaison_normalized') or (pari.get('combinaison', {}).get('normalized') if isinstance(pari.get('combinaison'), dict) else []), ensure_ascii=False),
                    pari.get('montant_raw') or (pari.get('montant', {}).get('raw') if isinstance(pari.get('montant'), dict) else None),
                    pari.get('montant_euros') or (pari.get('montant', {}).get('euros') if isinstance(pari.get('montant'), dict) else None),
                    pari.get('nb_paris'),
                    pari.get('position'),
                    pari.get('uncertain', False)
                ))
    
    print(f"  Inséré {len(ecd_parsed)} documents ECD")
    
    conn.commit()
    conn.close()
    print(f"\n✅ Base SQLite créée : {DB_PATH}")

def verify_db():
    """Vérifie le contenu de la base."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n=== VÉRIFICATION BASE ===")
    
    # Count par table
    tables = ['documents', 'courses', 'partants', 'resultats', 
              'media_selections', 'classements', 'commentaires',
              'ecd_documents', 'ecd_courses', 'ecd_paris', 'rep_documents']
    
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        count = cursor.fetchone()[0]
        print(f"  {t}: {count}")
    
    # Stats par type
    cursor.execute("SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type")
    print("\nDocuments par type:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Dates
    cursor.execute("SELECT MIN(date_publication), MAX(date_publication) FROM documents WHERE date_publication IS NOT NULL")
    min_d, max_d = cursor.fetchone()
    print(f"\nPériode: {min_d} à {max_d}")
    
    # Exemples de requêtes utiles
    print("\n=== EXEMPLES REQUÊTES ===")
    
    # Courses par hippodrome
    cursor.execute("""
        SELECT hippodrome, COUNT(*) as nb 
        FROM courses 
        WHERE hippodrome IS NOT NULL AND hippodrome != ''
        GROUP BY hippodrome 
        ORDER BY nb DESC 
        LIMIT 10
    """)
    print("\nTop 10 hippodromes:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Partants par cheval (top)
    cursor.execute("""
        SELECT nom_cheval_normalized, COUNT(*) as courses 
        FROM partants 
        WHERE nom_cheval_normalized IS NOT NULL AND nom_cheval_normalized != ''
        GROUP BY nom_cheval_normalized 
        ORDER BY courses DESC 
        LIMIT 10
    """)
    print("\nTop 10 chevaux (nb courses):")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # Résultats par type pari
    cursor.execute("SELECT type_pari, COUNT(*) FROM resultats GROUP BY type_pari")
    print("\nRésultats par type pari:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  CRÉATION BASE SQLITE UNIFIÉE PMU LONAB")
    print("=" * 60)
    
    # Supprimer l'ancienne base si existe
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Ancienne base supprimée: {DB_PATH}")
    
    load_and_insert_all()
    verify_db()
    
    print("\n✅ TERMINÉ - Base prête pour requêtes SQL")