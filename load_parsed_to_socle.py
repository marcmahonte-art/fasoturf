#!/usr/bin/env python3
"""
Charge les JSON parsés (all_parsed.json, rep_parsed.json, ecd_parsed.json)
dans la base socle SQLite (pmu_lonab.db).
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

PROCESSED_DIR = Path(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed")
SOCLE_DB = Path(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db")

FILES = {
    "all_parsed": "all_parsed.json",
    "rep_parsed": "rep_parsed.json",
    "ecd_parsed": "ecd_parsed.json",
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_existing_filenames(conn, table):
    try:
        return {row[0] for row in conn.execute(f"SELECT filename FROM {table}")}
    except sqlite3.Error:
        return set()

def get_nested(obj, key, subkey, default=''):
    val = obj.get(key, {})
    if isinstance(val, dict):
        return val.get(subkey, default)
    return obj.get(f"{key}_{subkey}", default)

def get_nested_opt(obj, key, subkey, default=None):
    val = obj.get(key, {})
    if isinstance(val, dict):
        return val.get(subkey, default)
    return obj.get(f"{key}_{subkey}", default)

def load_all_parsed(conn, data):
    existing_docs = get_existing_filenames(conn, "documents")
    existing_courses = get_existing_filenames(conn, "courses")
    existing_partants = get_existing_filenames(conn, "partants")
    existing_resultats = get_existing_filenames(conn, "resultats")
    existing_media = get_existing_filenames(conn, "media_selections")
    existing_classements = get_existing_filenames(conn, "classements")
    existing_commentaires = get_existing_filenames(conn, "commentaires")
    
    new_docs = 0
    new_courses = 0
    new_partants = 0
    new_resultats = 0
    new_media = 0
    new_classements = 0
    new_commentaires = 0
    
    for d in data:
        filename = d['filename']
        
        # 1. Documents
        if filename not in existing_docs:
            conn.execute("""
                INSERT INTO documents (filename, doc_type, date_publication, pages, raw_text)
                VALUES (?, ?, ?, ?, ?)
            """, (
                filename,
                d.get('doc_type'),
                d.get('date_publication'),
                d.get('pages'),
                d.get('raw_text', '')[:10000] if d.get('raw_text') else None
            ))
            doc_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            new_docs += 1
        else:
            row = conn.execute("SELECT id FROM documents WHERE filename = ?", (filename,)).fetchone()
            doc_id = row[0] if row else None
        
        if not doc_id:
            continue
            
        # 2. Courses
        if filename not in existing_courses:
            for c in d.get('courses', []):
                dist = c.get('distance')
                if isinstance(dist, dict):
                    dist_raw = dist.get('raw', '')
                    dist_m = dist.get('meters')
                else:
                    dist_raw = str(dist) if dist else ''
                    dist_m = None
                    
                mont = c.get('montant')
                if isinstance(mont, dict):
                    mont_raw = mont.get('raw', '')
                    mont_euros = mont.get('euros')
                else:
                    mont_raw = str(mont) if mont else ''
                    mont_euros = None
                
                conn.execute("""
                    INSERT INTO courses (document_id, course_id, date, reunion, course_num,
                                       hippodrome, discipline, distance_raw, distance_m,
                                       montant_raw, montant_euros, partants_declares, partants_effectifs,
                                       type_course, titre, heure_depart, heure_arret_jeux, raw_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    c.get('course_id', ''),
                    c.get('date'),
                    c.get('reunion', ''),
                    c.get('course_num', 0),
                    c.get('hippodrome'),
                    c.get('discipline'),
                    dist_raw,
                    dist_m,
                    mont_raw,
                    mont_euros,
                    c.get('partants_declares'),
                    c.get('partants_effectifs'),
                    c.get('type_course'),
                    c.get('titre'),
                    c.get('heure_depart'),
                    c.get('heure_arret_jeux'),
                    c.get('raw_text', '')[:10000] if c.get('raw_text') else None
                ))
            new_courses += 1
        
        # 3. Partants
        if filename not in existing_partants:
            for p in d.get('partants', []):
                conn.execute("""
                    INSERT INTO partants (document_id, course_id, numero, nom_cheval_raw, nom_cheval_normalized,
                                        sexe, age, poids, corde, distance_raw, distance_m,
                                        chrono_raw, chrono_normalized, performances_raw,
                                        performances_structured, gains_raw, gains_euros,
                                        driver_raw, driver_normalized, entraineur_raw,
                                        entraineur_normalized, proprietaire_raw,
                                        proprietaire_normalized, cote_raw, cote_decimale,
                                        commentaire, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    p.get('course_id', ''),
                    p.get('numero'),
                    get_nested(p, 'nom_cheval', 'raw', p.get('nom_cheval_raw', '')),
                    get_nested(p, 'nom_cheval', 'normalized', p.get('nom_cheval_normalized', '')),
                    p.get('sexe'),
                    p.get('age'),
                    p.get('poids'),
                    p.get('corde'),
                    get_nested(p, 'distance', 'raw', p.get('distance_raw', '')),
                    get_nested_opt(p, 'distance', 'meters', p.get('distance_m')),
                    get_nested(p, 'chrono', 'raw', p.get('chrono_raw', '')),
                    get_nested(p, 'chrono', 'normalized', p.get('chrono_normalized', '')),
                    get_nested(p, 'performances', 'raw', p.get('performances_raw', '')),
                    json.dumps(get_nested(p, 'performances', 'structured', p.get('performances_structured', [])), ensure_ascii=False) if get_nested(p, 'performances', 'structured', p.get('performances_structured', [])) else None,
                    get_nested(p, 'gains', 'raw', p.get('gains_raw', '')),
                    get_nested_opt(p, 'gains', 'euros', p.get('gains_euros')),
                    get_nested(p, 'driver', 'raw', p.get('driver_raw', '')),
                    get_nested(p, 'driver', 'normalized', p.get('driver_normalized', '')),
                    get_nested(p, 'entraineur', 'raw', p.get('entraineur_raw', '')),
                    get_nested(p, 'entraineur', 'normalized', p.get('entraineur_normalized', '')),
                    get_nested(p, 'proprietaire', 'raw', p.get('proprietaire_raw', '')),
                    get_nested(p, 'proprietaire', 'normalized', p.get('proprietaire_normalized', '')),
                    get_nested(p, 'cote', 'raw', p.get('cote_raw', '')),
                    get_nested_opt(p, 'cote', 'decimale', p.get('cote_decimale')),
                    p.get('commentaire'),
                    json.dumps(p.get('raw_data', {}), ensure_ascii=False) if p.get('raw_data') else None
                ))
            new_partants += 1
        
        # 4. Resultats
        if filename not in existing_resultats:
            r = d.get('resultat')
            if r:
                # Debug: build values tuple first
                vals = (
                    doc_id, r.get('course_id', ''), r.get('date'), r.get('type_pari'),
                    json.dumps(r.get('arrivee', []), ensure_ascii=False),
                    json.dumps(r.get('arrivee_complete', []), ensure_ascii=False),
                    r.get('npo'), r.get('np'),
                    json.dumps(r.get('disqualifies', []), ensure_ascii=False),
                    json.dumps(r.get('non_partants', []), ensure_ascii=False),
                    get_nested(r, 'gains_ordre', 'raw', r.get('gains_ordre_raw', '')),
                    get_nested_opt(r, 'gains_ordre', 'euros', r.get('gains_ordre_euros')),
                    get_nested(r, 'gains_desordre', 'raw', r.get('gains_desordre_raw', '')),
                    get_nested_opt(r, 'gains_desordre', 'euros', r.get('gains_desordre_euros')),
                    get_nested(r, 'gains_bonus', 'raw', r.get('gains_bonus_raw', '')),
                    get_nested_opt(r, 'gains_bonus', 'euros', r.get('gains_bonus_euros')),
                    r.get('nb_gagnants_ordre'), r.get('nb_gagnants_desordre'), r.get('nb_gagnants_bonus'),
                    get_nested(r, 'masse_partager', 'raw', r.get('masse_partager_raw', '')),
                    get_nested_opt(r, 'masse_partager', 'euros', r.get('masse_partager_euros')),
                    get_nested(r, 'rapports', 'gagnant', {}).get('raw', r.get('rapport_gagnant_raw', '')) if isinstance(r.get('rapports'), dict) else r.get('rapport_gagnant_raw', ''),
                    get_nested(r, 'rapports', 'gagnant', {}).get('euros', r.get('gains_ordre_euros')) if isinstance(r.get('rapports'), dict) else r.get('gains_ordre_euros'),
                    get_nested(r, 'rapports', 'place_a', {}).get('raw', r.get('rapport_place_a_raw', '')) if isinstance(r.get('rapports'), dict) else r.get('rapport_place_a_raw', ''),
                    get_nested(r, 'rapports', 'place_a', {}).get('euros', r.get('gains_ordre_euros')) if isinstance(r.get('rapports'), dict) else r.get('gains_ordre_euros'),
                    get_nested(r, 'rapports', 'place_b', {}).get('raw', r.get('rapport_place_b_raw', '')) if isinstance(r.get('rapports'), dict) else r.get('rapport_place_b_raw', ''),
                    get_nested(r, 'rapports', 'place_b', {}).get('euros', r.get('gains_ordre_euros')) if isinstance(r.get('rapports'), dict) else r.get('gains_ordre_euros'),
                    get_nested(r, 'map_paris', 'raw', r.get('map_paris_raw', '')),
                    get_nested_opt(r, 'map_paris', 'euros', r.get('map_paris_euros')),
                    r.get('raw_text', '')[:10000] if r.get('raw_text') else None
                )
                print(f"DEBUG: resultats values count = {len(vals)}")
                cols = 30
                ph = ', '.join(['?'] * cols)
                sql = f"""
                    INSERT INTO resultats (document_id, course_id, date, type_pari, arrivee, arrivee_complete,
                                         npo, np, disqualifies, non_partants,
                                         gains_ordre_raw, gains_ordre_euros, gains_desordre_raw,
                                         gains_desordre_euros, gains_bonus_raw, gains_bonus_euros,
                                         nb_gagnants_ordre, nb_gagnants_desordre, nb_gagnants_bonus,
                                         masse_partager_raw, masse_partager_euros,
                                         rapport_gagnant_raw, rapport_gagnant_euros,
                                         rapport_place_a_raw, rapport_place_a_euros,
                                         rapport_place_b_raw, rapport_place_b_euros,
                                         map_paris_raw, map_paris_euros, raw_text)
                    VALUES ({ph})
                """
                print(f"DEBUG: SQL placeholders = {sql.count('?')}")
                conn.execute(sql, vals)
                new_resultats += 1
        
        # 5. Media selections
        if filename not in existing_media:
            for m in d.get('media_selections', []):
                conn.execute("""
                    INSERT INTO media_selections (document_id, course_id, source, selection, rang)
                    VALUES (?, ?, ?, ?, ?)
                """, (doc_id, m.get('course_id'), m.get('source'),
                      json.dumps(m.get('selection', []), ensure_ascii=False),
                      json.dumps(m.get('rang', []), ensure_ascii=False)))
            new_media += 1
        
        # 6. Classements
        if filename not in existing_classements:
            for c in d.get('classements', []):
                conn.execute("""
                    INSERT INTO classements (document_id, course_id, forme, classe, progres, regularite)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (doc_id, c.get('course_id'),
                      json.dumps(c.get('forme', []), ensure_ascii=False),
                      json.dumps(c.get('classe', []), ensure_ascii=False),
                      json.dumps(c.get('progres', []), ensure_ascii=False),
                      json.dumps(c.get('regularite', []), ensure_ascii=False)))
            new_classements += 1
        
        # 7. Commentaires
        if filename not in existing_commentaires:
            for c in d.get('commentaires', []):
                conn.execute("""
                    INSERT INTO commentaires (document_id, course_id, numero_cheval, texte)
                    VALUES (?, ?, ?, ?)
                """, (doc_id, c.get('course_id'), c.get('numero_cheval'), c.get('texte')))
            new_commentaires += 1
    
    if new_docs: log(f"  documents: +{new_docs}")
    if new_courses: log(f"  courses: +{new_courses}")
    if new_partants: log(f"  partants: +{new_partants}")
    if new_resultats: log(f"  resultats: +{new_resultats}")
    if new_media: log(f"  media_selections: +{new_media}")
    if new_classements: log(f"  classements: +{new_classements}")
    if new_commentaires: log(f"  commentaires: +{new_commentaires}")
    
    return new_docs + new_courses + new_partants + new_resultats + new_media + new_classements + new_commentaires

