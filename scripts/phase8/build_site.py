#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 8 — INDUSTRIALISATION : SITE D'ANALYSE HONNÊTE (statique)
===============================================================

Génère un **site statique autonome** (`site/index.html`) à partir de la Master DB :
  - page unique (SPA) avec données embarquées, filtres et recherche ;
  - liste des courses filtrable (date, hippodrome, discipline, champ) ;
  - vue détaillée par course : partants, probabilité implicite du marché, classement
    « forme », écart marché↔forme, bandeau qualité, vérité terrain ;
  - **avertissement honnête** visible en permanence (bilan Phases 3-7).

Aucune dépendance externe, aucune API, aucun serveur requis : le fichier s'ouvre
directement dans un navigateur. Socle LONAB lu en lecture seule.

Usage : python scripts/phase8/build_site.py [--out site/index.html]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "phase3"))

from train_ensemble import FORM_FEATURES  # noqa: E402

MASTER_DB = ROOT / "pmu-lonab-scraper" / "data" / "master" / "pmu_master.db"
SOCLE_DB = ROOT / "pmu-lonab-scraper" / "data" / "processed" / "pmu_lonab.db"
MODEL_PATH = ROOT / "models" / "form_model_v1.json"
OUT_DEFAULT = ROOT / "site" / "index.html"

SOCLE_SHA_EXPECTED = "d71f6a013ff7fc5720ffd5824d0c71077cba1602c883073bd5bd60f41d2cdb42"

TITLE_POLLUTED = re.compile(r"^\s*\d+\s*[-–—]\s*\S+\s*:")
TITLE_MAX = 90


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def open_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def clean_title(t) -> str:
    t = (t or "").strip()
    if TITLE_POLLUTED.match(t):
        return t[:TITLE_MAX] + ("..." if len(t) > TITLE_MAX else "")
    return t[:TITLE_MAX] + ("..." if len(t) > TITLE_MAX else "")


def r4(v):
    return None if v is None else round(float(v), 4)


def apply_model(artifact, Xraw):
    """Applique le modèle de forme FIGÉ (le même que celui testé en Phase 7)."""
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


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #
def build_payload(conn: sqlite3.Connection, model):
    races = conn.execute(
        """
        SELECT mr.race_id, mr.date, mr.date_is_sentinel, mr.hippodrome_label_raw,
               mr.discipline, mr.discipline_status, mr.distance_m, mr.type_course,
               mr.titre, mr.n_runners_linked, mr.result_status,
               COUNT(mf.runner_id) AS n_feat
        FROM master_race mr
        JOIN market_runner_features mf ON mf.race_id = mr.race_id
        GROUP BY mr.race_id
        ORDER BY mr.date DESC, mr.hippodrome_label_raw
        """
    ).fetchall()

    feat_cols = ", ".join("m." + c for c in FORM_FEATURES)
    runners = conn.execute(
        f"""
        SELECT r.race_id, r.numero, r.age_raw, r.cote_decimale,
               r.performances_structured, r.result_position,
               h.name_normalized AS horse_name,
               m.m_prob_norm, m.m_rank, m.label_win,
               m.f_musique_avg, m.c_horse_winrate, m.c_jockey_winrate, m.c_trainer_winrate,
               m.f_age, m.f_sex, {feat_cols}
        FROM master_runner r
        LEFT JOIN master_horse h ON h.horse_id = r.horse_id
        JOIN market_runner_features m ON m.runner_id = r.runner_id
        ORDER BY r.race_id, r.numero
        """
    ).fetchall()

    # probabilité « forme » via le MODÈLE FIGÉ (identique à celui testé en Phase 7)
    Xraw = [[float(r[c]) if r[c] is not None else float("nan") for c in FORM_FEATURES]
            for r in runners]
    pf = apply_model(model, Xraw) if model else [float("nan")] * len(runners)
    pf_by_runner = {(r["race_id"], r["numero"]): p for r, p in zip(runners, pf)}

    by_race = {}
    for r in runners:
        by_race.setdefault(r["race_id"], []).append(r)

    races_out = []
    for rc in races:
        rid = rc["race_id"]
        lst = by_race.get(rid, [])
        if not lst:
            continue

        order = sorted(lst, key=lambda r: (-pf_by_runner.get((r["race_id"], r["numero"]), 0.0),
                                           r["numero"] or 0))
        frank = {r["numero"]: i + 1 for i, r in enumerate(order)}

        rl = []
        for r in lst:
            rl.append({
                "n": r["numero"],
                "h": r["horse_name"],
                "age": r["f_age"] if r["f_age"] is not None else r["age_raw"],
                "cote": r4(r["cote_decimale"]),
                "pm": r4(r["m_prob_norm"]),
                "mr": r["m_rank"],
                "fr": frank.get(r["numero"]),
                "pf": r4(pf_by_runner.get((r["race_id"], r["numero"]))),
                "mus": (r["performances_structured"] or "").replace('"', "").replace("[", "").replace("]", ""),
                "wh": r4(r["c_horse_winrate"]),
                "wj": r4(r["c_jockey_winrate"]),
                "wt": r4(r["c_trainer_winrate"]),
                "win": int(r["label_win"] or 0),
            })
        rl.sort(key=lambda x: (x["mr"] if x["mr"] else 999))

        # flags qualité
        flags = []
        if rc["date_is_sentinel"]:
            flags.append("date sentinelle")
        n_cote = sum(1 for x in rl if x["cote"])
        if n_cote < len(rl):
            flags.append(f"cotes manquantes {len(rl)-n_cote}")
        ages = {x["age"] for x in rl if x["age"]}
        if not ages:
            flags.append("âges indisponibles")
        elif len(ages) == 1 and len(rl) >= 5:
            flags.append("âges uniformes")
        hippo = (rc["hippodrome_label_raw"] or "").strip()
        if hippo.isdigit() or not hippo:
            flags.append("hippodrome non résolu")
        if TITLE_POLLUTED.match((rc["titre"] or "").strip()):
            flags.append("titre pollué")
        if rc["discipline_status"] != "present":
            flags.append("discipline incertaine")
        if not any(x["win"] for x in rl):
            flags.append("arrivée absente")

        races_out.append({
            "id": rid,
            "date": rc["date"],
            "hippo": rc["hippodrome_label_raw"] or "?",
            "disc": rc["discipline"] or "?",
            "dist": rc["distance_m"],
            "type": rc["type_course"] or "",
            "titre": clean_title(rc["titre"]),
            "n": len(rl),
            "flags": flags,
            "truth": any(x["win"] for x in rl),
            "runners": rl,
        })

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "socle_sha256": sha256_file(SOCLE_DB),
        "n_races": len(races_out),
        "n_runners": sum(r["n"] for r in races_out),
        "date_min": min((r["date"] for r in races_out), default=""),
        "date_max": max((r["date"] for r in races_out), default=""),
        "races": races_out,
    }


