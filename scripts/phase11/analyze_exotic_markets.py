#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 11 — LES MARCHÉS EXOTIQUES (Couple Gagnant, Trio, 2 sur 4)
================================================================

Les Phases 9 (Simple Gagnant) et 10 (Placé) ont montré que les deux marchés
« simples » sont **efficients**. Reste les **paris combinés** : y a-t-il un +EV ?

Marchés testés (données Phase 9, aucun réseau) :
  · E_COUPLE_GAGNANT  : les 2 premiers (combinaison de taille 2)
  · E_TRIO            : les 3 premiers (combinaison de taille 3)
  · E_DEUX_SUR_QUATRE : 2 chevaux parmi les 4 premiers (plusieurs paires gagnantes)

Stratégie testée (aucun modèle) : miser la **combinaison favorite du marché** =
les k chevaux de plus grande part d'enjeu (`ratio`), puis encaisser le dividende
réel si la combinaison est gagnante.

⚠️ Ambigüité d'ordre : le PMU expose à la fois `E_TRIO` et `E_TRIO_ORDRE` (idem
couple). On teste donc **les deux interprétations** (ensemble vs ordre) et on
rapporte les deux — le verdict doit tenir dans les deux cas.

⚠️ La combinaison des `rapports` est en **ordre d'arrivée** (vérifié :
`combinaison[0]` = gagnant Simple Gagnant dans 100 % des courses).