def load_rep_parsed(conn, data):
    existing_docs = get_existing_filenames(conn, "documents")
    existing_rep = {row[0] for row in conn.execute("SELECT document_id FROM rep_documents")}
    
    new_docs = 0
    new_rep = 0
    
    for d in data:
        filename = d['filename']
        
        if filename not in existing_docs:
            conn.execute("""
                INSERT INTO documents (filename, doc_type, date_publication, pages, raw_text)
                VALUES (?, ?, ?, ?, ?)
            """, (
                filename,
                d.get('doc_type'),
                d.get('date_publication'),
                d.get('pages'),
                d.get('raw_text', '')[:10000] if d.get('raw_text') else None
            ))
            doc_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            new_docs += 1
        else:
            row = conn.execute("SELECT id FROM documents WHERE filename = ?", (filename,)).fetchone()
            doc_id = row[0] if row else None
        
        if not doc_id:
            continue
            
        if doc_id not in existing_rep:
            rep = d.get('rep_document')
            if rep:
                conn.execute("""
                    INSERT INTO rep_documents (document_id, document_type, date_document, date_document_raw,
                                             date_course_cible, date_course_cible_raw,
                                             game_type, report_ordre_raw, report_ordre_euros,
                                             tierce_v_raw, tierce_v_value, raw_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    rep.get('document_type'), rep.get('date_document'), rep.get('date_document_raw'),
                    rep.get('date_course_cible'), rep.get('date_course_cible_raw'),
                    rep.get('game_type'), rep.get('report_ordre_raw'), rep.get('report_ordre_euros'),
                    rep.get('tierce_v_raw'), rep.get('tierce_v_value'),
                    rep.get('raw_text', '')[:10000] if rep.get('raw_text') else None
                ))
                new_rep += 1
    
    if new_docs: log(f"  documents (rep): +{new_docs}")
    if new_rep: log(f"  rep_documents: +{new_rep}")
    return new_docs + new_rep

def load_ecd_parsed(conn, data):
    existing_docs = get_existing_filenames(conn, "documents")
    existing_ecd = {row[0] for row in conn.execute("SELECT document_id FROM ecd_documents")}
    
    new_docs = 0
    new_ecd = 0
    
    for d in data:
        filename = d['filename']
        
        if filename not in existing_docs:
            conn.execute("""
                INSERT INTO documents (filename, doc_type, date_publication, pages, raw_text)
                VALUES (?, ?, ?, ?, ?)
            """, (
                filename,
                d.get('doc_type'),
                d.get('date_publication'),
                d.get('pages'),
                d.get('raw_text', '')[:10000] if d.get('raw_text') else None
            ))
            doc_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            new_docs += 1
        else:
            row = conn.execute("SELECT id FROM documents WHERE filename = ?", (filename,)).fetchone()
            doc_id = row[0] if row else None
        
        if not doc_id:
            continue
            
        if doc_id not in existing_ecd:
            ecd = d.get('ecd_document')
            if ecd:
                conn.execute("""
                    INSERT INTO ecd_documents (document_id, date, reunion, hippodrome, discipline, date_heure_extraction, raw_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    ecd.get('date'), ecd.get('reunion'), ecd.get('hippodrome'),
                    ecd.get('discipline'), ecd.get('date_heure_extraction'),
                    ecd.get('raw_text', '')[:10000] if ecd.get('raw_text') else None
                ))
                ecd_doc_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                
                for c in d.get('courses', []):
                    arrivee = c.get('arrivee', {})
                    conn.execute("""
                        INSERT INTO ecd_courses (ecd_document_id, course_id, document_id,
                                               numero_course, arrivee_raw, arrivee_positions,
                                               gains_total_raw, gains_total_euros, raw_text)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ecd_doc_id, c.get('course_id'), c.get('document_id'),
                        c.get('numero_course'),
                        arrivee.get('arrivee_raw') if arrivee else None,
                        json.dumps(arrivee.get('positions', []), ensure_ascii=False) if arrivee else None,
                        arrivee.get('gains_total_raw') if arrivee else None,
                        arrivee.get('gains_total_euros') if arrivee else None,
                        c.get('raw_text', '')[:10000] if c.get('raw_text') else None
                    ))
                    ecd_course_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    
                    for p in c.get('paris', []):
                        conn.execute("""
                            INSERT INTO ecd_paris (ecd_course_id, type_pari, combinaison_raw,
                                                 combinaison_normalized, montant_raw, montant_euros,
                                                 nb_paris, position, uncertain)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            ecd_course_id, p.get('type_pari'),
                            p.get('combinaison_raw'),
                            json.dumps(p.get('combinaison_normalized', []), ensure_ascii=False),
                            p.get('montant_raw'), p.get('montant_euros'),
                            p.get('nb_paris'), p.get('position'), p.get('uncertain', False)
                        ))
                new_ecd += 1
    
    if new_docs: log(f"  documents (ecd): +{new_docs}")
    if new_ecd: log(f"  ecd_documents: +{new_ecd}")
    return new_docs + new_ecd

