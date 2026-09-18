"""
CLI — génère le pronostic complet d'une course.

Exemples
--------
    python -m ml.scripts.run_prediction --list
    python -m ml.scripts.run_prediction --race 930
    python -m ml.scripts.run_prediction --date 2026-09-10
    python -m ml.scripts.run_prediction --demo
"""
from __future__ import annotations

import argparse
import json
import sys

from ..config import load_config
from ..data.providers import build_provider
from ..prediction.engine import generate_prediction


def _print_prediction(pred) -> None:
    payload = pred.as_api_payload()
    race = payload["race"]
    p = payload["prediction"]

    print("=" * 68)
    print(f"  {race['hippodrome']} — {race['date']}  ({race['discipline']} {race['distance'] or '?'}m)")
    print(f"  {race['fieldSize']} partants   |   source : {race['source'].upper()}")
    print("=" * 68)
    print(f"  Modèle     : {p['modelVersion']} / {p['predictionVersion']}")
    print(f"  Qualité    : {p['dataQuality']}")
    print(f"  Confiance  : {p['confidence']}")
    for reason in p["confidenceReasons"]:
        print(f"               - {reason}")
    print()
    print(f"  BASE       : {' - '.join(map(str, p['bases']))}")
    print(f"  CHANCES    : {' - '.join(map(str, p['chances']))}")
    print(f"  OUTSIDERS  : {' - '.join(map(str, p['outsiders']))}")
    print(f"  QUINTÉ     : {' - '.join(map(str, p['quinte']))}")
    print(f"  QUINTÉ ÉL. : {' - '.join(map(str, p['quinteElargi']))}")
    print(f"  TIERCÉ     : {' - '.join(map(str, p['tierce']))}")
    print(f"  QUARTÉ+    : {' - '.join(map(str, p['quarte']))}")
    if p["value"]:
        print(f"  VALUE      : {' - '.join(map(str, p['value']))}")
    print()
    print(f"  {'N°':>3} {'RANK':>6} {'WIN%':>6} {'TOP3%':>6} {'TOP5%':>6} "
          f"{'CATB%':>6} {'VALUE':>7} {'SCORE':>6} {'COTE':>6}")
    print("  " + "-" * 64)
    for r in p["runners"]:
        print(f"  {r['number']:>3} {r['rankScore']:>6.1f} {r['winProbability']*100:>6.1f} "
              f"{r['top3Probability']*100:>6.1f} {r['top5Probability']*100:>6.1f} "
              f"{r['catboostProbability']*100:>6.1f} {r['valueEdge']*100:>+6.1f}% "
              f"{r['finalScore']:>6.1f} {r['odds'] or 0:>6.1f}")
    print()
    top = p["runners"][0]
    print(f"  Facteurs favorables (n°{top['number']}) :")
    for f in top["factorsPositive"] or ["—"]:
        print(f"    + {f}")
    print(f"  Facteurs défavorables (n°{top['number']}) :")
    for f in top["factorsNegative"] or ["—"]:
        print(f"    - {f}")
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Génère un pronostic hippique.")
    parser.add_argument("--race", help="identifiant de course (document_id)")
    parser.add_argument("--date", help="date YYYY-MM-DD")
    parser.add_argument("--list", action="store_true", help="liste les courses exploitables")
    parser.add_argument("--demo", action="store_true", help="utilise le fournisseur DEMO")
    parser.add_argument("--json", action="store_true", help="sortie JSON brute")
    parser.add_argument("--limit", type=int, default=10, help="limite pour --list")
    args = parser.parse_args(argv)

    overrides = {"data_provider": "mock"} if args.demo else {}
    cfg = load_config(**overrides)
    provider = build_provider(cfg)

    if args.list:
        if hasattr(provider, "list_race_ids"):
            ids = provider.list_race_ids()
            print(f"{len(ids)} courses exploitables. Dernières {args.limit} :")
            for rid in ids[-args.limit:]:
                race = provider.get_race(rid)
                if race:
                    print(f"  {rid:>6}  {race.date}  {race.hippodrome:<24} "
                          f"{race.discipline:<8} {len(race.active_runners)} partants")
        else:
            for rid in provider.all_race_ids()[:args.limit]:
                print(f"  {rid}")
        return 0

    race_id = args.race
    if not race_id and args.date:
        races = provider.get_races(args.date)
        if not races:
            print(f"Aucune course pour {args.date}", file=sys.stderr)
            return 1
        race_id = races[0].external_id
    if not race_id:
        if hasattr(provider, "list_race_ids"):
            ids = provider.list_race_ids()
            race_id = ids[-1] if ids else None
        elif hasattr(provider, "all_race_ids"):
            race_id = provider.all_race_ids()[-1]
    if not race_id:
        print("Aucune course trouvée.", file=sys.stderr)
        return 1

    pred = generate_prediction(provider, str(race_id), config=cfg)
    if args.json:
        print(json.dumps(pred.as_api_payload(), indent=2, ensure_ascii=False))
    else:
        _print_prediction(pred)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