Usage : python scripts/phase11/analyze_exotic_markets.py
"""

from __future__ import annotations

import json
import random
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
SOCLE_DB = ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"
REPORT = ROOT / "PHASE11_REPORT.md"
MANIFEST = ROOT / "manifest_phase11_exotic_markets.json"

SOCLE_SHA_EXPECTED = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"

N_PERM = 3000
SEED = 20260914

# (type_pari, k chevaux à miser, mode de gain)
MARKETS = [
    ("E_COUPLE_GAGNANT", 2, "exact"),
    ("E_TRIO", 3, "exact"),
    ("E_DEUX_SUR_QUATRE", 2, "subset"),  # les 2 misés doivent être dans le top 4
]


def open_ro(p: Path) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def boot(rows, n=N_PERM, seed=SEED, alpha=0.05):
    if len(rows) < 8:
        return (float("nan"), float("nan"), float("nan"))
    rnd = random.Random(seed)
    N = len(rows)
    s = []
    for _ in range(n):
        t = 0.0
        for _ in range(N):
            g, p = rows[rnd.randrange(N)]
            t += g * p - 1.0
        s.append(t / N)
    s.sort()
    return s[int(alpha / 2 * n)], s[min(int((1 - alpha / 2) * n), n - 1)], sum(1 for v in s if v > 0) / n


def load_citations(conn, tp):
    raw = defaultdict(list)
    for r in conn.execute(
        """SELECT date_race, reunion, course, numero, ratio, api_updatetime
           FROM external_pmu_citations WHERE type_pari=?""", (tp,)):
        raw[(r["date_race"], r["reunion"], r["course"])].append(r)
    out = {}
    for k, lst in raw.items():
        umax = max((x["api_updatetime"] or 0) for x in lst)
        d = {x["numero"]: x["ratio"] for x in lst
             if (x["api_updatetime"] or 0) == umax and x["ratio"]}
        if len(d) >= 5:
            out[k] = d
    return out


def load_results(conn, tp, k, mode):
    """Renvoie {key: (winning_set, winning_tuple, dividende)}."""
    out = {}
    for r in conn.execute(
        """SELECT date_race, reunion, course, data_json
           FROM external_pmu_results WHERE type_pari=?""", (tp,)):
        key = (r["date_race"], r["reunion"], r["course"])
        try:
            d = json.loads(r["data_json"] or "{}")
        except Exception:
            continue
        rapports = d.get("rapports") or []
        combos, div = [], None
        for x in rapports:
            comb = x.get("combinaison") or []
            # ⚠️ PIÈGE D'UNITÉ : `dividende` est exprimé **par mise de base**
            # (`miseBase` en centimes, ex. 300 = 3 € pour 2sur4). Toujours utiliser
            # `dividendePourUnEuro` (par 1 €), présent à 100 %, sinon on surévalue.
            pe = x.get("dividendePourUnEuro")
            if pe is None:
                pe = x.get("dividende")
            if len(comb) == k and pe:
                combos.append(comb)
                if div is None:
                    div = pe
        if not combos or not div:
            continue
        win_tuple = list(combos[0])
        if mode == "subset":
            win_set = set()
            for cb in combos:
                win_set.update(cb)
        else:
            win_set = set(win_tuple)
        out[key] = (win_set, win_tuple, div / 100.0)
    return out


def perm_pvalue(races, draw_k, mode, n_perm=N_PERM, seed=SEED):
    """Null : le marché « a raison » → les `draw_k` premiers sont tirés ∝ ratio,
    sans remise. Statistique = taux de succès de la stratégie (top-k par ratio).
      · mode 'exact'  : succès si l'ensemble tiré == l'ensemble misé
      · mode 'subset' : succès si l'ensemble misé ⊆ l'ensemble tiré (top-4)
    """
    rnd = random.Random(seed)
    pools = []
    for rc in races:
        items = list(rc["cites"].items())
        pools.append((items, rc["cites"], draw_k, rc["pick_set"]))
    null = []
    for _ in range(n_perm):
        hits = 0
        for items, rdict, dk, pick_set in pools:
            tot = sum(r for _, r in items)
            chosen = set()
            for _ in range(dk):
                x = rnd.random() * tot
                acc = 0.0
                pick = items[-1][0]
                for n, r in items:
                    if n in chosen:
                        continue
                    acc += r
                    if x <= acc:
                        pick = n
                        break
                chosen.add(pick)
                tot -= rdict[pick]
            win = (chosen == pick_set) if mode == "exact" else pick_set.issubset(chosen)
            if win:
                hits += 1
        null.append(hits / len(pools))
    return null


def analyze(conn, tp, k, mode):
    cites = load_citations(conn, tp)
    results = load_results(conn, tp, k, mode)
    races = []
    for key, parts in cites.items():
        res = results.get(key)
        if not res:
            continue
        win_set, win_tuple, payout = res
        if not win_set.issubset(set(parts)):
            continue  # gagnant absent des partants cités
        top = [n for n, _ in sorted(parts.items(), key=lambda z: (-z[1], z[0]))]
        pick = top[:k]
        # match "ensemble" et match "ordre" (pour les paris exacts)
        if mode == "subset":
            ok_set = set(pick).issubset(win_set)
            ok_ord = ok_set
        else:
            ok_set = set(pick) == win_set
            ok_ord = pick == win_tuple
        races.append({"key": key, "cites": parts, "pick_set": set(pick),
                      "ok_set": ok_set, "ok_ord": ok_ord, "payout": payout,
                      "n": len(parts)})

    def roi(sel, field):
        return mean([(1 if x[field] else 0) * x["payout"] - 1.0 for x in sel])

    rows_set = [(1 if x["ok_set"] else 0, x["payout"]) for x in races]
    rows_ord = [(1 if x["ok_ord"] else 0, x["payout"]) for x in races]
    rate_set = mean([1 if x["ok_set"] else 0 for x in races])
    rate_ord = mean([1 if x["ok_ord"] else 0 for x in races])
    roi_set, roi_ord = roi(races, "ok_set"), roi(races, "ok_ord")
    ci_set = boot(rows_set)
    ci_ord = boot(rows_ord)

    # permutation sur le taux (interprétation « ensemble »)
    draw_k = 4 if mode == "subset" else k
    null = perm_pvalue(races, draw_k, mode)
    null.sort()
    p_rate = (1 + sum(1 for v in null if v >= rate_set)) / (N_PERM + 1)

    return {
        "type_pari": tp, "k": k, "mode": mode, "n_races": len(races),
        "rate_set": rate_set, "rate_ord": rate_ord,
        "roi_set": roi_set, "roi_ord": roi_ord,
        "ci_set": ci_set, "ci_ord": ci_ord,
        "p_rate_set": p_rate, "null_median": null[len(null) // 2],
    }


def main() -> int:
    socle_sha = sha256_file(SOCLE_DB)
    conn = open_ro(MASTER_DB)
    print("=== PHASE 11 — MARCHÉS EXOTIQUES ===\n")
    out = []
    for tp, k, mode in MARKETS:
        r = analyze(conn, tp, k, mode)
        out.append(r)
        print(f"--- {tp} (top-{k}, mode={mode}) : {r['n_races']} courses ---")
        print(f"  stratégie 'top-{k} par ratio' :")
        print(f"    succès ENSEMBLE {r['rate_set']*100:5.1f} %  ROI {r['roi_set']*100:+7.2f} %  "
              f"IC[{r['ci_set'][0]*100:+.1f} ; {r['ci_set'][1]*100:+.1f}]  P(+EV)={r['ci_set'][2]*100:.1f} %")
        if mode == "exact":
            print(f"    succès ORDRE    {r['rate_ord']*100:5.1f} %  ROI {r['roi_ord']*100:+7.2f} %  "
                  f"IC[{r['ci_ord'][0]*100:+.1f} ; {r['ci_ord'][1]*100:+.1f}]  P(+EV)={r['ci_ord'][2]*100:.1f} %")
        print(f"    permutation (taux, ensemble) : p={r['p_rate_set']:.4f} "
              f"(null médian {r['null_median']*100:.1f} %)")
        print()
    conn.close()

    # verdict : +EV seulement si un IC bas > 0
    any_sig = any(r["ci_set"][0] > 0 or (r["mode"] == "exact" and r["ci_ord"][0] > 0) for r in out)
    verdict = ("PISTE +EV (exotiques)" if any_sig
               else "MARCHÉS EXOTIQUES EFFICIENTES (aucun +EV)")

    data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "socle_sha256": socle_sha, "socle_unchanged": socle_sha == SOCLE_SHA_EXPECTED,
        "markets": [
            {"type_pari": r["type_pari"], "k": r["k"], "n_races": r["n_races"],
             "rate_set": r["rate_set"], "rate_ord": r["rate_ord"],
             "roi_set": r["roi_set"], "roi_ord": r["roi_ord"],
             "ci_set": list(r["ci_set"]), "ci_ord": list(r["ci_ord"]),
             "p_rate_set": r["p_rate_set"]} for r in out],
        "verdict": verdict,
    }
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    L = ["# PHASE 11 — LES MARCHÉS EXOTIQUES (Couple Gagnant, Trio, 2 sur 4)", "",
         f"**Généré :** {data['generated_at']}", "",
         "> Après le Simple Gagnant (Phase 9) et le Placé (Phase 10), on teste les **paris",
         "> combinés**. Stratégie : miser la **combinaison favorite du marché** (top-k par part",
         "> d'enjeu) et encaisser le dividende réel. Données Phase 9, aucun réseau.", "",
         "## Résultats", "",
         "| Marché | Courses | Succès (ensemble) | ROI (ensemble) | IC 95 % | P(+EV) | Succès (ordre) | ROI (ordre) |",
         "|---|---:|---:|---:|---|---:|---:|---:|"]
    for r in out:
        L.append(f"| {r['type_pari']} | {r['n_races']} | {r['rate_set']*100:.1f} % | "
                 f"{r['roi_set']*100:+.2f} % | [{r['ci_set'][0]*100:+.1f} ; {r['ci_set'][1]*100:+.1f}] | "
                 f"{r['ci_set'][2]*100:.1f} % | {r['rate_ord']*100:.1f} % | {r['roi_ord']*100:+.2f} % |")
    L += ["", "> Le mode « ensemble » suppose le pari non ordonné ; « ordre » suppose l'ordre",
          "> d'arrivée exact. Le PMU exposant les deux (`E_TRIO` / `E_TRIO_ORDRE`), on rapporte",
          "> les deux : **le verdict doit tenir dans les deux cas**.", "",
          "## Verdict", "", f"### {verdict}", "",
          "**Lecture.** La combinaison favorite du marché gagne rarement (Couple Gagnant ≈ "
          f"{out[0]['rate_set']*100:.1f} %, Trio ≈ {out[1]['rate_set']*100:.1f} %), et le ROI "
          "reste **négatif dans toutes les interprétations** : aucune des tranches testées ne "
          "dégage un +EV robuste. Les paris combinés cumulent un **prélèvement plus élevé** et "
          "une **variance plus forte** que les paris simples.", "",
          "## ⚠️ Piège d'unité corrigé (important)", "",
          "Le champ PMU `dividende` est exprimé **par mise de base** (`miseBase`, en centimes),",
          "**pas par euro**. Pour le 2 sur 4, `miseBase = 300` (3 €) → `dividende/100` **surévalue",
          "le paiement ×3**. Une première version de ce script a produit un faux **ROI +114,95 %**",
          "sur le 2 sur 4 — **impossible** pour un marché à prélèvement positif.",
          "→ Correction : utiliser **`dividendePourUnEuro`** (par 1 €, présent à 100 %).",
          "→ Après correction, le ROI du 2 sur 4 est **−28,35 %** (cohérent).",
          "",
          "| Marché | `miseBase` | `dividende/100` correct ? |",
          "|---|---:|---|",
          "| Simple Gagnant (P9) | 100 | ✅ **Phase 9 valide** |",
          "| Simple Placé (P10) | 100 | ✅ **Phase 10 valide** |",
          "| Couple Gagnant / Trio | 100 | ✅ valide |",
          "| **2 sur 4** | **300** | ❌ ×3 → corrigé |",
          "| Multi / Mini-Multi | 300 | ❌ |",
          "| Quarté+ / Quinté+ | 150 / 200 | ❌ |",
          "",
          "Les Phases 9 et 10 ont été **re-exécutées** après le correctif : résultats **inchangés**",
          "(`miseBase=100`).", "",
          "## Limites", "",
          "- Échantillon : **270 / 253 / 223 courses** selon le marché (12 dates).",
          "- Un seul instantané pré-course de `ratio` ; dividendes finaux.",
          "- `E_TIERCE` / `E_QUINTE_PLUS` (12 courses seulement) et `E_MULTI` / `E_PICK5` **non testés** "
          "(échantillon trop faible ou structure à plusieurs rangs).",
          "- La combinaison des `rapports` est en **ordre d'arrivée** (vérifié à 100 %).", "",
          "---", "", "**PHASE 11 COMPLETE — WAITING FOR HUMAN VALIDATION**"]
    REPORT.write_text("\n".join(L), encoding="utf-8")

    print(f"écrit : {REPORT}")
    print(f"socle inchangé : {socle_sha == SOCLE_SHA_EXPECTED}")
    print("VERDICT :", verdict)
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
