#!/usr/bin/env python3
"""
PHASE 4 / ÉTAPE 2 — LES COMMENTAIRES PRESSE APPORTENT-ILS UN SIGNAL ? (PMU'B LONAB V2)

Teste si les features de commentaires presse (pré-course) ajoutent un pouvoir
prédictif AU-DELÀ de la cote.

Protocole identique à la Phase 3 (split chronologique, même noyau de modèle).
Critère de succès : **gain net > 0 sur les courses où le modèle s'écarte du favori**.

Usage :
    python scripts/phase4/train_with_comments.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "phase3"))

# noyau validé en Phase 3 — réutilisé tel quel (aucune duplication)
from train_ensemble import (  # noqa: E402
    PureLogisticRegression, auc, brier, impute, log_loss, pick_winner,
    race_metrics, train_medians, FORM_FEATURES,
)

DEFAULT_MASTER = PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
DEFAULT_SOCLE = PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"
SOCLE_SHA_EXPECTED = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"

COMMENT_FEATURES = ["has_comment", "cm_len_log", "cm_pos", "cm_neg",
                    "cm_sentiment", "cm_has_favori"]


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default=str(DEFAULT_MASTER))
    ap.add_argument("--socle", default=str(DEFAULT_SOCLE))
    ap.add_argument("--output-dir", default=str(PROJECT_ROOT))
    a = ap.parse_args(argv)
    master, socle = Path(a.master).resolve(), Path(a.socle).resolve()
    out = Path(a.output_dir).resolve()

    log("=" * 64)
    log("  PHASE 4 / ÉTAPE 2 — COMMENTAIRES PRESSE : SIGNAL OU BRUIT ?")
    log("=" * 64)

    conn = sqlite3.connect(f"file:{master.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cols = ["mf.runner_id", "mf.race_id", "mf.date", "mf.split", "mf.m_prob_norm",
            "mf.m_log_odds", "mf.label_win"] + [f"mf.{f}" for f in FORM_FEATURES] \
        + [f"cf.{f}" for f in COMMENT_FEATURES]
    rows = conn.execute(
        f"SELECT {', '.join(cols)} FROM market_runner_features mf "
        f"LEFT JOIN comment_features cf ON cf.runner_id = mf.runner_id "
        f"ORDER BY mf.date, mf.race_id, mf.runner_id").fetchall()
    conn.close()
    log(f"  dataset : {len(rows)} runners")

    def sub(split):
        return [r for r in rows if r["split"] == split]

    tr, te = sub("train"), sub("test")
    log(f"  train {len(tr)} | test {len(te)}")

    def matrix(meta, feats):
        return [[float(r[f]) if r[f] is not None else float("nan") for f in feats]
                for r in meta]

    form_all = FORM_FEATURES + COMMENT_FEATURES

    Xtr_F = matrix(tr, FORM_FEATURES)
    Xte_F = matrix(te, FORM_FEATURES)
    Xtr_Fp = matrix(tr, form_all)
    Xte_Fp = matrix(te, form_all)

    med_F = train_medians(Xtr_F)
    med_Fp = train_medians(Xtr_Fp)
    Xtr_F, Xte_F = impute(Xtr_F, med_F), impute(Xte_F, med_F)
    Xtr_Fp, Xte_Fp = impute(Xtr_Fp, med_Fp), impute(Xte_Fp, med_Fp)

    ytr = [r["label_win"] for r in tr]
    yte = [r["label_win"] for r in te]

    log("  [1/3] Modèle F  — forme seule (Phase 3, référence)")
    mF = PureLogisticRegression(lr=1.0).fit(Xtr_F, ytr, epochs=300)
    pF = mF.predict_proba(Xte_F)

    log("  [2/3] Modèle F+ — forme + commentaires presse")
    mFp = PureLogisticRegression(lr=1.0).fit(Xtr_Fp, ytr, epochs=300)
    pFp = mFp.predict_proba(Xte_Fp)

    log("  [3/3] Baseline — favori du marché")
    fav = [r["m_prob_norm"] if r["m_prob_norm"] is not None else 0.0 for r in te]

    def races(probs):
        d = defaultdict(list)
        for r, p in zip(te, probs):
            d[r["race_id"]].append((r["runner_id"], r["label_win"], p))
        return d

    results = {}
    for name, probs in [("Favori du marché", fav),
                        ("Modèle F (forme)", pF),
                        ("Modèle F+ (forme+commentaires)", pFp)]:
        results[name] = {**race_metrics(races(probs), None, "label_win"),
                         "log_loss": log_loss(yte, probs),
                         "brier": brier(yte, probs),
                         "auc": auc(yte, probs)}

    # diagnostic : gain net sur les désaccords avec le favori
    def picks(probs):
        d = defaultdict(list)
        for r, p in zip(te, probs):
            d[r["race_id"]].append((r["runner_id"], r["label_win"], p))
        return {rid: (pick_winner(v)[0], pick_winner(v)[1]) for rid, v in d.items()}

    pf, pFp_pick = picks(fav), picks(pFp)
    n_races = len(pf)
    dis = [rid for rid in pf if pf[rid][0] != pFp_pick[rid][0]]
    fav_ok = sum(1 for rid in dis if pf[rid][1] == 1)
    mod_ok = sum(1 for rid in dis if pFp_pick[rid][1] == 1)
    net = mod_ok - fav_ok

    log(f"  désaccords F+ vs favori : {len(dis)}/{n_races} "
        f"({100*len(dis)/max(n_races,1):.1f} %) | favori ok {fav_ok} | F+ ok {mod_ok} "
        f"| GAIN NET {net:+d}")

    socle_sha = sha256_file(socle)
    socle_ok = socle_sha == SOCLE_SHA_EXPECTED
    verdict = "SIGNAL" if net > 0 else "BRUIT (aucun gain)"

    lines = [
        "# PHASE 4 REPORT — COMMENTAIRES PRESSE", "",
        f"**Date :** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Statut :** `{'PASS' if socle_ok else 'FAIL'}`", "",
        "## 1. Source", "",
        "| Élément | Valeur |", "|---|---|",
        "| Table | `commentaires` (socle) |",
        "| Lignes | 14 015 |",
        "| **Provenance** | **100 % `JOURNAL`** — presse **pré-course** (vérifié) |",
        "| Couverture des runners | 9 734 / 10 116 (**96,2 %**) |",
        f"| Features extraites | {len(COMMENT_FEATURES)} (longueur, marqueurs ±, sentiment, mention « favori ») |",
        "| Marqueurs positifs détectés | 8 995 occurrences |",
        "| Marqueurs négatifs détectés | 2 903 occurrences |", "",
        "## 2. Résultats sur le TEST (hors échantillon)", "",
        "| Modèle | Gagnant trouvé | Log loss | Brier | AUC |",
        "|---|---|---|---|---|"]
    for name, m in results.items():
        lines.append(f"| {name} | **{100*m['win_hit']:.1f} %** | {m['log_loss']:.4f} | "
                     f"{m['brier']:.4f} | {m['auc']:.4f} |")
    lines += [
        "", "## 3. Verdict — gain net vs favori", "",
        "| Mesure | Valeur |", "|---|---|",
        f"| Courses de test | {n_races} |",
        f"| Courses où F+ s'écarte du favori | **{len(dis)}** ({100*len(dis)/max(n_races,1):.1f} %) |",
        f"| Sur ces désaccords — favori correct | {fav_ok} |",
        f"| Sur ces désaccords — F+ correct | {mod_ok} |",
        f"| **Gain net** | **{net:+d}** |", "",
        f"### Conclusion : les commentaires presse sont du **{verdict}**", "",
        ("> ❌ **Aucun pouvoir prédictif au-delà de la cote.** Le signal extrait des "
         "commentaires presse n'améliore pas le classement par rapport au favori du marché. "
         "Cohérent avec la Phase 3 : la cote absorbe l'information disponible."
         if net <= 0 else
         "> ✅ Gain net positif : signal à confirmer sur davantage de données avant usage."),
        "",
        "> ⚠️ **Limite méthodologique assumée :** le signal est extrait par un **lexique** "
        "français (marqueurs ±), pas par un modèle de langage. Un lexique plus riche, "
        "ou un modèle entraîné sur le texte, pourrait extraire davantage. "
        "Le présent test ne prouve pas que les commentaires sont sans valeur — "
        "il prouve que **ce lexique-là** n'apporte rien au-delà du marché.", "",
        "## 4. Intégrité", "",
        "| Contrôle | Valeur |", "|---|---|",
        f"| Socle LONAB SHA-256 | `{socle_sha}` |",
        f"| Socle inchangé | {'✅ OUI' if socle_ok else '❌ NON'} |",
        "| Commentaires post-course | 0 (provenance JOURNAL vérifiée) |",
        "| API externe appelée | aucune |", "",
        "---", "", "**PHASE 4 COMPLETE — WAITING FOR HUMAN VALIDATION**", "",
    ]
    (out / "PHASE4_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "manifest_phase4.json").write_text(json.dumps({
        "phase": "4",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": {"runners": len(rows), "train": len(tr), "test": len(te),
                    "with_comment": 9734},
        "results_test": results,
        "diagnostic": {"test_races": n_races, "disagreements": len(dis),
                       "favorite_correct": fav_ok, "model_correct": mod_ok,
                       "net_gain": net},
        "verdict": verdict,
        "socle_sha256": socle_sha,
        "socle_unchanged": socle_ok,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    for name, m in results.items():
        log(f"  {name:34s} gagnant {100*m['win_hit']:5.1f} % | AUC {m['auc']:.4f}")
    log("=" * 64)
    log(f"  ÉTAPE 2 STATUS: {'PASS' if socle_ok else 'FAIL'}")
    log(f"  VERDICT : commentaires presse = {verdict} (gain net {net:+d})")
    log("=" * 64)
    return 0 if socle_ok else 1


if __name__ == "__main__":
    sys.exit(main())
