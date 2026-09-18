"""
SqliteDataProvider — lit la base réelle existante ``pmu_lonab.db``.

Mapping du schéma source vers le schéma interne
-----------------------------------------------
Le schéma source ne possède pas de clé ``course_id`` exploitable (elle est
vide). La jointure fiable est :

    courses.document_id  ==  partants.document_id     (1 course = 1 document)
    courses.date         ==  resultats.date           (726/734 dates : 1 course)

Vérifié le 2026-09-13 :
    - 726 dates sur 734 ne contiennent qu'une seule course
    - 707 dates disposent d'une arrivée réelle
    => dataset étiqueté réel exploitable pour l'entraînement et le backtest.

IMPORTANT — anti-fuite : ``partants.performances_structured`` est la forme du
cheval **avant** la course (musique). Elle est utilisée comme feature. Le
résultat de la course (``resultats.arrivee``) n'est JAMAIS exposé au moteur de
prédiction ; il n'est lu que par l'évaluateur, après coup.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from ..schema import HistoricalRun, Horse, OddsPoint, Person, Race, RaceResult, Runner


class SqliteDataProvider:
    """Fournisseur branché sur la base SQLite réelle du projet."""

    name = "sqlite"

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base introuvable : {self.db_path}")
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._history_index: dict[str, list[HistoricalRun]] | None = None
        self._race_cache: dict[str, Race] = {}

    # -- Helpers -----------------------------------------------------

    def _query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self._conn.execute(sql, params).fetchall()

    @staticmethod
    def _parse_json_list(raw: str | None) -> list:
        if not raw:
            return []
        try:
            value = json.loads(raw)
            return value if isinstance(value, list) else []
        except (ValueError, TypeError):
            return []

    @staticmethod
    def _parse_gains(raw: str | None) -> float | None:
        if not raw:
            return None
        cleaned = raw.replace("\u202f", "").replace(" ", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _parse_weight(raw: str | None) -> float | None:
        if not raw:
            return None
        cleaned = raw.upper().replace("KG", "").replace(",", ".").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    # -- Index d'historique ------------------------------------------

    def _build_history_index(self) -> dict[str, list[HistoricalRun]]:
        """
        Construit l'historique réel de chaque cheval à partir de ses
        apparitions dans la base, avec la position d'arrivée quand elle est
        connue (jointure par date).
        """
        if self._history_index is not None:
            return self._history_index

        rows = self._query("""
            SELECT p.nom_cheval_normalized AS horse,
                   c.date                 AS date,
                   c.hippodrome           AS hippodrome,
                   c.discipline           AS discipline,
                   c.distance_m           AS distance_m,
                   p.numero               AS numero,
                   p.cote_decimale        AS cote,
                   p.driver_normalized    AS jockey,
                   p.entraineur_normalized AS trainer,
                   r.arrivee              AS arrivee
            FROM partants p
            JOIN courses c ON c.document_id = p.document_id
            LEFT JOIN resultats r ON r.date = c.date
            WHERE p.nom_cheval_normalized IS NOT NULL
              AND p.nom_cheval_normalized <> ''
            ORDER BY c.date ASC
        """)

        index: dict[str, list[HistoricalRun]] = {}
        for row in rows:
            horse = row["horse"]
            if not horse:
                continue
            arrivee = self._parse_json_list(row["arrivee"])
            position: int | None = None
            if arrivee and row["numero"] is not None:
                try:
                    position = arrivee.index(row["numero"]) + 1
                except ValueError:
                    position = None
            index.setdefault(horse, []).append(HistoricalRun(
                date=row["date"] or "",
                finish_position=position,
                distance=row["distance_m"],
                terrain="",
                hippodrome=(row["hippodrome"] or "").upper(),
                jockey=(row["jockey"] or "").upper(),
                trainer=(row["trainer"] or "").upper(),
                odds=row["cote"],
            ))

        self._history_index = index
        return index

    # -- Construction d'une course -----------------------------------

    def _row_to_race(self, course_row: sqlite3.Row, partants: list[sqlite3.Row]) -> Race:
        runners: list[Runner] = []
        history_index = self._build_history_index()
        race_date = course_row["date"] or ""

        for p in partants:
            name = (p["nom_cheval_normalized"] or "").upper().strip()
            if not name or name == "NON PARTANT":
                continue
            numero = p["numero"]
            if numero is None:
                continue

            form = self._parse_json_list(p["performances_structured"])
            # Forme pré-course -> HistoricalRun (positions seules, sans date).
            form_runs = [
                HistoricalRun(date="", finish_position=int(pos), terrain="", hippodrome="")
                for pos in form
                if isinstance(pos, int)
            ]

            # Historique réel : apparitions antérieures strictement AVANT la course.
            past = [
                run for run in history_index.get(name, [])
                if run.date and race_date and run.date < race_date
            ]

            cote = p["cote_decimale"]
            runners.append(Runner(
                number=int(numero),
                horse=Horse(name=name),
                jockey=Person(name=(p["driver_normalized"] or "").upper()) if p["driver_normalized"] else None,
                trainer=Person(name=(p["entraineur_normalized"] or "").upper()) if p["entraineur_normalized"] else None,
                draw=p["corde"] if isinstance(p["corde"], int) else None,
                weight=self._parse_weight(p["poids"]) or self._parse_weight(p["chrono_raw"]),
                official_rating=self._parse_gains(p["gains_raw"]),
                current_odds=float(cote) if cote else None,
                odds_history=[OddsPoint(odds=float(cote))] if cote else [],
                history=past if past else form_runs,
            ))

        discipline = (course_row["discipline"] or "").upper()
        distance = course_row["distance_m"]
        # Le champ distance est parfois mal parsé (ex. 25) : on le signale.
        if distance is not None and distance < 400:
            distance = None

        return Race(
            date=race_date,
            hippodrome=(course_row["hippodrome"] or "").upper(),
            external_id=str(course_row["document_id"]),
            start_time=(course_row["heure_depart"] or "")[:5],
            country="FR",
            discipline=discipline,
            race_type=(course_row["type_course"] or "").upper(),
            distance=distance,
            terrain="",
            prize=course_row["montant_euros"],
            number_of_runners=len(runners),
            status="finished",
            runners=runners,
            source="real",
        )

    # -- DataProvider ------------------------------------------------

    def get_meetings(self, date: str) -> list[dict]:
        rows = self._query(
            "SELECT DISTINCT hippodrome FROM courses WHERE date = ?", (date,)
        )
        return [
            {"id": f"{date}-{r['hippodrome']}", "date": date, "hippodrome": r["hippodrome"]}
            for r in rows
        ]

    def get_races(self, date: str) -> list[Race]:
        courses = self._query(
            "SELECT * FROM courses WHERE date = ? ORDER BY document_id", (date,)
        )
        races = []
        for course in courses:
            key = str(course["document_id"])
            if key in self._race_cache:
                races.append(self._race_cache[key])
                continue
            partants = self._query(
                "SELECT * FROM partants WHERE document_id = ? ORDER BY numero",
                (course["document_id"],),
            )
            race = self._row_to_race(course, partants)
            self._race_cache[key] = race
            races.append(race)
        return races

    def get_race(self, race_id: str) -> Race | None:
        if race_id in self._race_cache:
            return self._race_cache[race_id]
        course = self._query(
            "SELECT * FROM courses WHERE document_id = ?", (race_id,)
        )
        if not course:
            return None
        partants = self._query(
            "SELECT * FROM partants WHERE document_id = ? ORDER BY numero", (race_id,)
        )
        race = self._row_to_race(course[0], partants)
        self._race_cache[race_id] = race
        return race

    def get_runners(self, race_id: str) -> list[Runner]:
        race = self.get_race(race_id)
        return list(race.runners) if race else []

    def get_horse_history(self, horse_id: str) -> list[dict]:
        index = self._build_history_index()
        runs = index.get(horse_id.upper(), [])
        return [
            {
                "date": r.date,
                "finish_position": r.finish_position,
                "distance": r.distance,
                "hippodrome": r.hippodrome,
                "jockey": r.jockey,
                "trainer": r.trainer,
                "odds": r.odds,
            }
            for r in runs
        ]

    def _person_stats(self, field: str, name: str) -> list[dict]:
        if not name:
            return []
        column = "p.driver_normalized" if field == "jockey" else "p.entraineur_normalized"
        rows = self._query(f"""
            SELECT c.date, c.document_id, p.numero, r.arrivee
            FROM partants p
            JOIN courses c ON c.document_id = p.document_id
            LEFT JOIN resultats r ON r.date = c.date
            WHERE {column} = ?
        """, (name.upper(),))
        out = []
        for row in rows:
            arrivee = self._parse_json_list(row["arrivee"])
            pos = None
            if arrivee and row["numero"] is not None:
                try:
                    pos = arrivee.index(row["numero"]) + 1
                except ValueError:
                    pos = None
            out.append({"date": row["date"], "finish_position": pos})
        return out

    def get_jockey_history(self, jockey_id: str) -> list[dict]:
        return self._person_stats("jockey", jockey_id)

    def get_trainer_history(self, trainer_id: str) -> list[dict]:
        return self._person_stats("trainer", trainer_id)

    def get_odds(self, race_id: str) -> dict[int, list[dict]]:
        """Cotes disponibles depuis ``api_cotes`` (par type de pari)."""
        rows = self._query("""
            SELECT numero, cote_directe, masse_enjeu, updatetime
            FROM api_cotes
            WHERE course_id = ? AND type_pari = 'E_SIMPLE_GAGNANT'
        """, (race_id,))
        out: dict[int, list[dict]] = {}
        for row in rows:
            if row["numero"] is None:
                continue
            out.setdefault(int(row["numero"]), []).append({
                "odds": row["cote_directe"],
                "timestamp": row["updatetime"],
                "masse": row["masse_enjeu"],
            })
        return out

    @staticmethod
    def _parse_arrival(arrivee_complete: str | None, arrivee: str | None) -> list[int]:
        """
        L'arrivée est stockée sous deux formes dans la base source :

            arrivee          : '[8, 11, 12, 6, 2]'                (entiers)
            arrivee_complete : '[{"position":1,"numero":8}, ...]' (dicts)

        On privilégie ``arrivee_complete`` (plus riche) et on retombe sur
        ``arrivee`` sinon.
        """
        complete = SqliteDataProvider._parse_json_list(arrivee_complete)
        if complete and all(isinstance(x, dict) for x in complete):
            ordered = sorted(
                (x for x in complete if x.get("numero") is not None),
                key=lambda x: x.get("position", 999),
            )
            return [int(x["numero"]) for x in ordered]
        simple = SqliteDataProvider._parse_json_list(arrivee)
        return [int(x) for x in simple if str(x).strip().lstrip("-").isdigit()]

    def get_results(self, race_id: str) -> RaceResult | None:
        """Arrivée réelle — lue UNIQUEMENT par l'évaluateur, jamais par le moteur."""
        race = self.get_race(race_id)
        if not race:
            return None
        row = self._query(
            "SELECT arrivee, arrivee_complete FROM resultats WHERE date = ?",
            (race.date,),
        )
        if not row:
            return None
        order = self._parse_arrival(row[0]["arrivee_complete"], row[0]["arrivee"])
        if not order:
            return None
        return RaceResult(race_id=race_id, finish_order=order)

    # -- Utilitaires -------------------------------------------------

    def list_race_ids(self, date_from: str | None = None, date_to: str | None = None,
                      min_runners: int = 8, only_with_results: bool = True) -> list[str]:
        """Liste des courses exploitables (avec arrivée réelle par défaut)."""
        sql = """
            SELECT c.document_id AS id, COUNT(p.id) AS n
            FROM courses c
            JOIN partants p ON p.document_id = c.document_id
            WHERE c.date IS NOT NULL AND c.date <> ''
        """
        params: list = []
        if date_from:
            sql += " AND c.date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND c.date <= ?"
            params.append(date_to)
        if only_with_results:
            sql += " AND EXISTS (SELECT 1 FROM resultats r WHERE r.date = c.date AND r.arrivee NOT IN ('', '[]'))"
        sql += " GROUP BY c.document_id HAVING n >= ? ORDER BY c.date ASC"
        params.append(min_runners)
        return [str(r["id"]) for r in self._query(sql, tuple(params))]

    def close(self) -> None:
        self._conn.close()
