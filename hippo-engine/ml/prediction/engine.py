"""
Moteur de prédiction — ``generate_prediction(race_id)`` (#20).

Pipeline complet :

    1. récupérer la course          11. calculer la Value
    2. récupérer les partants       12. fusionner les scores
    3. récupérer l'historique       13. classer les chevaux
    4. récupérer les cotes          14. sélectionner les bases
    5. calculer les features        15. sélectionner les chances
    6. exécuter RANK                16. sélectionner les outsiders
    7. exécuter Win                 17. construire le Quinté
    8. exécuter Top3                18. calculer la confiance
    9. exécuter Top5                19. sauvegarder la prédiction
   10. exécuter CatBoost

Le résultat distingue explicitement PRÉDICTION et DONNÉE RÉELLE (règle #49).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..config import Config, load_config
from ..data.schema import Race
from ..features.engineering import (
    Features,
    assess_data_quality,
    build_factors,
    compute_features,
)
from ..models.probabilistic import compute_probabilities
from ..models.rank import compute_rank_all
from .fusion import compute_fusion
from .quinte import RankedEntry, Selection, quinte_combinations, select
from .value import compute_value_all


@dataclass
class Prediction:
    race_id: str
    race_date: str
    hippodrome: str
    discipline: str
    distance: int | None
    field_size: int
    model_version: str
    prediction_version: str
    data_timestamp: str
    data_quality: str
    confidence: str
    confidence_reasons: list[str] = field(default_factory=list)
    entries: list[RankedEntry] = field(default_factory=list)
    selection: Selection = field(default_factory=Selection)
    combos: dict = field(default_factory=dict)
    features: dict[int, Features] = field(default_factory=dict)
    is_demo: bool = False

    def as_api_payload(self) -> dict:
        """Format de sortie de l'API interne (#27)."""
        return {
            "race": {
                "id": self.race_id,
                "date": self.race_date,
                "hippodrome": self.hippodrome,
                "discipline": self.discipline,
                "distance": self.distance,
                "fieldSize": self.field_size,
                "source": "demo" if self.is_demo else "real",
            },
            "prediction": {
                "modelVersion": self.model_version,
                "predictionVersion": self.prediction_version,
                "dataTimestamp": self.data_timestamp,
                "dataQuality": self.data_quality,
                "confidence": self.confidence,
                "confidenceReasons": self.confidence_reasons,
                "bases": self.selection.bases,
                "chances": self.selection.chances,
                "outsiders": self.selection.outsiders,
                "value": self.selection.value,
                "quinte": self.selection.quinte,
                "quinteElargi": self.selection.quinte_elargi,
                "tierce": self.selection.tierce,
                "quarte": self.selection.quarte,
                "combos": self.combos,
                "rationale": self.selection.rationale,
                "runners": [
                    {
                        "number": e.number,
                        "rankScore": round(e.rank_score, 2),
                        "winProbability": round(e.win_probability, 4),
                        "top3Probability": round(e.top3_probability, 4),
                        "top5Probability": round(e.top5_probability, 4),
                        "catboostProbability": round(e.catboost_probability, 4),
                        "valueScore": round(e.value_score, 2),
                        "valueEdge": round(e.value_edge, 4),
                        "finalScore": round(e.final_score, 2),
                        "confidence": e.confidence,
                        "odds": e.odds,
                        "factorsPositive": self.features[e.number].factors_positive,
                        "factorsNegative": self.features[e.number].factors_negative,
                    }
                    for e in self.entries
                ],
            },
        }


def _confidence(quality: str, entries: list[RankedEntry], features: dict[int, Features]) -> tuple[str, list[str]]:
    """Confiance calculée (#19) — jamais « gagnant assuré »."""
    reasons: list[str] = []
    score = 0

    if quality == "DATA_COMPLETE":
        score += 2
        reasons.append("données complètes (cotes + historique)")
    elif quality == "DATA_PARTIAL":
        score += 1
        reasons.append("données partielles")
    else:
        reasons.append("données insuffisantes")

    if entries:
        top = entries[0]
        # Accord entre modèles : Top3 et CatBoost proches
        spread = abs(top.top3_probability - top.catboost_probability)
        if spread <= 0.15:
            score += 2
            reasons.append(f"bon accord entre modèles (écart {spread:.2f})")
        elif spread <= 0.30:
            score += 1
            reasons.append(f"accord modéré entre modèles (écart {spread:.2f})")
        else:
            reasons.append(f"désaccord entre modèles (écart {spread:.2f})")

        # Séparation du peloton
        if len(entries) >= 3:
            gap = top.final_score - entries[2].final_score
            if gap >= 15:
                score += 2
                reasons.append(f"peloton bien séparé (écart top1-top3 : {gap:.1f} pts)")
            elif gap >= 8:
                score += 1
                reasons.append(f"séparation moyenne (écart top1-top3 : {gap:.1f} pts)")
            else:
                reasons.append(f"peloton resserré (écart top1-top3 : {gap:.1f} pts)")

        # Volatilité des cotes
        if any(f.odds_trend == "DRIFTING" for f in features.values()):
            score -= 1
            reasons.append("cotes volatiles sur certains partants")

    if score >= 5:
        return "HIGH", reasons
    if score >= 3:
        return "MEDIUM", reasons
    return "LOW", reasons


