"""
Feature engineering (#8) — calculé UNIQUEMENT sur des données pré-course.

Règle absolue (#8, #43) : aucune feature ne peut dépendre du résultat de la
course courante. La seule donnée autorisée sur la course cible est ce qui est
connu AVANT le départ : partants déclarés, corde, poids, valeur, cotes.

``partants.performances_structured`` (musique) est une donnée **antérieure** à
la course : elle est autorisée. ``resultats.arrivee`` ne l'est jamais.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from statistics import mean

from ..data.schema import HistoricalRun, Race, Runner

# Toute feature listée ici est vérifiée par tests/test_no_leakage.py
FORBIDDEN_FEATURE_NAMES = {
    "finish_position", "arrivee", "official_result", "result",
    "position", "winner", "podium",
}


@dataclass(slots=True)
class Features:
    """Vecteur de caractéristiques d'un partant."""
    number: int

    # Forme
    form_3: float = 0.0
    form_5: float = 0.0
    form_10: float = 0.0
    best_finish: int | None = None
    worst_finish: int | None = None
    starts: int = 0
    wins: int = 0
    places: int = 0
    win_rate: float = 0.0
    place_rate: float = 0.0
    top3_rate: float = 0.0
    top5_rate: float = 0.0
    regularity: float = 0.0

    # Spécialisations (nécessitent un historique attribué)
    distance_score: float = 0.5
    terrain_score: float = 0.5
    course_score: float = 0.5
    distance_starts: int = 0
    course_starts: int = 0

    # Entourage
    jockey_win_rate: float = 0.0
    jockey_place_rate: float = 0.0
    trainer_win_rate: float = 0.0
    trainer_place_rate: float = 0.0
    jockey_horse_rate: float = 0.0

    # Conditions de course
    weight_score: float = 0.5
    draw_score: float = 0.5
    rating_score: float = 0.5

    # Marché
    field_size: int = 0
    odds: float | None = None
    odds_probability: float = 0.0
    odds_movement: float = 0.0
    odds_change_percentage: float = 0.0
    odds_trend: str = "STABLE"

    # Percentiles peloton (0..1)
    horse_rating_percentile: float = 0.5
    horse_form_percentile: float = 0.5
    horse_weight_percentile: float = 0.5
    horse_jockey_percentile: float = 0.5
    horse_trainer_percentile: float = 0.5

    # Traçabilité
    data_quality: str = "DATA_COMPLETE"
    factors_positive: list[str] = field(default_factory=list)
    factors_negative: list[str] = field(default_factory=list)

    def to_vector(self) -> dict[str, float]:
        """Vecteur numérique plat (les listes de facteurs sont exclues)."""
        out: dict[str, float] = {}
        for f in fields(self):
            if f.name == "number":
                continue
            value = getattr(self, f.name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            out[f.name] = float(value)
        return out


def _form_score(runs: list[HistoricalRun], n: int) -> float:
    """Score 0..1 sur les n dernières sorties (1 = victoire)."""
    positions = [r.finish_position for r in runs[:n] if r.finish_position]
    if not positions:
        return 0.0
    # Une 1re place vaut 1.0, une 10e+ vaut ~0.0
    scores = [max(0.0, 1.0 - (p - 1) / 9.0) for p in positions]
    return round(mean(scores), 4)


def _rate(runs: list[HistoricalRun], threshold: int) -> float:
    positions = [r.finish_position for r in runs if r.finish_position]
    if not positions:
        return 0.0
    return round(sum(1 for p in positions if p <= threshold) / len(positions), 4)


def _specialisation(runs: list[HistoricalRun], *, distance: int | None,
                    hippodrome: str, terrain: str) -> tuple[float, int, int]:
    """Retourne (score 0..1, nb_courses_distance, nb_courses_hippodrome)."""
    distance_starts = 0
    course_starts = 0
    hits: list[float] = []

    for run in runs:
        if run.finish_position is None:
            continue
        similar = False
        if distance and run.distance and abs(run.distance - distance) <= 400:
            distance_starts += 1
            similar = True
        if hippodrome and run.hippodrome and run.hippodrome == hippodrome:
            course_starts += 1
            similar = True
        if similar:
            hits.append(max(0.0, 1.0 - (run.finish_position - 1) / 9.0))

    score = round(mean(hits), 4) if hits else 0.5
    return score, distance_starts, course_starts


def _percentile(values: list[float], value: float) -> float:
    """Rang percentile (0..1) de ``value`` dans ``values``."""
    if not values:
        return 0.5
    below = sum(1 for v in values if v < value)
    equal = sum(1 for v in values if v == value)
    return round((below + 0.5 * equal) / len(values), 4)


def _odds_movement(history: list) -> tuple[float, float, str]:
    """Analyse le mouvement de cote (#17). Une baisse n'est PAS une preuve."""
    points = [p.odds for p in history if getattr(p, "odds", None)]
    if len(points) < 2:
        return 0.0, 0.0, "STABLE"
    first, last = points[0], points[-1]
    if not first:
        return 0.0, 0.0, "STABLE"
    change = (last - first) / first
    movement = round(first - last, 4)
    if change <= -0.10:
        trend = "STEAMING"      # la cote baisse (argent qui arrive)
    elif change >= 0.10:
        trend = "DRIFTING"      # la cote monte (délaissé)
    else:
        trend = "STABLE"
    return movement, round(change, 4), trend


def compute_features(
    race: Race,
    *,
    jockey_stats: dict[str, dict] | None = None,
    trainer_stats: dict[str, dict] | None = None,
) -> dict[int, Features]:
    """
    Calcule le vecteur de features de chaque partant actif.

    ``jockey_stats`` / ``trainer_stats`` : taux pré-calculés sur l'historique
    (clé = nom normalisé), fournis par l'appelant pour éviter toute fuite.
    """
    jockey_stats = jockey_stats or {}
    trainer_stats = trainer_stats or {}
    actives = race.active_runners
    field_size = len(actives)

    # --- Agrégats du peloton (calculés AVANT les percentiles) ---
    ratings: list[float] = []
    forms: list[float] = []
    weights: list[float] = []
    jockey_rates: list[float] = []
    trainer_rates: list[float] = []

    prelim: dict[int, dict] = {}
    for runner in actives:
        runs = runner.history or []
        form_5 = _form_score(runs, 5)
        jkey = runner.jockey.name if runner.jockey else ""
        tkey = runner.trainer.name if runner.trainer else ""
        jstat = jockey_stats.get(jkey, {})
        tstat = trainer_stats.get(tkey, {})
        j_win = float(jstat.get("win_rate", 0.0))
        t_win = float(tstat.get("win_rate", 0.0))

        prelim[runner.number] = {
            "runs": runs, "form_5": form_5, "j_win": j_win, "t_win": t_win,
            "jstat": jstat, "tstat": tstat, "jkey": jkey, "tkey": tkey,
        }
        ratings.append(runner.official_rating or 0.0)
        forms.append(form_5)
        weights.append(runner.weight or 0.0)
        jockey_rates.append(j_win)
        trainer_rates.append(t_win)

    # --- Vecteurs individuels ---
    out: dict[int, Features] = {}
    for runner in actives:
        p = prelim[runner.number]
        runs: list[HistoricalRun] = p["runs"]

        feat = Features(number=runner.number)
        feat.field_size = field_size
        feat.odds = runner.current_odds

        feat.form_3 = _form_score(runs, 3)
        feat.form_5 = p["form_5"]
        feat.form_10 = _form_score(runs, 10)

        positions = [r.finish_position for r in runs if r.finish_position]
        feat.starts = len(positions)
        feat.wins = sum(1 for x in positions if x == 1)
        feat.places = sum(1 for x in positions if x <= 3)
        feat.best_finish = min(positions) if positions else None
        feat.worst_finish = max(positions) if positions else None
        feat.win_rate = _rate(runs, 1)
        feat.place_rate = _rate(runs, 3)
        feat.top3_rate = feat.place_rate
        feat.top5_rate = _rate(runs, 5)
        # Régularité : 1 - écart-type normalisé des positions
        if len(positions) >= 2:
            avg = mean(positions)
            variance = mean([(x - avg) ** 2 for x in positions])
            feat.regularity = round(max(0.0, 1.0 - (variance ** 0.5) / 8.0), 4)

        dist_score, dist_starts, course_starts = _specialisation(
            runs, distance=race.distance, hippodrome=race.hippodrome, terrain=race.terrain
        )
        feat.distance_score = dist_score
        feat.course_score = dist_score
        feat.distance_starts = dist_starts
        feat.course_starts = course_starts
        feat.terrain_score = dist_score  # terrain non renseigné dans la base source

        feat.jockey_win_rate = p["j_win"]
        feat.jockey_place_rate = float(p["jstat"].get("place_rate", 0.0))
        feat.trainer_win_rate = p["t_win"]
        feat.trainer_place_rate = float(p["tstat"].get("place_rate", 0.0))
        feat.jockey_horse_rate = _jockey_horse_rate(runs, p["jkey"])

        # Score poids : plus léger = mieux (normalisé sur le peloton)
        if runner.weight and weights and max(weights) > min(weights):
            span = max(weights) - min(weights)
            feat.weight_score = round(1.0 - (runner.weight - min(weights)) / span, 4)
        # Score corde : les cordes basses sont avantagées en plat
        if runner.draw and field_size:
            feat.draw_score = round(1.0 - (runner.draw - 1) / max(field_size - 1, 1), 4)
        # Score valeur (gains) : percentile dans le peloton
        feat.rating_score = _percentile(ratings, runner.official_rating or 0.0)

        # Marché
        if runner.current_odds and runner.current_odds > 0:
            feat.odds_probability = round(1.0 / runner.current_odds, 4)
        movement, change, trend = _odds_movement(runner.odds_history)
        feat.odds_movement = movement
        feat.odds_change_percentage = change
        feat.odds_trend = trend

        # Percentiles peloton
        feat.horse_rating_percentile = _percentile(ratings, runner.official_rating or 0.0)
        feat.horse_form_percentile = _percentile(forms, p["form_5"])
        feat.horse_weight_percentile = _percentile(weights, runner.weight or 0.0)
        feat.horse_jockey_percentile = _percentile(jockey_rates, p["j_win"])
        feat.horse_trainer_percentile = _percentile(trainer_rates, p["t_win"])

        out[runner.number] = feat

    return out


def _jockey_horse_rate(runs: list[HistoricalRun], jockey: str) -> float:
    if not jockey:
        return 0.0
    subset = [r for r in runs if r.jockey and r.jockey == jockey and r.finish_position]
    if not subset:
        return 0.0
    return round(sum(1 for r in subset if r.finish_position <= 3) / len(subset), 4)


def assess_data_quality(features: dict[int, Features], race: Race) -> str:
    """
    Qualité des données (#32).

    DATA_COMPLETE      : cotes + historique suffisant
    DATA_PARTIAL       : quelques manques
    DATA_INSUFFICIENT  : impossible de produire une prédiction fiable
    """
    if not features:
        return "DATA_INSUFFICIENT"
    n = len(features)
    with_odds = sum(1 for f in features.values() if f.odds)
    with_history = sum(1 for f in features.values() if f.starts >= 3)

    if with_odds / n >= 0.8 and with_history / n >= 0.6:
        return "DATA_COMPLETE"
    if with_odds / n >= 0.5 or with_history / n >= 0.4:
        return "DATA_PARTIAL"
    return "DATA_INSUFFICIENT"


def build_factors(features: dict[int, Features]) -> None:
    """
    Génère les facteurs explicatifs (#39) **à partir des features réellement
    calculées**. Aucune explication inventée.
    """
    for feat in features.values():
        pos, neg = [], []
        if feat.form_5 >= 0.7:
            pos.append(f"excellente forme récente (score forme {feat.form_5:.2f})")
        elif feat.form_5 <= 0.3 and feat.starts > 0:
            neg.append(f"forme récente faible (score forme {feat.form_5:.2f})")
        if feat.win_rate >= 0.25:
            pos.append(f"taux de victoire élevé ({feat.win_rate:.0%})")
        if feat.horse_rating_percentile >= 0.75:
            pos.append(f"valeur parmi les meilleures du peloton (P{feat.horse_rating_percentile:.0%})")
        elif feat.horse_rating_percentile <= 0.25:
            neg.append(f"valeur faible dans le peloton (P{feat.horse_rating_percentile:.0%})")
        if feat.jockey_win_rate >= 0.15:
            pos.append(f"jockey performant ({feat.jockey_win_rate:.0%} de victoires)")
        if feat.distance_starts >= 3 and feat.distance_score >= 0.6:
            pos.append("bon historique sur distance similaire")
        elif feat.distance_starts >= 3 and feat.distance_score <= 0.35:
            neg.append("historique faible sur distance similaire")
        if feat.weight_score <= 0.25:
            neg.append("poids élevé dans le peloton")
        if feat.draw_score <= 0.2:
            neg.append(f"corde extérieure (n° {feat.number})")
        if feat.odds_trend == "STEAMING":
            pos.append("cote en baisse (argent qui arrive)")
        elif feat.odds_trend == "DRIFTING":
            neg.append("cote en hausse (délaissé par le marché)")
        if feat.starts < 3:
            neg.append(f"peu de références ({feat.starts} sortie(s))")

        feat.factors_positive = pos
        feat.factors_negative = neg
