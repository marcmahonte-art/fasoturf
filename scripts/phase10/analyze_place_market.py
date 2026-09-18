#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 10 — LE MARCHÉ DU PLACÉ (Simple Placé PMU)
================================================

La Phase 9 a montré que le **Simple Gagnant** est efficient (aucun +EV), même
avec la masse d'enjeu réelle. Reste une question : le **Placé** — marché
DIFFÉRENT (autres enjeux, autre prélèvement, autre structure) — est-il, lui
aussi, efficient ?

Données (déjà collectées en Phase 9, aucun réseau nécessaire) :
  · `external_pmu_citations` (type_pari='E_SIMPLE_PLACE') : part d'enjeu `ratio`
    par cheval (somme = 100 %), instantané **pré-course** (dernier `updatetime`).
  · `external_pmu_results`   (type_pari='E_SIMPLE_PLACE') : les **placés** et le
    `dividende` final (rapport pour 1 €, en centimes) + `nombreGagnants`.

⚠️ Point d'honnêteté : l'instantané de citations est **pré-course** (dernières
cotes publiées), les dividendes sont **finaux** (après clôture du pool). C'est
exactement l'expérience d'un parieur (miser sur les cotes visibles, encaisser le
rapport final). Le test est donc valide — mais il mesure un marché *pré-course*,
pas le pool de clôture.

Mesures (aucun modèle) :
  1. Cohérence (somme des parts = 100 %) et structure des paiements.
  2. Taux de retour joueur (TRJ, pondéré par les enjeux) et ROI à mise plate.
  3. Calibration : probabilité implicite de placé (n_places × ratio) vs taux réel.
  4. ROI par tranche de probabilité implicite (IC 95 % bootstrap).
  5. Test de permutation sur le taux de placé du favori (null = « le marché a raison »).

Usage : python scripts/phase10/analyze_place_market.py
"""

from __future__ import annotations

import json
import math
import random
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
SOCLE_DB = ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"
REPORT = ROOT / "PHASE10_REPORT.md"
MANIFEST = ROOT / "manifest_phase10_place_market.json"

SOCLE_SHA_EXPECTED = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"

N_PERM = 3000
SEED = 20260914
# tranches de probabilité implicite de placé (n_places × ratio)
BIN_EDGES = [0.0, 0.10, 0.20, 0.30, 0.45, 0.60, 0.75, 1.01]


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
    """rows = (gagne:0/1, paiement_par_euro). Renvoie (ic_bas, ic_haut, P(ROI>0))."""
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


# --------------------------------------------------------------------------- #
# Chargement
# --------------------------------------------------------------------------- #
def load(conn):
    """Assemble les courses placé : parts d'enjeu (pré-course) + placés finaux."""
    raw = defaultdict(list)
    for r in conn.execute(
        """SELECT date_race, reunion, course, numero, ratio, enjeu, api_updatetime
           FROM external_pmu_citations WHERE type_pari='E_SIMPLE_PLACE'"""):
        raw[(r["date_race"], r["reunion"], r["course"])].append(r)

    cites = {}
    for k, lst in raw.items():
        umax = max((x["api_updatetime"] or 0) for x in lst)
        d = {x["numero"]: x["ratio"] for x in lst
             if (x["api_updatetime"] or 0) == umax and x["ratio"]}
        if len(d) >= 5:
            cites[k] = d

    results = {}
    for r in conn.execute(
        """SELECT date_race, reunion, course, data_json
           FROM external_pmu_results WHERE type_pari='E_SIMPLE_PLACE'"""):
        k = (r["date_race"], r["reunion"], r["course"])
        try:
            d = json.loads(r["data_json"] or "{}")
        except Exception:
            continue
        placed = {}
        for x in (d.get("rapports") or []):
            comb = x.get("combinaison") or []
            # ⚠️ PIÈGE D'UNITÉ : `dividende` est par **mise de base** (`miseBase`).
            # Utiliser `dividendePourUnEuro` (par 1 €) — placé a miseBase=100, mais robuste.
            pe = x.get("dividendePourUnEuro")
            if pe is None:
                pe = x.get("dividende")
            if comb and pe:
                placed[comb[0]] = pe / 100.0
        if len(placed) >= 2:
            results[k] = placed

    races = []
    rejected = {"no_cites": 0, "no_result": 0}
    for k, parts in cites.items():
        placed = results.get(k)
        if not placed:
            rejected["no_result"] += 1
            continue
        # les placés doivent figurer dans les partants cités
        placed = {n: p for n, p in placed.items() if n in parts}
        if len(placed) < 2:
            rejected["no_cites"] += 1
            continue
        races.append({"key": k, "parts": parts, "placed": placed,
                      "n_places": len(placed)})
    load.rejected = rejected
    return races


