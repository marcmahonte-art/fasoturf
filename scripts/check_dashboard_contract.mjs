/**
 * Contrôle de contrat : vérifie que la réponse réelle de l'API contient
 * exactement les champs que les types TypeScript du frontend attendent.
 *
 * Il protège contre la dérive silencieuse entre `backend/schemas/*` et
 * `src/types/*` — une dérive qui ne se voit ni au type-check ni au build.
 *
 * Usage (backend démarré) :
 *   node scripts/check_dashboard_contract.mjs
 *   FASOTURF_API=http://127.0.0.1:8000 node scripts/check_dashboard_contract.mjs
 */
const BASE = process.env.FASOTURF_API ?? "http://127.0.0.1:8000";
let failures = 0;

function check(label, condition, detail = "") {
  const mark = condition ? "  OK " : "FAIL ";
  console.log(`[${mark}] ${label}${detail ? " — " + detail : ""}`);
  if (!condition) failures += 1;
}

function missingKeys(obj, keys) {
  return keys.filter((k) => !(k in obj));
}

const ROOT_KEYS = [
  "targetDate", "user", "subscription", "nextRace", "followedRaces", "topPredictions",
  "predictionContext", "predictionUnavailableReason", "performance",
  "performanceUnavailableReason", "coverage", "notifications", "dataStatus", "isLive",
];

const res = await fetch(`${BASE}/api/dashboard`);
check("GET /api/dashboard", res.ok, `HTTP ${res.status}`);
if (!res.ok) {
  console.log("\n1 ÉCHEC(S) — backend injoignable");
  process.exit(1);
}
const d = await res.json();

const rootMissing = missingKeys(d, ROOT_KEYS);
check("champs racine", rootMissing.length === 0, rootMissing.join(", "));

check("honnêteté : abonnement non configuré", d.subscription.configured === false);
check("honnêteté : notifications non configurées", d.notifications.configured === false);
check(
  "honnêteté : performances personnelles absentes",
  d.performance === null && !!d.performanceUnavailableReason,
);

if (d.nextRace) {
  const raceSummaryKeys = [
    "id", "meetingNumber", "raceNumber", "hippodrome", "participantCount",
    "distanceMeters", "startTime", "betType", "discipline", "imageUrl",
    "status", "date", "isLonab", "origin",
  ];
  const m = missingKeys(d.nextRace, raceSummaryKeys);
  check("champs RaceSummary", m.length === 0, m.join(", "));
}

if (d.topPredictions.length > 0) {
  const p = d.topPredictions[0];
  const predictionKeys = [
    "horseId", "horseName", "horseNumber", "winProbability", "top3Probability",
    "top5Probability", "rank", "confidence", "modelVersion", "predictionVersion",
    "raceLabel", "raceId", "odds", "valueEdge", "origin",
  ];
  const m = missingKeys(p, predictionKeys);
  check("champs Prediction", m.length === 0, m.join(", "));
  check(
    "probabilité en ratio 0–1",
    p.winProbability > 0 && p.winProbability <= 1,
    `#${p.horseNumber} ${p.horseName} = ${p.winProbability} → ${Math.round(p.winProbability * 100)} %`,
  );
}

// --- Fiche course réelle (page /courses/:raceId) ---
const raceId = d.nextRace?.id;
if (raceId) {
  const rr = await fetch(`${BASE}/api/races/${raceId}`);
  check("GET /api/races/{id}", rr.ok, `HTTP ${rr.status}`);
  if (rr.ok) {
    const race = await rr.json();
    const detailKeys = [
      "id", "date", "reunion", "course", "hippodrome", "title", "discipline",
      "distance", "terrain", "starters", "time", "status", "hasResult",
      "favoriteOdds", "accent", "runners", "meteo", "isLonab", "lonabBet",
      "arrivee", "arriveeSource", "quinteDividende", "quinteGagnants",
    ];
    const m = missingKeys(race, detailKeys);
    check("champs RaceDetail", m.length === 0, m.join(", "));

    if (race.runners?.length) {
      const runnerKeys = [
        "number", "name", "age", "music", "jockey", "trainer", "odds",
        "marketProb", "marketRank", "isWinner", "position",
      ];
      const rm = missingKeys(race.runners[0], runnerKeys);
      check("champs RaceRunner", rm.length === 0, rm.join(", "));
    }
  }

  // --- Pronostic par identifiant de course (UUID) ---
  const pr = await fetch(`${BASE}/api/predictions/race/${raceId}`);
  const pred = await pr.json();
  const predOk = pr.ok && (pred.available === false || Array.isArray(pred.runners));
  check(
    "GET /api/predictions/race/{id}",
    predOk,
    pred.available === false ? `indisponible : ${pred.reason}` : `${pred.runners.length} partants`,
  );
}

