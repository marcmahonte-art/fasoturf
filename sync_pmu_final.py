#!/usr/bin/env python3
"""
Sync complet PMU API -> Base SQLite Locale
Version finale corrigée
"""

import sqlite3
import socket
import dns.resolver
import requests
import json
import time
from datetime import datetime, timedelta, date
from pathlib import Path

# ==================== CONFIG ====================
DB_PATH = Path(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db")
BASE_URL = "https://online.turfinfo.api.pmu.fr/rest/client/61"

# ==================== DNS FIX ====================
resolver = dns.resolver.Resolver()
resolver.nameservers = ['8.8.8.8', '1.1.1.1']
original_getaddrinfo = socket.getaddrinfo

def custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host in ['www.pmu.fr', 'online.turfinfo.api.pmu.fr', 'turfinfo.api.pmu.fr', 'api.pmu.fr', 'data.pmu.fr']:
        try:
            answers = resolver.resolve(host, 'A')
            ips = [r.to_text() for r in answers]
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ips[0], port))]
        except Exception as e:
            print('DNS failed for ' + host + ': ' + str(e))
    return original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = custom_getaddrinfo

# ==================== SESSION ====================
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.pmu.fr/',
    'Accept-Language': 'fr-FR,fr;q=0.9',
})

BASE = "https://online.turfinfo.api.pmu.fr/rest/client/61"