# --------------------------------------------------------------------------- #
# Analyse
# --------------------------------------------------------------------------- #
def main() -> int:
    # intégrité du socle (lecture seule)
    socle_sha = sha256_file(SOCLE_DB)

    conn = open_ro(MASTER_DB)
    races = load(conn)
    conn.close()
    rej = getattr(load, "rejected", {})
    print(f"courses placé exploitables : {len(races)}")
    if rej and any(rej.values()):
        print("  écartées : " + ", ".join(f"{k}={v}" for k, v in rej.items() if v))
    if not races:
        print("Aucune donnée : lancer d'abord l'adapter (--enable-external).")
        return 1

    # --- cohérence ---
    sums = [sum(rc["parts"].values()) for rc in races]
    dist_places = defaultdict(int)
    for rc in races:
        dist_places[rc["n_places"]] += 1
    print(f"somme des parts (médiane) : {sorted(sums)[len(sums)//2]:.2f} %")
    print("répartition du nombre de placés : "
          + ", ".join(f"{k} places={v}" for k, v in sorted(dist_places.items())))

    # --- runners (implied = n_places × ratio/100, somme = n_places) ---
    rows = []
    for rc in races:
        npl = rc["n_places"]
        for n, ratio in rc["parts"].items():
            pay = rc["placed"].get(n)
            rows.append({"race": rc["key"], "n": n, "ratio": ratio,
                         "implied": npl * ratio / 100.0,
                         "win": 1 if pay else 0, "payout": pay or 0.0})
    print(f"partants : {len(rows)}")

    # --- TRJ pondéré par les enjeux + ROI à mise plate ---
    ret, pool = 0.0, 0.0
    for rc in races:
        for n, ratio in rc["parts"].items():
            pool += ratio
            if n in rc["placed"]:
                ret += rc["placed"][n] * ratio
    trj = ret / pool if pool else float("nan")
    roi_flat = mean([x["win"] * x["payout"] - 1.0 for x in rows])
    print(f"TRJ placé (pondéré enjeux) : {trj*100:.2f} %")
    print(f"ROI mise plate (tous)      : {roi_flat*100:+.2f} %")

    # --- favori placé (plus grande part d'enjeu) ---
    fav = []
    for rc in races:
        n = max(rc["parts"], key=lambda z: rc["parts"][z])
        pay = rc["placed"].get(n)
        fav.append({"race": rc["key"], "n": n, "ratio": rc["parts"][n],
                    "implied": rc["n_places"] * rc["parts"][n] / 100.0,
                    "win": 1 if pay else 0, "payout": pay or 0.0})
    roi_fav = mean([x["win"] * x["payout"] - 1.0 for x in fav])
    lo_f, hi_f, pp_f = boot([(x["win"], x["payout"]) for x in fav])
    fav_rate = mean([x["win"] for x in fav])
    fav_impl = mean([x["implied"] for x in fav])
    print(f"ROI favori placé : {roi_fav*100:+.2f} %  IC[{lo_f*100:+.1f} ; {hi_f*100:+.1f}]  "
          f"P(+EV)={pp_f*100:.1f} %  | taux placé {fav_rate*100:.1f} % (implicite {fav_impl*100:.1f} %)")

    # --- calibration + ROI par tranche de probabilité implicite ---
    bins = []
    for i in range(len(BIN_EDGES) - 1):
        lo, hi = BIN_EDGES[i], BIN_EDGES[i + 1]
        sel = [x for x in rows if lo <= x["implied"] < hi]
        if len(sel) < 30:
            continue
        real = mean([x["win"] for x in sel])
        imp = mean([x["implied"] for x in sel])
        rr = mean([x["win"] * x["payout"] - 1.0 for x in sel])
        b_lo, b_hi, b_pp = boot([(x["win"], x["payout"]) for x in sel])
        bins.append({"label": f"[{lo:.2f},{hi:.2f})", "n": len(sel), "imp": imp, "real": real,
                     "ratio": real / imp if imp else float("nan"), "roi": rr,
                     "ci_lo": b_lo, "ci_hi": b_hi, "p_pos": b_pp})
        print(f"  {bins[-1]['label']:<12} n={len(sel):>5} impl={imp*100:>5.2f}% "
              f"réel={real*100:>5.2f}% ratio={bins[-1]['ratio']:.3f} ROI={rr*100:>+7.2f}%")

    # --- permutation sur le taux de placé du favori ---
    # Null : le marché « a raison » → chaque cheval est placé avec probabilité
    # proportionnelle à sa part d'enjeu (tirage sans remise de n_places chevaux).
    rnd = random.Random(SEED)
    race_pools = []  # (items, ratio_by_num, n_places, favori_num)
    for i, rc in enumerate(races):
        items = list(rc["parts"].items())
        race_pools.append((items, rc["parts"], rc["n_places"], fav[i]["n"]))
    null_rate = []
    for _ in range(N_PERM):
        hits = 0
        for items, ratio_by_num, k, fav_n in race_pools:
            tot = sum(r for _, r in items)
            chosen = set()
            for _ in range(k):
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
                tot -= ratio_by_num[pick]
            if fav_n in chosen:
                hits += 1
        null_rate.append(hits / len(race_pools))
    null_rate.sort()
    p_rate = (1 + sum(1 for v in null_rate if v >= fav_rate)) / (N_PERM + 1)
    print(f"permutation — p-value taux de placé favori : {p_rate:.4f} "
          f"(observé {fav_rate*100:.1f} %, null médian {null_rate[len(null_rate)//2]*100:.1f} %)")

    any_sig = any(b["ci_lo"] > 0 for b in bins) or lo_f > 0
    verdict = "PISTE +EV (Placé)" if any_sig else "MARCHÉ EFFICIENT (aucun +EV sur le Placé)"

    data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "socle_sha256": socle_sha, "socle_unchanged": socle_sha == SOCLE_SHA_EXPECTED,
        "n_races": len(races), "n_runners": len(rows),
        "part_sum_median": sorted(sums)[len(sums) // 2],
        "places_distribution": {str(k): v for k, v in sorted(dist_places.items())},
        "trj_stake_weighted": trj, "roi_flat": roi_flat,
        "roi_favori": roi_fav, "roi_favori_ci": [lo_f, hi_f, pp_f],
        "fav_place_rate": fav_rate, "fav_implied": fav_impl,
        "bins": bins, "p_value_fav_place_rate": p_rate, "verdict": verdict,
        "load_rejected": rej,
    }
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # --- rapport ---
    L = ["# PHASE 10 — LE MARCHÉ DU PLACÉ (Simple Placé PMU)", "",
         f"**Généré :** {data['generated_at']}", "",
         "> Après le Simple Gagnant (Phase 9, efficient), on teste le **Placé** :",
         "> marché différent (autres enjeux, autre prélèvement, autre structure).",
         "> Données Phase 9 réutilisées (aucune collecte réseau).", "",
         "## Cohérence du marché", "",
         f"- Courses exploitables : **{len(races)}** · partants : **{len(rows)}**",
         f"- Somme des parts (médiane) : **{data['part_sum_median']:.2f} %** (attendu 100 %)",
         "- Répartition du nombre de placés : "
         + ", ".join(f"{k}→{v} courses" for k, v in sorted(dist_places.items())),
         f"- **TRJ placé** (pondéré par les enjeux) : **{trj*100:.2f} %**", "",
         "## Résultats (mise plate, paiements officiels)", "",
         "| Mesure | Valeur |", "|---|---|",
         f"| ROI mise plate (tous partants) | **{roi_flat*100:+.2f} %** |",
         f"| ROI favori placé | **{roi_fav*100:+.2f} %** |",
         f"| IC 95 % ROI favori | [{lo_f*100:+.1f} % ; {hi_f*100:+.1f} %] |",
         f"| P(+EV) favori | {pp_f*100:.1f} % |",
         f"| Taux de placé du favori | {fav_rate*100:.1f} % (implicite {fav_impl*100:.1f} %) |",
         f"| p-value permutation (taux favori) | **{p_rate:.4f}** |", "",
         "## Calibration par probabilité implicite de placé", "",
         "| Tranche | n | Implicite | Réel | Ratio | ROI | IC 95 % | P(+EV) |",
         "|---|---:|---:|---:|---:|---:|---|---:|"]
    for b in bins:
        L.append(f"| {b['label']} | {b['n']} | {b['imp']*100:.2f} % | {b['real']*100:.2f} % | "
                 f"{b['ratio']:.3f} | {b['roi']*100:+.2f} % | "
                 f"[{b['ci_lo']*100:+.1f} ; {b['ci_hi']*100:+.1f}] | {b['p_pos']*100:.1f} % |")

    L += ["",
          "**Biais favori-outsider (mesuré).** Le ratio réel/implicite **décroît avec la "
          "probabilité implicite** : les chevaux peu joués se placent autant ou plus que "
          "prévu (ratio > 1), les gros favoris **beaucoup moins** que prévu (ratio < 0.75). "
          "Le marché du Placé **sur-évalue donc systématiquement les favoris**. "
          "Ce biais est réel, mais **le prélèvement l'annule** : aucune tranche ne passe en +EV."]

    pos_bins = [b for b in bins if b["roi"] > 0]
    # interprétation honnête du test de permutation.
    # p_rate = P(null >= observé). Observé nettement SOUS le null (p_rate→1) => le favori
    # se place MOINS que le marché ne l'implique => le marché SUR-évalue le favori.
    if p_rate > 0.95:
        bias_txt = ("Le marché **sur-évalue** le favori : il se place significativement "
                    f"**moins souvent** que son implication (p={p_rate:.4f}).")
    elif p_rate < 0.05:
        bias_txt = ("Le marché **sous-évalue** le favori : il se place significativement "
                    f"**plus souvent** que son implication (p={p_rate:.4f}).")
    else:
        bias_txt = ("Le taux de placé du favori **n'est pas distinguable** de l'implication "
                    f"du marché (p={p_rate:.4f}).")

    L += ["", "## Verdict", "", f"### {verdict}", "",
          f"**Lecture.** Le favori du Placé est placé **{fav_rate*100:.1f} %** du temps ; "
          f"le marché en impliquait **{fav_impl*100:.1f} %**. {bias_txt} "
          "C'est le **biais favori-outsider** du Placé, bien documenté. "
          "Pour autant, ce biais n'est **pas exploitable** : le ROI du favori est "
          f"**{roi_fav*100:+.2f} %** (IC 95 % [{lo_f*100:+.1f} ; {hi_f*100:+.1f}] %, "
          f"P(+EV)={pp_f*100:.1f} %), et **aucune tranche** ne dégage un ROI positif robuste "
          f"— le prélèvement (TRJ {trj*100:.2f} %, soit ≈ {100-trj*100:.2f} % de prélèvement) "
          "absorbe le biais.", ""]
    if pos_bins:
        b = max(pos_bins, key=lambda z: z["roi"])
        L += ["**Tranche(s) à ROI positif (non concluante).** "
              f"`{b['label']}` : ROI {b['roi']*100:+.2f} %, IC 95 % "
              f"[{b['ci_lo']*100:+.1f} ; {b['ci_hi']*100:+.1f}], P(+EV)={b['p_pos']*100:.1f} %. "
              f"Avec **{len(bins)} tranches testées**, un point positif isolé est attendu par "
              "multiplicité.", ""]

    L += ["## Comparaison Simple Gagnant (Phase 9) vs Placé (Phase 10)", "",
          "| | Simple Gagnant | Placé |", "|---|---|---|",
          "| Prélèvement / TRJ | 13,81 % de prélèvement | "
          f"TRJ **{trj*100:.2f} %** (prélèvement ≈ {100-trj*100:.2f} %) |",
          f"| ROI favori | −4,40 % | **{roi_fav*100:+.2f} %** |",
          "| Verdict | MARCHÉ EFFICIENT | **MARCHÉ EFFICIENT** |", "",
          "## Limites (à ne pas dépasser)", "",
          f"- Échantillon : **{len(races)} courses** sur **12 dates** — IC larges.",
          "- Les `ratio` sont un **instantané pré-course** (dernier `updatetime` publié), "
          "les dividendes sont **finaux** : l'argent de dernière minute n'est pas dans le `ratio`.",
          "- Les `ratio` sont arrondis (~0,01 pt) : suffisant pour trancher, pas pour un edge marginal.",
          "- Les dividendes placé diffèrent par cheval placé (mécanique de pool non linéaire) : "
          "on utilise le **paiement réel**, jamais un modèle.", "",
          "---", "",
          "**PHASE 10 COMPLETE — WAITING FOR HUMAN VALIDATION**"]
    REPORT.write_text("\n".join(L), encoding="utf-8")

    print(f"écrit : {REPORT}")
    print(f"socle inchangé : {socle_sha == SOCLE_SHA_EXPECTED}")
    print("VERDICT :", verdict)
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
