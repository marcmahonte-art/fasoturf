#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 6 — PIVOT : LECTEUR DE COURSE (analyse honnête)
=====================================================

Après les Phases 3-4-5 (aucun edge démontré contre le marché), l'objectif
change : on ne prédit plus « pour gagner », on **lit** une course de façon
transparente et honnête.

Ce que l'outil fait
-------------------
Pour une course donnée, il produit un rapport qui contient :
  1. Les métadonnées de la course (hippodrome, discipline, distance, type…).
  2. Un **bandeau de qualité de données** (date sentinelle, cotes manquantes,
     âges uniformes, noms suspects, arrivée absente).
  3. Un tableau des partants trié par **probabilité implicite du marché**
     (le meilleur prédicteur mesuré), enrichi du contexte statistique :
     musique, gains, taux de victoire cumulés cheval/jockey/entraîneur.
  4. Un **second classement « forme »** (modèle de référence, performance
     PUBLIÉE) et l'**écart de rang marché ↔ forme** = signal de divergence.
  5. La vérité terrain si l'arrivée est connue.

Ce que l'outil NE fait PAS (et ne prétendra jamais)
--------------------------------------------------
  ✗ Promettre un gain. Mesuré en Phases 3-5 : aucun edge sur le socle.
  ✗ Remplacer le marché. Le marché est le meilleur prédicteur (AUC 0.7560) ;
    le modèle de forme (AUC 0.6856) est MOINS bon.
  ✗ Inventer une donnée absente (mouvement de cote, météo, non-partants).

L'« écart marché ↔ forme » a été TESTÉ (Phase 7) : **non significatif** (p = 0,30,
non répliqué sur `val`) → affiché à titre **descriptif**, PAS comme un signal exploitable.

Usage
-----
  python scripts/phase6/race_reader.py --list 10
  python scripts/phase6/race_reader.py --date 2026-09-08
  python scripts/phase6/race_reader.py --race <race_id>
  python scripts/phase6/race_reader.py --race <race_id> --out reports/ma_course.md
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "phase3"))

from train_ensemble import FORM_FEATURES  # noqa: E402

MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
MODEL_PATH = ROOT / "models" / "form_model_v1.json"
REPORTS_DIR = ROOT / "reports"

SUSPECT_NAME = re.compile(r"^\s*\d+\s*[-–—]\s*")

# Titre pollué : le parseur concatène parfois un commentaire (« 3 - NORVILLE : ... »)
TITLE_POLLUTED = re.compile(r"^\s*\d+\s*[-–—]\s*\S+\s*:")

TITLE_MAX = 90


def clean_title(t) -> str:
    """Le parseur concatène parfois un commentaire au titre — on tronque."""
    t = (t or "").strip()
    if len(t) <= TITLE_MAX:
        return t
    return t[: TITLE_MAX - 3] + "..."


def title_is_polluted(t) -> bool:
    return bool(TITLE_POLLUTED.match((t or "").strip()))

# Colonnes de features de forme présentes dans market_runner_features
FEATURE_COLS = list(FORM_FEATURES)