def main():
    log("=" * 60)
    log("CHARGEMENT JSON PARSÉS -> SOCLE DB")
    log("=" * 60)
    
    if not SOCLE_DB.exists():
        log(f"ERREUR: Base socle introuvable: {SOCLE_DB}")
        return 1
    
    conn = sqlite3.connect(str(SOCLE_DB))
    conn.execute("PRAGMA foreign_keys = ON")
    
    total_new = 0
    
    f = PROCESSED_DIR / FILES["all_parsed"]
    if f.exists():
        log(f"Chargement: {f.name}")
        with open(f, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        total_new += load_all_parsed(conn, data)
    else:
        log(f"  Fichier absent: {f.name}")
    
    f = PROCESSED_DIR / FILES["rep_parsed"]
    if f.exists():
        log(f"Chargement: {f.name}")
        with open(f, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        total_new += load_rep_parsed(conn, data)
    else:
        log(f"  Fichier absent: {f.name}")
    
    f = PROCESSED_DIR / FILES["ecd_parsed"]
    if f.exists():
        log(f"Chargement: {f.name}")
        with open(f, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        total_new += load_ecd_parsed(conn, data)
    else:
        log(f"  Fichier absent: {f.name}")
    
    conn.commit()
    conn.close()
    
    log("=" * 60)
    log(f"TERMINÉ - {total_new} nouveaux fichiers chargés au total")
    log("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())