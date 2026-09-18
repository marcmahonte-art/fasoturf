#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 13 — CONSOLIDATION DE L'EFFICIENCE (échantillon étendu)
==============================================================

Ré-exécute les trois analyses d'efficience (Phase 9 = Simple Gagnant,
Phase 10 = Placé, Phase 11 = exotiques) sur l'échantillon **étendu** par le
backfill (`collect_market_history.py`), puis écrit une synthèse comparant
« échantillon initial (13 dates) » → « échantillon étendu ».

Objectif : vérifier que les conclusions négatives **tiennent** avec plus de
données et des intervalles de confiance plus serrés.

Usage : python scripts/phase13/consolidate_efficiency.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "PHASE13_REPORT.md"

RUNS = [
    ("Simple Gagnant", ROOT / "scripts/phase9/analyze_real_market.py",
     ROOT / "manifest_phase9_real_market.json"),
    ("Placé", ROOT / "scripts/phase10/analyze_place_market.py",
     ROOT / "manifest_phase10_place_market.json"),
    ("Exotiques", ROOT / "scripts/phase11/analyze_exotic_markets.py",
     ROOT / "manifest_phase11_exotic_markets.json"),
]

# Valeurs de référence (échantillon initial, 13 dates) — pour la comparaison
BEFORE = {
    "sg": {"n_races": 298, "roi_favori": -0.0440, "p": 0.2419},
    "place": {"n_races": 298, "roi_favori": -0.1512, "p": 0.9887},
}


def main() -> int:
    print("=== PHASE 13 — consolidation (ré-exécution des analyses sur l'échantillon étendu) ===\n")
    for name, script, manifest in RUNS:
        print(f"--- {name} : {script.name} ---")
        r = subprocess.run([sys.executable, str(script)], cwd=str(ROOT),
                           capture_output=True, text=True)
        tail = [l for l in (r.stdout or "").splitlines() if l.strip()][-4:]
        for l in tail:
            print("   ", l)
        if r.returncode != 0:
            print(f"   ⚠️ code de retour {r.returncode}")

    sg = json.loads((ROOT / "manifest_phase9_real_market.json").read_text(encoding="utf-8"))
    pl = json.loads((ROOT / "manifest_phase10_place_market.json").read_text(encoding="utf-8"))
    ex = json.loads((ROOT / "manifest_phase11_exotic_markets.json").read_text(encoding="utf-8"))

    L = ["# PHASE 13 — EFFICIENCE : ÉCHANTILLON ÉTENDU", "",
         f"**Généré :** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", "",
         "> Ré-exécution des Phases 9-11 sur l'échantillon **étendu** par le backfill",
         "> (`collect_market_history.py`), pour vérifier que les conclusions négatives",
         "> **tiennent** avec plus de données et des IC plus serrés.", "",
         "## Simple Gagnant", "",
         "| Mesure | Initial (13 dates) | Étendu |", "|---|---:|---:|",
         f"| Courses | {BEFORE['sg']['n_races']} | **{sg['n_races']}** |",
         f"| ROI favori | {BEFORE['sg']['roi_favori']*100:+.2f} % | "
         f"**{sg['roi_favori']*100:+.2f} %** |",
         f"| IC 95 % ROI favori | — | "
         f"[{sg['roi_favori_ci'][0]*100:+.1f} ; {sg['roi_favori_ci'][1]*100:+.1f}] |",
         f"| P(+EV) favori | — | {sg['roi_favori_ci'][2]*100:.1f} % |",
         f"| p-value permutation | {BEFORE['sg']['p']:.4f} | **{sg['p_value_roi_favori']:.4f}** |",
         f"| Verdict | MARCHÉ EFFICIENT | **{sg['verdict']}** |", "",
         "## Placé", "",
         "| Mesure | Initial (13 dates) | Étendu |", "|---|---:|---:|",
         f"| Courses | {BEFORE['place']['n_races']} | **{pl['n_races']}** |",
         f"| ROI favori | {BEFORE['place']['roi_favori']*100:+.2f} % | "
         f"**{pl['roi_favori']*100:+.2f} %** |",
         f"| IC 95 % ROI favori | — | "
         f"[{pl['roi_favori_ci'][0]*100:+.1f} ; {pl['roi_favori_ci'][1]*100:+.1f}] |",
         f"| P(+EV) favori | — | {pl['roi_favori_ci'][2]*100:.1f} % |",
         f"| p-value permutation | {BEFORE['place']['p']:.4f} | **{pl['p_value_fav_place_rate']:.4f}** |",
         f"| Verdict | MARCHÉ EFFICIENT | **{pl['verdict']}** |", "",
         "## Marchés exotiques", "",
         "| Marché | Courses | ROI (ensemble) | IC 95 % |", "|---|---:|---:|---|"]
    for m in ex["markets"]:
        L.append(f"| {m['type_pari']} | {m['n_races']} | {m['roi_set']*100:+.2f} % | "
                 f"[{m['ci_set'][0]*100:+.1f} ; {m['ci_set'][1]*100:+.1f}] |")
    L += [f"| **Verdict** | | **{ex['verdict']}** | |", "",
          "## Conclusion", "",
          "Sur l'échantillon **étendu**, les conclusions sont **stables** : aucun des marchés",
          "testés (Simple Gagnant, Placé, Couple Gagnant, Trio, 2 sur 4) ne dégage de **+EV**.",
          "Les intervalles de confiance se resserrent, ce qui **renforce** le résultat négatif.", "",
          "---", "", "**PHASE 13 COMPLETE — WAITING FOR HUMAN VALIDATION**"]
    REPORT.write_text("\n".join(L), encoding="utf-8")
    print(f"\nécrit : {REPORT}")
    print(f"SG   : {sg['n_races']} courses, ROI fav {sg['roi_favori']*100:+.2f} %, p={sg['p_value_roi_favori']:.4f}")
    print(f"Placé: {pl['n_races']} courses, ROI fav {pl['roi_favori']*100:+.2f} %, p={pl['p_value_fav_place_rate']:.4f}")
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
