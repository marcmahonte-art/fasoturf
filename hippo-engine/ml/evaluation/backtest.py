"""
Backtesting (#30).

Compare les prédictions aux arrivées réelles sur une période donnée, et
produit des performances agrégées — **toujours avec période, volume et
méthodologie** (règle #31).

Sortie :
    courses_tested, wins, top3_hits, top5_hits, quinte_hits, ROI,
    performance_by_month, performance_by_hippodrome,
    performance_by_race_type, performance_by_odds_range
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ..config import Config, load_config
from ..prediction.engine import generate_prediction
from .metrics import (
    EvaluationSummary,
    RaceEvaluation,
    brier_score,
    log_loss,
    summarise,
)


@dataclass
class BacktestResult:
    summary: EvaluationSummary
    by_month: dict[str, dict] = field(default_factory=dict)
    by_hippodrome: dict[str, dict] = field(default_factory=dict)
    by_race_type: dict[str, dict] = field(default_factory=dict)
    by_odds_range: dict[str, dict] = field(default_factory=dict)


def _odds_bucket(odds: float | None) -> str:
    if not odds:
        return "inconnue"
    if odds < 3:
        return "1.0-2.9 (favori)"
    if odds < 6:
        return "3.0-5.9"
    if odds < 10:
        return "6.0-9.9"
    if odds < 20:
        return "10.0-19.9"
    return "20.0+ (outsider)"


def evaluate_race(prediction, result) -> RaceEvaluation:
    """
    Évalue une prédiction face à l'arrivée réelle.

    On calcule deux familles de métriques :

    - **fortes** : le n°1 du modèle a-t-il gagné ? quelle est la précision du
      top 3 prédit (combien de nos 3 chevaux sont dans le vrai top 3) ?
    - **référence** : les mêmes mesures appliquées au favori du marché
      (cote la plus basse). Sans cette référence, un taux brut n'est pas
      interprétable.
    """
    actual = result.finish_order
    if not actual:
        return RaceEvaluation(race_id=prediction.race_id, date=prediction.race_date)

    ev = RaceEvaluation(race_id=prediction.race_id, date=prediction.race_date)

    actual_top3 = actual[:3]
    actual_top5 = actual[:5]
    predicted_top3 = prediction.selection.tierce
    predicted_top5 = prediction.selection.quinte

    # --- Métriques fortes ---
    model_top = prediction.entries[0].number if prediction.entries else None
    ev.winner_hit = bool(model_top is not None and model_top == actual[0])
    ev.top3_overlap = len(set(predicted_top3) & set(actual_top3))

    # --- Référence : favori du marché (cote la plus basse) ---
    with_odds = [e for e in prediction.entries if e.odds]
    if with_odds:
        favorite = min(with_odds, key=lambda e: e.odds)
        ev.favorite_winner_hit = favorite.number == actual[0]
        # Top 3 du marché = les 3 cotes les plus basses
        market_top3 = [e.number for e in sorted(with_odds, key=lambda e: e.odds)[:3]]
        ev.favorite_top3_overlap = len(set(market_top3) & set(actual_top3))

    # --- Métriques faibles (indicatives) ---
    ev.top3_hit = bool(set(predicted_top3) & set(actual_top3))
    ev.top5_hit = bool(set(predicted_top5) & set(actual_top5))
    ev.tierce_hit = set(predicted_top3) == set(actual_top3) and len(actual_top3) >= 3
    ev.quarte_hit = set(prediction.selection.quarte) == set(actual[:4]) and len(actual) >= 4
    ev.quinte_hit = set(predicted_top5) == set(actual_top5) and len(actual) >= 5
    ev.base_hit = bool(set(prediction.selection.bases) & set(actual_top3))

    # Probabilités vs résultat
    numbers = [e.number for e in prediction.entries]
    y_true = [1 if n in actual_top3 else 0 for n in numbers]
    y_prob = [e.top3_probability for e in prediction.entries]
    ev.brier = brier_score(y_true, y_prob)
    ev.log_loss = log_loss(y_true, y_prob)

    # ROI simplifié : mise 1 € sur les chevaux VALUE, gain = cote si gagnant
    stake = 0.0
    gain = 0.0
    for entry in prediction.entries:
        if entry.is_value and entry.odds:
            stake += 1.0
            if entry.number == actual[0]:
                gain += entry.odds
    ev.roi = round((gain - stake) / stake, 4) if stake > 0 else 0.0
    return ev


def run_backtest(
    provider,
    race_ids: list[str],
    *,
    config: Config | None = None,
    models: dict | None = None,
    verbose: bool = False,
) -> BacktestResult:
    cfg = config or load_config()
    evaluations: list[RaceEvaluation] = []
    race_meta: dict[str, dict] = {}

    for race_id in race_ids:
        result = provider.get_results(race_id)
        if not result or not result.finish_order:
            continue
        try:
            prediction = generate_prediction(provider, race_id, config=cfg, models=models)
        except Exception as exc:  # pragma: no cover - robustesse backtest
            if verbose:
                print(f"  [skip] {race_id} : {exc}")
            continue
        if not prediction.entries:
            continue

        ev = evaluate_race(prediction, result)
        evaluations.append(ev)

        race = provider.get_race(race_id)
        top_odds = prediction.entries[0].odds
        race_meta[race_id] = {
            "month": ev.date[:7],
            "hippodrome": race.hippodrome if race else "",
            "race_type": race.race_type if race else "",
            "odds_range": _odds_bucket(top_odds),
        }
        if verbose and len(evaluations) % 50 == 0:
            print(f"  ... {len(evaluations)} courses évaluées")

    summary = summarise(
        evaluations,
        method=(
            f"Prédictions générées AVANT course, comparées aux arrivées réelles. "
            f"Modèle {cfg.model_version}. Découpage temporel."
        ),
    )

    def _aggregate(key: str) -> dict[str, dict]:
        buckets: dict[str, list[RaceEvaluation]] = defaultdict(list)
        for ev in evaluations:
            meta = race_meta.get(ev.race_id, {})
            buckets[meta.get(key, "inconnu")].append(ev)
        out = {}
        for name, evs in buckets.items():
            n = len(evs)
            out[name] = {
                "races": n,
                "top3_hit_rate": round(100.0 * sum(e.top3_hit for e in evs) / n, 2),
                "top5_hit_rate": round(100.0 * sum(e.top5_hit for e in evs) / n, 2),
                "quinte_hit_rate": round(100.0 * sum(e.quinte_hit for e in evs) / n, 2),
                "avg_roi": round(sum(e.roi for e in evs) / n, 4),
            }
        return dict(sorted(out.items()))

    return BacktestResult(
        summary=summary,
        by_month=_aggregate("month"),
        by_hippodrome=_aggregate("hippodrome"),
        by_race_type=_aggregate("race_type"),
        by_odds_range=_aggregate("odds_range"),
    )
