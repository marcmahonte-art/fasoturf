"""
Moteur de prédiction et de pronostics pour les courses Tiercé, Quarté et 4+1 LONAB.
Combine l'activité du jockey (Aspiturf), le déferrage, la musique, et la détection de value.
"""
import sqlite3
import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.prediction.jockey_activity import JockeyActivityCalculator
from app.enrichment.enricher import PMUDataEnricher

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path(r"C:\Users\Lenovo\Desktop\PMU\pmu-lonab-scraper\data\processed\pmu_lonab.db")

class LonabPredictor:
    """Analyseur et générateur de pronostics pour les courses LONAB."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.activity_calc = JockeyActivityCalculator()
        self.enricher = PMUDataEnricher(self.db_path)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _parse_musique(musique_raw: Optional[str]) -> float:
        """Calcule un score de forme entre 0 et 3 d'après les dernières performances."""
        if not musique_raw:
            return 1.0
        # Extraire les chiffres
        digits = [int(x) for x in re.findall(r'\b[0-9]\b', musique_raw)]
        if not digits:
            return 1.0
        # Les 3 premières places donnent des points
        score = 0.0
        for i, pos in enumerate(digits[:4]):
            weight = 1.0 / (i + 1)
            if pos == 1:
                score += 3.0 * weight
            elif pos == 2:
                score += 2.0 * weight
            elif pos == 3:
                score += 1.5 * weight
            elif pos in (4, 5):
                score += 0.8 * weight
            elif pos == 0:
                score -= 0.5 * weight
        return max(0.0, score)

    def predict_race(self, date_str: str) -> Dict[str, Any]:
        """
        Génère une analyse prédictive complète pour la course LONAB d'une date donnée.
        date_str: '2024-02-11' ou '11022024'.
        """
        clean_date = date_str.replace("/", "-").strip()
        if len(clean_date) == 8 and clean_date.isdigit():
            clean_date = f"{clean_date[4:8]}-{clean_date[2:4]}-{clean_date[0:2]}"

        # 1. Vérifier si la date est enrichie dans SQLite, sinon l'enrichir automatiquement
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT count(*) FROM partants_enrichis WHERE date_course = ?", (clean_date,))
            if c.fetchone()[0] == 0:
                logger.info("Enrichissement automatique pour la date %s...", clean_date)
                self.enricher.enrich_date(clean_date)

            # Charger les partants avec jointure sur partants_enrichis et courses
            c.execute("""
                SELECT 
                    p.numero,
                    p.nom_cheval_normalized,
                    p.driver_normalized,
                    p.cote_decimale,
                    p.gains_euros,
                    p.performances_raw,
                    c.hippodrome,
                    c.discipline,
                    c.distance_m,
                    c.titre,
                    pe.deferre,
                    pe.musique_officielle,
                    pe.nom_pere,
                    pe.nom_mere,
                    pe.oeilleres
                FROM partants p
                JOIN documents d ON p.document_id = d.id
                LEFT JOIN courses c ON p.document_id = c.document_id
                LEFT JOIN partants_enrichis pe ON (p.nom_cheval_normalized = pe.nom_cheval_normalized AND pe.date_course = ?)
                WHERE (d.date_publication = ? OR d.filename LIKE ?) AND d.doc_type = 'JOURNAL'
                ORDER BY p.numero ASC
            """, (clean_date, clean_date, f"%{clean_date[8:10]}_{clean_date[5:7]}_{clean_date[0:4]}%"))

            rows = c.fetchall()

            # Si non trouvé par date directe, tenter par correspondance filename
            if not rows:
                c.execute("""
                    SELECT 
                        p.numero, p.nom_cheval_normalized, p.driver_normalized,
                        p.cote_decimale, p.gains_euros, p.performances_raw,
                        c.hippodrome, c.discipline, c.distance_m, c.titre,
                        pe.deferre, pe.musique_officielle, pe.nom_pere, pe.nom_mere, pe.oeilleres
                    FROM partants p
                    JOIN documents d ON p.document_id = d.id
                    LEFT JOIN courses c ON p.document_id = c.document_id
                    LEFT JOIN partants_enrichis pe ON (p.nom_cheval_normalized = pe.nom_cheval_normalized AND pe.date_course = ?)
                    WHERE d.filename LIKE ? AND d.doc_type = 'JOURNAL'
                    ORDER BY p.numero ASC
                """, (clean_date, f"%{clean_date[8:10]}-{clean_date[5:7]}-{clean_date[0:4]}%"))
                rows = c.fetchall()

            # Charger également l'arrivée réelle et rapports si disponibles
            c.execute("""
                SELECT arrivee, non_partants, gains_ordre_euros, gains_desordre_euros, gains_bonus_euros, masse_partager_euros
                FROM resultats r
                JOIN documents d ON r.document_id = d.id
                WHERE d.filename LIKE ? OR r.date = ?
            """, (f"%{clean_date[8:10]}_{clean_date[5:7]}_{clean_date[0:4]}%", clean_date))
            res_row = c.fetchone()
            arrivee_reelle = []
            db_non_partants = []
            rapports_officiels = {}
            if res_row:
                if res_row["arrivee"]:
                    try:
                        arrivee_reelle = json.loads(res_row["arrivee"])
                    except:
                        pass
                if res_row["non_partants"]:
                    try:
                        db_non_partants = json.loads(res_row["non_partants"])
                    except:
                        pass
                rapports_officiels = {
                    "ordre": res_row["gains_ordre_euros"] or 0,
                    "desordre": res_row["gains_desordre_euros"] or 0,
                    "bonus": res_row["gains_bonus_euros"] or 0,
                    "masse": res_row["masse_partager_euros"] or 0
                }

        non_partants_list = list(db_non_partants)

        if not rows:
            # Tenter de charger directement depuis le programme de l'API PMU (courses du jour / futures)
            clean_api_date = f"{clean_date[8:10]}{clean_date[5:7]}{clean_date[0:4]}"
            prog = self.activity_calc.client.get_programme(clean_api_date)
            if prog and "programme" in prog:
                reunions = prog["programme"].get("reunions", [])
                r1 = next((r for r in reunions if r.get("numOfficiel") == 1), reunions[0] if reunions else None)
                if r1:
                    courses = r1.get("courses", [])
                    best_course = max(courses, key=lambda x: (x.get("montantPrix", 0), x.get("nombreDeclaresPartants", 0))) if courses else None
                    if best_course:
                        c_num = best_course.get("numOrdre")
                        parts_data = self.activity_calc.client.get_participants(clean_api_date, r1.get("numOfficiel", 1), c_num)
                        if parts_data and "participants" in parts_data:
                            live_rows = []
                            for p in parts_data["participants"]:
                                is_np = (p.get("statut") == "NON_PARTANT" or p.get("nonPartant") is True)
                                num_pmu = p.get("numPmu")
                                if is_np and num_pmu not in non_partants_list:
                                    non_partants_list.append(num_pmu)

                                cote_val = p.get("dernierRapportDirect", {}).get("rapport") or p.get("dernierRapportReference", {}).get("rapport") or 15.0
                                gains_c = p.get("gainsParticipant", {}).get("gainsCarriere", 0)
                                if gains_c and gains_c > 1000:
                                    gains_c = gains_c // 100
                                live_rows.append({
                                    "numero": num_pmu,
                                    "nom_cheval_normalized": p.get("nom", "").strip().upper(),
                                    "driver_normalized": p.get("driver", "").strip().upper(),
                                    "cote_decimale": float(cote_val),
                                    "gains_euros": gains_c,
                                    "performances_raw": p.get("musique", ""),
                                    "hippodrome": (r1.get("hippodrome", {}).get("libelleCourt") or "PARISLONGCHAMP").upper(),
                                    "discipline": (best_course.get("discipline") or "PLAT").upper(),
                                    "distance_m": best_course.get("distance", 0),
                                    "titre": f"R1C{c_num} - {best_course.get('libelle', '')}",
                                    "deferre": p.get("deferre", ""),
                                    "musique_officielle": p.get("musique", ""),
                                    "nom_pere": p.get("nomPere", ""),
                                    "nom_mere": p.get("nomMere", ""),
                                    "oeilleres": p.get("oeilleres", ""),
                                    "is_non_partant": is_np
                                })
                            rows = live_rows

        if not rows:
            return {"status": "error", "message": f"Aucun partant trouvé pour la date {clean_date}"}

        # Convertir en liste de dictionnaires pour homogénéiser sqlite3.Row et dicts live API
        rows = [dict(r) for r in rows]

        # 2. Calculer l'activité des jockeys sur la journée
        daily_activity = self.activity_calc.get_daily_activity(clean_date)

        # 3. Calculer les scores individuels de chaque cheval
        scored_horses = []
        course_title = rows[0].get("titre") or f"Course du {clean_date}"
        hippodrome = rows[0].get("hippodrome") or "Hippodrome"
        discipline = (rows[0].get("discipline") or "").upper()

        for r in rows:
            num = r["numero"]
            is_np = r.get("is_non_partant", False) or (num in non_partants_list)
            driver_name = r["driver_normalized"] or ""
            montes = self.activity_calc.get_jockey_montes(clean_date, driver_name)
            jockey_prof = self.activity_calc.get_profile(montes)

            # Bonus Jockey
            score_jockey = jockey_prof["score_bonus"]

            # Bonus Déferrage
            deferre = (r["deferre"] or "").upper()
            score_deferre = 0.0
            if "DEFERRE_ANTERIEURS_POSTERIEURS" in deferre or "DEFERRE_DES_4" in deferre:
                score_deferre = 2.5
            elif "POSTERIEURS" in deferre or "ANTERIEURS" in deferre:
                score_deferre = 1.2

            # Score Forme / Musique
            musique_to_use = r["musique_officielle"] or r["performances_raw"] or ""
            score_musique = self._parse_musique(musique_to_use)

            # Score Cote (cote modérée = plus de chance)
            cote = r["cote_decimale"] or 20.0
            prob_marche = min(0.5, 1.0 / cote) if cote > 0 else 0.05
            score_cote = prob_marche * 10.0

            # Score composite total
            total_score = round(score_cote + score_jockey + score_deferre + score_musique, 2)

            # Détection de Value Bet selon le TRJ 65% LONAB
            is_value_outsider = (cote >= 10.0 and (score_jockey >= 2.0 or score_deferre >= 2.0))
            is_fake_favorite = (cote <= 5.0 and score_jockey <= 0.0 and score_deferre == 0.0)

            scored_horses.append({
                "numero": num,
                "nom": r["nom_cheval_normalized"],
                "driver": driver_name,
                "montes_jour": montes,
                "profil_jockey": jockey_prof["profile"],
                "emoji_jockey": jockey_prof["emoji"],
                "score_jockey": score_jockey,
                "deferre": deferre if deferre else "NON_RENSEIGNE",
                "score_deferre": score_deferre,
                "musique": musique_to_use,
                "cote": cote,
                "gains": r["gains_euros"],
                "pere": r["nom_pere"],
                "score_total": total_score,
                "is_value_outsider": is_value_outsider,
                "is_fake_favorite": is_fake_favorite,
                "is_non_partant": is_np
            })

        # Séparer les partants actifs des non-partants
        actifs = [h for h in scored_horses if not h["is_non_partant"]]
        nps = [h["numero"] for h in scored_horses if h["is_non_partant"]]

        # Trier les chevaux actifs par score décroissant
        ranked = sorted(actifs, key=lambda x: x["score_total"], reverse=True)

        # 4. Formuler les sélections selon le règlement PMU'B LONAB
        # A. Tiercé & Quarté
        bases_tierce = ranked[:3]
        selection_quarte = ranked[:4]

        # B. 4+1 Ticket Sécurité (Objectif : Assurer le Désordre et la couverture Bonus 120)
        # Top 5 chevaux les plus réguliers
        ticket_securite_4plus1 = ranked[:5]

        # C. 4+1 Ticket Spéculatif (Objectif : Gros Rapport EV+ face aux 35% de prélèvement LONAB)
        # 3 bases solides + les 2 meilleurs Value Outsiders (ou complétés par les suivants)
        bases_solides = ranked[:3]
        value_outsiders_pool = [h for h in ranked[3:] if h["is_value_outsider"]]
        ticket_speculatif_4plus1 = list(bases_solides)
        if len(value_outsiders_pool) >= 2:
            ticket_speculatif_4plus1.extend(value_outsiders_pool[:2])
        elif len(value_outsiders_pool) == 1:
            ticket_speculatif_4plus1.append(value_outsiders_pool[0])
            for h in ranked[3:]:
                if h not in ticket_speculatif_4plus1:
                    ticket_speculatif_4plus1.append(h)
                    break
        else:
            ticket_speculatif_4plus1 = ranked[:5]

        # D. Cheval de Complément officiel (Recommandation LONAB pour éviter la dégradation en "Venant")
        # Le cheval immédiatement suivant dans le classement IA qui n'est pas dans le ticket sécurité
        cheval_complement = ranked[5]["numero"] if len(ranked) > 5 else None

        # E. Formules Champ Réduit (Bases + Associés)
        # 4+1 en champ réduit : 3 Bases + 3 Associés
        champ_reduit_4plus1 = {
            "bases": [h["numero"] for h in bases_solides],
            "associes": [h["numero"] for h in ranked[3:6]],
            "nb_combinaisons": 3,
            "cout_300fcfa": 900,
            "cout_500fcfa": 1500
        }

        # Tiercé en champ réduit : 2 Bases + 3 Associés
        champ_reduit_tierce = {
            "bases": [h["numero"] for h in ranked[:2]],
            "associes": [h["numero"] for h in ranked[2:5]],
            "nb_combinaisons": 3,
            "cout_300fcfa": 900,
            "cout_500fcfa": 1500
        }

        # F. Analyse d'Espérance de Valeur (EV / TRJ 65%)
        cotes_secu = [h["cote"] for h in ticket_securite_4plus1 if h["cote"] > 0]
        moyenne_cote_secu = round(sum(cotes_secu) / len(cotes_secu), 1) if cotes_secu else 10.0
        
        cotes_spec = [h["cote"] for h in ticket_speculatif_4plus1 if h["cote"] > 0]
        moyenne_cote_spec = round(sum(cotes_spec) / len(cotes_spec), 1) if cotes_spec else 15.0

        if moyenne_cote_secu < 5.0:
            ev_status_secu = "Combinaison très populaire (Risque de faible rapport face au prélèvement de 35%)"
        else:
            ev_status_secu = "Équilibrée régularité (Bonne couverture des 119 désordres + 120 bonus)"

        ev_status_spec = "Optimisée EV+ (Intègre des outsiders déferrés pour battre le prélèvement LONAB)"

        value_outsiders = [h for h in ranked if h["is_value_outsider"]]
        fake_favorites = [h for h in ranked if h["is_fake_favorite"]]

        return {
            "date": clean_date,
            "titre": course_title,
            "hippodrome": hippodrome,
            "discipline": discipline,
            "total_partants": len(ranked),
            "non_partants": nps,
            "cheval_complement": cheval_complement,
            "arrivee_reelle": arrivee_reelle,
            "rapports_officiels": rapports_officiels,
            "classement_ia": ranked,
            "bases_tierce": [h["numero"] for h in bases_tierce],
            "selection_quarte": [h["numero"] for h in selection_quarte],
            "ticket_securite_4plus1": [h["numero"] for h in ticket_securite_4plus1],
            "ticket_speculatif_4plus1": [h["numero"] for h in ticket_speculatif_4plus1],
            "champ_reduit_4plus1": champ_reduit_4plus1,
            "champ_reduit_tierce": champ_reduit_tierce,
            "analyse_trj": {
                "moyenne_cote_securite": moyenne_cote_secu,
                "ev_securite": ev_status_secu,
                "moyenne_cote_speculatif": moyenne_cote_spec,
                "ev_speculatif": ev_status_spec
            },
            "value_outsiders": [h["numero"] for h in value_outsiders],
            "fake_favorites": [h["numero"] for h in fake_favorites]
        }

