#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 7 — VALIDATION DU SIGNAL DE DIVERGENCE (robustesse)
=========================================================

La Phase 6 a trouvé un « signal faible » : dans la tranche « forte divergence
positive » (le marché sous-classe un cheval que la forme recommande), le taux de
victoire réel (4,42 %) dépasse l'implicite (3,92 %) — ratio 1,129, ROI −0,77 %,
mais IC énorme et P(+EV) = 46,7 %.

Ce script teste si ce ratio > 1 est **réel ou du hasard** :

  1. RÉPLICATION sur le split `val` (données jamais utilisées pour ce test).
  2. STABILITÉ TEMPORELLE : on coupe le test en deux moitiés par date.
  3. TEST DE PERMUTATION : on re-tire le gagnant de chaque course **selon les
     probabilités du marché** (null = « le marché a raison »), 2 000 fois, et on
     regarde si le ratio observé (1,129) sort de la distribution nulle.
     → C'est LE test qui dit si la divergence apporte de l'information AU-DELÀ du marché.

Mesure pure : aucun ré-entraînement (modèle figé `models/form_model_v1.json`).

Usage : python scripts/phase7/validate_divergence.py
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
OUT_JSON = ROOT / "manifest_phase7_divergence.json"
REPORT = ROOT / "PHASE7_REPORT.md"

N_PERM = 2000
SEED = 20260914
POS_DELTA = 3


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


def load_split(conn, artifact, split):
    cols = ", ".join(["runner_id", "race_id", "date", "m_prob_norm", "m_rank", "m_implied"]
                     + FORM_FEATURES + ["label_win"])
    rows = conn.execute(
        f"SELECT {cols} FROM market_runner_features WHERE split=? "
        f"ORDER BY date, race_id, runner_id", (split,)
    ).fetchall()
    Xraw = [[float(r[c]) if r[c] is not None else float("nan") for c in FORM_FEATURES] for r in rows]
    pf = apply_model(artifact, Xraw)
    by_race = {}
    for r, p in zip(rows, pf):
        by_race.setdefault(r["race_id"], []).append((r, p))
    recs = []
    for rid, lst in by_race.items():
        order = sorted(lst, key=lambda t: (-t[1], t[0]["runner_id"]))
        frank = {t[0]["runner_id"]: i + 1 for i, t in enumerate(order)}
        for r, p in lst:
            mr, fr = r["m_rank"], frank[r["runner_id"]]
            recs.append({
                "race_id": rid, "runner_id": r["runner_id"], "date": r["date"],
                "m_rank": mr, "f_rank": fr, "delta": (mr - fr) if (mr and fr) else None,
                "p_market": r["m_prob_norm"] or 0.0, "win": int(r["label_win"] or 0),
                "cote": (1.0 / r["m_implied"]) if r["m_implied"] else None,
            })
    return recs


def bucket_stats(recs, pred):
    sel = [x for x in recs if pred(x["delta"])]
    if not sel:
        return None
    n = len(sel)
    real = sum(x["win"] for x in sel) / n
    imp = sum(x["p_market"] for x in sel) / n
    roi = sum((x["win"] * x["cote"] - 1.0) for x in sel if x["cote"]) / n
    return {"n": n, "real": real, "imp": imp, "ratio": real / imp if imp else float("nan"), "roi": roi}


