"""
Métriques ML (#15) — implémentées en Python pur.

Classification  : accuracy, precision, recall, F1, ROC-AUC
Probabilités    : log loss, Brier score, calibration
Pronostics      : Top1 / Top3 / Top5 / Quinté hit rate

Toute métrique publiée doit être accompagnée de sa période et de son volume
(règle #31).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


def accuracy(y_true: list[int], y_pred: list[int]) -> float:
    if not y_true:
        return 0.0
    return round(_safe_div(sum(1 for a, b in zip(y_true, y_pred) if a == b), len(y_true)), 4)


def precision_recall_f1(y_true: list[int], y_pred: list[int]) -> dict[str, float]:
    tp = sum(1 for a, b in zip(y_true, y_pred) if a == 1 and b == 1)
    fp = sum(1 for a, b in zip(y_true, y_pred) if a == 0 and b == 1)
    fn = sum(1 for a, b in zip(y_true, y_pred) if a == 1 and b == 0)
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp, "fp": fp, "fn": fn,
    }


def roc_auc(y_true: list[int], y_score: list[float]) -> float:
    """AUC par la méthode des rangs (Mann-Whitney U)."""
    positives = [s for t, s in zip(y_true, y_score) if t == 1]
    negatives = [s for t, s in zip(y_true, y_score) if t == 0]
    if not positives or not negatives:
        return 0.5
    # Rang moyen pour gérer les ex æquo
    pairs = sorted(zip(y_score, y_true), key=lambda p: p[0])
    ranks: list[float] = [0.0] * len(pairs)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1
    rank_sum_pos = sum(rank for rank, (_score, label) in zip(ranks, pairs) if label == 1)
    n_pos, n_neg = len(positives), len(negatives)
    auc = (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return round(auc, 4)


def log_loss(y_true: list[int], y_prob: list[float], eps: float = 1e-15) -> float:
    if not y_true:
        return 0.0
    total = 0.0
    for label, prob in zip(y_true, y_prob):
        p = min(max(prob, eps), 1 - eps)
        total += -(label * math.log(p) + (1 - label) * math.log(1 - p))
    return round(total / len(y_true), 6)


def brier_score(y_true: list[int], y_prob: list[float]) -> float:
    if not y_true:
        return 0.0
    total = sum((prob - label) ** 2 for label, prob in zip(y_true, y_prob))
    return round(total / len(y_true), 6)


def calibration_curve(y_true: list[int], y_prob: list[float], bins: int = 10) -> list[dict]:
    """Courbe de fiabilité : probabilité moyenne prédite vs fréquence observée."""
    buckets: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for label, prob in zip(y_true, y_prob):
        idx = min(int(prob * bins), bins - 1)
        buckets[idx].append((prob, label))
    curve = []
    for idx, bucket in enumerate(buckets):
        if not bucket:
            continue
        avg_prob = sum(p for p, _ in bucket) / len(bucket)
        observed = sum(l for _, l in bucket) / len(bucket)
        curve.append({
            "bin": idx,
            "predicted": round(avg_prob, 4),
            "observed": round(observed, 4),
            "count": len(bucket),
        })
    return curve


@dataclass
class RaceEvaluation:
    race_id: str
    date: str
    # Métriques fortes (non triviales)
    winner_hit: bool = False          # le n°1 du modèle a gagné
    top3_overlap: int = 0             # combien de nos 3 premiers sont dans le vrai top 3
    favorite_winner_hit: bool = False # le favori du marché a gagné (référence)
    favorite_top3_overlap: int = 0    # top 3 du favori de marché (référence)
    # Métriques faibles (conservées pour compatibilité)
    tierce_hit: bool = False
    quarte_hit: bool = False
    quinte_hit: bool = False
    base_hit: bool = False
    top3_hit: bool = False
    top5_hit: bool = False
    brier: float = 0.0
    log_loss: float = 0.0
    roi: float = 0.0


@dataclass
class EvaluationSummary:
    races_tested: int = 0
    period_from: str = ""
    period_to: str = ""
    # Métriques fortes
    winner_hit_rate: float = 0.0
    favorite_winner_hit_rate: float = 0.0
    top3_precision: float = 0.0
    favorite_top3_precision: float = 0.0
    edge_vs_favorite: float = 0.0
    # Métriques faibles
    top3_hit_rate: float = 0.0
    top5_hit_rate: float = 0.0
    quinte_hit_rate: float = 0.0
    tierce_hit_rate: float = 0.0
    base_hit_rate: float = 0.0
    avg_brier: float = 0.0
    avg_log_loss: float = 0.0
    avg_roi: float = 0.0
    method: str = ""
    details: list[RaceEvaluation] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "races_tested": self.races_tested,
            "period": {"from": self.period_from, "to": self.period_to},
            "winner_hit_rate": self.winner_hit_rate,
            "favorite_winner_hit_rate": self.favorite_winner_hit_rate,
            "top3_precision": self.top3_precision,
            "favorite_top3_precision": self.favorite_top3_precision,
            "edge_vs_favorite": self.edge_vs_favorite,
            "top3_hit_rate": self.top3_hit_rate,
            "top5_hit_rate": self.top5_hit_rate,
            "quinte_hit_rate": self.quinte_hit_rate,
            "tierce_hit_rate": self.tierce_hit_rate,
            "base_hit_rate": self.base_hit_rate,
            "avg_brier": self.avg_brier,
            "avg_log_loss": self.avg_log_loss,
            "avg_roi": self.avg_roi,
            "method": self.method,
        }


def summarise(evaluations: list[RaceEvaluation], *, method: str = "") -> EvaluationSummary:
    """Agrège les évaluations en un résumé — toujours avec période et volume."""
    if not evaluations:
        return EvaluationSummary(method=method)
    n = len(evaluations)
    dates = sorted(e.date for e in evaluations if e.date)

    winner_rate = 100.0 * sum(e.winner_hit for e in evaluations) / n
    fav_winner_rate = 100.0 * sum(e.favorite_winner_hit for e in evaluations) / n
    top3_prec = 100.0 * sum(e.top3_overlap for e in evaluations) / (3 * n)
    fav_top3_prec = 100.0 * sum(e.favorite_top3_overlap for e in evaluations) / (3 * n)

    return EvaluationSummary(
        races_tested=n,
        period_from=dates[0] if dates else "",
        period_to=dates[-1] if dates else "",
        winner_hit_rate=round(winner_rate, 2),
        favorite_winner_hit_rate=round(fav_winner_rate, 2),
        top3_precision=round(top3_prec, 2),
        favorite_top3_precision=round(fav_top3_prec, 2),
        edge_vs_favorite=round(winner_rate - fav_winner_rate, 2),
        top3_hit_rate=round(100.0 * sum(e.top3_hit for e in evaluations) / n, 2),
        top5_hit_rate=round(100.0 * sum(e.top5_hit for e in evaluations) / n, 2),
        quinte_hit_rate=round(100.0 * sum(e.quinte_hit for e in evaluations) / n, 2),
        tierce_hit_rate=round(100.0 * sum(e.tierce_hit for e in evaluations) / n, 2),
        base_hit_rate=round(100.0 * sum(e.base_hit for e in evaluations) / n, 2),
        avg_brier=round(sum(e.brier for e in evaluations) / n, 6),
        avg_log_loss=round(sum(e.log_loss for e in evaluations) / n, 6),
        avg_roi=round(sum(e.roi for e in evaluations) / n, 4),
        method=method,
        details=evaluations,
    )
