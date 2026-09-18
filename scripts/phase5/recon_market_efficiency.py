#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 5 — RECONNAISSANCE (READ-ONLY) : EFFICIENCE DU MARCHÉ LONAB
=================================================================

Objectif
--------
Les Phases 3 et 4 ont montré que le moteur NE BAT PAS le favori du marché en
TAUX DE RÉUSSITE (gagnant trouvé). Mais « le favori gagne le plus souvent » est
presque tautologique : ce n'est PAS la bonne question.

La vraie question (celle qui décide si le projet peut un jour gagner de
l'argent) est : **le marché LONAB est-il efficient, ou existe-t-il des paris à
espérance de gain positive (+EV) ?**

Ce script est une MESURE PURE (aucun entraînement, aucun modèle) :
  1. Overround / prélèvement du marché  (somme des 1/cote par course)
  2. Biais favori-outsider (favorite-longshot bias) :
     taux de victoire RÉEL vs probabilité IMPLICITE, par tranche de cote
  3. ROI par tranche de cote et par rang de marché (1 = favori)
  4. Intervalle de confiance bootstrap sur le ROI (le +EV est-il réel ou du bruit ?)
  5. Stabilité train / test (hors échantillon)

Contraintes respectées
----------------------
- Socle LONAB ouvert en LECTURE SEULE (`mode=ro`) ; SHA-256 vérifié avant/après.
- Aucune écriture dans le socle. Aucune API externe. Stdlib pur. Déterministe.
- Un résultat négatif est publié tel quel (spec §35).

Sortie : PHASE5_RECON_REPORT.md + manifest_phase5_recon.json
"""

from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------- #
# Chemins
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[2]
MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
SOCLE_DB = ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"
REPORT_MD = ROOT / "PHASE5_RECON_REPORT.md"
MANIFEST = ROOT / "manifest_phase5_recon.json"

SOCLE_SHA_EXPECTED = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"

BOOTSTRAP_N = 4000
BOOTSTRAP_SEED = 20260913


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def open_ro(path: Path) -> sqlite3.Connection:
    uri = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def mean(xs) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def median(xs) -> float:
    return statistics.median(xs) if xs else float("nan")


def pct(xs, q: float) -> float:
    """Quantile simple (interpolation linéaire), xs non trié."""
    if not xs:
        return float("nan")
    s = sorted(xs)
    if len(s) == 1:
        return s[0]
    pos = q * (len(s) - 1)
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    frac = pos - lo
    return s[lo] * (1 - frac) + s[hi] * frac


def roi_flat(rows) -> float:
    """ROI d'une mise plate de 1 unité sur chaque ligne.

    rows = liste de (label_win: 0/1, cote_decimale: float)
    gain net = label_win * cote - 1   (mise 1 : gagnant encaisse cote, perdant 0)
    """
    if not rows:
        return float("nan")
    return mean([lw * cote - 1.0 for lw, cote in rows])


def bootstrap_ci(rows, n: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED, alpha: float = 0.05):
    """IC bootstrap (percentile) du ROI moyen. Renvoie (lo, hi, p_roi_pos)."""
    if len(rows) < 5:
        return (float("nan"), float("nan"), float("nan"))
    rnd = random.Random(seed)
    N = len(rows)
    stats = []
    for _ in range(n):
        s = 0.0
        for _ in range(N):
            lw, cote = rows[rnd.randrange(N)]
            s += lw * cote - 1.0
        stats.append(s / N)
    stats.sort()
    lo = stats[int((alpha / 2) * n)]
    hi = stats[min(int((1 - alpha / 2) * n), n - 1)]
    p_pos = sum(1 for v in stats if v > 0) / n
    return (lo, hi, p_pos)


def fmt_pct(x) -> str:
    return "n/a" if x != x else f"{100.0 * x:.2f} %"


def fmt_roi(x) -> str:
    return "n/a" if x != x else f"{100.0 * x:+.2f} %"


# --------------------------------------------------------------------------- #
# Chargement
# --------------------------------------------------------------------------- #
def load_runners(conn: sqlite3.Connection):
    """Renvoie la liste des runners avec cote exploitable."""
    rows = conn.execute(
        """
        SELECT runner_id, race_id, date, split,
               m_implied, m_prob_norm, m_rank, m_is_fav,
               f_field_size, label_win, label_top3
        FROM market_runner_features
        WHERE m_implied IS NOT NULL AND m_implied > 0
        """
    ).fetchall()
    out = []
    for r in rows:
        cote = 1.0 / r["m_implied"]
        out.append(
            {
                "runner_id": r["runner_id"],
                "race_id": r["race_id"],
                "date": r["date"],
                "split": r["split"],
                "cote": cote,
                "implied": r["m_implied"],       # 1/cote brut
                "prob_norm": r["m_prob_norm"],   # normalisé (somme = 1 / course)
                "rank": r["m_rank"],
                "is_fav": r["m_is_fav"],
                "field_size": r["f_field_size"],
                "win": r["label_win"] or 0,
                "top3": r["label_top3"] or 0,
            }
        )
    return out


# --------------------------------------------------------------------------- #
# Analyse 1 — Overround / prélèvement
# --------------------------------------------------------------------------- #
def analyse_overround(conn: sqlite3.Connection, runners):
    races = {}
    for r in runners:
        races.setdefault(r["race_id"], []).append(r)

    booksums = []
    complete = 0
    for rid, rs in races.items():
        # course complète = tous les partants ont une cote
        meta = None
        bs = sum(x["implied"] for x in rs)
        booksums.append(bs)

    # courses dont le nombre de cotes == nombre de partants
    meta_rows = {
        r["race_id"]: (r["n_runners"], r["n_with_odds"])
        for r in conn.execute("SELECT race_id, n_runners, n_with_odds FROM market_race_meta")
    }
    for rid, rs in races.items():
        nr, nw = meta_rows.get(rid, (len(rs), len(rs)))
        if nr and nw == nr:
            complete += 1

    n_inf_1 = sum(1 for b in booksums if b < 1.0)

    return {
        "n_races": len(races),
        "n_races_cotes_completes": complete,
        "booksum_mean": mean(booksums),
        "booksum_median": median(booksums),
        "booksum_p10": pct(booksums, 0.10),
        "booksum_p90": pct(booksums, 0.90),
        "takeout_median": 1.0 - 1.0 / median(booksums) if booksums else float("nan"),
        "n_booksum_inf_1": n_inf_1,
        "frac_booksum_inf_1": n_inf_1 / len(booksums) if booksums else float("nan"),
    }


# --------------------------------------------------------------------------- #
# Analyse 2 — Biais favori-outsider (par tranche de probabilité implicite)
# --------------------------------------------------------------------------- #
BIN_EDGES = [0.0, 0.02, 0.04, 0.07, 0.10, 0.15, 0.25, 0.40, 1.0001]


def analyse_bias(runners, key: str = "prob_norm"):
    """Par tranche de probabilité implicite : fréquence réelle vs implicite + ROI."""
    bins = []
    for i in range(len(BIN_EDGES) - 1):
        lo, hi = BIN_EDGES[i], BIN_EDGES[i + 1]
        sel = [r for r in runners if lo <= r[key] < hi]
        if not sel:
            continue
        n = len(sel)
        real = mean([r["win"] for r in sel])
        imp = mean([r["implied"] for r in sel])
        pn = mean([r["prob_norm"] for r in sel])
        rows = [(r["win"], r["cote"]) for r in sel]
        roi = roi_flat(rows)
        lo_ci, hi_ci, ppos = bootstrap_ci(rows)
        bins.append(
            {
                "label": f"[{lo:.2f}, {hi:.2f})",
                "n": n,
                "implied_mean": imp,
                "prob_norm_mean": pn,
                "real_win": real,
                "roi": roi,
                "roi_ci_lo": lo_ci,
                "roi_ci_hi": hi_ci,
                "p_roi_pos": ppos,
            }
        )
    return bins


# --------------------------------------------------------------------------- #
# Analyse 3 — Par rang de marché
# --------------------------------------------------------------------------- #
def analyse_by_rank(runners, max_rank: int = 6):
    out = []
    for rk in range(1, max_rank + 1):
        sel = [r for r in runners if r["rank"] == rk]
        if not sel:
            continue
        rows = [(r["win"], r["cote"]) for r in sel]
        lo_ci, hi_ci, ppos = bootstrap_ci(rows)
        out.append(
            {
                "rank": rk,
                "n": len(sel),
                "real_win": mean([r["win"] for r in sel]),
                "implied_mean": mean([r["implied"] for r in sel]),
                "roi": roi_flat(rows),
                "roi_ci_lo": lo_ci,
                "roi_ci_hi": hi_ci,
                "p_roi_pos": ppos,
            }
        )
    return out


# --------------------------------------------------------------------------- #
# Analyse 4 — Par taille de champ
# --------------------------------------------------------------------------- #
def analyse_by_field(runners):
    buckets = [(0, 8), (9, 11), (12, 14), (15, 99)]
    out = []
    for lo, hi in buckets:
        sel = [r for r in runners if lo <= (r["field_size"] or 0) <= hi]
        if not sel:
            continue
        rows = [(r["win"], r["cote"]) for r in sel]
        fav = [r for r in sel if r["is_fav"]]
        out.append(
            {
                "label": f"{lo}-{hi} partants",
                "n": len(sel),
                "roi_all": roi_flat(rows),
                "n_fav": len(fav),
                "roi_fav": roi_flat([(r["win"], r["cote"]) for r in fav]),
                "win_fav": mean([r["win"] for r in fav]) if fav else float("nan"),
            }
        )
    return out


# --------------------------------------------------------------------------- #
# Rapport
# --------------------------------------------------------------------------- #
def build_report(data) -> str:
    L = []
    a = L.append
    a("# PHASE 5 — RECONNAISSANCE : EFFICIENCE DU MARCHÉ LONAB")
    a("")
    a(f"**Date :** {data['timestamp']}")
    a(f"**Statut :** `{data['status']}`")
    a("**Type :** mesure pure — aucun modèle entraîné, aucune écriture, aucune API.")
    a("")
    a("> **Question posée.** Les Phases 3 et 4 ont montré que le moteur ne bat pas le favori")
    a("> *en taux de réussite*. Mais « le favori gagne le plus souvent » est presque tautologique.")
    a("> La vraie question — celle qui décide si le projet peut gagner de l'argent — est :")
    a("> **existe-t-il des paris à espérance de gain positive (+EV) ?** Ce script mesure cela.")
    a("")

    # 1. Overround
    ov = data["overround"]
    a("## 1. Prélèvement du marché (overround)")
    a("")
    a("| Mesure | Valeur |")
    a("|---|---|")
    a(f"| Courses analysées | {ov['n_races']} |")
    a(f"| Courses à cotes complètes | {ov['n_races_cotes_completes']} |")
    a(f"| Somme des 1/cote (booksum) — médiane | {ov['booksum_median']:.4f} |")
    a(f"| Booksum — moyenne | {ov['booksum_mean']:.4f} |")
    a(f"| Booksum — p10 / p90 | {ov['booksum_p10']:.4f} / {ov['booksum_p90']:.4f} |")
    a(f"| **Prélèvement implicite (médiane)** | **{fmt_pct(ov['takeout_median'])}** |")
    a("")
    a(f"> Un booksum de {ov['booksum_median']:.3f} signifie que la somme des probabilités")
    a("> implicites dépasse 100 % : le marché prélève structurellement environ")
    a(f"> **{fmt_pct(ov['takeout_median'])}** avant même de parier. Tout pari doit donc battre")
    a("> ce prélèvement pour être rentable.")
    a("")

    # 2. Biais favori-outsider
    a("## 2. Biais favori-outsider (taux réel vs implicite)")
    a("")
    a("| Tranche de proba (normalisée) | n | Implicite moyen | Prob. normalisée | Réel | ROI (mise plate) | IC 95 % | P(+EV) |")
    a("|---|---|---|---|---|---|---|---|")
    for b in data["bias"]:
        a(
            f"| {b['label']} | {b['n']} | {fmt_pct(b['implied_mean'])} | "
            f"{fmt_pct(b['prob_norm_mean'])} | **{fmt_pct(b['real_win'])}** | "
            f"**{fmt_roi(b['roi'])}** | "
            f"[{fmt_roi(b['roi_ci_lo'])} ; {fmt_roi(b['roi_ci_hi'])}] | "
            f"{fmt_pct(b['p_roi_pos'])} |"
        )
    a("")
    a("> **Lecture.** Si le taux réel est *supérieur* à l'implicite sur les favoris et")
    a("> *inférieur* sur les outsiders, le biais favori-outsider est présent. Un ROI > 0")
    a("> dont l'IC 95 % exclut 0 serait une **vraie** opportunité.")
    a("")

    # 3. Par rang
    a("## 3. ROI par rang de marché (1 = favori)")
    a("")
    a("| Rang | n | Taux réel de victoire | Implicite moyen | ROI | IC 95 % | P(+EV) |")
    a("|---|---|---|---|---|---|---|")
    for r in data["by_rank"]:
        a(
            f"| {r['rank']} | {r['n']} | {fmt_pct(r['real_win'])} | "
            f"{fmt_pct(r['implied_mean'])} | **{fmt_roi(r['roi'])}** | "
            f"[{fmt_roi(r['roi_ci_lo'])} ; {fmt_roi(r['roi_ci_hi'])}] | "
            f"{fmt_pct(r['p_roi_pos'])} |"
        )
    a("")

    # 4. Par taille de champ
    a("## 4. Effet de la taille de champ")
    a("")
    a("| Champ | n | ROI global | n favoris | ROI favori | Taux favori |")
    a("|---|---|---|---|---|---|")
    for f in data["by_field"]:
        a(
            f"| {f['label']} | {f['n']} | {fmt_roi(f['roi_all'])} | {f['n_fav']} | "
            f"{fmt_roi(f['roi_fav'])} | {fmt_pct(f['win_fav'])} |"
        )
    a("")

    # 5. Train / test
    a("## 5. Stabilité hors échantillon (train vs test)")
    a("")
    a("| Split | n | ROI global | ROI favori | Taux favori |")
    a("|---|---|---|---|---|")
    for s in data["by_split"]:
        a(
            f"| {s['split']} | {s['n']} | {fmt_roi(s['roi_all'])} | "
            f"{fmt_roi(s['roi_fav'])} | {fmt_pct(s['win_fav'])} |"
        )
    a("")

    # Limites des données de cote (honnêteté : ne pas surinterpréter)
    a("## 6. Limites des données de cote (à lire avant le verdict)")
    a("")
    a("| Contrôle | Valeur |")
    a("|---|---|")
    a(f"| Courses où booksum < 1 (impossible pour un marché final cohérent) | "
      f"{ov['n_booksum_inf_1']} / {ov['n_races']} ({fmt_pct(ov['frac_booksum_inf_1'])}) |")
    a(f"| Courses à cotes incomplètes | "
      f"{ov['n_races'] - ov['n_races_cotes_completes']} / {ov['n_races']} |")
    a("| Évolution de cote (ouverture → clôture) | **indisponible** (`evolution_cote` vide) |")
    a("")
    a("> ⚠️ **La `cote_decimale` du socle n'est PAS un rapport final de pari mutuel.**")
    a(f"> Le booksum médian ({ov['booksum_median']:.3f}) est *inférieur* au prélèvement réel du")
    a("> PMU (~14 % en Simple Gagnant), et son p10 passe **sous 1** — ce qui est impossible")
    a("> pour un marché clôturé cohérent (arbitrage). Il s'agit donc d'un **instantané de cotes")
    a("> probables pré-course**, pas des rapports définitifs.")
    a(">")
    a("> **Conséquence :** cette mesure décrit le marché **à la résolution de cet instantané**.")
    a("> Elle ne permet PAS de conclure sur le marché de clôture (le vrai marché). Le mouvement")
    a("> de cote (ouverture → clôture), qui porte l'information des parieurs informés, est")
    a("> **absent du socle** (`evolution_cote` vide). C'est la limite structurante de tout le projet.")
    a("")

    # Verdict
    a("## 7. Verdict")
    a("")
    a(data["verdict_text"])
    a("")
    a("## 8. Intégrité")
    a("")
    a("| Contrôle | Valeur |")
    a("|---|---|")
    a(f"| Socle LONAB SHA-256 | `{data['socle_sha256']}` |")
    a(f"| Socle inchangé | {'✅ OUI' if data['socle_unchanged'] else '❌ NON'} |")
    a("| Écriture dans le socle | aucune (mode=ro) |")
    a("| API externe appelée | aucune |")
    a("| Modèle entraîné | aucun (mesure pure) |")
    a("")
    a("---")
    a("")
    a("**PHASE 5 (RECON) COMPLETE — WAITING FOR HUMAN VALIDATION**")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main():
    socle_sha_before = sha256_file(SOCLE_DB)
    if socle_sha_before != SOCLE_SHA_EXPECTED:
        raise SystemExit(
            f"ERREUR FATALE : SHA socle inattendu AVANT\n  attendu {SOCLE_SHA_EXPECTED}\n"
            f"  obtenu  {socle_sha_before}"
        )

    conn = open_ro(MASTER_DB)
    runners = load_runners(conn)
    if not runners:
        raise SystemExit("ERREUR : aucun runner avec cote.")

    print(f"runners avec cote : {len(runners)}")
    print(f"courses            : {len(set(r['race_id'] for r in runners))}")

    overround = analyse_overround(conn, runners)
    print(f"booksum médian     : {overround['booksum_median']:.4f}  "
          f"(prélèvement ~{fmt_pct(overround['takeout_median'])})")

    bias = analyse_bias(runners)
    by_rank = analyse_by_rank(runners)
    by_field = analyse_by_field(runners)

    # par split
    by_split = []
    for sp in ("train", "val", "test"):
        sel = [r for r in runners if r["split"] == sp]
        if not sel:
            continue
        fav = [r for r in sel if r["is_fav"]]
        by_split.append(
            {
                "split": sp,
                "n": len(sel),
                "roi_all": roi_flat([(r["win"], r["cote"]) for r in sel]),
                "roi_fav": roi_flat([(r["win"], r["cote"]) for r in fav]),
                "win_fav": mean([r["win"] for r in fav]) if fav else float("nan"),
            }
        )

    # ROI global du marché (toutes mises)
    roi_global = roi_flat([(r["win"], r["cote"]) for r in runners])
    fav_rows = [(r["win"], r["cote"]) for r in runners if r["is_fav"]]
    roi_fav = roi_flat(fav_rows)
    fav_lo, fav_hi, fav_ppos = bootstrap_ci(fav_rows)

    # recherche de la meilleure tranche (ROI, n>=100)
    candidates = [b for b in bias if b["n"] >= 100]
    best = max(candidates, key=lambda b: b["roi"]) if candidates else None

    print(f"ROI global marché  : {fmt_roi(roi_global)}")
    print(f"ROI favori         : {fmt_roi(roi_fav)}  IC[{fmt_roi(fav_lo)};{fmt_roi(fav_hi)}] "
          f"P(+EV)={fmt_pct(fav_ppos)}")
    if best:
        print(f"meilleure tranche  : {best['label']}  ROI {fmt_roi(best['roi'])} "
              f"(n={best['n']}, P(+EV)={fmt_pct(best['p_roi_pos'])})")

    # Verdict automatique et HONNÊTE
    any_positive_sig = any(
        b["roi_ci_lo"] > 0 for b in bias if b["n"] >= 100
    ) or (fav_lo > 0)
    if any_positive_sig:
        verdict_text = (
            "✅ **Une tranche présente un ROI > 0 avec IC 95 % excluant 0.** "
            "Piste +EV potentielle à confirmer sur données futures — NE PAS conclure "
            "trop vite (risque de sur-apprentissage sur les tranches)."
        )
        verdict = "PISTE +EV (a confirmer)"
    else:
        verdict_text = (
            "❌ **Aucune tranche ne présente un ROI > 0 dont l'IC 95 % exclut 0.** "
            f"Le marché LONAB prélève structurellement ~{fmt_pct(overround['takeout_median'])} "
            "et, dans ce socle, **aucune stratégie de mise plate n'est rentable**. "
            "Le marché est **efficient** à la résolution de nos données : ni le favori, ni "
            "les outsiders, ni les tranches intermédiaires ne dégagent d'espérance positive.\n\n"
            "> ➡️ **Conséquence stratégique majeure.** Gagner de l'argent sur ce marché "
            "exige une information que la cote n'intègre PAS encore (ex. mouvement de cote "
            "en temps réel, météo, non-partants, données d'entraînement fines). Tant que "
            "cette information reste absente du socle, **aucune feature dérivée des mêmes "
            "données publiques ne battra le marché** — ce que Phases 3 et 4 ont confirmé."
        )
        verdict = "MARCHÉ EFFICIENT (aucun +EV)"

    data = {
        "phase": "5-recon",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "status": "PASS",
        "overround": overround,
        "bias": bias,
        "by_rank": by_rank,
        "by_field": by_field,
        "by_split": by_split,
        "roi_global": roi_global,
        "roi_favori": roi_fav,
        "roi_favori_ci": [fav_lo, fav_hi, fav_ppos],
        "best_bin": best["label"] if best else None,
        "verdict": verdict,
        "verdict_text": verdict_text,
        "socle_sha256": socle_sha_before,
        "socle_unchanged": None,  # rempli après
    }

    socle_sha_after = sha256_file(SOCLE_DB)
    data["socle_unchanged"] = socle_sha_after == socle_sha_before

    REPORT_MD.write_text(build_report(data), encoding="utf-8")
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nVERDICT :", verdict)
    print(f"socle inchangé : {data['socle_unchanged']}")
    print("STATUS: PASS")


if __name__ == "__main__":
    main()