// --- Statistiques (page /statistiques) ---
const sr = await fetch(`${BASE}/api/statistics`);
check("GET /api/statistics", sr.ok, `HTTP ${sr.status}`);
if (sr.ok) {
  const stats = await sr.json();
  check(
    "chaque mesure porte sa méthode",
    !!(stats.favouriteWinRate?.method && stats.oddsCoverage?.method && stats.resultCoverage?.method),
  );
  check(
    "volumes exposés",
    typeof stats.coverage?.exploitableRaces === "number",
    `${stats.coverage?.exploitableRaces} courses exploitables`,
  );
}

// --- Programme (page /courses) et courses analysables (page /analyses) ---
const sumr = await fetch(`${BASE}/api/races/summary?limit=5`);
check("GET /api/races/summary", sumr.ok, `HTTP ${sumr.status}`);
if (sumr.ok) {
  const list = await sumr.json();
  check("liste de programme non vide", Array.isArray(list) && list.length > 0, `${list.length} entrées`);
  if (list.length > 0) {
    const m = missingKeys(list[0], [
      "id", "meetingNumber", "raceNumber", "hippodrome", "participantCount",
      "distanceMeters", "startTime", "betType", "discipline", "imageUrl",
      "status", "date", "isLonab", "origin",
    ]);
    check("champs RaceSummary (liste)", m.length === 0, m.join(", "));
  }
}

const anr = await fetch(`${BASE}/api/races/summary?analysable=true&limit=5`);
check("GET /api/races/summary?analysable=true", anr.ok, `HTTP ${anr.status}`);
if (anr.ok) {
  const list = await anr.json();
  check("courses analysables retournées", Array.isArray(list) && list.length > 0, `${list.length} entrées`);
}

const dr = await fetch(`${BASE}/api/dates?limit=5`);
check("GET /api/dates", dr.ok, `HTTP ${dr.status}`);
if (dr.ok) {
  const list = await dr.json();
  const m = list.length ? missingKeys(list[0], ["date", "label", "count", "isToday"]) : [];
  check("champs DateItem", m.length === 0, m.join(", "));
}

// --- Chevaux (pages /chevaux et /chevaux/:id) ---
const hr = await fetch(`${BASE}/api/horses?limit=3`);
check("GET /api/horses", hr.ok, `HTTP ${hr.status}`);
if (hr.ok) {
  const horses = await hr.json();
  if (horses.length > 0) {
    const m = missingKeys(horses[0], [
      "id", "name", "starts", "firstSeenDate", "lastSeenDate",
      "sexBirthyearVariants", "father", "mother", "coat", "breed", "homonymRisk",
    ]);
    check("champs HorseSummary", m.length === 0, m.join(", "));

    const hd = await fetch(`${BASE}/api/horses/${horses[0].id}`);
    check("GET /api/horses/{id}", hd.ok, `HTTP ${hd.status}`);
    if (hd.ok) {
      const detail = await hd.json();
      const dm = missingKeys(detail, ["horse", "statistics", "recentRuns"]);
      const sm = missingKeys(detail.statistics ?? {}, [
        "starts", "wins", "top3", "top5", "unknown", "winRate", "top3Rate",
      ]);
      check("champs HorseDetail", dm.length === 0 && sm.length === 0, [...dm, ...sm].join(", "));
      // Honnêteté : un taux n'est publié que si son dénominateur est connu.
      // Le dénominateur est `starts - unknown` (positions réellement connues),
      // jamais `starts` seul — sinon un taux serait calculé sur des inconnues.
      const s = detail.statistics ?? {};
      const known = (s.starts ?? 0) - (s.unknown ?? 0);
      check(
        "taux cheval cohérents avec leur dénominateur",
        known > 0 ? s.winRate !== null && s.top3Rate !== null : s.winRate === null,
        `${s.wins} victoires / ${known} positions connues (${s.starts} participations, ${s.unknown} inconnues) → ${s.winRate}`,
      );
    }
  }
}

