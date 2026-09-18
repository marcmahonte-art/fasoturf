"""
CLI — entraînement des modèles Win / Top3 / Top5 (#13, #14).

Découpage **chronologique** obligatoire :

    ... -> train_until -> valid_until -> ... (test)

Exemples
--------
    python -m ml.scripts.train --limit 400
    python -m ml.scripts.train --train-until 2025-06-30 --valid-until 2025-12-31
"""
from __future__ import annotations

import argparse
import json

from ..config import ARTIFACTS_DIR, load_config
from ..data.providers import build_provider
from ..evaluation.metrics import brier_score, log_loss, roc_auc
from ..models.catboost_model import TARGETS, train_all_targets
from ..models.dataset import build_dataset, rank_dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Entraîne les modèles de probabilité.")
    parser.add_argument("--limit", type=int, default=0, help="limiter le nombre de courses")
    parser.add_argument("--train-until", default=None)
    parser.add_argument("--valid-until", default=None)
    parser.add_argument("--version", default="v1")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args(argv)

    overrides = {"data_provider": "mock"} if args.demo else {}
    cfg = load_config(**overrides)
    if args.train_until:
        cfg.train_until = args.train_until
    if args.valid_until:
        cfg.valid_until = args.valid_until

    provider = build_provider(cfg)
    race_ids = provider.list_race_ids() if hasattr(provider, "list_race_ids") else provider.all_race_ids()
    if args.limit:
        race_ids = race_ids[:args.limit]

    print(f"Construction du dataset sur {len(race_ids)} courses...")
    dataset = build_dataset(provider, race_ids, config=cfg, verbose=False)
    stats = rank_dataset(dataset)
    print(f"  lignes : {stats['rows']}   courses : {stats['races']}")
    print(f"  positifs -> win {stats['positive_win']} | top3 {stats['positive_top3']} "
          f"| top5 {stats['positive_top5']}")
    if not dataset.rows:
        print("Dataset vide : rien à entraîner.")
        return 1

    train, valid, test = dataset.split_chronological(cfg.train_until, cfg.valid_until)
    print(f"  split  -> train {len(train)} | valid {len(valid)} | test {len(test)}")

    X_train, y_train = train.split_xy()
    X_valid, y_valid = valid.split_xy() if len(valid) else ([], {t: [] for t in TARGETS})

    models = train_all_targets(X_train, y_train, dataset.feature_names, version=args.version)
    print(f"\nModèles entraînés (backend : {models['win'].backend})")
    print(f"  features : {len(dataset.feature_names)}")

    # Évaluation sur validation (ou train si validation vide)
    X_eval, y_eval = (X_valid, y_valid) if len(valid) else (X_train, y_train)
    label = "validation" if len(valid) else "train"
    print(f"\nMétriques sur {label} :")
    for target in TARGETS:
        # Les lignes de cible inconnue (-1) sont exclues, comme à l'entraînement.
        pairs = [(x, y) for x, y in zip(X_eval, y_eval[target]) if y != -1]
        if not pairs:
            print(f"  {target:<5} (aucune ligne exploitable)")
            continue
        X_t = [x for x, _ in pairs]
        y_true = [y for _, y in pairs]
        proba = models[target].predict_proba(X_t)
        auc = roc_auc(y_true, proba)
        brier = brier_score(y_true, proba)
        ll = log_loss(y_true, proba)
        models[target].metrics = {"roc_auc": auc, "brier": brier, "log_loss": ll,
                                  "n": len(y_true), "split": label}
        print(f"  {target:<5} AUC {auc:.4f} | Brier {brier:.4f} | LogLoss {ll:.4f} | n={len(y_true)}")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    for target, model in models.items():
        path = model.save()
        print(f"  sauvegardé : {path.name}")

    (ARTIFACTS_DIR / "training_report.json").write_text(
        json.dumps({
            "version": args.version,
            "backend": models["win"].backend,
            "dataset": stats,
            "split": {"train": len(train), "valid": len(valid), "test": len(test)},
            "metrics": {t: models[t].metrics for t in TARGETS},
        }, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