# ==================== DB INIT ====================
def init_db(conn):
    cursor = conn.cursor()
    
    cursor.execute('DROP TABLE IF EXISTS api_partants')
    cursor.execute('''
        CREATE TABLE api_partants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT NOT NULL,
            numero_pmu INTEGER,
            nom TEXT,
            age INTEGER,
            sexe TEXT,
            race TEXT,
            statut TEXT,
            corde INTEGER,
            oeilleres TEXT,
            proprietaire TEXT,
            entraineur TEXT,
            deferre TEXT,
            driver TEXT,
            driver_change BOOLEAN,
            musique TEXT,
            nb_courses INTEGER,
            nb_victoires INTEGER,
            nb_places INTEGER,
            gains_carriere INTEGER,
            pere TEXT,
            mere TEXT,
            ordre_arrivee INTEGER,
            engagement TEXT,
            supplement BOOLEAN,
            handicap_distance INTEGER,
            poids INTEGER,
            temps_obtenu TEXT,
            reduction_km TEXT,
            dernier_rapport_direct REAL,
            dernier_rapport_reference REAL,
            avis_entraineur TEXT,
            data_json TEXT,
            UNIQUE(course_id, numero_pmu)
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_courses')
    cursor.execute('''
        CREATE TABLE api_courses (
            course_id TEXT PRIMARY KEY,
            date TEXT,
            reunion INTEGER,
            course_num INTEGER,
            hippodrome_code TEXT,
            hippodrome_nom TEXT,
            discipline TEXT,
            distance INTEGER,
            type_course TEXT,
            titre TEXT,
            heure_depart TEXT,
            partants_declares INTEGER,
            partants_effectifs INTEGER,
            data_json TEXT,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_rapports')
    cursor.execute('''
        CREATE TABLE api_rapports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, type_pari TEXT, arrivee TEXT,
            arrivee_consolidee TEXT, gains_base REAL, gains_ordre REAL,
            gains_desordre REAL, nb_gagnants INTEGER, masse_partager REAL,
            rapports_consolides TEXT, risques TEXT, data_json TEXT,
            UNIQUE(course_id, type_pari)
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_cotes')
    cursor.execute('''
        CREATE TABLE api_cotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, type_pari TEXT, numero INTEGER,
            cote_directe REAL, masse_enjeu INTEGER, cote_reference REAL,
            evolution_cote REAL, risque REAL, updatetime TEXT,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_meteo')
    cursor.execute('''
        CREATE TABLE api_meteo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL, hippodrome_code TEXT NOT NULL,
            temperature REAL, vent_force REAL, vent_direction TEXT,
            nebulosite_code INTEGER, condition TEXT, terrain TEXT,
            data_json TEXT,
            UNIQUE(date, hippodrome_code)
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_pronostics')
    cursor.execute('''
        CREATE TABLE api_pronostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, source TEXT, pronostics TEXT,
            nb_partants INTEGER, data_json TEXT,
            UNIQUE(course_id, source)
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_ecuries')
    cursor.execute('''
        CREATE TABLE api_ecuries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE, casaque_url TEXT, data_json TEXT
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_partants_course ON api_partants(course_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rapports_course ON api_rapports(course_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cotes_course ON api_cotes(course_id)')
    
    print("[OK] Base initialisee")

def safe_get(d, *keys, default=None):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default

def extract_str(val):
    if val is None:
        return None
    if isinstance(val, str):
        return val
    if isinstance(val, dict):
        return val.get('text') or val.get('libelle') or json.dumps(val, ensure_ascii=False)
    return str(val)

def ms_to_time(ms):
    if not ms:
        return None
    try:
        dt = datetime.fromtimestamp(ms / 1000)
        return dt.strftime("%H:%M")
    except:
        return None

def timestamp_to_date(ts):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts / 1000).strftime("%d%m%Y")
    except:
        return None

def sync_programme(conn, date_ddmmyyyy):
    cursor = conn.cursor()
    url = BASE_URL + "/programme/" + date_ddmmyyyy + "?specialisation=INTERNET"
    
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return 0
        
        data = r.json()
        prog = data.get('programme', {}) if isinstance(data, dict) else {}
        reunions = prog.get('reunions', [])
        
        count = 0
        for reun in reunions:
            reun_num = reun.get('numOfficiel')
            if not reun_num:
                continue
                
            hippodrome = reun.get('hippodrome', {}) if isinstance(reun.get('hippodrome'), dict) else {}
            hippo_code = hippodrome.get('code')
            hippo_nom = hippodrome.get('libelle')
            date_reunion_ts = reun.get('dateReunion')
            date_reunion = timestamp_to_date(date_reunion_ts) if date_reunion_ts else date_ddmmyyyy
            
            courses = reun.get('courses', [])
            for course in courses:
                course_num = course.get('numOrdre')
                if not course_num:
                    continue
                    
                course_id = date_reunion + "_R" + str(reun_num) + "_C" + str(course_num)
                
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO api_courses
                    (course_id, date, reunion, course_num, hippodrome_code, hippodrome_nom,
                     discipline, distance, type_course, titre, heure_depart,
                     partants_declares, partants_effectifs, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    course_id,
                    date_reunion,
                    reun.get('numOfficiel'),
                    course.get('numOrdre'),
                    course.get('hippodrome', {}).get('code') if isinstance(course.get('hippodrome'), dict) else None,
                    course.get('hippodrome', {}).get('libelle') if isinstance(course.get('hippodrome'), dict) else None,
                    course.get('discipline'),
                    course.get('distance'),
                    course.get('specialite'),
                    course.get('libelle') or course.get('libelleCourt'),
                    ms_to_time(course.get('heureDepart')),
                    course.get('nombreDeclaresPartants'),
                    len(course.get('participants', [])) if isinstance(course.get('participants'), list) else 0,
                    json.dumps(course, ensure_ascii=False)
                ))
        
        return len(reunions)
    
    except Exception as e:
        print("  ERREUR programme: " + str(e))
        return 0

def sync_course_details(conn, date_ddmmyyyy, reun_num, course_num):
    course_id = date_ddmmyyyy + "_R" + str(reun_num) + "_C" + str(course_num)
    
    # 1. Partants - 32 valeurs pour 32 colonnes
    try:
        url = BASE_URL + "/programme/" + date_ddmmyyyy + "/R" + str(reun_num) + "/C" + str(course_num) + "/participants?specialisation=INTERNET"
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            participants = data.get('participants', [])
            ecuries = data.get('ecuries', [])
            
            cursor = conn.cursor()
            for ec in ecuries:
                cursor.execute('''
                    INSERT OR IGNORE INTO api_ecuries (nom, casaque_url, data_json)
                    VALUES (?, ?, ?)
                ''', (ec.get('nom'), ec.get('urlCasaque'), json.dumps(ec, ensure_ascii=False)))
            
            for p in participants:
                cursor.execute('''
                    INSERT OR REPLACE INTO api_partants
                    (course_id, numero_pmu, nom, age, sexe, race, statut, corde,
                     oeilleres, proprietaire, entraineur, deferre, driver, driver_change,
                     musique, nb_courses, nb_victoires, nb_places, gains_carriere,
                     pere, mere, ordre_arrivee, engagement, supplement, handicap_distance,
                     poids, temps_obtenu, reduction_km, dernier_rapport_direct,
                     dernier_rapport_reference, avis_entraineur, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    course_id,
                    p.get('numPmu'),
                    p.get('nom'),
                    p.get('age'),
                    p.get('sexe'),
                    p.get('race'),
                    p.get('statut'),
                    p.get('placeCorde'),
                    p.get('oeilleres'),
                    p.get('proprietaire'),
                    p.get('entraineur'),
                    p.get('deferre'),
                    p.get('driver'),
                    p.get('driverChange'),
                    p.get('musique'),
                    p.get('nombreCourses'),
                    p.get('nombreVictoires'),
                    p.get('nombrePlaces'),
                    p.get('gainsParticipant'),
                    p.get('nomPere'),
                    p.get('nomMere'),
                    p.get('ordreArrivee'),
                    p.get('engagement'),
                    p.get('supplement'),
                    p.get('handicapDistance'),
                    p.get('poidsConditionMonteChange'),
                    p.get('tempsObtenu'),
                    p.get('reductionKilometrique'),
                    p.get('dernierRapportDirect'),
                    p.get('dernierRapportReference'),
                    p.get('avisEntraineur'),
                    json.dumps(p, ensure_ascii=False)
                ))
    except Exception as e:
        print("  WARN Partants: " + str(e))
    
    # 2. Rapports
    try:
        url = BASE_URL + "/programme/" + date_ddmmyyyy + "/R" + str(reun_num) + "/C" + str(course_num) + "/rapports-definitifs?specialisation=INTERNET&combinaisonEnTableau=true"
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            rapports = r.json()
            if isinstance(rapports, list):
                cursor = conn.cursor()
                for rap in rapports:
                    conn.cursor().execute('''
                        INSERT OR REPLACE INTO api_rapports
                        (course_id, type_pari, arrivee, arrivee_consolidee, gains_base,
                         gains_ordre, gains_desordre, nb_gagnants, masse_partager,
                         rapports_consolides, risques, data_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        date_ddmmyyyy + "_R" + str(reun_num) + "_C" + str(course_num),
                        rap.get('typePari'),
                        json.dumps(rap.get('arrivee', []), ensure_ascii=False),
                        json.dumps(rap.get('arriveeConsolidee', []), ensure_ascii=False),
                        rap.get('gainsBase'),
                        rap.get('gainsOrdre'),
                        rap.get('gainsDesordre'),
                        rap.get('nbGagnants'),
                        rap.get('massePartager'),
                        json.dumps(rap.get('rapportsConsolides', []), ensure_ascii=False),
                        json.dumps(rap.get('risques', []), ensure_ascii=False),
                        json.dumps(rap, ensure_ascii=False)
                    ))
    except Exception as e:
        print("  WARN Rapports: " + str(e))
    
    # 3. Citations (cotes)
    try:
        url = BASE_URL + "/programme/" + date_ddmmyyyy + "/R" + str(reun_num) + "/C" + str(course_num) + "/citations?paris=&specialisation=INTERNET&combinaisonEnTableau=true"
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            cursor = conn.cursor()
            for cit in data.get('listeCitations', []):
                for p in cit.get('participants', []):
                    cursor.execute('''
                        INSERT INTO api_cotes
                        (course_id, type_pari, numero, cote_directe, masse_enjeu,
                         cote_reference, evolution_cote, risque, updatetime)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        date_ddmmyyyy + "_R" + str(reun_num) + "_C" + str(course_num),
                        cit.get('typePari'),
                        p.get('numero'),
                        p.get('coteDirecte'),
                        p.get('masseEnjeu'),
                        p.get('coteReference'),
                        p.get('evolutionCote'),
                        p.get('risque'),
                        cit.get('updatetime')
                    ))
    except Exception as e:
        print("  WARN Cotes: " + str(e))

    # 4. Pronostics
    try:
        url = BASE_URL + "/programme/" + date_ddmmyyyy + "/R" + str(reun_num) + "/C" + str(course_num) + "/pronostics?commentaire=true"
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            conn.cursor().execute('''
                INSERT OR REPLACE INTO api_pronostics
                (course_id, source, pronostics, nb_partants, data_json)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                date_ddmmyyyy + "_R" + str(reun_num) + "_C" + str(course_num),
                data.get('source', 'PMU'),
                json.dumps(data.get('pronostics', []), ensure_ascii=False),
                data.get('nb_partants'),
                json.dumps(data, ensure_ascii=False)
            ))
    except Exception as e:
        print("  WARN Pronostics: " + str(e))

def sync_meteo(conn, date_ddmmyyyy, hippodrome_codes):
    cursor = conn.cursor()
    for hippo in hippodrome_codes:
        try:
            url = BASE_URL + "/programme/" + date_ddmmyyyy + "/hippodrome/" + hippo + "/meteo"
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                m = r.json()
                # Extraire les valeurs dict -> string
                vent_dir = m.get('vent_direction')
                vent_dir_str = vent_dir.get('text') if isinstance(vent_dir, dict) else str(vent_dir) if vent_dir else None
                condition = m.get('nebulosite_libelle_long')
                condition_str = condition.get('text') if isinstance(condition, dict) else str(condition) if condition else None
                
                conn.cursor().execute('''
                    INSERT OR REPLACE INTO api_meteo
                    (date, hippodrome_code, temperature, vent_force, vent_direction,
                     nebulosite_code, condition, terrain, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_ddmmyyyy, hippo,
                    m.get('temperature'),
                    m.get('vent_force'),
                    vent_dir.get('text') if isinstance(vent_dir, dict) else str(vent_dir) if vent_dir else None,
                    m.get('nebulosite_code'),
                    m.get('nebulosite_libelle_long', {}).get('text') if isinstance(m.get('nebulosite_libelle_long'), dict) else m.get('nebulosite_libelle_long'),
                    m.get('terrain'),
                    json.dumps(m, ensure_ascii=False)
                ))
        except Exception as e:
            print("  WARN Meteo " + hippo + ": " + str(e))

def sync_date_range(start_date, end_date):
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    
    # Recreate tables with correct schema
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS api_partants')
    cursor.execute('''
        CREATE TABLE api_partants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT NOT NULL,
            numero_pmu INTEGER, nom TEXT, age INTEGER, sexe TEXT, race TEXT,
            statut TEXT, corde INTEGER, oeilleres TEXT, proprietaire TEXT,
            entraineur TEXT, deferre TEXT, driver TEXT, driver_change BOOLEAN,
            musique TEXT, nb_courses INTEGER, nb_victoires INTEGER, nb_places INTEGER,
            gains_carriere INTEGER, pere TEXT, mere TEXT, ordre_arrivee INTEGER,
            engagement TEXT, supplement BOOLEAN, handicap_distance INTEGER,
            poids INTEGER, temps_obtenu TEXT, reduction_km TEXT,
            dernier_rapport_direct REAL, dernier_rapport_reference REAL,
            avis_entraineur TEXT, data_json TEXT,
            UNIQUE(course_id, numero_pmu)
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_courses')
    cursor.execute('''
        CREATE TABLE api_courses (
            course_id TEXT PRIMARY KEY,
            date TEXT, reunion INTEGER, course_num INTEGER,
            hippodrome_code TEXT, hippodrome_nom TEXT,
            discipline TEXT, distance INTEGER, type_course TEXT,
            titre TEXT, heure_depart TEXT, partants_declares INTEGER,
            partants_effectifs INTEGER, data_json TEXT,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_rapports')
    cursor.execute('''
        CREATE TABLE api_rapports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, type_pari TEXT, arrivee TEXT,
            arrivee_consolidee TEXT, gains_base REAL, gains_ordre REAL,
            gains_desordre REAL, nb_gagnants INTEGER, masse_partager REAL,
            rapports_consolides TEXT, risques TEXT, data_json TEXT,
            UNIQUE(course_id, type_pari)
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_cotes')
    cursor.execute('''
        CREATE TABLE api_cotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, type_pari TEXT, numero INTEGER,
            cote_directe REAL, masse_enjeu INTEGER, cote_reference REAL,
            evolution_cote REAL, risque REAL, updatetime TEXT,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_meteo')
    cursor.execute('''
        CREATE TABLE api_meteo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL, hippodrome_code TEXT NOT NULL,
            temperature REAL, vent_force REAL, vent_direction TEXT,
            nebulosite_code INTEGER, condition TEXT, terrain TEXT,
            data_json TEXT,
            UNIQUE(date, hippodrome_code)
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_pronostics')
    cursor.execute('''
        CREATE TABLE api_pronostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, source TEXT, pronostics TEXT,
            nb_partants INTEGER, data_json TEXT,
            UNIQUE(course_id, source)
        )
    ''')
    
    cursor.execute('DROP TABLE IF EXISTS api_ecuries')
    cursor.execute('''
        CREATE TABLE api_ecuries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE, casaque_url TEXT, data_json TEXT
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_partants_course ON api_partants(course_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rapports_course ON api_rapports(course_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cotes_course ON api_cotes(course_id)')
    
    conn.commit()
    print("[OK] Base initialisee")
    
    current = start_date
    total_courses = 0
    
    while current <= end_date:
        date_str = current.strftime("%d%m%Y")
        print("\n" + "="*50)
        print("[DATE] SYNC " + current.strftime("%Y-%m-%d") + " (" + current.strftime("%d%m%Y") + ")")
        print("="*50)
        
        nb = sync_programme(conn, current.strftime("%d%m%Y"))
        if nb == 0:
            print("  Aucune course pour " + current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
            continue
        
        cursor = conn.cursor()
        cursor.execute('SELECT course_id, reunion, course_num FROM api_courses WHERE date = ?', (current.strftime("%d%m%Y"),))
        courses = cursor.fetchall()
        
        cursor.execute('SELECT DISTINCT hippodrome_code FROM api_courses WHERE date = ?', (current.strftime("%d%m%Y"),))
        hippos = [row[0] for row in cursor.fetchall() if row[0]]
        
        if hippos:
            sync_meteo(conn, current.strftime("%d%m%Y"), hippos)
        
        for course_id, reun_num, course_num in courses:
            print("  LISTE R" + str(reun_num) + " C" + str(course_num) + "...")
            sync_course_details(conn, current.strftime("%d%m%Y"), reun_num, course_num)
            time.sleep(0.3)
        
        conn.commit()
        print("  OK " + str(len(courses)) + " courses synchronisees")
        
        current += timedelta(days=1)
    
    conn.close()
    print("\n[OK] TERMINE")

if __name__ == "__main__":
    end = date.today()
    start = end - timedelta(days=7)
    
    print("SYNC PMU API -> LOCAL")
    print("   Periode: " + str(start) + " a " + str(end))
    print("   Base: " + str(DB_PATH))
    
    try:
        session.get(BASE_URL + "/programme/11092026?specialisation=INTERNET", timeout=10)
        print("OK API accessible")
    except Exception as e:
        print("ERREUR API inaccessible: " + str(e))
        exit(1)
    
    sync_date_range(start, end)