def perm_test(recs, pred, obs_ratio, obs_roi, n_perm=N_PERM, seed=SEED):
    """Null : le gagnant de chaque course est tiré ~ probabilités du marché."""
    rnd = random.Random(seed)
    by_race = {}
    for x in recs:
        by_race.setdefault(x["race_id"], []).append(x)
    sel = [x for x in recs if pred(x["delta"])]
    if not sel:
        return None
    imp = sum(x["p_market"] for x in sel) / len(sel)
    ratios, rois = [], []
    for _ in range(n_perm):
        wins = {}
        for rid, lst in by_race.items():
            tot = sum(x["p_market"] for x in lst)
            if tot <= 0:
                continue
            r = rnd.random() * tot
            acc = 0.0
            for x in lst:
                acc += x["p_market"]
                if r <= acc:
                    wins[x["runner_id"]] = 1
                    break
        real = sum(wins.get(x["runner_id"], 0) for x in sel) / len(sel)
        ratios.append(real / imp if imp else float("nan"))
        rois.append(sum((wins.get(x["runner_id"], 0) * x["cote"] - 1.0)
                        for x in sel if x["cote"]) / len(sel))
    p_ratio = (1 + sum(1 for v in ratios if v >= obs_ratio)) / (n_perm + 1)
    p_roi = (1 + sum(1 for v in rois if v >= obs_roi)) / (n_perm + 1)
    ratios.sort()
    return {
        "p_value_ratio": p_ratio,
        "p_value_roi": p_roi,
        "null_ratio_p50": ratios[n_perm // 2],
        "null_ratio_p95": ratios[int(0.95 * n_perm)],
        "null_ratio_mean": sum(ratios) / n_perm,
    }


POS = lambda d: d is not None and d >= POS_DELTA


def main() -> int:
    artifact = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    conn = open_ro(MASTER_DB)
    val = load_split(conn, artifact, "val")
    test = load_split(conn, artifact, "test")
    conn.close()

    print("=" * 90)
    print("  PHASE 7 — VALIDATION DU SIGNAL DE DIVERGENCE")
    print("=" * 90)

    out = {}

    # 1) réplication val / test
    print("\n[1] RÉPLICATION (tranche « forte divergence positive », delta >= 3)")
    print(f"{'split':<10} {'n':>5} {'réel':>8} {'implicite':>10} {'ratio':>7} {'ROI':>9}")
    for name, recs in (("val", val), ("test", test)):
        st = bucket_stats(recs, POS)
        out[f"replication_{name}"] = st
        print(f"{name:<10} {st['n']:>5} {100*st['real']:>7.2f}% {100*st['imp']:>9.2f}% "
              f"{st['ratio']:>7.3f} {100*st['roi']:>8.2f}%")

    # 2) stabilité temporelle sur test
    print("\n[2] STABILITÉ TEMPORELLE (test coupé en 2 par date)")
    dates = sorted({x["date"] for x in test})
    mid = dates[len(dates) // 2]
    halves = [("1ʳᵉ moitié", [x for x in test if x["date"] < mid]),
              ("2ᵉ moitié", [x for x in test if x["date"] >= mid])]
    print(f"{'moitié':<12} {'n':>5} {'réel':>8} {'implicite':>10} {'ratio':>7} {'ROI':>9}")
    for name, recs in halves:
        st = bucket_stats(recs, POS)
        out[f"temporal_{name}"] = st
        if st:
            print(f"{name:<12} {st['n']:>5} {100*st['real']:>7.2f}% {100*st['imp']:>9.2f}% "
                  f"{st['ratio']:>7.3f} {100*st['roi']:>8.2f}%")

    # 3) test de permutation sur test
    print(f"\n[3] TEST DE PERMUTATION (null = le marché a raison, {N_PERM} tirages)")
    obs = out["replication_test"]
    pt = perm_test(test, POS, obs["ratio"], obs["roi"])
    out["permutation_test"] = {**pt, "obs_ratio": obs["ratio"], "obs_roi": obs["roi"]}
    print(f"  ratio observé     : {obs['ratio']:.3f}")
    print(f"  ratio nul (moy)   : {pt['null_ratio_mean']:.3f}  "
          f"(p50 {pt['null_ratio_p50']:.3f}, p95 {pt['null_ratio_p95']:.3f})")
    print(f"  p-value (ratio)   : {pt['p_value_ratio']:.4f}")
    print(f"  p-value (ROI)     : {pt['p_value_roi']:.4f}")

    # verdict honnête
    sig = pt["p_value_ratio"] < 0.05
    repl = (out.get("replication_val", {}) or {}).get("ratio", 0) > 1.0
    if sig and repl:
        verdict = "SIGNAL ROBUSTE (ratio hors du hasard ET répliqué sur val)"
    elif sig:
        verdict = "SIGNAL NON RÉPLIQUÉ (significatif sur test, mais pas confirmé sur val)"
    elif repl:
        verdict = "SIGNAL FAIBLE PERSISTANT (ratio > 1 sur val et test, mais non significatif)"
    else:
        verdict = "BRUIT (non significatif et non répliqué)"
    out["verdict"] = verdict
    print(f"\nVERDICT : {verdict}")

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"écrit : {OUT_JSON}")

    write_report(out)
    print(f"écrit : {REPORT}")
    print("STATUS: PASS")
    return 0


def write_report(out) -> None:
    rt = out["replication_test"]
    rv = out.get("replication_val")
    pt = out["permutation_test"]
    L = []
    a = L.append
    a("# PHASE 7 — VALIDATION DU SIGNAL DE DIVERGENCE")
    a("")
    a("**Statut :** `PASS` · mesure pure, aucun ré-entraînement, socle lu en lecture seule.")
    a("")
    a("## Question")
    a("")
    a("La Phase 6 a relevé un « signal faible » : la tranche où le marché **sous-classe** un "
      "cheval que la forme recommande (delta ≥ 3) affichait un ratio réel/implicite de 1,129 "
      "et un ROI de −0,77 %. **Est-ce réel ou du hasard ?**")
    a("")
    a("## 1. Réplication sur deux échantillons hors entraînement")
    a("")
    a("| Split | n | Taux réel | Implicite | Ratio | ROI |")
    a("|---|---:|---:|---:|---:|---:|")
    for name in ("val", "test"):
        st = out.get(f"replication_{name}")
        if st:
            a(f"| {name} | {st['n']} | {100*st['real']:.2f} % | {100*st['imp']:.2f} % | "
              f"**{st['ratio']:.3f}** | {100*st['roi']:.2f} % |")
    a("")
    a("## 2. Stabilité temporelle (test coupé en deux par date)")
    a("")
    a("| Moitié | n | Taux réel | Implicite | Ratio | ROI |")
    a("|---|---:|---:|---:|---:|---:|")
    for name in ("1ʳᵉ moitié", "2ᵉ moitié"):
        st = out.get(f"temporal_{name}")
        if st:
            a(f"| {name} | {st['n']} | {100*st['real']:.2f} % | {100*st['imp']:.2f} % | "
              f"**{st['ratio']:.3f}** | {100*st['roi']:.2f} % |")
    a("")
    a("## 3. Test de permutation (le test décisif)")
    a("")
    a("Hypothèse nulle : **le gagnant de chaque course est tiré selon les probabilités du "
      "marché** (le marché a raison). On re-tire 2 000 fois et on regarde si le ratio observé "
      "sort de la distribution nulle.")
    a("")
    a("| Mesure | Valeur |")
    a("|---|---|")
    a(f"| Ratio observé | **{rt['ratio']:.3f}** |")
    a(f"| Ratio nul — moyenne | {pt['null_ratio_mean']:.3f} |")
    a(f"| Ratio nul — médiane | {pt['null_ratio_p50']:.3f} |")
    a(f"| Ratio nul — p95 | {pt['null_ratio_p95']:.3f} |")
    a(f"| **p-value (ratio)** | **{pt['p_value_ratio']:.4f}** |")
    a(f"| p-value (ROI) | {pt['p_value_roi']:.4f} |")
    a("")
    a("## Verdict")
    a("")
    a(f"### {out['verdict']}")
    a("")
    if pt["p_value_ratio"] >= 0.05:
        a("Le ratio observé **n'est pas distinguable du hasard** : sous l'hypothèse « le marché "
          "a raison », un ratio au moins aussi élevé apparaît dans une proportion non "
          "négligeable des tirages. **Le signal de divergence n'apporte pas d'information "
          "démontrée au-delà du marché.**")
    else:
        a("Le ratio observé sort de la distribution nulle — piste à confirmer sur données futures.")
    a("")
    a("> ⚠️ Rappel : ce résultat porte sur un socle dont les cotes sont un **instantané "
      "pré-course** (Phase 5). Même un signal réel ne serait pas nécessairement exploitable.")
    a("")
    a("---")
    a("")
    a("**PHASE 7 COMPLETE — WAITING FOR HUMAN VALIDATION**")
    REPORT.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
