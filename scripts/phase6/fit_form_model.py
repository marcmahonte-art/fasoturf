#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 6 — PIVOT : fige le MODÈLE DE FORME de référence
======================================================

Ce modèle n'est PAS un modèle de paris. C'est un **modèle de référence
descriptif**, dont la performance est MESURÉE et PUBLIÉE (elle est inférieure
au marché — Phases 3/4). Il sert uniquement à produire un **second classement**
pour repérer les divergences « marché ↔ forme ».

- Réutilise le noyau validé de la Phase 3 (aucune réimplémentation).
- Entraîne sur le split `train`, mesure sur `train`/`val`/`test`.
- Écrit `models/form_model_v1.json` (coefficients + standardisation + médianes
  + métriques + métadonnées). Déterministe, stdlib pur.

Usage : python scripts/phase6/fit_form_model.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "phase3"))

from train_ensemble import (  # noqa: E402
    FORM_FEATURES,
    PureLogisticRegression,
    auc,
    brier,
    build_matrix,
    impute,
    load_dataset,
    log_loss,
    train_medians,
)

MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
SOCLE_DB = ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"
MODEL_PATH = ROOT / "models" / "form_model_v1.json"

SOCLE_SHA_EXPECTED = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"

# Config identique à la Phase 3 (modèle F) pour reproductibilité stricte.
LR = 1.0
EPOCHS = 300
L2 = 1e-3


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def open_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default=str(MASTER_DB))
    ap.add_argument("--out", default=str(MODEL_PATH))
    a = ap.parse_args(argv)

    master = Path(a.master).resolve()
    out = Path(a.out).resolve()

    socle_sha = sha256_file(SOCLE_DB)
    if socle_sha != SOCLE_SHA_EXPECTED:
        raise SystemExit(f"ERREUR FATALE : SHA socle inattendu : {socle_sha}")

    conn = open_ro(master)
    rows = load_dataset(conn)
    conn.close()
    print(f"dataset : {len(rows)} runners")

    Xtr_raw, mtr = build_matrix(rows, "train", FORM_FEATURES)
    Xva_raw, mva = build_matrix(rows, "val", FORM_FEATURES)
    Xte_raw, mte = build_matrix(rows, "test", FORM_FEATURES)
    print(f"train {len(Xtr_raw)} | val {len(Xva_raw)} | test {len(Xte_raw)}")

    meds = train_medians(Xtr_raw)
    Xtr = impute(Xtr_raw, meds)
    Xva = impute(Xva_raw, meds)
    Xte = impute(Xte_raw, meds)

    ytr = [int(r["label_win"] or 0) for r in mtr]
    yva = [int(r["label_win"] or 0) for r in mva]
    yte = [int(r["label_win"] or 0) for r in mte]

    model = PureLogisticRegression(lr=LR, epochs=EPOCHS, l2=L2)
    model.fit(Xtr, ytr)

    ptr = model.predict_proba(Xtr)
    pva = model.predict_proba(Xva)
    pte = model.predict_proba(Xte)

    metrics = {}
    for name, y, p in (("train", ytr, ptr), ("val", yva, pva), ("test", yte, pte)):
        metrics[name] = {
            "n": len(y),
            "auc": auc(y, p),
            "log_loss": log_loss(y, p),
            "brier": brier(y, p),
        }
        print(f"  {name:5s} n={len(y):5d}  AUC={metrics[name]['auc']:.4f} "
              f"logloss={metrics[name]['log_loss']:.4f} brier={metrics[name]['brier']:.4f}")

    artifact = {
        "model_name": "form_model_v1",
        "purpose": ("Modele de reference DESCRIPTIF (forme seule). "
                    "Performance inferieure au marche — NE PAS utiliser comme "
                    "promesse de gain. Sert a reperer les divergences marche<->forme."),
        "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "train_config": {"lr": LR, "epochs": EPOCHS, "l2": L2, "split": "train"},
        "features": FORM_FEATURES,
        "impute_medians": meds,
        "standardization": {"mu": model.mu, "sd": model.sd},
        "coefficients": {"w": model.w, "b": model.b},
        "metrics": metrics,
        "n_train": len(Xtr),
        "socle_sha256": socle_sha,
        "note": ("Le marche reste le meilleur predicteur mesure (AUC 0.7560 vs "
                 "0.6856 pour ce modele). Ce modele ne bat PAS le marche."),
    }

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nmodèle écrit : {out}")
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
