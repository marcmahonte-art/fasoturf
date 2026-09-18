#!/usr/bin/env python3
"""
Build SQLite database - direct copy of working inline test.
"""

import sqlite3
import json
from pathlib import Path

PROCESSED_DIR = Path(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed")
DB_PATH = PROCESSED_DIR / "pmu_lonab.db"

if DB_PATH.exists():
    DB_PATH.unlink()

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('PRAGMA foreign_keys = ON')
cursor.execute('PRAGMA journal_mode = WAL')

# Schema
cursor.execute('''
    CREATE TABLE documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE NOT NULL,
        doc_type TEXT NOT NULL,
        date_publication TEXT,
        pages INTEGER,
        quality_score INTEGER,
        quality_status TEXT,
        parsing_errors TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        course_id TEXT NOT NULL,
        date TEXT,
        reunion TEXT,
        course_num INTEGER,
        hippodrome TEXT,
        discipline TEXT,
        distance_raw TEXT,
        distance_m INTEGER,
        montant_raw TEXT,
        montant_euros INTEGER,
        partants_declares INTEGER,
        partants_effectifs INTEGER,
        type_course TEXT,
        titre TEXT,
        heure_depart TEXT,
        heure_arret_jeux TEXT,
        raw_text TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
''')

cursor.execute('''
    CREATE TABLE partants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        course_id TEXT NOT NULL,
        numero INTEGER NOT NULL,
        nom_cheval_raw TEXT,
        nom_cheval_normalized TEXT,
        sexe TEXT,
        age TEXT,
        poids TEXT,
        corde TEXT,
        distance_raw TEXT,
        distance_m INTEGER,
        chrono_raw TEXT,
        chrono_normalized TEXT,
        performances_raw TEXT,
        performances_structured TEXT,
        gains_raw TEXT,
        gains_euros INTEGER,
        driver_raw TEXT,
        driver_normalized TEXT,
        entraineur_raw TEXT,
        entraineur_normalized TEXT,
        proprietaire_raw TEXT,
        proprietaire_normalized TEXT,
        cote_raw TEXT,
        cote_decimale REAL,
        commentaire TEXT,
        raw_data TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
''')

cursor.execute('''
    CREATE TABLE resultats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        course_id TEXT NOT NULL,
        date TEXT,
        type_pari TEXT,
        arrivee TEXT,
        arrivee_complete TEXT,
        npo INTEGER,
        np INTEGER,
        disqualifies TEXT,
        non_partants TEXT,
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
''')

cursor.execute('''
    CREATE TABLE media_selections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        course_id TEXT NOT NULL,
        source TEXT,
        selection TEXT,
        rang TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
''')

cursor.execute('''
    CREATE TABLE classements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        course_id TEXT NOT NULL,
        forme TEXT,
        classe TEXT,
        progres TEXT,
        regularite TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
''')

cursor.execute('''
    CREATE TABLE commentaires (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        course_id TEXT NOT NULL,
        numero_cheval INTEGER NOT NULL,
        texte TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
''')

cursor.execute('''
    CREATE TABLE ecd_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        date TEXT,
        reunion TEXT,
        hippodrome TEXT,
        discipline TEXT,
        date_heure_extraction TEXT,
        raw_text TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
''')

cursor.execute('''
    CREATE TABLE ecd_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        course_id TEXT NOT NULL,
        numero_course INTEGER,
        arrivee_raw TEXT,
        arrivee_positions TEXT,
        gains_total_raw TEXT,
        gains_total_euros INTEGER,
        page_num INTEGER,
        y_position REAL,
        raw_text TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
''')

cursor.execute('''
    CREATE TABLE ecd_paris (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ecd_course_id INTEGER NOT NULL,
        type_pari TEXT,
        combinaison_raw TEXT,
        combinaison_normalized TEXT,
        montant_raw TEXT,
        montant_euros INTEGER,
        nb_paris INTEGER,
        position TEXT,
        uncertain BOOLEAN,
        FOREIGN KEY (ecd_course_id) REFERENCES ecd_courses(id)
    )
''')

cursor.execute('''
    CREATE TABLE rep_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        document_type TEXT,
        date_document TEXT,
        date_document_raw TEXT,
        date_course_cible TEXT,
        date_course_cible_raw TEXT,
        game_type TEXT,
        report_ordre_raw TEXT,
        report_ordre_euros INTEGER,
        tierce_v_raw TEXT,
        tierce_v_value INTEGER,
        raw_text TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
''')

# Indexes
cursor.execute("CREATE INDEX idx_documents_type ON documents(doc_type)")
cursor.execute("CREATE INDEX idx_documents_date ON documents(date_publication)")
cursor.execute("CREATE INDEX idx_courses_doc ON courses(document_id)")
cursor.execute("CREATE INDEX idx_courses_date ON courses(date)")
cursor.execute("CREATE INDEX idx_courses_hippo ON courses(hippodrome)")
cursor.execute("CREATE INDEX idx_partants_doc ON partants(document_id)")
cursor.execute("CREATE INDEX idx_partants_course ON partants(course_id)")
cursor.execute("CREATE INDEX idx_partants_nom ON partants(nom_cheval_normalized)")
cursor.execute("CREATE INDEX idx_resultats_doc ON resultats(document_id)")
cursor.execute("CREATE INDEX idx_resultats_date ON resultats(date)")
cursor.execute("CREATE INDEX idx_ecd_doc ON ecd_documents(document_id)")
cursor.execute("CREATE INDEX idx_ecd_courses_doc ON ecd_courses(document_id)")
cursor.execute("CREATE INDEX idx_rep_doc ON rep_documents(document_id)")

# Load data
with open(PROCESSED_DIR / 'all_parsed.json', 'r', encoding='utf-8') as f:
    all_parsed = json.load(f)
with open(PROCESSED_DIR / 'rep_parsed.json', 'r', encoding='utf-8') as f:
    rep_parsed = json.load(f)
with open(PROCESSED_DIR / 'ecd_parsed.json', 'r', encoding='utf-8') as f:
    ecd_parsed = json.load(f)

all_docs = all_parsed + rep_parsed + ecd_parsed

# Insert documents
filename_to_id = {}
for doc in all_docs:
    cursor.execute('''
        INSERT OR REPLACE INTO documents 
        (filename, doc_type, date_publication, pages, quality_score, quality_status, parsing_errors)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        doc.get('filename'),
        doc.get('doc_type'),
        doc.get('date_publication'),
        doc.get('pages'),
        doc.get('quality_score'),
        doc.get('quality_status'),
        json.dumps(doc.get('parsing_errors', []), ensure_ascii=False)
    ))
    filename_to_id[doc['filename']] = cursor.lastrowid

print('Inserted documents:', len(filename_to_id))

# Insert courses
for doc in all_parsed:
    doc_id = filename_to_id.get(doc['filename'])
    if not doc_id:
        continue
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
print('Inserted courses')

# Insert partants - EXACT COPY OF WORKING INLINE TEST
cols = ['document_id', 'course_id', 'numero', 'nom_cheval_raw', 'nom_cheval_normalized', 
        'sexe', 'age', 'poids', 'corde', 'distance_raw', 'distance_m',
        'chrono_raw', 'chrono_normalized', 'performances_raw', 'performances_structured',
        'gains_raw', 'gains_euros', 'driver_raw', 'driver_normalized',
        'entraineur_raw', 'entraineur_normalized', 'proprietaire_raw', 
        'proprietaire_normalized', 'cote_raw', 'cote_decimale', 'commentaire', 'raw_data']

qs = ', '.join(['?'] * len(cols))
sql = 'INSERT INTO partants (' + ', '.join(cols) + ') VALUES (' + qs + ')'

count = 0
for doc in all_parsed:
    doc_id = filename_to_id.get(doc['filename'])
    if not doc_id:
        continue
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
        cursor.execute(sql, vals)
        count += 1

print('Inserted partants:', count)

# Insert resultats
resultat_count = 0
for doc in all_parsed:
    doc_id = filename_to_id.get(doc['filename'])
    if not doc_id:
        continue
    r = doc.get('resultat')
    if not r:
        continue
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
    resultat_count += 1
print('Inserted resultats:', resultat_count)

# Insert media, classements, commentaires
for doc in all_parsed:
    doc_id = filename_to_id.get(doc['filename'])
    if not doc_id:
        continue
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

# Insert rep
for doc in rep_parsed:
    doc_id = filename_to_id.get(doc['filename'])
    if not doc_id:
        continue
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
print('Inserted REP:', len(rep_parsed))

# Insert ecd
for doc in ecd_parsed:
    doc_id = filename_to_id.get(doc['filename'])
    if not doc_id:
        continue
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
print('Inserted ECD:', len(ecd_parsed))

conn.commit()

# Verify
print("\n=== VERIFICATION ===")
tables = ['documents', 'courses', 'partants', 'resultats', 
          'media_selections', 'classements', 'commentaires',
          'ecd_documents', 'ecd_courses', 'ecd_paris', 'rep_documents']
for t in tables:
    cursor.execute(f"SELECT COUNT(*) FROM {t}")
    print(f"  {t}: {cursor.fetchone()[0]}")

cursor.execute("SELECT doc_type, COUNT(*) FROM documents GROUP BY doc_type")
print("\nDocuments by type:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

cursor.execute("SELECT MIN(date_publication), MAX(date_publication) FROM documents WHERE date_publication IS NOT NULL")
min_d, max_d = cursor.fetchone()
print(f"\nDate range: {min_d} to {max_d}")

# Sample queries
print("\n=== SAMPLE QUERIES ===")
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

cursor.execute("""
    SELECT nom_cheval_normalized, COUNT(*) as courses 
    FROM partants 
    WHERE nom_cheval_normalized IS NOT NULL AND nom_cheval_normalized != ''
    GROUP BY nom_cheval_normalized 
    ORDER BY courses DESC 
    LIMIT 10
""")
print("\nTop 10 chevaux:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

cursor.execute("SELECT type_pari, COUNT(*) FROM resultats GROUP BY type_pari")
print("\nRésultats par type:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

conn.close()
print(f"\n✅ Database created: {DB_PATH}")