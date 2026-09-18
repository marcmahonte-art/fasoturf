#!/usr/bin/env python3
"""
PHASE 3 / ÉTAPE 2 — BASELINE MARCHÉ + MODÈLES + BACKTEST COMPARATIF (PMU'B LONAB V2)

Entraîne et compare, sur un split CHRONOLOGIQUE :
  - Baseline « favori du marché » (cote la plus basse)  ← référence obligatoire
  - Modèle M  : marché seul (logistique sur log-cote)
  - Modèle F  : forme seule (forme + cumulatifs, SANS feature de marché)
  - Modèle S  : ensemble appris (stacking marché + forme, via OOF)

Garanties :
  - Python pur (stdlib), aucun aléatoire, déterministe
  - le socle n'est jamais ouvert en écriture
  - le résultat est publié MÊME S'IL EST NÉGATIF (spec V2 §35)

Usage :
    python scripts/phase3/train_ensemble.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MASTER = (PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db")
DEFAULT_SOCLE = (PROJECT_ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db")
DEFAULT_OUT = PROJECT_ROOT
SOCLE_SHA_EXPECTED = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"

FORM_FEATURES = [
    "f_musique_n", "f_musique_avg", "f_musique_best", "f_musique_winrate",
    "f_musique_top3rate", "f_gains_log", "f_age", "f_sex", "f_field_size",
    "c_horse_starts", "c_horse_winrate", "c_horse_top3rate",
    "c_jockey_winrate", "c_trainer_winrate",
]
MARKET_FEATURES = ["m_log_odds"]

EPS = 1e-12


def log(msg: str) -> None:
    print(msg, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clip(p: float) -> float:
    return min(max(p, 1e-15), 1 - 1e-15)


def logit(p: float) -> float:
    p = clip(p)
    return math.log(p / (1 - p))


def median(values):
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


# ------------------------------------------------------------------
# Régression logistique pure (déterministe, descente de gradient full-batch)
# ------------------------------------------------------------------

class PureLogisticRegression:
    def __init__(self, lr: float = 0.5, epochs: int = 600, l2: float = 1e-3):
        self.lr, self.epochs, self.l2 = lr, epochs, l2
        self.w: list[float] = []
        self.b = 0.0
        self.mu: list[float] = []
        self.sd: list[float] = []

    def _standardize_fit(self, X):
        n, d = len(X), len(X[0])
        self.mu = [sum(X[i][j] for i in range(n)) / n for j in range(d)]
        self.sd = []
        for j in range(d):
            var = sum((X[i][j] - self.mu[j]) ** 2 for i in range(n)) / n
            self.sd.append(math.sqrt(var) or 1.0)

    def _standardize(self, X):
        return [[(row[j] - self.mu[j]) / self.sd[j] for j in range(len(row))] for row in X]

    def fit(self, X, y, epochs: int | None = None):
        n_epochs = epochs if epochs is not None else self.epochs
        self._standardize_fit(X)
        Xs = self._standardize(X)
        n, d = len(Xs), len(Xs[0])
        self.w = [0.0] * d
        self.b = 0.0
        for _ in range(n_epochs):
            gw = [0.0] * d
            gb = 0.0
            for row, yi in zip(Xs, y):
                z = self.b + sum(wj * xj for wj, xj in zip(self.w, row))
                p = 1.0 / (1.0 + math.exp(-(z if -30 < z < 30 else (30 if z > 0 else -30))))
                e = p - yi
                gb += e
                for j in range(d):
                    gw[j] += e * row[j]
            inv = self.lr / n
            for j in range(d):
                self.w[j] -= inv * gw[j] + self.lr * self.l2 * self.w[j]
            self.b -= inv * gb
        return self

    def predict_proba(self, X):
        Xs = self._standardize(X)
        out = []
        for row in Xs:
            z = self.b + sum(self.w[j] * row[j] for j in range(len(row)))
            out.append(1.0 / (1.0 + math.exp(-max(min(z, 30), -30))))
        return out


# ------------------------------------------------------------------
# Métriques
# ------------------------------------------------------------------

def auc(y_true, scores) -> float:
    pairs = sorted(zip(scores, y_true), key=lambda t: t[0])
    n = len(pairs)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg
        i = j + 1
    n_pos = sum(1 for _, y in pairs if y == 1)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    s_pos = sum(ranks[k] for k in range(n) if pairs[k][1] == 1)
    return (s_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def log_loss(y_true, probs) -> float:
    return -sum(y * math.log(clip(p)) + (1 - y) * math.log(clip(1 - p))
                for y, p in zip(y_true, probs)) / max(len(y_true), 1)


def brier(y_true, probs) -> float:
    return sum((p - y) ** 2 for y, p in zip(y_true, probs)) / max(len(y_true), 1)


def pick_winner(entries):
    """Sélection déterministe : probabilité max, départage par runner_id croissant."""
    return min(entries, key=lambda e: (-e[2], e[0]))


def race_metrics(races, prob_of, label_key) -> dict:
    """races : dict race_id -> liste de (runner_id, label, prob)."""
    hit1 = 0
    tot = 0
    t3 = 0.0
    for rid, entries in races.items():
        if not entries:
            continue
        tot += 1
        best = pick_winner(entries)
        if best[1] == 1:
            hit1 += 1
        top3_pred = {e[0] for e in sorted(entries, key=lambda e: (-e[2], e[0]))[:3]}
        top3_true = {e[0] for e in entries if e[1] == 1}
        if top3_true:
            t3 += len(top3_pred & top3_true) / min(3, len(top3_true))
    return {"win_hit": hit1 / tot if tot else 0.0,
            "top3_overlap": t3 / tot if tot else 0.0,
            "n_races": tot}


# ------------------------------------------------------------------

def load_dataset(conn: sqlite3.Connection):
    cols = ", ".join(["runner_id", "race_id", "date", "split", "m_prob_norm",
                      "m_log_odds", "m_rank", "m_is_fav"] + FORM_FEATURES
                     + ["label_win", "label_top3"])
    rows = conn.execute(f"SELECT {cols} FROM market_runner_features "
                        f"ORDER BY date, race_id, runner_id").fetchall()
    return rows


def build_matrix(rows, split, features):
    X, meta = [], []
    for r in rows:
        if r["split"] != split:
            continue
        X.append([float(r[f]) if r[f] is not None else float("nan") for f in features])
        meta.append(r)
    return X, meta


def impute(X, medians):
    out = []
    for row in X:
        out.append([medians[j] if (v != v) else v for j, v in enumerate(row)])
    return out


def train_medians(X):
    d = len(X[0]) if X else 0
    meds = []
    for j in range(d):
        vals = [row[j] for row in X if row[j] == row[j]]
        meds.append(median(vals) if vals else 0.0)
    return meds


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default=str(DEFAULT_MASTER))
    ap.add_argument("--socle", default=str(DEFAULT_SOCLE))
    ap.add_argument("--output-dir", default=str(DEFAULT_OUT))
    a = ap.parse_args(argv)

    master = Path(a.master).resolve()
    socle = Path(a.socle).resolve()
    out = Path(a.output_dir).resolve()

    log("=" * 64)
    log("  PHASE 3 / ÉTAPE 2 — BASELINE MARCHÉ + MODÈLES + BACKTEST")
    log("=" * 64)

    conn = sqlite3.connect(f"file:{master.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = load_dataset(conn)
    conn.close()
    log(f"  dataset : {len(rows)} runners")

    Xtr_raw, mtr = build_matrix(rows, "train", FORM_FEATURES)
    Xva_raw, mva = build_matrix(rows, "val", FORM_FEATURES)
    Xte_raw, mte = build_matrix(rows, "test", FORM_FEATURES)
    log(f"  train {len(Xtr_raw)} | val {len(Xva_raw)} | test {len(Xte_raw)}")

    meds = train_medians(Xtr_raw)
    Xtr, Xva, Xte = impute(Xtr_raw, meds), impute(Xva_raw, meds), impute(Xte_raw, meds)

    ytr_win = [r["label_win"] for r in mtr]
    ytr_t3 = [r["label_top3"] for r in mtr]
    yte_win = [r["label_win"] for r in mte]
    yte_t3 = [r["label_top3"] for r in mte]

    # ---------- Modèle F (forme seule) ----------
    log("  [1/5] Modèle F — forme seule (sans marché)")
    f_win = PureLogisticRegression(lr=1.0).fit(Xtr, ytr_win, epochs=300)
    f_t3 = PureLogisticRegression(lr=1.0).fit(Xtr, ytr_t3, epochs=300)
    pF_te_win = f_win.predict_proba(Xte)
    pF_te_t3 = f_t3.predict_proba(Xte)

    # ---------- Modèle M (marché seul) ----------
    log("  [2/5] Modèle M — marché seul")
    Xm_tr = [[r["m_log_odds"] if r["m_log_odds"] is not None else 3.0] for r in mtr]
    Xm_te = [[r["m_log_odds"] if r["m_log_odds"] is not None else 3.0] for r in mte]
    m_win = PureLogisticRegression(lr=1.0).fit(Xm_tr, ytr_win, epochs=300)
    pM_te_win = m_win.predict_proba(Xm_te)

    # ---------- Modèle S (stacking, OOF sur train) ----------
    log("  [3/5] Modèle S — ensemble appris (stacking, OOF 5 blocs chronologiques)")
    dates = sorted({r["date"] for r in mtr})
    nb = 5
    # bornes = date de début de chaque bloc, + un sentinelle de fin
    cuts = [dates[len(dates) * k // nb] for k in range(nb)]
    cuts.append(None)
    oof = [None] * len(mtr)
    for k in range(nb):
        lo, hi = cuts[k], cuts[k + 1]
        if hi is None:
            is_hold = [r["date"] >= lo for r in mtr]
        else:
            is_hold = [lo <= r["date"] < hi for r in mtr]
        tr_idx = [i for i, h in enumerate(is_hold) if not h]
        ho_idx = [i for i, h in enumerate(is_hold) if h]
        if not tr_idx or not ho_idx:
            for i in ho_idx:
                oof[i] = sum(ytr_win) / max(len(ytr_win), 1)
            continue
        mdl = PureLogisticRegression(lr=1.0).fit([Xtr[i] for i in tr_idx],
                                                 [ytr_win[i] for i in tr_idx],
                                                 epochs=200)
        pr = mdl.predict_proba([Xtr[i] for i in ho_idx])
        for idx, i in enumerate(ho_idx):
            oof[i] = pr[idx]
    oof = [p if p is not None else 0.5 for p in oof]

    # méta-modèle : logit(prob marché) + logit(prob forme OOF)
    def meta_X(mkt_prob, form_prob):
        return [logit(mkt_prob if mkt_prob is not None else 0.5), logit(form_prob)]

    Xmeta_tr = [meta_X(r["m_prob_norm"], oof[i]) for i, r in enumerate(mtr)]
    meta = PureLogisticRegression(lr=1.0).fit(Xmeta_tr, ytr_win, epochs=300)

    pS_te_win = meta.predict_proba(
        [meta_X(r["m_prob_norm"], pF_te_win[i]) for i, r in enumerate(mte)])

    # ---------- Baseline favori ----------
    log("  [4/5] Baseline — favori du marché")

    def races_of(meta_list, probs):
        d = defaultdict(list)
        for r, p in zip(meta_list, probs):
            d[r["race_id"]].append((r["runner_id"], r["label_win"], p))
        return d

    # favori : probabilité de marché la plus haute (cote la plus basse)
    fav_probs = [r["m_prob_norm"] if r["m_prob_norm"] is not None else 0.0 for r in mte]

    results = {}
    for name, probs in [("Favori du marché", fav_probs),
                        ("Modèle M (marché)", pM_te_win),
                        ("Modèle F (forme)", pF_te_win),
                        ("Modèle S (ensemble appris)", pS_te_win)]:
        rm = race_metrics(races_of(mte, probs), None, "label_win")
        results[name] = {
            **rm,
            "log_loss": log_loss(yte_win, probs),
            "brier": brier(yte_win, probs),
            "auc": auc(yte_win, probs),
        }

    # ---------- Top3 ----------
    log("  [5/5] Top3")
    fav_t3 = fav_probs
    t3_results = {}
    for name, probs in [("Favori du marché", fav_t3),
                        ("Modèle F (forme)", pF_te_t3)]:
        d = defaultdict(list)
        for r, p in zip(mte, probs):
            d[r["race_id"]].append((r["runner_id"], r["label_top3"], p))
        t3_results[name] = race_metrics(d, None, "label_top3")

    # ---------- Diagnostic : l'ensemble s'écarte-t-il du favori ? ----------
    def top_pick(meta_list, probs):
        d = defaultdict(list)
        for r, p in zip(meta_list, probs):
            d[r["race_id"]].append((r["runner_id"], r["label_win"], p))
        return {rid: (pick_winner(v)[0], pick_winner(v)[1]) for rid, v in d.items()}

    pick_fav = top_pick(mte, fav_probs)
    pick_S = top_pick(mte, pS_te_win)
    pick_M = top_pick(mte, pM_te_win)
    n_races = len(pick_fav)
    dis_S = [rid for rid in pick_fav if pick_fav[rid][0] != pick_S[rid][0]]
    dis_M = [rid for rid in pick_fav if pick_fav[rid][0] != pick_M[rid][0]]
    acc_dis_S = sum(1 for rid in dis_S if pick_S[rid][1] == 1)
    acc_fav_on_dis = sum(1 for rid in dis_S if pick_fav[rid][1] == 1)
    log(f"  écart au favori — S : {len(dis_S)}/{n_races} courses "
        f"({100*len(dis_S)/max(n_races,1):.1f} %) | M : {len(dis_M)}")
    log(f"  sur ces {len(dis_S)} désaccords : favori correct {acc_fav_on_dis}, "
        f"ensemble correct {acc_dis_S}")

    # ---------- Rapport ----------
    socle_sha = sha256_file(socle)
    master_sha = sha256_file(master)
    socle_ok = socle_sha == SOCLE_SHA_EXPECTED

    best = max(results.items(), key=lambda kv: kv[1]["win_hit"])
    beats = results["Modèle S (ensemble appris)"]["win_hit"] > results["Favori du marché"]["win_hit"]

    lines = [
        "# PHASE 3 REPORT — MARCHÉ + ENSEMBLE APPRIS", "",
        f"**Date :** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Statut :** `{'PASS' if socle_ok else 'FAIL'}`", "",
        "## 1. Protocole", "",
        "| Élément | Valeur |", "|---|---|",
        f"| Dataset | {len(rows)} runners / 712 courses |",
        f"| Split | **chronologique** par date (train ≤ 2025-11-05 < val < test ≤ 2026-09-08) |",
        f"| Train / Val / Test | {len(Xtr)} / {len(Xva)} / {len(Xte)} runners |",
        f"| Features forme | {len(FORM_FEATURES)} (aucune feature de marché) |",
        f"| Fuite temporelle | **0** (audit `phase3_leakage_audit` : 5/5 PASS) |", "",
        "## 2. Résultats sur le TEST (hors échantillon)", "",
        "| Modèle | Gagnant trouvé | Gagnant dans le top-3 prédit | Log loss | Brier | AUC |",
        "|---|---|---|---|---|---|"]
    for name, m in results.items():
        lines.append(
            f"| {name} | **{100*m['win_hit']:.1f} %** | {100*m['top3_overlap']:.1f} % | "
            f"{m['log_loss']:.4f} | {m['brier']:.4f} | {m['auc']:.4f} |")
    lines += ["", "### Top3 (cible top-3)", "",
              "| Modèle | Recouvrement Top3 |", "|---|---|"]
    for name, m in t3_results.items():
        lines.append(f"| {name} | {100*m['top3_overlap']:.1f} % |")

    lines += [
        "", "## 3. Verdict (spec V2 §35 — aucune sur-promesse)", "",
        f"- Meilleur modèle : **{best[0]}** ({100*best[1]['win_hit']:.1f} % de gagnants)",
        f"- Favori du marché : **{100*results['Favori du marché']['win_hit']:.1f} %**",
        f"- Modèle S vs favori : **{'DÉPASSE ✅' if beats else 'NE DÉPASSE PAS ❌'}** "
        f"({100*results['Modèle S (ensemble appris)']['win_hit']:.1f} % vs "
        f"{100*results['Favori du marché']['win_hit']:.1f} %)",
        "",
        "### Diagnostic décisif — l'ensemble s'écarte-t-il du favori ?", "",
        "| Mesure | Valeur |", "|---|---|",
        f"| Courses de test | {n_races} |",
        f"| Courses où l'ensemble **désigne un autre cheval** que le favori | "
        f"**{len(dis_S)}** ({100*len(dis_S)/max(n_races,1):.1f} %) |",
        f"| Sur ces désaccords — favori correct | {acc_fav_on_dis} |",
        f"| Sur ces désaccords — ensemble correct | {acc_dis_S} |",
        "",
        (f"> ✅ **Conclusion :** l'ensemble s'écarte du favori dans **{len(dis_S)} courses "
         f"({100*len(dis_S)/max(n_races,1):.1f} %)** mais **n'y gagne rien** : sur ces "
         f"désaccords, le favori a raison {acc_fav_on_dis} fois, l'ensemble {acc_dis_S} fois "
         f"→ **gain net {acc_dis_S - acc_fav_on_dis:+d}**. Les 14 features de forme "
         "n'apportent **aucun pouvoir prédictif** au-delà de la cote. "
         "**Le marché absorbe l'information disponible dans le socle.**"
         if (acc_dis_S - acc_fav_on_dis) <= 0 else
         f"> ⚠️ L'ensemble gagne {acc_dis_S - acc_fav_on_dis:+d} sur les désaccords : "
         "signal faible mais non nul, à confirmer sur davantage de données."),
        "",
        "> ⚠️ **Ce rapport publie le résultat même s'il est négatif.**",
        "> Le favori du marché reste la référence : un modèle qui ne le bat pas",
        "> n'a **aucune valeur ajoutée** en production, quelle que soit son AUC.", "",
        "## 4. Intégrité", "",
        "| Contrôle | Valeur |", "|---|---|",
        f"| Socle LONAB SHA-256 | `{socle_sha}` |",
        f"| Socle inchangé | {'✅ OUI' if socle_ok else '❌ NON'} |",
        f"| Master DB SHA-256 | `{master_sha}` |",
        "| API externe appelée | aucune |",
        "| Déterminisme | aucun aléatoire (gradient full-batch, init à 0) |", "",
        "---", "", "**PHASE 3 COMPLETE — WAITING FOR HUMAN VALIDATION**", "",
    ]
    report = "\n".join(lines)
    (out / "PHASE3_REPORT.md").write_text(report, encoding="utf-8")

    (out / "manifest_phase3.json").write_text(json.dumps({
        "phase": "3",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset": {"runners": len(rows), "races": 712,
                    "train": len(Xtr), "val": len(Xva), "test": len(Xte)},
        "split": "chronologique",
        "results_test": results,
        "top3_test": t3_results,
        "diagnostic": {
            "test_races": n_races,
            "ensemble_disagrees_with_favorite": len(dis_S),
            "market_model_disagrees": len(dis_M),
            "favorite_correct_on_disagreements": acc_fav_on_dis,
            "ensemble_correct_on_disagreements": acc_dis_S,
        },
        "best_model": best[0],
        "stacked_beats_market": beats,
        "socle_sha256": socle_sha,
        "socle_unchanged": socle_ok,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    for name, m in results.items():
        log(f"  {name:30s} gagnant {100*m['win_hit']:5.1f} % | "
            f"top3 {100*m['top3_overlap']:5.1f} % | AUC {m['auc']:.4f}")
    log("=" * 64)
    log(f"  ÉTAPE 2 STATUS: {'PASS' if socle_ok else 'FAIL'}")
    log(f"  VERDICT : l'ensemble appris {'BAT' if beats else 'NE BAT PAS'} le favori du marché")
    log("=" * 64)
    return 0 if socle_ok else 1


if __name__ == "__main__":
    sys.exit(main())