def generate_prediction(
    provider,
    race_id: str,
    *,
    config: Config | None = None,
    models: dict | None = None,
    jockey_stats: dict | None = None,
    trainer_stats: dict | None = None,
) -> Prediction:
    """
    Génère la prédiction complète d'une course.

    ``models`` : dict optionnel {win, top3, top5} de ProbabilityModel entraînés.
    En leur absence, les probabilités proviennent du modèle Plackett-Luce
    appliqué au score RANK (démarrage à froid, clairement traçable).
    """
    cfg = config or load_config()

    # 1-4. Données
    race: Race = provider.get_race(race_id)
    if race is None:
        raise ValueError(f"Course introuvable : {race_id}")

    # 5. Features
    features = compute_features(race, jockey_stats=jockey_stats, trainer_stats=trainer_stats)
    build_factors(features)
    quality = assess_data_quality(features, race)

    if quality == "DATA_INSUFFICIENT":
        return Prediction(
            race_id=race_id, race_date=race.date, hippodrome=race.hippodrome,
            discipline=race.discipline, distance=race.distance,
            field_size=len(features), model_version=cfg.model_version,
            prediction_version=cfg.prediction_version,
            data_timestamp=datetime.now(timezone.utc).isoformat(),
            data_quality=quality, confidence="LOW",
            confidence_reasons=["Données insuffisantes pour une prédiction fiable."],
            features=features, is_demo=race.source == "demo",
        )

    # 6. RANK
    ranks = compute_rank_all(features, cfg.rank_weights)

    # 7-9. Modèles ML (si entraînés) — sinon score RANK comme force
    base_scores = {num: ranks[num].rank_score for num in features}
    if models:
        X = [[features[num].to_vector().get(name, 0.0) for name in models["win"].feature_names]
             for num in features]
        probs = {
            "win": dict(zip(features.keys(), models["win"].predict_proba(X))),
            "top3": dict(zip(features.keys(), models["top3"].predict_proba(X))),
            "top5": dict(zip(features.keys(), models["top5"].predict_proba(X))),
        }
        catboost_probs = probs["win"]
    else:
        pl = compute_probabilities(base_scores)
        probs = {
            "win": {n: pl[n].win_probability for n in features},
            "top3": {n: pl[n].top3_probability for n in features},
            "top5": {n: pl[n].top5_probability for n in features},
        }
        catboost_probs = dict(probs["win"])

    # 11. VALUE
    odds = {num: features[num].odds for num in features}
    values = compute_value_all(
        probs["win"], odds,
        value_threshold=cfg.value_threshold,
        value_ratio_threshold=cfg.value_ratio_threshold,
    )

    # 12. FUSION
    entries: list[RankedEntry] = []
    for num in features:
        fusion = compute_fusion(
            num,
            rank=ranks[num],
            features=features[num],
            catboost_probability=catboost_probs.get(num, 0.0),
            top3_probability=probs["top3"].get(num, 0.0),
            value=values[num],
            weights=cfg.weights,
        )
        entries.append(RankedEntry(
            number=num,
            final_score=fusion.final_score,
            rank_score=ranks[num].rank_score,
            win_probability=probs["win"].get(num, 0.0),
            top3_probability=probs["top3"].get(num, 0.0),
            top5_probability=probs["top5"].get(num, 0.0),
            catboost_probability=catboost_probs.get(num, 0.0),
            value_score=values[num].value_score,
            value_edge=values[num].value_edge,
            odds=odds[num],
            confidence="MEDIUM",
            is_value=values[num].is_value,
            regularity=features[num].regularity,
        ))

    # 13. Classement
    entries.sort(key=lambda e: e.final_score, reverse=True)

    # 18. Confiance (calculée avant d'annoter chaque entrée)
    confidence, reasons = _confidence(quality, entries, features)
    for entry in entries:
        entry.confidence = confidence if entry is entries[0] else (
            "MEDIUM" if entry.final_score >= entries[0].final_score * 0.75 else "LOW"
        )

    # 14-17. Sélection + Quinté
    selection = select(
        entries,
        value_threshold=cfg.value_threshold,
    )
    combos = {
        "champ_reduit": quinte_combinations(selection, champ_reduit=True),
        "champ_total": quinte_combinations(selection, champ_reduit=False),
    }

    return Prediction(
        race_id=race_id,
        race_date=race.date,
        hippodrome=race.hippodrome,
        discipline=race.discipline,
        distance=race.distance,
        field_size=len(features),
        model_version=cfg.model_version,
        prediction_version=cfg.prediction_version,
        data_timestamp=datetime.now(timezone.utc).isoformat(),
        data_quality=quality,
        confidence=confidence,
        confidence_reasons=reasons,
        entries=entries,
        selection=selection,
        combos=combos,
        features=features,
        is_demo=race.source == "demo",
    )
