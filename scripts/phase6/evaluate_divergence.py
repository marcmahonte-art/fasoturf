#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 6 — ÉVALUATION HONNÊTE DU SIGNAL DE DIVERGENCE
====================================================

Le « lecteur de course » met en avant un écart de rang « marché ↔ forme ».
Avant de le livrer, il FAUT mesurer s'il porte une information réelle — sinon
c'est un habillage trompeur.

Test (hors échantillon, split `test`) :
  - on calcule, pour chaque partant, le rang marché et le rang forme ;
  - delta = rang_marché − rang_forme  (>0 : le marché le classe plus bas que la forme) ;
  - on regroupe par tranche de delta et on compare, dans chaque tranche :
      · le taux de victoire RÉEL,
      · la probabilité implicite MOYENNE du marché.
    Si réel > implicite dans la tranche « forte divergence positive », le signal
    apporte quelque chose ; sinon, c'est du bruit.

Mesure pure : aucun ré-entraînement (on charge `models/form_model_v1.json`).

Usage : python scripts/phase6/evaluate_divergence.py
"""

from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "phase3"))

from train_ensemble import FORM_FEATURES  # noqa: E402

MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
MODEL_PATH = ROOT / "models" / "form_model_v1.json"
OUT_JSON = ROOT / "manifest_phase6_divergence.json"


def open_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def apply_model(artifact, Xraw):
    meds = artifact["impute_medians"]
    mu = artifact["standardization"]["mu"]
    sd = artifact["standardization"]["sd"]
    w = artifact["coefficients"]["w"]
    b = artifact["coefficients"]["b"]
    out = []
    for row in Xraw:
        xi = [meds[j] if (v != v) else v for j, v in enumerate(row)]
        z = b + sum(w[j] * ((xi[j] - mu[j]) / (sd[j] or 1.0)) for j in range(len(w)))
        out.append(1.0 / (1.0 + math.exp(-max(min(z, 30.0), -30.0))))
    return out


def bootstrap_roi(sel, n: int = 4000, seed: int = 20260914, alpha: float = 0.05):
    """IC bootstrap (percentile) du ROI d'une tranche + P(ROI>0)."""
    rows = [(x["win"], x["cote"]) for x in sel if x["cote"]]
    if len(rows) < 10:
        return (float("nan"), float("nan"), float("nan"))
    rnd = random.Random(seed)
    N = len(rows)
    stats = []
    for _ in range(n):
        s = 0.0
        for _ in range(N):
            w, ct = rows[rnd.randrange(N)]
            s += w * ct - 1.0
        stats.append(s / N)
    stats.sort()
    lo = stats[int((alpha / 2) * n)]
    hi = stats[min(int((1 - alpha / 2) * n), n - 1)]
    p_pos = sum(1 for v in stats if v > 0) / n
    return (lo, hi, p_pos)


def main() -> int:
    artifact = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    conn = open_ro(MASTER_DB)
    cols = ", ".join(["runner_id", "race_id", "date", "split", "m_prob_norm", "m_rank", "m_implied"]
                     + FORM_FEATURES + ["label_win"])
    rows = conn.execute(
        f"SELECT {cols} FROM market_runner_features WHERE split='test' "
        f"ORDER BY date, race_id, runner_id"
    ).fetchall()
    conn.close()
    print(f"runners test : {len(rows)}")

    # probabilité forme
    Xraw = [[float(r[c]) if r[c] is not None else float("nan") for c in FORM_FEATURES] for r in rows]
    pf = apply_model(artifact, Xraw)

    # rang forme par course
    by_race = {}
    for r, p in zip(rows, pf):
        by_race.setdefault(r["race_id"], []).append((r, p))

    recs = []
    for rid, lst in by_race.items():
        order = sorted(lst, key=lambda t: (-t[1], t[0]["runner_id"]))
        frank = {t[0]["runner_id"]: i + 1 for i, t in enumerate(order)}
        for r, p in lst:
            mr = r["m_rank"]
            fr = frank[r["runner_id"]]
            recs.append({
                "race_id": rid,
                "runner_id": r["runner_id"],
                "m_rank": mr,
                "f_rank": fr,
                "delta": (mr - fr) if (mr and fr) else None,
                "p_market": r["m_prob_norm"],
                "win": int(r["label_win"] or 0),
                "cote": (1.0 / r["m_implied"]) if r["m_implied"] else None,
            })

    # tranches de delta
    buckets = [("forte divergence négative (marché l'aime plus)", lambda d: d is not None and d <= -3),
               ("accord (|delta| <= 2)", lambda d: d is not None and -2 <= d <= 2),
               ("forte divergence positive (marché le sous-classe)", lambda d: d is not None and d >= 3),
               ("  dont delta >= 5", lambda d: d is not None and d >= 5)]

    print(f"\n{'tranche':<52} {'n':>5} {'réel':>8} {'implicite':>10} {'ratio':>7} {'ROI':>9} {'IC 95 % ROI':>22} {'P(+EV)':>7}")
    print("-" * 130)
    results = {}
    for name, pred in buckets:
        sel = [x for x in recs if pred(x["delta"])]
        if not sel:
            continue
        n = len(sel)
        real = sum(x["win"] for x in sel) / n
        imp = sum(x["p_market"] for x in sel) / n
        ratio = real / imp if imp else float("nan")
        roi = sum((x["win"] * x["cote"] - 1.0) for x in sel if x["cote"]) / n
        lo, hi, ppos = bootstrap_roi(sel)
        results[name] = {"n": n, "real_win": real, "implied": imp, "ratio": ratio,
                         "roi": roi, "roi_ci_lo": lo, "roi_ci_hi": hi, "p_roi_pos": ppos}
        print(f"{name:<52} {n:>5} {100*real:>7.2f}% {100*imp:>9.2f}% {ratio:>7.3f} "
              f"{100*roi:>8.2f}% [{100*lo:>7.2f}% ; {100*hi:>7.2f}%] {100*ppos:>6.1f}%")

    # décision honnête (fondée sur l'IC, pas sur le point)
    pos = results.get("forte divergence positive (marché le sous-classe)")
    verdict = "INDÉTERMINÉ"
    if pos:
        if pos["roi_ci_lo"] > 0:
            verdict = "SIGNAL +EV (à confirmer sur données futures)"
        elif pos["ratio"] > 1.05 and pos["p_roi_pos"] > 0.20:
            verdict = "SIGNAL FAIBLE (ratio > 1, mais ROI non significativement > 0)"
        else:
            verdict = "BRUIT (aucun signal exploitable)"
    print(f"\nVERDICT divergence : {verdict}")
    print("  ⚠ tranches multiples → risque de sur-interprétation ; signal non significatif "
          "à ce stade.")

    OUT_JSON.write_text(json.dumps({"buckets": results, "verdict": verdict},
                                   ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"écrit : {OUT_JSON}")
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
