"""
Orchestrateur d'enrichissement des données PMU dans la base SQLite.
"""
import sqlite3
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.enrichment.pmu_client import PMUApiClient
from app.enrichment.matcher import PMURaceMatcher

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS partants_enrichis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    nom_cheval_normalized TEXT NOT NULL,
    date_course TEXT NOT NULL,
    reunion_num INTEGER,
    course_num INTEGER,
    numero_pmu INTEGER,
    deferre TEXT,
    musique_officielle TEXT,
    nom_pere TEXT,
    nom_mere TEXT,
    nom_pere_mere TEXT,
    race TEXT,
    robe TEXT,
    oeilleres TEXT,
    gains_carriere_euros INTEGER,
    gains_annee_euros INTEGER,
    gains_victoires_euros INTEGER,
    taux_reclamation INTEGER,
    raw_api_data TEXT,
    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    UNIQUE(nom_cheval_normalized, date_course)
);

CREATE INDEX IF NOT EXISTS idx_enrichis_cheval ON partants_enrichis(nom_cheval_normalized);
CREATE INDEX IF NOT EXISTS idx_enrichis_date ON partants_enrichis(date_course);
"""

class PMUDataEnricher:
    """Gère l'enrichissement des données de la base SQLite via l'API PMU."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.client = PMUApiClient()
        self.matcher = PMURaceMatcher(self.client)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Crée la table partants_enrichis si elle n'existe pas."""
        with self._get_connection() as conn:
            conn.executescript(CREATE_TABLE_SQL)

    @staticmethod
    def _extract_date(filename: str, default_date: Optional[str]) -> Optional[str]:
        if default_date and default_date != '1995-07-18' and len(default_date) == 10:
            return default_date
        m = re.search(r'(\d{2})[-_](\d{2})[-_](\d{4})', filename)
        if m:
            day, month, year = m.groups()
            return f"{year}-{month}-{day}"
        return default_date

    def enrich_date(self, date_str: str) -> Dict[str, Any]:
        """
        Enrichit tous les chevaux d'une date donnée.
        date_str: format 'AAAA-MM-JJ' (ex: '2024-02-11') ou 'JJMMAAAA'.
        """
        # Formater la date en AAAA-MM-JJ
        clean_date = date_str.replace("/", "-")
        if len(clean_date) == 8 and clean_date.isdigit():
            clean_date = f"{clean_date[4:8]}-{clean_date[2:4]}-{clean_date[0:2]}"
        
        with self._get_connection() as conn:
            c = conn.cursor()
            # Trouver les chevaux dans partants pour cette date
            c.execute("""
                SELECT p.id as partant_id, p.document_id, p.numero, p.nom_cheval_normalized,
                       d.filename, d.date_publication, c.hippodrome
                FROM partants p
                JOIN documents d ON p.document_id = d.id
                LEFT JOIN courses c ON p.document_id = c.document_id
                WHERE d.doc_type = 'JOURNAL'
            """)
            all_partants = c.fetchall()

            matching_rows = []
            hippodrome_hint = None
            for p in all_partants:
                d_val = self._extract_date(p['filename'], p['date_publication'])
                if d_val == clean_date:
                    matching_rows.append(p)
                    if p['hippodrome'] and not p['hippodrome'].isdigit():
                        hippodrome_hint = p['hippodrome']

            if not matching_rows:
                return {"status": "not_found", "message": f"Aucun document trouvé pour la date {clean_date}", "enriched": 0}

            lonab_horses = [r["nom_cheval_normalized"] for r in matching_rows]
            doc_id = matching_rows[0]["document_id"]

            # Trouver la course officielle PMU
            match = self.matcher.find_matching_course(clean_date, lonab_horses, hippodrome_hint)
            if not match:
                return {"status": "no_pmu_match", "message": f"Aucune course correspondante trouvée sur le PMU pour le {clean_date}", "enriched": 0}

            r_num, c_num, course_info = match
            participants_data = self.client.get_participants(clean_date, r_num, c_num)
            if not participants_data or "participants" not in participants_data:
                return {"status": "no_participants", "message": "Participants introuvables via l'API", "enriched": 0}

            pmu_parts = participants_data["participants"]
            enriched_count = 0

            for pmu_p in pmu_parts:
                nom = pmu_p.get("nom", "").strip().upper()
                gains = pmu_p.get("gainsParticipant", {})
                
                # Gains en euros (l'API renvoie souvent les gains en centimes)
                gains_carriere = gains.get("gainsCarriere")
                if gains_carriere is not None and gains_carriere > 1000:
                    gains_carriere = gains_carriere // 100
                gains_annee = gains.get("gainsAnneeEnCours")
                if gains_annee is not None and gains_annee > 1000:
                    gains_annee = gains_annee // 100
                gains_vic = gains.get("gainsVictoires")
                if gains_vic is not None and gains_vic > 1000:
                    gains_vic = gains_vic // 100

                c.execute("""
                    INSERT OR REPLACE INTO partants_enrichis (
                        document_id, nom_cheval_normalized, date_course,
                        reunion_num, course_num, numero_pmu,
                        deferre, musique_officielle,
                        nom_pere, nom_mere, nom_pere_mere,
                        race, robe, oeilleres,
                        gains_carriere_euros, gains_annee_euros, gains_victoires_euros,
                        taux_reclamation, raw_api_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    nom,
                    clean_date,
                    r_num,
                    c_num,
                    pmu_p.get("numPmu"),
                    pmu_p.get("deferre"),
                    pmu_p.get("musique"),
                    pmu_p.get("nomPere"),
                    pmu_p.get("nomMere"),
                    pmu_p.get("nomPereMere"),
                    pmu_p.get("race"),
                    pmu_p.get("robe", {}).get("libelleCourt") if isinstance(pmu_p.get("robe"), dict) else pmu_p.get("robe"),
                    pmu_p.get("oeilleres"),
                    gains_carriere,
                    gains_annee,
                    gains_vic,
                    pmu_p.get("tauxReclamation"),
                    json.dumps(pmu_p, ensure_ascii=False)
                ))
                enriched_count += 1

            conn.commit()
            return {
                "status": "success",
                "date": clean_date,
                "reunion": r_num,
                "course": c_num,
                "course_nom": course_info.get("libelle"),
                "enriched": enriched_count
            }

    def enrich_horse(self, horse_name: str) -> Dict[str, Any]:
        """
        Enrichit l'historique de toutes les courses d'un cheval présent dans la base.
        """
        clean_name = horse_name.strip().upper()
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT DISTINCT d.filename, d.date_publication
                FROM partants p
                JOIN documents d ON p.document_id = d.id
                WHERE p.nom_cheval_normalized = ? AND d.doc_type = 'JOURNAL'
            """, (clean_name,))
            rows = c.fetchall()

        if not rows:
            return {"status": "not_found", "message": f"Cheval '{clean_name}' non trouvé dans la base", "courses": 0}

        dates = sorted({self._extract_date(r['filename'], r['date_publication']) for r in rows if r['filename']})
        results = []
        for d in dates:
            if d and d != '1995-07-18':
                res = self.enrich_date(d)
                results.append(res)

        return {
            "status": "success",
            "cheval": clean_name,
            "total_dates": len(dates),
            "details": results
        }

    def enrich_batch(self, limit: int = 10) -> Dict[str, Any]:
        """
        Enrichit les dates non encore traitées (jusqu'à `limit` dates).
        """
        with self._get_connection() as conn:
            c = conn.cursor()
            # Récupérer toutes les dates distinctes des journaux
            c.execute("SELECT DISTINCT filename, date_publication FROM documents WHERE doc_type = 'JOURNAL'")
            doc_rows = c.fetchall()
            
            all_dates = sorted({self._extract_date(r['filename'], r['date_publication']) for r in doc_rows if r['filename']})
            all_dates = [d for d in all_dates if d and d != '1995-07-18']

            # Récupérer les dates déjà enrichies
            c.execute("SELECT DISTINCT date_course FROM partants_enrichis")
            enriched_dates = {r[0] for r in c.fetchall()}

        pending_dates = [d for d in all_dates if d not in enriched_dates][:limit]
        
        success_count = 0
        total_enriched_horses = 0

        for d in pending_dates:
            res = self.enrich_date(d)
            if res.get("status") == "success":
                success_count += 1
                total_enriched_horses += res.get("enriched", 0)

        return {
            "total_pending_processed": len(pending_dates),
            "successful_dates": success_count,
            "total_horses_enriched": total_enriched_horses
        }