// --- Jockeys / entraîneurs (pages /jockeys, /entraineurs) ---
for (const [path, role] of [
  ["/api/jockeys", "jockey"],
  ["/api/trainers", "trainer"],
]) {
  const r = await fetch(`${BASE}${path}?limit=3`);
  check(`GET ${path}`, r.ok, `HTTP ${r.status}`);
  if (!r.ok) continue;
  const persons = await r.json();
  if (persons.length === 0) continue;
  const m = missingKeys(persons[0], [
    "id", "name", "role", "appearances", "resolutionConfidence",
  ]);
  check(`champs PersonSummary (${role})`, m.length === 0, m.join(", "));
  check(
    `rôle correct pour ${path}`,
    persons.every((p) => p.role === role),
    `${persons.length} entrées`,
  );

  const pd = await fetch(`${BASE}${path}/${persons[0].id}`);
  check(`GET ${path}/{id}`, pd.ok, `HTTP ${pd.status}`);
  if (pd.ok) {
    const detail = await pd.json();
    const dm = missingKeys(detail, ["person", "statistics", "recentRuns"]);
    const sm = missingKeys(detail.statistics ?? {}, [
      "mounts", "wins", "top3", "unknown", "winRate", "top3Rate",
    ]);
    check(`champs PersonDetail (${role})`, dm.length === 0 && sm.length === 0, [...dm, ...sm].join(", "));

    const ps = detail.statistics ?? {};
    const known = (ps.mounts ?? 0) - (ps.unknown ?? 0);
    check(
      `taux ${role} cohérents avec leur dénominateur`,
      known > 0 ? ps.winRate !== null : ps.winRate === null,
      `${ps.wins} victoires / ${known} positions connues (${ps.mounts} participations, ${ps.unknown} inconnues) → ${ps.winRate}`,
    );
  }
}

// --- Pronostics mis en avant (page /pronostics) ---
const fr = await fetch(`${BASE}/api/predictions/featured?limit=5`);
check("GET /api/predictions/featured", fr.ok, `HTTP ${fr.status}`);
if (fr.ok) {
  const featured = await fr.json();
  const m = missingKeys(featured, ["raceId", "context", "predictions", "unavailableReason"]);
  check("champs FeaturedPredictions", m.length === 0, m.join(", "));
  const items = featured.predictions ?? [];
  check(
    "pronostics accompagnés de leur contexte (ou indisponibilité expliquée)",
    items.length > 0 ? !!featured.context : !!featured.unavailableReason,
    items.length > 0 ? `${items.length} pronostics` : String(featured.unavailableReason).slice(0, 70),
  );
  if (items.length > 0) {
    const p = items[0];
    check(
      "probabilité en ratio 0–1 (featured)",
      p.winProbability > 0 && p.winProbability <= 1,
      `#${p.horseNumber} ${p.horseName} = ${p.winProbability}`,
    );
  }
}

// --- Page publique : le programme affiché doit être la journée la plus récente
// de la base, jamais un instantané figé. Si ces deux dates divergent, la page
// publique annonce un programme périmé comme s'il était courant.
{
  const feedRes = await fetch(`${BASE}/api/races?limit=50`);
  const datesRes = await fetch(`${BASE}/api/dates?limit=1`);
  if (feedRes.ok && datesRes.ok) {
    const feed = await feedRes.json();
    const dates = await datesRes.json();
    const feedDates = [...new Set((feed ?? []).map((race) => race.date))].sort();
    const newestInFeed = feedDates.length > 0 ? feedDates[feedDates.length - 1] : null;
    const newestInBase = dates?.[0]?.date ?? null;
    check(
      "programme public aligné sur la journée la plus récente",
      !!newestInFeed && newestInFeed === newestInBase,
      `flux=${newestInFeed} · base=${newestInBase}`,
    );
    const accentsOk = (feed ?? []).every(
      (race) => ["green", "gold", "red"].includes(race.accent),
    );
    check("accent graphique fourni par l'API", accentsOk, "green | gold | red");
  }
}

console.log("");
console.log(failures === 0 ? "CONTRAT CONFORME" : `${failures} ÉCHEC(S)`);
process.exit(failures === 0 ? 0 : 1);
