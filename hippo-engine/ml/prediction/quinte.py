"""
Générateurs de pronostics (#21-24).

Logique de sélection **explicable** :

    BASE      : score final élevé + forte proba Top3 + faible incertitude
    CHANCE    : score élevé + régularité + proba Top5 élevée
    OUTSIDER  : value positive + score raisonnable + proba non négligeable
    VALUE     : model_probability > implied_probability

Produit : Quinté (ordre/désordre/champ réduit/champ total), Tiercé, Quarté+.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RankedEntry:
    """Un partant classé, avec toutes ses métriques."""
    number: int
    final_score: float
    rank_score: float
    win_probability: float
    top3_probability: float
    top5_probability: float
    catboost_probability: float
    value_score: float
    value_edge: float
    odds: float | None
    confidence: str
    is_value: bool = False
    regularity: float = 0.0


@dataclass(slots=True)
class Selection:
    bases: list[int] = field(default_factory=list)
    chances: list[int] = field(default_factory=list)
    outsiders: list[int] = field(default_factory=list)
    value: list[int] = field(default_factory=list)
    quinte: list[int] = field(default_factory=list)
    quinte_elargi: list[int] = field(default_factory=list)
    tierce: list[int] = field(default_factory=list)
    quarte: list[int] = field(default_factory=list)
    rationale: dict[str, list[str]] = field(default_factory=dict)


def rank_entries(entries: list[RankedEntry]) -> list[RankedEntry]:
    return sorted(entries, key=lambda e: e.final_score, reverse=True)


def _uncertainty(entry: RankedEntry) -> float:
    """Faible incertitude = accord entre les modèles. 0 = très sûr."""
    signals = [entry.top3_probability, entry.catboost_probability]
    if not signals:
        return 1.0
    spread = max(signals) - min(signals)
    return spread


def select(
    entries: list[RankedEntry],
    *,
    n_base: int = 2,
    n_chance: int = 3,
    n_outsider: int = 2,
    value_threshold: float = 0.03,
) -> Selection:
    """Construit la sélection complète à partir des partants classés."""
    ordered = rank_entries(entries)
    if not ordered:
        return Selection()

    sel = Selection()

    # --- BASE : score élevé, forte proba Top3, faible incertitude ---
    base_candidates = [
        e for e in ordered
        if e.top3_probability >= 0.25 and _uncertainty(e) <= 0.35
    ]
    if len(base_candidates) < n_base:
        base_candidates = ordered[:max(n_base, 3)]
    sel.bases = [e.number for e in base_candidates[:n_base]]
    sel.rationale["base"] = [
        f"n°{e.number} : score {e.final_score:.1f}, Top3 {e.top3_probability:.1%}, "
        f"accord modèles {1 - _uncertainty(e):.0%}"
        for e in base_candidates[:n_base]
    ]

    used = set(sel.bases)

    # --- CHANCES : score élevé + régularité + Top5 élevée ---
    chance_pool = [
        e for e in ordered
        if e.number not in used and e.top5_probability >= 0.35
    ]
    if len(chance_pool) < n_chance:
        chance_pool = [e for e in ordered if e.number not in used]
    sel.chances = [e.number for e in chance_pool[:n_chance]]
    sel.rationale["chance"] = [
        f"n°{e.number} : Top5 {e.top5_probability:.1%}, régularité {e.regularity:.2f}"
        for e in chance_pool[:n_chance]
    ]
    used.update(sel.chances)

    # --- OUTSIDERS : value positive + score raisonnable ---
    outsider_pool = [
        e for e in ordered
        if e.number not in used and e.is_value and e.final_score >= 35.0
    ]
    if not outsider_pool:
        # Repli explicable : les mieux classés restants à cote >= 10
        outsider_pool = [
            e for e in ordered
            if e.number not in used and (e.odds or 0) >= 10.0
        ]
    sel.outsiders = [e.number for e in outsider_pool[:n_outsider]]
    sel.rationale["outsider"] = [
        f"n°{e.number} : value {e.value_edge:+.1%} (cote {e.odds}), score {e.final_score:.1f}"
        for e in outsider_pool[:n_outsider]
    ]

    # --- VALUE : model_probability > implied_probability ---
    sel.value = [e.number for e in ordered if e.is_value]
    sel.rationale["value"] = [
        f"n°{e.number} : edge {e.value_edge:+.1%} (cote {e.odds})"
        for e in ordered if e.is_value
    ]

    # --- QUINTÉ : bases + chances + 1er outsider ---
    quinte = list(sel.bases) + list(sel.chances)
    if sel.outsiders:
        quinte.append(sel.outsiders[0])
    # Compléter si nécessaire par les mieux classés restants
    for e in ordered:
        if len(quinte) >= 5:
            break
        if e.number not in quinte:
            quinte.append(e.number)
    sel.quinte = quinte[:5]

    # --- QUINTÉ ÉLARGI : 7 chevaux ---
    elargi = list(sel.quinte)
    outsider_entries = [x for x in ordered if x.number in sel.outsiders]
    remainder = [x for x in ordered if x.number not in elargi]
    for entry in outsider_entries + remainder:
        if len(elargi) >= 7:
            break
        if entry.number not in elargi:
            elargi.append(entry.number)
    sel.quinte_elargi = elargi

    # --- TIERCÉ / QUARTÉ+ : les meilleurs du classement ---
    sel.tierce = [e.number for e in ordered[:3]]
    sel.quarte = [e.number for e in ordered[:4]]

    return sel


def quinte_combinations(sel: Selection, *, champ_reduit: bool = False) -> dict:
    """
    Formules de jeu (#22). Le champ réduit se limite à base + chances,
    le champ total couvre la sélection élargie.
    """
    if champ_reduit:
        pool = list(dict.fromkeys(sel.bases + sel.chances))
    else:
        pool = list(dict.fromkeys(sel.quinte_elargi or sel.quinte))
    n = len(pool)
    # Nombre de combinaisons ordonnées de 5 parmi n
    combos = 1
    for i in range(5):
        combos *= max(n - i, 0)
    return {
        "type": "champ_reduit" if champ_reduit else "champ_total",
        "chevaux": pool,
        "taille_champ": n,
        "combinaisons_ordre": combos,
        "cout_unite_1euro": combos,
        "quinte_ordre": sel.quinte,
        "quinte_desordre": sorted(sel.quinte),
    }
