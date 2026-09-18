"""
Modèles probabilistes Win / Top3 / Top5 (#10, #11, #12).

Modèle de Plackett-Luce : chaque cheval reçoit une « force » ; l'arrivée est
tirée séquentiellement sans remise. On en déduit :

    P(victoire)  = force_i / somme(forces)
    P(Top 3)     = probabilité d'être dans les 3 premiers
    P(Top 5)     = probabilité d'être dans les 5 premiers

Implémenté en Python pur (aucune dépendance). Déterministe (seed fixe) pour
que les tests soient reproductibles.

Calibration (#12) : après calcul, les probabilités de victoire sont
normalisées pour sommer à 1 sur la course.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass(slots=True)
class ProbabilityResult:
    number: int
    win_probability: float
    top3_probability: float
    top5_probability: float


def strengths_from_scores(
    scores: dict[int, float],
    *,
    temperature: float = 8.0,
    min_strength: float = 1e-6,
) -> dict[int, float]:
    """
    Convertit des scores (0..100) en forces strictement positives via softmax.

    ``temperature`` contrôle la dispersion : plus elle est petite, plus le
    meilleur score domine.
    """
    if not scores:
        return {}
    scaled = {num: s / max(temperature, 1e-6) for num, s in scores.items()}
    peak = max(scaled.values())
    exps = {num: math.exp(v - peak) for num, v in scaled.items()}
    total = sum(exps.values()) or 1.0
    return {num: max(v / total, min_strength) for num, v in exps.items()}


def win_probabilities(strengths: dict[int, float]) -> dict[int, float]:
    """P(victoire) exacte sous Plackett-Luce."""
    total = sum(strengths.values()) or 1.0
    return {num: round(s / total, 6) for num, s in strengths.items()}


def simulate_topk(
    strengths: dict[int, float],
    *,
    k: int,
    n_sims: int = 2000,
    seed: int = 12345,
) -> dict[int, float]:
    """
    Estime P(cheval dans le top k) par simulation Monte-Carlo déterministe.

    Le tirage suit Plackett-Luce : à chaque position, on tire un cheval avec
    une probabilité proportionnelle à sa force parmi les chevaux restants.
    """
    numbers = list(strengths.keys())
    if not numbers:
        return {}
    if len(numbers) <= k:
        return {num: 1.0 for num in numbers}

    rng = random.Random(seed)
    counts = {num: 0 for num in numbers}

    for _ in range(n_sims):
        pool = list(numbers)
        weights = [strengths[n] for n in pool]
        for _pos in range(k):
            total = sum(weights)
            if total <= 0:
                break
            target = rng.random() * total
            cumulative = 0.0
            chosen_idx = len(pool) - 1
            for idx, w in enumerate(weights):
                cumulative += w
                if cumulative >= target:
                    chosen_idx = idx
                    break
            counts[pool[chosen_idx]] += 1
            pool.pop(chosen_idx)
            weights.pop(chosen_idx)

    return {num: round(counts[num] / n_sims, 6) for num in numbers}


def calibrate_win_probabilities(probs: dict[int, float]) -> dict[int, float]:
    """Ramène la somme des probabilités de victoire à 1 (#12)."""
    total = sum(probs.values())
    if total <= 0:
        return probs
    return {num: round(p / total, 6) for num, p in probs.items()}


def compute_probabilities(
    scores: dict[int, float],
    *,
    n_sims: int = 2000,
    seed: int = 12345,
    temperature: float = 8.0,
) -> dict[int, ProbabilityResult]:
    """Calcule Win / Top3 / Top5 pour tous les partants d'une course."""
    strengths = strengths_from_scores(scores, temperature=temperature)
    win = calibrate_win_probabilities(win_probabilities(strengths))
    top3 = simulate_topk(strengths, k=3, n_sims=n_sims, seed=seed)
    top5 = simulate_topk(strengths, k=5, n_sims=n_sims, seed=seed + 1)

    out: dict[int, ProbabilityResult] = {}
    for num in strengths:
        out[num] = ProbabilityResult(
            number=num,
            win_probability=win.get(num, 0.0),
            top3_probability=top3.get(num, 0.0),
            top5_probability=top5.get(num, 0.0),
        )
    return out
