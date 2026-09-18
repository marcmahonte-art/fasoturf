#!/usr/bin/env python3
"""
Sync complet PMU API -> Base SQLite Locale
Récupère : programme, partants, rapports, cotes, météo, pronostics
"""

import sqlite3
import socket
import dns.resolver
import requests
import json
from datetime import datetime, timedelta
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
    
    # Courses (programme)
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
    
    # Partants (chevaux)
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
    
    # Rapports (résultats)
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
    
    # Cotes temps réel
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_cotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, type_pari TEXT, numero INTEGER,
            cote_directe REAL, masse_enjeu INTEGER, cote_reference REAL,
            evolution_cote REAL, risque REAL, updatetime TEXT,
            synced_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Météo
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_meteo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, hippodrome_code TEXT, temperature REAL,
            vent_force REAL, vent_direction TEXT, nebulosite_code INTEGER,
            condition TEXT, terrain TEXT, data_json TEXT,
            UNIQUE(date, hippodrome_code)
        )
    ''')
    
    # Pronostics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_pronostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id TEXT, source TEXT, pronostics TEXT,
            nb_partants INTEGER, data_json TEXT,
            UNIQUE(course_id, source)
        )
    ''')
    
    # Ecuries/Casaques (référence)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_ecuries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE, casaque_url TEXT, data_json TEXT
        )
    ''')
    
    # Index
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_partants_course ON api_partants(course_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rapports_course ON api_rapports(course_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cotes_course ON api_cotes(course_id)')
    
    print("[OK] Base initialisée")

# ==================== HELPERS ====================
def safe_get(d, *keys, default=None):
    """Accès sécurisé imbriqué"""
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k)
        else:
            return default
    return d if d is not None else default

def format_date_ddmmyyyy(date_str):
    """Convertit YYYY-MM-DD -> DDMMYYYY"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d%m%Y")
    except:
        return date_str

# ==================== SYNC FUNCTIONS ====================
def sync_programme(conn, date_ddmmyyyy):
    """Sync programme complet pour une date"""
    cursor = conn.cursor()
    url = f"{BASE_URL}/programme/{date_ddmmyyyy}?specialisation=INTERNET"
    
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            print(f"  [ERREUR] Programme {date_ddmmyyyy}: HTTP {r.status_code}")
            return 0
        
        data = r.json()
        prog = safe_get(data, 'programme', default={})
        reunions = safe_get(prog, 'reunions', default=[])
        
        count = 0
        for reun in reunions:
            reun_num = safe_get(reun, 'numeroReunion')
            hippodrome = safe_get(reun, 'hippodrome', default={})
            hippo_code = safe_get(hippodrome, 'code')
            hippo_nom = safe_get(hippodrome, 'libelle')
            
            courses = safe_get(reun, 'courses', default=[])
            for course in courses:
                course_num = safe_get(course, 'numeroCourse')
                course_id = f"{safe_get(reun, 'dateProgramme', date_ddmmyyyy)}_R{safe_get(reun, 'numeroReunion')}_C{safe_get(course, 'numeroCourse')}"
                
                cursor.execute('''
                    INSERT OR REPLACE INTO api_courses
                    (course_id, date, reunion, course_num, hippodrome_code, hippodrome_nom,
                     discipline, distance, type_course, titre, heure_depart,
                     partants_declares, partants_effectifs, data_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    course_id,
                    safe_get(reun, 'dateProgramme', date_ddmmyyyy),
                    safe_get(reun, 'numeroReunion'),
                    safe_get(course, 'numeroCourse'),
                    safe_get(reun, 'hippodrome', 'code'),
                    safe_get(reun, 'hippodrome', 'libelle'),
                    safe_get(course, 'libelleDiscipline'),
                    safe_get(course, 'distance'),
                    safe_get(course, 'typeCourse'),
                    safe_get(course, 'libelleCourse'),
                    safe_get(course, 'heureDepart'),
                    safe_get(course, 'nombreDeclares'),
                    safe_get(course, 'nombrePartants'),
                    json.dumps(safe_get(course, default={}), ensure_ascii=False)
                ))
                count += 1
        
        return len(safe_get(reun, 'courses', default=[])) if reunions else 0
    
    except Exception as e:
        print(f"  [ERREUR] Erreur programme {date_ddmmyyyy}: {e}")
        return 0