# --------------------------------------------------------------------------- #
# Accès données
# --------------------------------------------------------------------------- #
def open_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def load_model(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def apply_model(artifact, Xraw):
    """Applique le modèle logistique figé (standardisation + imputation)."""
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


def to_float(v):
    if v is None:
        return float("nan")
    try:
        f = float(v)
        return f
    except (TypeError, ValueError):
        return float("nan")


# --------------------------------------------------------------------------- #
# Chargement d'une course
# --------------------------------------------------------------------------- #
RUNNER_SQL = f"""
SELECT r.numero, r.cote_decimale, r.performances_structured, r.sexe_raw, r.age_raw,
       r.gains_euros, r.result_position, r.result_status,
       h.name_normalized AS horse_name, h.homonym_risk, h.resolution_confidence,
       h.n_starts AS horse_starts,
       j.name_normalized AS jockey_name,
       t.name_normalized AS trainer_name,
       m.m_prob_norm, m.m_rank, m.m_implied, m.m_is_fav, m.label_win, m.label_top3,
       {", ".join("m." + c for c in FEATURE_COLS)}
FROM master_runner r
LEFT JOIN master_horse  h ON h.horse_id  = r.horse_id
LEFT JOIN master_person j ON j.person_id = r.jockey_id
LEFT JOIN master_person t ON t.person_id = r.trainer_id
LEFT JOIN market_runner_features m ON m.runner_id = r.runner_id
WHERE r.race_id = ?
ORDER BY r.numero
"""


def load_race(conn: sqlite3.Connection, race_id: str):
    meta = conn.execute("SELECT * FROM master_race WHERE race_id = ?", (race_id,)).fetchone()
    if meta is None:
        return None, []
    runners = conn.execute(RUNNER_SQL, (race_id,)).fetchall()
    return meta, runners


def list_races(conn: sqlite3.Connection, limit: int = 10):
    return conn.execute(
        """
        SELECT mr.race_id, mr.date, mr.hippodrome_label_raw, mr.discipline,
               mr.n_runners_linked, mr.result_status, mr.date_is_sentinel,
               COUNT(mf.runner_id) AS n_feat
        FROM master_race mr
        LEFT JOIN market_runner_features mf ON mf.race_id = mr.race_id
        GROUP BY mr.race_id
        ORDER BY (n_feat > 0) DESC, mr.date DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


# --------------------------------------------------------------------------- #
# Analyse
# --------------------------------------------------------------------------- #
def analyze(meta, runners, model):
    """Construit la lecture structurée d'une course."""
    rows = []
    for r in runners:
        d = {k: r[k] for k in r.keys()}
        d["cote"] = to_float(r["cote_decimale"])
        d["p_market"] = to_float(r["m_prob_norm"])
        d["market_rank"] = r["m_rank"]
        d["has_features"] = r["m_prob_norm"] is not None
        rows.append(d)

    # features de forme + probabilité modèle
    if model is not None:
        Xraw = [[to_float(r.get(c)) for c in FEATURE_COLS] for r in rows]
        # seulement si au moins une ligne a des features
        if any(r["has_features"] for r in rows):
            probs = apply_model(model, Xraw)
            for r, p in zip(rows, probs):
                r["p_form"] = p if r["has_features"] else float("nan")
        else:
            for r in rows:
                r["p_form"] = float("nan")
    else:
        for r in rows:
            r["p_form"] = float("nan")

    # rang forme (1 = meilleure proba forme)
    ranked = sorted([r for r in rows if r["p_form"] == r["p_form"]],
                    key=lambda r: (-r["p_form"], r["numero"] or 0))
    for i, r in enumerate(ranked, 1):
        r["form_rank"] = i
    for r in rows:
        r.setdefault("form_rank", None)
        if r["market_rank"] and r["form_rank"]:
            r["rank_delta"] = r["market_rank"] - r["form_rank"]  # >0 : marché le sous-estime
        else:
            r["rank_delta"] = None

    # qualité des données
    flags = []
    if meta["date_is_sentinel"]:
        flags.append("date sentinelle 1995-07-18 (date réelle non extraite)")
    n_cote = sum(1 for r in rows if r["cote"] == r["cote"] and r["cote"] > 0)
    if n_cote < len(rows):
        flags.append(f"cotes manquantes : {len(rows) - n_cote}/{len(rows)} partants")
    ages = {r["age_raw"] for r in rows if r["age_raw"]}
    if not ages:
        flags.append("âges indisponibles (colonne vide)")
    elif len(ages) == 1 and len(rows) >= 5:
        flags.append(f"âges uniformes ({list(ages)[0]}) — artefact de parsing probable")
    hippo = (meta["hippodrome_label_raw"] or "").strip()
    if hippo.isdigit() or not hippo:
        flags.append(f"hippodrome non résolu (valeur brute : {hippo!r})")
    if meta["discipline_status"] != "present":
        flags.append(f"discipline incertaine (statut : {meta['discipline_status']})")
    if title_is_polluted(meta["titre"]):
        flags.append("titre pollué (probable commentaire concaténé au titre)")
    n_susp = sum(1 for r in rows if r["horse_name"] and SUSPECT_NAME.match(r["horse_name"]))
    if n_susp:
        flags.append(f"noms de chevaux suspects : {n_susp}")
    if not any(r["label_win"] for r in rows):
        flags.append("arrivée non disponible pour cette course")

    return {
        "rows": rows,
        "flags": flags,
        "n_cote": n_cote,
        "model_metrics": (model or {}).get("metrics", {}),
        "has_truth": any(r["label_win"] for r in rows),
    }


def fmt_pct(p, nd=1):
    if p is None or p != p:
        return "—"
    return f"{100 * p:.{nd}f} %"


def fmt_num(v, nd=2):
    if v is None or v != v:
        return "—"
    return f"{v:.{nd}f}"


# --------------------------------------------------------------------------- #
# Rendu
# --------------------------------------------------------------------------- #
def render_console(meta, analysis):
    rows = analysis["rows"]
    lines = []
    lines.append("=" * 78)
    lines.append("  LECTEUR DE COURSE — analyse honnête (Phase 6)")
    lines.append("=" * 78)
    lines.append(f"  {meta['date']}  |  {meta['hippodrome_label_raw']}  |  "
                 f"{meta['discipline']}  |  {meta['distance_m']} m  |  {meta['type_course']}")
    lines.append(f"  {clean_title(meta['titre'])}")
    lines.append(f"  partants : {len(rows)}  |  cotes : {analysis['n_cote']}  |  "
                 f"arrivée : {'connue' if analysis['has_truth'] else 'non disponible'}")
    if analysis["flags"]:
        lines.append("  ⚠ QUALITÉ : " + " ; ".join(analysis["flags"]))
    lines.append("-" * 78)
    lines.append(f"  {'n°':<3} {'Cheval':<22} {'Âge':<5} {'Cote':>6} {'P(marché)':>9} "
                 f"{'Rk':>3} {'Musique':<16} {'W%ch':>5} {'W%jo':>5} {'P(forme)':>9} {'Δrk':>4}")
    lines.append("-" * 78)
    ordered = sorted(rows, key=lambda r: (r["market_rank"] if r["market_rank"] else 999, r["numero"] or 0))
    for r in ordered:
        mus = (r["performances_structured"] or "").replace('"', "").replace("[", "").replace("]", "")
        delta = r["rank_delta"]
        dstr = f"{delta:+d}" if isinstance(delta, int) else "—"
        lines.append(
            f"  {str(r['numero'] or '?'):<3} {str(r['horse_name'] or '?')[:22]:<22} "
            f"{str(r['age_raw'] or '—'):<5} {fmt_num(r['cote'], 1):>6} {fmt_pct(r['p_market']):>9} "
            f"{str(r['market_rank'] or '—'):>3} {mus[:16]:<16} "
            f"{fmt_pct(r['c_horse_winrate'], 0):>5} {fmt_pct(r['c_jockey_winrate'], 0):>5} "
            f"{fmt_pct(r['p_form']):>9} {dstr:>4}"
        )
    lines.append("-" * 78)

    # synthèse honnête
    fav = next((r for r in rows if r["market_rank"] == 1), None)
    if fav:
        lines.append(f"  Le marché désigne n°{fav['numero']} {fav['horse_name']} "
                     f"favori ({fmt_pct(fav['p_market'])}).")
    div = [r for r in rows if isinstance(r["rank_delta"], int) and r["rank_delta"] >= 3]
    if div:
        lines.append("  Divergences marché↔forme (signal TESTÉ — Phase 7 : NON significatif) :")
        for r in sorted(div, key=lambda r: -r["rank_delta"])[:5]:
            lines.append(f"    · n°{r['numero']} {r['horse_name']} : "
                         f"rang marché {r['market_rank']} vs rang forme {r['form_rank']} "
                         f"({fmt_pct(r['p_market'])} vs {fmt_pct(r['p_form'])})")
    else:
        lines.append("  Aucune divergence majeure (rang marché ↔ forme cohérents).")
    lines.append("")
    lines.append("  ⚠ Ceci n'est PAS une promesse de gain. Mesuré (Phases 3-7) :")
    lines.append("    · le modèle de forme est MOINS bon que le marché ;")
    lines.append("    · l'écart marché↔forme a été testé (Phase 7) → NON significatif")
    lines.append("      (p=0,30, non répliqué) → traité comme du BRUIT, pas un signal.")
    if analysis["has_truth"]:
        w = next((r for r in rows if r["label_win"]), None)
        if w:
            lines.append(f"  ✔ Vérité terrain : gagnant n°{w['numero']} {w['horse_name']} "
                         f"(cote {fmt_num(w['cote'], 1)}, rang marché {w['market_rank']}, "
                         f"rang forme {w['form_rank']}).")
    lines.append("=" * 78)
    return "\n".join(lines)


def render_markdown(meta, analysis):
    rows = analysis["rows"]
    L = []
    a = L.append
    a("# Lecture de course — analyse honnête")
    a("")
    a(f"**{meta['date']}** · {meta['hippodrome_label_raw']} · {meta['discipline']} · "
      f"{meta['distance_m']} m · {meta['type_course']}")
    a("")
    a(f"> {clean_title(meta['titre'])}")
    a("")
    a(f"- **Partants :** {len(rows)} · **cotes disponibles :** {analysis['n_cote']} · "
      f"**arrivée :** {'connue' if analysis['has_truth'] else 'non disponible'}")
    if analysis["flags"]:
        a("")
        a("### ⚠ Qualité des données")
        a("")
        for f in analysis["flags"]:
            a(f"- {f}")
    a("")
    a("### Partants (triés par probabilité implicite du marché)")
    a("")
    a("| n° | Cheval | Âge | Cote | P(marché) | Rang | Musique | W%cheval | W%jockey | W%entr. | P(forme) | Rang forme | Δ |")
    a("|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|")
    ordered = sorted(rows, key=lambda r: (r["market_rank"] if r["market_rank"] else 999, r["numero"] or 0))
    for r in ordered:
        mus = (r["performances_structured"] or "").replace('"', "").replace("[", "").replace("]", "")
        delta = r["rank_delta"]
        dstr = f"{delta:+d}" if isinstance(delta, int) else "—"
        mark = "**" if r["label_win"] else ""
        a(f"| {r['numero']} | {mark}{r['horse_name'] or '?'}{mark} | {r['age_raw'] or '—'} | "
          f"{fmt_num(r['cote'], 1)} | {fmt_pct(r['p_market'])} | {r['market_rank'] or '—'} | "
          f"`{mus}` | {fmt_pct(r['c_horse_winrate'], 0)} | {fmt_pct(r['c_jockey_winrate'], 0)} | "
          f"{fmt_pct(r['c_trainer_winrate'], 0)} | {fmt_pct(r['p_form'])} | "
          f"{r['form_rank'] or '—'} | {dstr} |")
    a("")
    a("### Synthèse")
    a("")
    fav = next((r for r in rows if r["market_rank"] == 1), None)
    if fav:
        a(f"Le marché désigne **n°{fav['numero']} {fav['horse_name']}** favori "
          f"({fmt_pct(fav['p_market'])}).")
        a("")
    div = [r for r in rows if isinstance(r["rank_delta"], int) and r["rank_delta"] >= 3]
    if div:
        a("**Divergences marché↔forme** — ⚠ signal **testé et NON significatif** (Phase 7) :")
        a("")
        for r in sorted(div, key=lambda r: -r["rank_delta"])[:6]:
            a(f"- n°{r['numero']} **{r['horse_name']}** — rang marché {r['market_rank']} "
              f"vs rang forme {r['form_rank']} ({fmt_pct(r['p_market'])} vs {fmt_pct(r['p_form'])})")
    else:
        a("Aucune divergence majeure : les deux classements sont cohérents.")
    a("")
    a("### ⚠ Avertissement")
    a("")
    a("Ceci **n'est pas une promesse de gain**. Mesuré en Phases 3-7 :")
    a("")
    a("- Le marché est le meilleur prédicteur (AUC **0.7560**).")
    m = analysis["model_metrics"].get("test", {})
    if m:
        a(f"- Le modèle de forme est **moins bon** (AUC **{m.get('auc', float('nan')):.4f}**).")
    a("- Aucune stratégie de mise plate n'est rentable sur ce socle (Phase 5).")
    a("- L'écart marché↔forme a été testé (Phase 7) : **p = 0,30, non répliqué sur `val`** "
      "→ traité comme du **bruit**, pas un signal.")
    a("")
    a("L'« écart marché ↔ forme » est affiché à titre **descriptif**, pas comme un conseil de pari.")
    a("")
    if analysis["has_truth"]:
        w = next((r for r in rows if r["label_win"]), None)
        if w:
            a("### ✔ Vérité terrain")
            a("")
            a(f"Gagnant : **n°{w['numero']} {w['horse_name']}** — cote {fmt_num(w['cote'], 1)}, "
              f"rang marché {w['market_rank']}, rang forme {w['form_rank']}.")
            a("")
    a("---")
    a("")
    a("_Généré par `scripts/phase6/race_reader.py` — socle LONAB lu en lecture seule._")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Lecteur de course honnête (Phase 6).")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--race", help="race_id à analyser")
    g.add_argument("--date", help="analyser la première course de cette date (YYYY-MM-DD)")
    g.add_argument("--list", type=int, nargs="?", const=10, help="lister N courses disponibles")
    ap.add_argument("--out", help="chemin du rapport markdown à écrire")
    ap.add_argument("--json", help="chemin d'export JSON")
    ap.add_argument("--csv", help="chemin d'export CSV des partants")
    a = ap.parse_args(argv)

    conn = open_ro(MASTER_DB)
    model = load_model(MODEL_PATH)

    if a.list is not None:
        rows = list_races(conn, a.list)
        print(f"{'race_id':<38} {'date':<12} {'hippodrome':<26} {'disc':<8} {'n':>3} {'feat':>4} {'résultat'}")
        print("-" * 120)
        for r in rows:
            print(f"{r['race_id']:<38} {r['date']:<12} "
                  f"{(r['hippodrome_label_raw'] or '')[:26]:<26} {(r['discipline'] or '')[:8]:<8} "
                  f"{r['n_runners_linked'] or 0:>3} {r['n_feat']:>4} {r['result_status']}")
        return 0

    if a.date:
        row = conn.execute(
            """
            SELECT mr.race_id FROM master_race mr
            JOIN market_runner_features mf ON mf.race_id = mr.race_id
            WHERE mr.date = ? GROUP BY mr.race_id
            ORDER BY COUNT(mf.runner_id) DESC LIMIT 1
            """,
            (a.date,),
        ).fetchone()
        if row is None:
            print(f"aucune course avec features pour la date {a.date}")
            return 1
        race_id = row["race_id"]
    else:
        race_id = a.race

    meta, runners = load_race(conn, race_id)
    if meta is None:
        print(f"course introuvable : {race_id}")
        return 1
    if not runners:
        print(f"aucun partant pour {race_id}")
        return 1

    analysis = analyze(meta, runners, model)
    print(render_console(meta, analysis))

    out_path = Path(a.out) if a.out else (REPORTS_DIR / f"race_{race_id[:8]}.md")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_markdown(meta, analysis), encoding="utf-8")
    print(f"\nrapport markdown : {out_path}")

    if a.csv:
        cp = Path(a.csv)
        cp.parent.mkdir(parents=True, exist_ok=True)
        with cp.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["numero", "cheval", "age", "cote", "p_marche", "rang_marche",
                        "musique", "w_cheval", "w_jockey", "w_entraineur", "p_forme",
                        "rang_forme", "delta", "gagnant"])
            for r in sorted(analysis["rows"], key=lambda r: r["numero"] or 0):
                w.writerow([r["numero"], r["horse_name"], r["age_raw"], r["cote"],
                            r["p_market"], r["market_rank"], r["performances_structured"],
                            r["c_horse_winrate"], r["c_jockey_winrate"], r["c_trainer_winrate"],
                            r["p_form"], r["form_rank"], r["rank_delta"], r["label_win"]])
        print(f"export CSV       : {cp}")

    if a.json:
        jp = Path(a.json)
        jp.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "race": {k: meta[k] for k in meta.keys()},
            "flags": analysis["flags"],
            "model_metrics": analysis["model_metrics"],
            "runners": analysis["rows"],
        }
        jp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"export JSON      : {jp}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