# --------------------------------------------------------------------------- #
# Rendu HTML
# --------------------------------------------------------------------------- #
CSS = """
:root{
  --bg:#f6f7f9; --panel:#ffffff; --ink:#16181d; --muted:#5b6270;
  --line:#e3e6ea; --accent:#1f6feb; --good:#0f7b3f; --warn:#a86400; --bad:#b3261e;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{background:var(--panel);border-bottom:1px solid var(--line);padding:18px 24px;position:sticky;top:0;z-index:5}
h1{margin:0;font-size:20px;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:13px;margin-top:4px}
.wrap{max-width:1180px;margin:0 auto;padding:20px 24px 60px}
.banner{background:#fff8e6;border:1px solid #f0d9a0;border-left:4px solid var(--warn);
  border-radius:8px;padding:12px 16px;margin:16px 0;font-size:13.5px}
.banner b{color:var(--warn)}
.stats{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 14px;min-width:120px}
.stat .k{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.stat .v{font-size:19px;font-weight:600;margin-top:2px}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
input,select{padding:8px 10px;border:1px solid var(--line);border-radius:7px;background:#fff;font:inherit;color:inherit}
input[type=search]{min-width:220px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{padding:9px 10px;text-align:left;border-bottom:1px solid var(--line);font-size:13.5px;white-space:nowrap}
th{background:#fafbfc;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);cursor:default}
tbody tr{cursor:pointer}
tbody tr:hover{background:#f2f6ff}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.tag{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;border:1px solid var(--line);color:var(--muted);margin-left:4px}
.tag.warn{border-color:#f0d9a0;background:#fff8e6;color:var(--warn)}
.detail{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px;margin-top:18px}
.detail h2{margin:0 0 4px;font-size:18px}
.kv{color:var(--muted);font-size:13px;margin-bottom:12px}
.flag{color:var(--warn)}
.fav{font-weight:600}
.win{background:#eafaf0}
.delta-pos{color:var(--good);font-weight:600}
.delta-neg{color:var(--bad)}
.back{background:none;border:none;color:var(--accent);cursor:pointer;font:inherit;padding:0;margin-bottom:10px}
.muted{color:var(--muted)}
.hidden{display:none}
footer{color:var(--muted);font-size:12.5px;margin-top:30px;border-top:1px solid var(--line);padding-top:14px}
code{background:#f0f2f5;padding:1px 5px;border-radius:4px;font-size:12.5px}
"""


