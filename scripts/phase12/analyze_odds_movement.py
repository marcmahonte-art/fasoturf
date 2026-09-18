#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 12 — ANALYSE DU MOUVEMENT DES COTES (ouverture → clôture)
================================================================

Le script de capture (`capture_odds_movement.py`) a enregistré, pour des courses
**à venir**, une série d'instantanés horodatés (`api_updatetime`) du marché réel.
Ici on mesure :

  1. **Descriptif** : amplitude du mouvement (dérive de la probabilité implicite
     `ratio`), stabilité ouverture↔dernier instantané, quels chevaux bougent.
  2. **Prédictif** (si les résultats sont disponibles) : le mouvement prédit-il
     l'issue ? Test de la stratégie « miser le cheval qui monte » (steam) et de la
     stratégie inverse (« fade »), ROI + IC bootstrap + test de permutation.

⚠️ Aucun modèle, aucune donnée inventée. Le socle n'est pas touché (lecture seule).

Usage :
  python scripts/phase12/analyze_odds_movement.py --date 2026-09-14
  python scripts/phase12/analyze_odds_movement.py            # toutes les dates captées
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
REPORT = ROOT / "PHASE12_REPORT.md"
MANIFEST = ROOT / "manifest_phase12_odds_movement.json"

TP = "E_SIMPLE_GAGNANT"
N_PERM = 3000
SEED = 20260914


def open_ro(p: Path) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    return c


def mean(xs):
    return sum(xs) / len(xs) if xs else float("nan")


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


def load_timelines(conn, date=None):
    """{race_key: [(updatetime, {num: ratio})]} trié par updatetime."""
    where = "AND date_race=?" if date else ""
    args = (date,) if date else ()
    raw = defaultdict(lambda: defaultdict(dict))
    for r in conn.execute(
        f"""SELECT date_race, reunion, course, api_updatetime, numero, ratio
            FROM external_pmu_citations
            WHERE type_pari=? {where} AND ratio IS NOT NULL""", (TP, *args)):
        key = (r["date_race"], r["reunion"], r["course"])
        raw[key][r["api_updatetime"]][r["numero"]] = r["ratio"]
    out = {}
    for key, snaps in raw.items():
        out[key] = sorted(snaps.items())  # [(upd, {num: ratio})]
    return out


