#!/usr/bin/env python3
"""
Sync complet PMU API -> Base SQLite Locale
Récupère : programme, partants, rapports, cotes, météo, pronostics
Version corrigée avec les bons noms de champs API
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_courses (
            course_id TEXT PRIMARY KEY,
            date TEXT, reunion INTEGER, course_num INTEGER,
            hippodrome_code TEXT, hippodrome_nom TEXT,
            discipline TEXT, distance INTEGER, type_course TEXT,
            titre TEXT, heure_depart TEXT, partants_declares INTEGER,
            partants_effectifs INTEGER, data_json TEXT,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_partants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, numero_pmu INTEGER, nom TEXT, age INTEGER,
            sexe TEXT, race TEXT, statut TEXT, corde INTEGER,
            oeilleres TEXT, proprietaire TEXT, entraineur TEXT,
            deferre TEXT, driver TEXT, driver_change BOOLEAN,
            musique TEXT, nb_courses INTEGER, nb_victoires INTEGER,
            nb_places INTEGER, gains_carriere INTEGER,
            pere TEXT, mere TEXT, ordre_arrivee INTEGER,
            engagement TEXT, supplement BOOLEAN, handicap_distance INTEGER,
            poids INTEGER, temps_obtenu TEXT, reduction_km TEXT,
            dernier_rapport_direct REAL, dernier_rapport_reference REAL,
            avis_entraineur TEXT, data_json TEXT,
            UNIQUE(course_id, numero_pmu)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_rapports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, type_pari TEXT, arrivee TEXT,
            arrivee_consolidee TEXT, gains_base REAL, gains_ordre REAL,
            gains_desordre REAL, nb_gagnants INTEGER, masse_partager REAL,
            rapports_consolides TEXT, risques TEXT, data_json TEXT,
            UNIQUE(course_id, type_pari)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_cotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, type_pari TEXT, numero INTEGER,
            cote_directe REAL, masse_enjeu INTEGER, cote_reference REAL,
            evolution_cote REAL, risque REAL, updatetime TEXT,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_meteo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, hippodrome_code TEXT, temperature REAL,
            vent_force REAL, vent_direction TEXT, nebulosite_code INTEGER,
            condition TEXT, terrain TEXT, data_json TEXT,
            UNIQUE(date, hippodrome_code)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_pronostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, source TEXT, pronostics TEXT,
            nb_partants INTEGER, data_json TEXT,
            UNIQUE(course_id, source)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_ecuries (
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

def ms_to_time(ms):
    """Convertit timestamp ms en HH:MM"""
    if not ms:
        return None
    try:
        dt = datetime.fromtimestamp(ms / 1000)
        return dt.strftime("%H:%M")
    except:
        return None

def sync_programme(conn, date_ddmmyyyy):
    cursor = conn.cursor()
    url = f"{BASE_URL}/programme/{date_ddmmyyyy}?specialisation=INTERNET"
    
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return 0
        
        data = r.json()
        prog = safe_get(data, 'programme', default={})
        reunions = safe_get(prog, 'reunions', default=[])
        
        count = 0
        for reun in reunions:
            reun_num = safe_get(reun, 'numOfficiel')
            if not reun_num:
                continue
                
            hippodrome = safe_get(reun, 'hippodrome', default={})
            hippo_code = safe_get(hippodrome, 'code')
            hippo_nom = safe_get(hippodrome, 'libelle')
            date_reunion_ts = safe_get(reun, 'dateReunion')
            if date_reunion_ts:
                date_reunion = datetime.fromtimestamp(date_reunion_ts / 1000).strftime("%d%m%Y")
            else:
                date_reunion = date_ddmmyyyy
            
            courses = safe_get(reun, 'courses', default=[])
            for course in courses:
                course_num = safe_get(course, 'numOrdre')
                if not course_num:
                    continue
                    
                course_id = f"{date_reunion}_R{reun_num}_C{course_num}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO api_courses
                    (course_id, date, reunion, course_num, hippodrome_code, hippodrome_nom,
                     discipline, distance, type_course, titre, heure_depart,
                     partants_declares, partants_effectifs, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    course_id,
                    date_reunion,
                    reun_num,
                    safe_get(course, 'numOrdre'),
                    hippo_code,
                    safe_get(course, 'hippodrome', 'libelle') or hippo_nom,
                    safe_get(course, 'discipline'),
                    safe_get(course, 'distance'),
                    safe_get(course, 'specialite'),
                    safe_get(course, 'libelle') or safe_get(course, 'libelleCourt'),
                    ms_to_time(safe_get(course, 'heureDepart')),
                    safe_get(course, 'nombreDeclaresPartants'),
                    safe_get(course, 'participants', default=[]).__len__(),
                    json.dumps(safe_get(course, default={}), ensure_ascii=False)
                ))
                count += 1
        
        return count
    
    except Exception as e:
        print("  ERREUR programme: " + str(e))
        return 0

def sync_course_details(conn, date_ddmmyyyy, reun_num, course_num):
    cursor = conn.cursor()
    course_id = f"{date_ddmmyyyy}_R{reun_num}_C{course_num}"
    
    # 1. Partants
    try:
        url = f"{BASE_URL}/programme/{date_ddmmyyyy}/R{reun_num}/C{course_num}/participants?specialisation=INTERNET"
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            participants = safe_get(data, 'participants', default=[])
            ecuries = safe_get(data, 'ecuries', default=[])
            
            for ec in ecuries:
                cursor.execute('''
                    INSERT OR IGNORE INTO api_ecuries (nom, casaque_url, data_json)
                    VALUES (?, ?, ?)
                ''', (safe_get(ec, 'nom'), safe_get(ec, 'urlCasaque'), json.dumps(ec, ensure_ascii=False)))
            
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
                    safe_get(p, 'numPmu'),
                    safe_get(p, 'nom'),
                    safe_get(p, 'age'),
                    safe_get(p, 'sexe'),
                    safe_get(p, 'race'),
                    safe_get(p, 'statut'),
                    safe_get(p, 'placeCorde'),
                    safe_get(p, 'oeilleres'),
                    safe_get(p, 'proprietaire'),
                    safe_get(p, 'entraineur'),
                    safe_get(p, 'deferre'),
                    safe_get(p, 'driver'),
                    safe_get(p, 'driverChange'),
                    safe_get(p, 'musique'),
                    safe_get(p, 'nombreCourses'),
                    safe_get(p, 'nombreVictoires'),
                    safe_get(p, 'nombrePlaces'),
                    safe_get(p, 'gainsParticipant'),
                    safe_get(p, 'nomPere'),
                    safe_get(p, 'nomMere'),
                    safe_get(p, 'ordreArrivee'),
                    safe_get(p, 'engagement'),
                    safe_get(p, 'supplement'),
                    safe_get(p, 'handicapDistance'),
                    safe_get(p, 'poidsConditionMonteChange'),  # poids
                    safe_get(p, 'tempsObtenu'),
                    safe_get(p, 'reductionKilometrique'),
                    safe_get(p, 'dernierRapportDirect'),
                    safe_get(p, 'dernierRapportReference'),
                    safe_get(p, 'avisEntraineur'),
                    json.dumps(p, ensure_ascii=False)
                ))
    except Exception as e:
        print("  WARN Partants: " + str(e))
    
    # 2. Rapports
    try:
        url = f"{BASE_URL}/programme/{date_ddmmyyyy}/R{reun_num}/C{course_num}/rapports-definitifs?specialisation=INTERNET&combinaisonEnTableau=true"
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            rapports = r.json()
            if isinstance(rapports, list):
                for rap in rapports:
                    cursor.execute('''
                        INSERT OR REPLACE INTO api_rapports
                        (course_id, type_pari, arrivee, arrivee_consolidee, gains_base,
                         gains_ordre, gains_desordre, nb_gagnants, masse_partager,
                         rapports_consolides, risques, data_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        course_id,
                        safe_get(rap, 'typePari'),
                        json.dumps(safe_get(rap, 'arrivee', default=[]), ensure_ascii=False),
                        json.dumps(safe_get(rap, 'arriveeConsolidee', default=[]), ensure_ascii=False),
                        safe_get(rap, 'gainsBase'),
                        safe_get(rap, 'gainsOrdre'),
                        safe_get(rap, 'gainsDesordre'),
                        safe_get(rap, 'nbGagnants'),
                        safe_get(rap, 'massePartager'),
                        json.dumps(safe_get(rap, 'rapportsConsolides', default=[]), ensure_ascii=False),
                        json.dumps(safe_get(rap, 'risques', default=[]), ensure_ascii=False),
                        json.dumps(rap, ensure_ascii=False)
                    ))
    except Exception as e:
        print("  WARN Rapports: " + str(e))
    
    # 3. Citations (cotes)
    try:
        url = f"{BASE_URL}/programme/{date_ddmmyyyy}/R{reun_num}/C{course_num}/citations?paris=&specialisation=INTERNET&combinaisonEnTableau=true"
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            for cit in safe_get(data, 'listeCitations', default=[]):
                for p in safe_get(cit, 'participants', default=[]):
                    cursor.execute('''
                        INSERT INTO api_cotes
                        (course_id, type_pari, numero, cote_directe, masse_enjeu,
                         cote_reference, evolution_cote, risque, updatetime)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        course_id,
                        safe_get(cit, 'typePari'),
                        safe_get(p, 'numero'),
                        safe_get(p, 'coteDirecte'),
                        safe_get(p, 'masseEnjeu'),
                        safe_get(p, 'coteReference'),
                        safe_get(p, 'evolutionCote'),
                        safe_get(p, 'risque'),
                        safe_get(cit, 'updatetime')
                    ))
    except Exception as e:
        print("  WARN Cotes: " + str(e))

    # 4. Pronostics
    try:
        url = f"{BASE_URL}/programme/{date_ddmmyyyy}/R{reun_num}/C{course_num}/pronostics?commentaire=true"
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            cursor.execute('''
                INSERT OR REPLACE INTO api_pronostics
                (course_id, source, pronostics, nb_partants, data_json)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                course_id,
                safe_get(data, 'source', 'PMU'),
                json.dumps(safe_get(data, 'pronostics', default=[]), ensure_ascii=False),
                safe_get(data, 'nb_partants'),
                json.dumps(data, ensure_ascii=False)
            ))
    except Exception as e:
        print("  WARN Pronostics: " + str(e))

def sync_meteo(conn, date_ddmmyyyy, hippodrome_codes):
    cursor = conn.cursor()
    for hippo in hippodrome_codes:
        try:
            url = f"{BASE_URL}/programme/{date_ddmmyyyy}/hippodrome/{hippo}/meteo"
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                m = r.json()
                cursor.execute('''
                    INSERT OR REPLACE INTO api_meteo
                    (date, hippodrome_code, temperature, vent_force, vent_direction,
                     nebulosite_code, condition, terrain, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_ddmmyyyy, hippo,
                    safe_get(m, 'temperature'),
                    safe_get(m, 'vent_force'),
                    safe_get(m, 'vent_direction'),
                    safe_get(m, 'nebulosite_code'),
                    safe_get(m, 'nebulosite_libelle_long'),
                    safe_get(m, 'terrain'),
                    json.dumps(m, ensure_ascii=False)
                ))
        except Exception as e:
            print("  WARN Meteo " + hippo + ": " + str(e))

def sync_date_range(start_date, end_date):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    
    current = start_date
    total_courses = 0
    
    while current <= end_date:
        date_str = current.strftime("%d%m%Y")
        print("\n" + "="*50)
        print("[DATE] SYNC " + current.strftime("%Y-%m-%d") + " (" + date_str + ")")
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