def sync_course_details(conn, date_ddmmyyyy, reun_num, course_num):
    """Sync partants, rapports, cotes pour une course"""
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
            
            # Ecuries
            for ec in safe_get(data, 'ecuries', default=[]):
                cursor.execute('''
                    INSERT OR IGNORE INTO api_ecuries (nom, casaque_url, data_json)
                    VALUES (?, ?, ?)
                ''', (safe_get(ec, 'nom'), safe_get(ec, 'urlCasaque'), json.dumps(ec, ensure_ascii=False)))
            
            # Partants
            for p in safe_get(data, 'participants', default=[]):
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
                    safe_get(p, 'poidsConditionMonteChange'),
                    safe_get(p, 'tempsObtenu'),
                    safe_get(p, 'reductionKilometrique'),
                    safe_get(p, 'dernierRapportDirect'),
                    safe_get(p, 'dernierRapportReference'),
                    safe_get(p, 'avisEntraineur'),
                    json.dumps(p, ensure_ascii=False)
                ))
    except Exception as e:
        print(f"  [WARN] Partants: {e}")
    
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
        print(f"  [WARN] Rapports: {e}")
    
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
        print(f"  [WARN] Cotes: {e}")

    # 4. Pronostics
    try:
        url = f"{BASE_URL}/programme/{date_ddmmyyyy}/R{reun_num}/C{safe_get(course_num)}/pronostics?commentaire=true"
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
        print(f"  [WARN] Pronostics: {e}")

def sync_meteo(conn, date_ddmmyyyy, hippodrome_codes):
    """Sync météo pour les hippodromes du jour"""
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
            print(f"  [WARN] Météo {hippo}: {e}")

# ==================== MAIN SYNC ====================
def sync_date_range(start_date, end_date):
    """Sync pour une plage de dates"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    init_db(conn)
    
    current = start_date
    total_courses = 0
    
    while current <= end_date:
        date_str = current.strftime("%d%m%Y")
        print(f"\n{'='*50}")
        print(f"[DATE] SYNC {current.strftime('%Y-%m-%d')} ({date_str})")
        print(f"{'='*50}")
        
        # 1. Programme
        nb = sync_programme(conn, current.strftime("%d%m%Y"))
        if nb == 0:
            print(f"  Aucune course pour {current.strftime('%Y-%m-%d')}")
            current += timedelta(days=1)
            continue
        
        # Récupérer les courses créées
        cursor = conn.cursor()
        cursor.execute('SELECT course_id, reunion, course_num FROM api_courses WHERE date = ?', (current.strftime("%d%m%Y"),))
        courses = cursor.fetchall()
        
        # Récupérer hippodromes uniques pour météo
        cursor.execute('SELECT DISTINCT hippodrome_code FROM api_courses WHERE date = ?', (current.strftime("%d%m%Y"),))
        hippos = [row[0] for row in cursor.fetchall() if row[0]]
        
        # 2. Météo
        if hippos:
            sync_meteo(conn, current.strftime("%d%m%Y"), hippos)
        
        # 3. Détails par course
        for course_id, reun_num, course_num in courses:
            print(f"  [LISTE] R{reun_num} C{course_num}...")
            sync_course_details(conn, current.strftime("%d%m%Y"), reun_num, course_num)
            total_courses += 1
            time.sleep(0.3)  # Rate limiting
        
        conn.commit()
        print(f"  [OK] {len(courses)} courses synchronisées")
        
        current += timedelta(days=1)
    
    conn.close()
    print(f"\n[OK] TERMINÉ - {total_courses} courses totales synchronisées")

# ==================== MAIN ====================
if __name__ == "__main__":
    import time
    from datetime import date
    
    # Par défaut : derniers 7 jours + aujourd'hui + 2 jours
    end = date.today()
    start = end - timedelta(days=7)
    
    print("SYNC PMU API -> LOCAL")
    print(f"   Periode: {start} a {end}")
    print(f"   Base: {DB_PATH}")
    
    # Test rapide de connectivite
    try:
        session.get(f"{BASE_URL}/programme/11092026?specialisation=INTERNET", timeout=10)
        print("OK API accessible")
    except Exception as e:
        print(f"ERREUR API inaccessible: {e}")
        exit(1)
    
    sync_date_range(start, end)