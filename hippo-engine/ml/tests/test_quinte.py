"""Tests du générateur de Quinté (#22) et de la logique de sélection (#21)."""
from __future__ import annotations

from ml.prediction.quinte import RankedEntry, quinte_combinations, select


def _entry(number: int, score: float, *, top3=0.3, top5=0.5, catb=0.15,
           value=0.0, odds=10.0, is_value=False, reg=0.5) -> RankedEntry:
    return RankedEntry(
        number=number, final_score=score, rank_score=score,
        win_probability=catb, top3_probability=top3, top5_probability=top5,
        catboost_probability=catb, value_score=max(value * 100, 0),
        value_edge=value, odds=odds, confidence="MEDIUM",
        is_value=is_value, regularity=reg,
    )


class TestSelection:
    def test_quinte_has_five_horses(self):
        entries = [_entry(n, 90 - n * 3, top3=0.5 - n * 0.02, top5=0.7 - n * 0.02)
                   for n in range(1, 15)]
        sel = select(entries)
        assert len(sel.quinte) == 5
        assert len(set(sel.quinte)) == 5, "Le Quinté ne doit pas contenir de doublon"

    def test_bases_are_best_scores(self):
        entries = [_entry(n, 90 - n * 3, top3=0.5 - n * 0.02, top5=0.7 - n * 0.02)
                   for n in range(1, 15)]
        sel = select(entries)
        # Les bases doivent provenir du haut du classement
        assert all(b <= 5 for b in sel.bases)

    def test_no_overlap_between_categories(self):
        entries = [_entry(n, 90 - n * 3) for n in range(1, 15)]
        sel = select(entries)
        assert not (set(sel.bases) & set(sel.chances))
        assert not (set(sel.bases) & set(sel.outsiders))

    def test_value_detection(self):
        entries = [
            _entry(1, 90, top3=0.5, top5=0.7, value=0.10, is_value=True, odds=15),
            _entry(2, 85, top3=0.45, top5=0.65),
            _entry(3, 80, top3=0.4, top5=0.6),
        ]
        sel = select(entries)
        assert 1 in sel.value

    def test_rationale_is_provided(self):
        entries = [_entry(n, 90 - n * 3) for n in range(1, 10)]
        sel = select(entries)
        assert "base" in sel.rationale
        assert len(sel.rationale["base"]) > 0

    def test_empty_input(self):
        sel = select([])
        assert sel.quinte == []
        assert sel.bases == []


class TestCombinations:
    def test_champ_total_count(self):
        entries = [_entry(n, 90 - n * 3, top3=0.5, top5=0.7) for n in range(1, 12)]
        sel = select(entries)
        combos = quinte_combinations(sel, champ_reduit=False)
        n = combos["taille_champ"]
        expected = n * (n - 1) * (n - 2) * (n - 3) * (n - 4)
        assert combos["combinaisons_ordre"] == expected

    def test_champ_reduit_is_smaller(self):
        entries = [_entry(n, 90 - n * 3, top3=0.5, top5=0.7) for n in range(1, 16)]
        sel = select(entries)
        reduit = quinte_combinations(sel, champ_reduit=True)
        total = quinte_combinations(sel, champ_reduit=False)
        assert reduit["taille_champ"] <= total["taille_champ"]

    def test_desordre_is_sorted(self):
        entries = [_entry(n, 90 - n * 3, top3=0.5, top5=0.7) for n in range(1, 12)]
        sel = select(entries)
        combos = quinte_combinations(sel)
        assert combos["quinte_desordre"] == sorted(combos["quinte_desordre"])