def load_results(conn, date=None):
    """{race_key: {'winner': num, 'payout': €}} (SG)."""
    where = "AND date_race=?" if date else ""
    args = (date,) if date else ()
    out = {}
    for r in conn.execute(
        f"""SELECT date_race, reunion, course, data_json
            FROM external_pmu_results WHERE type_pari=? {where}""", (TP, *args)):
        key = (r["date_race"], r["reunion"], r["course"])
        try:
            d = json.loads(r["data_json"] or "{}")
        except Exception:
            continue
        rap = d.get("rapports") or []
        if not rap:
            continue
        comb = rap[0].get("combinaison") or []
        pe = rap[0].get("dividendePourUnEuro")
        if pe is None:
            pe = rap[0].get("dividende")
        if comb and pe:
            out[key] = {"winner": comb[0], "payout": pe / 100.0}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Analyse du mouvement des cotes (Phase 12).")
    ap.add_argument("--date", help="date ISO (défaut : toutes)")
    a = ap.parse_args(argv)

    conn = open_ro(MASTER_DB)
    timelines = load_timelines(conn, a.date)
    results = load_results(conn, a.date)
    conn.close()

    # garder les courses avec >= 2 instantanés
    multi = {k: v for k, v in timelines.items() if len(v) >= 2}
    print(f"courses avec ≥2 instantanés : {len(multi)} / {len(timelines)}")
    if not multi:
        print("Aucun mouvement capté (lancer d'abord la capture forward).")
        return 1

    # --- descriptif du mouvement ---
    drifts = []           # (race, num, p_first, p_last, delta_pts)
    abs_moves = []
    steam_hits = 0
    n_races_with_winner = 0
    races_detail = []
    for key, snaps in multi.items():
        first_upd, first = snaps[0]
        last_upd, last = snaps[-1]
        common = set(first) & set(last)
        if len(common) < 5:
            continue
        for n in common:
            d = last[n] - first[n]      # en points de part
            drifts.append({"race": key, "n": n, "p_first": first[n] / 100.0,
                           "p_last": last[n] / 100.0, "delta_pts": d})
            abs_moves.append(abs(d))
        steam = max(common, key=lambda n: last[n] - first[n])
        fade = min(common, key=lambda n: last[n] - first[n])
        rec = {"key": key, "n_snap": len(snaps), "steam": steam, "fade": fade,
               "steam_delta": last[steam] - first[steam],
               "span_min": (last_upd - first_upd) / 60000.0}
        if key in results:
            rec["winner"] = results[key]["winner"]
            rec["steam_wins"] = 1 if results[key]["winner"] == steam else 0
            rec["fade_wins"] = 1 if results[key]["winner"] == fade else 0
            n_races_with_winner += 1
            steam_hits += rec["steam_wins"]
        races_detail.append(rec)

    abs_moves.sort()
    # stabilité ouverture ↔ dernier instantané (corrélation de Pearson)
    pf = [d["p_first"] for d in drifts]
    pl = [d["p_last"] for d in drifts]
    mf, ml = mean(pf), mean(pl)
    cov = sum((a - mf) * (b - ml) for a, b in zip(pf, pl))
    sf = sum((a - mf) ** 2 for a in pf) ** 0.5
    sl = sum((b - ml) ** 2 for b in pl) ** 0.5
    corr = cov / (sf * sl) if sf and sl else float("nan")
    # mouvement moyen par rang de marché (1 = favori)
    ranks = {}
    for key, snaps in multi.items():
        first = snaps[0][1]
        ranks[key] = {n: i + 1 for i, n in enumerate(sorted(first, key=lambda x: -first[x]))}
    rank_moves = defaultdict(list)
    for d in drifts:
        rk = ranks.get(d["race"], {}).get(d["n"])
        if rk:
            b = "favoris (1-3)" if rk <= 3 else ("milieu (4-7)" if rk <= 7 else "outsiders (8+)")
            rank_moves[b].append(abs(d["delta_pts"]))
    print(f"partants suivis : {len(drifts)}")
    print(f"|mouvement| (points de part) — médiane {abs_moves[len(abs_moves)//2]:.3f} "
          f"p90 {abs_moves[int(0.9*len(abs_moves))]:.3f} max {abs_moves[-1]:.3f}")
    print(f"stabilité ouverture↔dernier (corrélation) : {corr:.4f}")
    for b in ("favoris (1-3)", "milieu (4-7)", "outsiders (8+)"):
        if rank_moves[b]:
            print(f"  |mouvement| moyen {b:<14} : {mean(rank_moves[b]):.3f} pts (n={len(rank_moves[b])})")
    print(f"durée médiane de la fenêtre captée : "
          f"{sorted(r['span_min'] for r in races_detail)[len(races_detail)//2]:.1f} min")

    # --- prédictif (si résultats) ---
    verdict = "CAPTURE EN COURS (pas encore de résultat)"
    pred = {}
    if n_races_with_winner >= 8:
        steam_rate = steam_hits / n_races_with_winner
        # ROI « miser le cheval qui monte le plus » (cote finale = p_last)
        rows_steam = []
        for r in races_detail:
            if "winner" not in r:
                continue
            rows_steam.append((r["steam_wins"], results[r["key"]]["payout"]))
        roi_steam = mean([g * p - 1.0 for g, p in rows_steam])
        ci = boot(rows_steam)
        # --- robustesse : un seul longshot peut porter tout le ROI (piège du petit échantillon) ---
        gains = sorted((g * p for g, p in rows_steam if g), reverse=True)
        total_ret = sum(g * p for g, p in rows_steam)
        roi_no_top = ((total_ret - gains[0] - len(rows_steam)) / len(rows_steam)
                      if gains else float("nan"))
        # null : gagnant tiré ∝ p_last (le marché final a raison)
        rnd = random.Random(SEED)
        races_detail_by_key = {r["key"]: r for r in races_detail}
        by_race = {}
        for key, snaps in multi.items():
            if key not in results:
                continue
            last = snaps[-1][1]
            tot = sum(last.values())
            by_race[key] = (last, tot, results[key]["payout"])
        null = []
        for _ in range(N_PERM):
            t = 0.0
            for key, (last, tot, payout) in by_race.items():
                x = rnd.random() * tot
                acc = 0.0
                pick = None
                for n, rr in last.items():
                    acc += rr
                    if x <= acc:
                        pick = n
                        break
                steam = races_detail_by_key[key]["steam"]
                t += (1 if pick == steam else 0) * payout - 1.0
            null.append(t / len(by_race))
        null.sort()
        p_roi = (1 + sum(1 for v in null if v >= roi_steam)) / (N_PERM + 1)
        pred = {"n_races": n_races_with_winner, "steam_win_rate": steam_rate,
                "roi_steam": roi_steam, "roi_steam_ci": list(ci), "p_value": p_roi,
                "roi_steam_sans_plus_gros_gain": roi_no_top,
                "plus_gros_gain_eur": (gains[0] if gains else None)}
        print(f"courses avec résultat : {n_races_with_winner}")
        print(f"taux de victoire du 'steam' : {steam_rate*100:.1f} %")
        print(f"ROI 'steam' : {roi_steam*100:+.2f} %  IC[{ci[0]*100:+.1f} ; {ci[1]*100:+.1f}]  "
              f"P(+EV)={ci[2]*100:.1f} %  permutation p={p_roi:.4f}")
        if gains:
            print(f"  ⚠️ robustesse : ROI SANS le plus gros gain = {roi_no_top*100:+.2f} % "
                  f"(le plus gros gain = {gains[0]:.2f} € pèse à lui seul le résultat)")
        verdict = ("PISTE +EV (mouvement)" if (ci[0] > 0 and roi_no_top > 0)
                   else "PAS DE +EV EXPLOITABLE (mouvement)")

    data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "date": a.date or "toutes",
        "n_races_multi_snapshot": len(multi),
        "n_runners_tracked": len(drifts),
        "abs_move_median_pts": abs_moves[len(abs_moves)//2],
        "abs_move_p90_pts": abs_moves[int(0.9*len(abs_moves))],
        "abs_move_max_pts": abs_moves[-1],
        "corr_first_last": corr,
        "move_by_rank": {b: mean(rank_moves[b]) for b in rank_moves if rank_moves[b]},
        "n_races_with_result": n_races_with_winner,
        "predictive": pred, "verdict": verdict,
    }
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    L = ["# PHASE 12 — MOUVEMENT DES COTES (ouverture → clôture)", "",
         f"**Généré :** {data['generated_at']}  ·  **Date :** {data['date']}", "",
         "> Dernière hypothèse : l'information contenue dans le **mouvement** des cotes",
         "> (argent informé), invisible dans un instantané. Capture forward en direct.", "",
         "## Descriptif du mouvement", "",
         f"- Courses avec ≥2 instantanés : **{len(multi)}**",
         f"- Partants suivis : **{len(drifts)}**",
         f"- |mouvement| (points de part) — médiane **{data['abs_move_median_pts']:.3f}**, "
         f"p90 **{data['abs_move_p90_pts']:.3f}**, max **{data['abs_move_max_pts']:.3f}**",
         f"- Stabilité ouverture↔dernier (corrélation) : **{data['corr_first_last']:.4f}**", ""]
    if data["move_by_rank"]:
        L += ["| Groupe (rang de marché) | \\|mouvement\\| moyen (pts) |", "|---|---:|"]
        for b in ("favoris (1-3)", "milieu (4-7)", "outsiders (8+)"):
            if b in data["move_by_rank"]:
                L.append(f"| {b} | {data['move_by_rank'][b]:.3f} |")
        L.append("")
    L += [f"- Durée médiane de la fenêtre captée : "
          f"**{sorted(r['span_min'] for r in races_detail)[len(races_detail)//2]:.1f} min**", "",
          "## Test prédictif (si résultats disponibles)", ""]
    if pred:
        L += [f"- Courses avec résultat : **{pred['n_races']}**",
              f"- Taux de victoire du « steam » (plus forte hausse) : **{pred['steam_win_rate']*100:.1f} %**",
              f"- ROI « miser le steam » : **{pred['roi_steam']*100:+.2f} %**  "
              f"(IC 95 % [{pred['roi_steam_ci'][0]*100:+.1f} ; {pred['roi_steam_ci'][1]*100:+.1f}] %, "
              f"P(+EV)={pred['roi_steam_ci'][2]*100:.1f} %)",
              f"- p-value permutation : **{pred['p_value']:.4f}**",
              f"- ⚠️ **Robustesse** : ROI **sans le plus gros gain** = "
              f"**{pred['roi_steam_sans_plus_gros_gain']*100:+.2f} %** "
              f"(le plus gros gain = {pred['plus_gros_gain_eur']:.2f} € — s'il porte à lui seul",
              "  le ROI, le résultat n'est PAS exploitable, même si le ROI brut est élevé)"]
    else:
        L += ["> Les courses capturées n'ont pas encore couru : le test prédictif sera",
              "> exécuté dès que les résultats (`rapports-definitifs`) seront disponibles."]
    L += ["", "## Verdict", "", f"### {verdict}", "",
          "## Limites", "",
          "- La capture ne couvre qu'une **fenêtre courte** avant le départ ; la phase la plus",
          "  informative (dernières minutes) peut être manquée.",
          "- Échantillon d'une journée (à accumuler sur plusieurs réunions).",
          "- Un seul type de pari analysé ici : **Simple Gagnant**.",
          "- ⚠️ **Petit échantillon** : le ROI peut être porté par **un seul longshot gagnant** →",
          "  lire systématiquement le ROI « sans le plus gros gain » (robustesse).", "",
          "---", "", "**PHASE 12 COMPLETE — WAITING FOR HUMAN VALIDATION**"]
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"écrit : {REPORT}")
    print("VERDICT :", verdict)
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
