"""
CLI — backtesting (#30).

Exemple
-------
    python -m ml.scripts.backtest_cli --from 2026-01-01 --to 2026-09-30
    python -m ml.scripts.backtest_cli --all --models
"""
from __future__ import annotations

import argparse
import json

from ..config import ARTIFACTS_DIR, load_config
from ..data.providers import build_provider
from ..evaluation.backtest import run_backtest
from ..models.catboost_model import TARGETS, ProbabilityModel


def _load_models() -> dict | None:
    models = {}
    for target in TARGETS:
        path = ARTIFACTS_DIR / f"catboost_{target}_v1.json"
        if not path.exists():
            return None
        models[target] = ProbabilityModel.load(path)
    return models


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backtest du moteur de pronostics.")
    parser.add_argument("--from", dest="date_from", help="date de début YYYY-MM-DD")
    parser.add_argument("--to", dest="date_to", help="date de fin YYYY-MM-DD")
    parser.add_argument("--all", action="store_true", help="toutes les courses")
    parser.add_argument("--models", action="store_true", help="utiliser les modèles entraînés")
    parser.add_argument("--json", action="store_true", help="sortie JSON")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args(argv)

    overrides = {"data_provider": "mock"} if args.demo else {}
    cfg = load_config(**overrides)
    provider = build_provider(cfg)

    if hasattr(provider, "list_race_ids"):
        race_ids = provider.list_race_ids(
            date_from=None if args.all else args.date_from,
            date_to=None if args.all else args.date_to,
        )
    else:
        race_ids = provider.all_race_ids()

    models = _load_models() if args.models else None
    if args.models and models is None:
        print("Aucun modèle entraîné trouvé dans les artefacts ; "
              "exécutez d'abord : python -m ml.scripts.train")
        return 1

    print(f"Backtest sur {len(race_ids)} courses "
          f"({'modèles entraînés' if models else 'score RANK seul'})...")
    result = run_backtest(provider, race_ids, config=cfg, models=models, verbose=True)
    s = result.summary

    if args.json:
        print(json.dumps({
            "summary": s.as_dict(),
            "by_month": result.by_month,
            "by_hippodrome": result.by_hippodrome,
            "by_race_type": result.by_race_type,
            "by_odds_range": result.by_odds_range,
        }, indent=2, ensure_ascii=False))
        return 0

    print()
    print("=" * 62)
    print("  RESULTAT DU BACKTEST")
    print("=" * 62)
    print(f"  courses testées       : {s.races_tested}")
    print(f"  période               : {s.period_from} -> {s.period_to}")
    print(f"  méthodologie          : {s.method}")
    print()
    print("  --- Modèle vs référence marché ---")
    print(f"  gagnant trouvé        : {s.winner_hit_rate:>6.1f} %")
    print(f"  favori du marché      : {s.favorite_winner_hit_rate:>6.1f} %")
    print(f"  écart                 : {s.edge_vs_favorite:>+6.1f} pts")
    print(f"  précision top 3       : {s.top3_precision:>6.1f} %")
    print(f"  précision top 3 marché: {s.favorite_top3_precision:>6.1f} %")
    print()
    print("  --- Probabilités ---")
    print(f"  Brier moyen           : {s.avg_brier:.4f}   (0.25 = aléatoire)")
    print(f"  Log loss moyen        : {s.avg_log_loss:.4f}")
    print(f"  ROI moyen (VALUE)     : {s.avg_roi * 100:+.2f} %")
    print()
    print("  --- Par tranche de cote (favori du jour) ---")
    for name, stats in result.by_odds_range.items():
        print(f"    {name:<22} n={stats['races']:<4} "
              f"top3 {stats['top3_hit_rate']:>5.1f}%  ROI {stats['avg_roi']*100:>+6.2f}%")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