JS = r"""
const $ = (s,el=document)=>el.querySelector(s);
const pct = v => (v==null? '—' : (100*v).toFixed(1)+' %');
const num = v => (v==null? '—' : (Math.round(v*10)/10));
let view = 'list';

function renderStats(){
  const d=DATA;
  $('#stats').innerHTML = `
    <div class="stat"><div class="k">Courses</div><div class="v">${d.n_races}</div></div>
    <div class="stat"><div class="k">Partants</div><div class="v">${d.n_runners}</div></div>
    <div class="stat"><div class="k">Période</div><div class="v" style="font-size:14px">${d.date_min} → ${d.date_max}</div></div>
    <div class="stat"><div class="k">Généré</div><div class="v" style="font-size:14px">${d.generated_at}</div></div>`;
}

function hippos(){
  return [...new Set(DATA.races.map(r=>r.hippo))].sort();
}
function discs(){
  return [...new Set(DATA.races.map(r=>r.disc))].sort();
}

function initFilters(){
  $('#f-hippo').innerHTML = '<option value="">Tous hippodromes</option>' +
    hippos().map(h=>`<option>${h}</option>`).join('');
  $('#f-disc').innerHTML = '<option value="">Toutes disciplines</option>' +
    discs().map(d=>`<option>${d}</option>`).join('');
}

function filtered(){
  const q=$('#f-q').value.trim().toLowerCase();
  const h=$('#f-hippo').value, d=$('#f-disc').value;
  const from=$('#f-from').value, to=$('#f-to').value;
  return DATA.races.filter(r=>{
    if(h && r.hippo!==h) return false;
    if(d && r.disc!==d) return false;
    if(from && r.date<from) return false;
    if(to && r.date>to) return false;
    if(q){
      const inRace = (r.hippo+' '+r.disc+' '+r.titre).toLowerCase().includes(q);
      const inHorse = r.runners.some(x=>(x.h||'').toLowerCase().includes(q));
      if(!inRace && !inHorse) return false;
    }
    return true;
  });
}

function renderList(){
  const rows = filtered();
  $('#count').textContent = rows.length + ' course(s)';
  const fav = r => { const f=r.runners.find(x=>x.mr===1); return f? `n°${f.n} ${f.h||''} (${pct(f.pm)})` : '—'; };
  $('#list').innerHTML = `
    <table>
      <thead><tr>
        <th>Date</th><th>Hippodrome</th><th>Disc.</th><th class="num">Dist.</th>
        <th>Type</th><th class="num">Part.</th><th>Favori du marché</th><th>Qualité</th>
      </tr></thead>
      <tbody>${rows.map(r=>`
        <tr onclick="openRace('${r.id}')">
          <td>${r.date}</td>
          <td>${r.hippo}</td>
          <td>${r.disc}</td>
          <td class="num">${r.dist??'—'}</td>
          <td>${r.type||'—'}</td>
          <td class="num">${r.n}</td>
          <td>${fav(r)}</td>
          <td>${r.flags.length? r.flags.map(f=>`<span class="tag warn">${f}</span>`).join('') : '<span class="muted">ok</span>'}</td>
        </tr>`).join('')}
      </tbody>
    </table>`;
  $('#detail').classList.add('hidden');
  $('#listWrap').classList.remove('hidden');
}

function openRace(id){
  const r = DATA.races.find(x=>x.id===id);
  if(!r) return;
  const fav = r.runners.find(x=>x.mr===1);
  const winner = r.runners.find(x=>x.win);
  $('#listWrap').classList.add('hidden');
  $('#detail').classList.remove('hidden');
  $('#detail').innerHTML = `
    <button class="back" onclick="renderList()">← retour à la liste</button>
    <h2>${r.hippo} — ${r.disc} ${r.dist?('· '+r.dist+' m'):''} ${r.type?('· '+r.type):''}</h2>
    <div class="kv">${r.date} · ${r.n} partants · ${r.truth?'arrivée connue':'arrivée non disponible'}
      ${r.flags.length? ' · <span class="flag">⚠ '+r.flags.join(' ; ')+'</span>' : ''}
      ${r.titre? '<br>'+r.titre : ''}</div>
    <table>
      <thead><tr>
        <th class="num">n°</th><th>Cheval</th><th class="num">Âge</th><th class="num">Cote</th>
        <th class="num">P(marché)</th><th class="num">Rk</th><th>Musique</th>
        <th class="num">W%cheval</th><th class="num">W%jockey</th>
        <th class="num">P(forme)</th><th class="num">Rang forme</th><th class="num">Δ rang</th>
      </tr></thead>
      <tbody>${r.runners.map(x=>{
        const d = (x.mr&&x.fr)? (x.mr-x.fr) : null;
        const dcls = d==null? '' : (d>=3? 'delta-pos' : (d<=-3? 'delta-neg':''));
        return `<tr class="${x.win?'win':''}">
          <td class="num">${x.n}</td>
          <td>${x.h||'?'}${x.mr===1?' <span class="tag">favori</span>':''}${x.win?' <span class="tag">gagnant</span>':''}</td>
          <td class="num">${x.age??'—'}</td>
          <td class="num">${num(x.cote)}</td>
          <td class="num">${pct(x.pm)}</td>
          <td class="num">${x.mr??'—'}</td>
          <td><code>${x.mus||''}</code></td>
          <td class="num">${pct(x.wh)}</td>
          <td class="num">${pct(x.wj)}</td>
          <td class="num">${pct(x.pf)}</td>
          <td class="num">${x.fr??'—'}</td>
          <td class="num ${dcls}">${d==null?'—':(d>0?'+':'')+d}</td>
        </tr>`;}).join('')}
      </tbody>
    </table>
    <div class="banner" style="margin-top:14px">
      <b>Avertissement.</b> La colonne « Rang forme » est <b>descriptive</b>, pas un signal :
      testée en Phase 7, elle s'est révélée <b>non significative</b> (p = 0,30, non répliquée).
      Le marché reste le meilleur prédicteur (AUC 0.7560 vs 0.6856). Aucun pari +EV démontré.
      ${winner? '<br>✔ Gagnant réel : n°'+winner.n+' '+ (winner.h||'') +' (rang marché '+winner.mr+').' : ''}
    </div>`;
}

function boot(){
  renderStats(); initFilters(); renderList();
  ['f-q','f-hippo','f-disc','f-from','f-to'].forEach(id=>{
    $('#'+id).addEventListener('input', renderList);
  });
}
document.addEventListener('DOMContentLoaded', boot);
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lecteur de Course — analyse honnête (LONAB)</title>
<style>__CSS__</style>
</head>
<body>
<header>
  <h1>Lecteur de Course — analyse honnête</h1>
  <div class="sub">Socle LONAB (lecture seule) · <span id="socle"></span> · outil d'analyse, pas de pronostic payant</div>
</header>
<div class="wrap">

  <div class="banner">
    <b>Ce que ce site est — et n'est pas.</b> Il restitue la lecture du marché et un contexte
    statistique descriptif. Cinq mesures indépendantes (Phases 3 à 7) ont montré qu'<b>aucune
    information du socle ne permet de battre le marché</b> : forme (gain net 0), commentaires
    (−6), +EV par tranche (aucun), écart marché↔forme (p = 0,30 → bruit). <b>Aucune promesse
    de gain.</b> Le marché reste le meilleur prédicteur (AUC 0.7560).
  </div>

  <div class="stats" id="stats"></div>

  <div class="filters">
    <input type="search" id="f-q" placeholder="Rechercher un cheval, un hippodrome…">
    <select id="f-hippo"></select>
    <select id="f-disc"></select>
    <input type="date" id="f-from" title="à partir du">
    <input type="date" id="f-to" title="jusqu'au">
    <span class="muted" style="align-self:center" id="count"></span>
  </div>

  <div id="listWrap"><div id="list"></div></div>
  <div id="detail" class="detail hidden"></div>

  <footer>
    Généré par <code>scripts/phase8/build_site.py</code> — données lues en lecture seule dans
    <code>pmu_master.db</code> (socle LONAB non modifié). Aucune API externe, aucune dépendance.
    <br>Méthodologie et résultats complets : <code>PHASE3_REPORT.md</code> … <code>PHASE7_REPORT.md</code>.
  </footer>
</div>
<script>const DATA = __DATA__;</script>
<script>__JS__</script>
</body>
</html>
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master", default=str(MASTER_DB))
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    a = ap.parse_args(argv)

    sha = sha256_file(SOCLE_DB)
    if sha != SOCLE_SHA_EXPECTED:
        raise SystemExit(f"ERREUR FATALE : SHA socle inattendu : {sha}")

    model = json.loads(MODEL_PATH.read_text(encoding="utf-8")) if MODEL_PATH.exists() else None
    if model is None:
        raise SystemExit(f"modèle introuvable : {MODEL_PATH} (lancer scripts/phase6/fit_form_model.py)")

    conn = open_ro(Path(a.master).resolve())
    payload = build_payload(conn, model)
    conn.close()
    print(f"courses : {payload['n_races']} | partants : {payload['n_runners']} "
          f"| période : {payload['date_min']} -> {payload['date_max']}")

    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    data_json = data_json.replace("</", "<\\/")

    doc = (HTML_TEMPLATE
           .replace("__CSS__", CSS)
           .replace("__JS__", JS)
           .replace("__DATA__", data_json)
           .replace('<span id="socle"></span>',
                    f'<span id="socle">socle {payload["socle_sha256"][:12]}…</span>'))

    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    size_mb = out.stat().st_size / 1e6
    print(f"site écrit : {out} ({size_mb:.2f} Mo)")
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
