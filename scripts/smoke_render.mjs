/**
 * Test de rendu réel des pages FasoTurf.
 *
 * Ce que ce test apporte que les autres ne couvrent pas :
 *
 *   - `test_api.py` vérifie le **serveur** (codes HTTP, formes de réponse) ;
 *   - `check_dashboard_contract.mjs` vérifie le **contrat** entre l'API et les
 *     types TypeScript ;
 *   - ce script vérifie que le **bundle compilé s'exécute vraiment** : il monte
 *     l'application dans un DOM (jsdom), laisse les composants charger leurs
 *     données depuis l'API réelle, puis contrôle le HTML produit.
 *
 * Il attrape donc ce qu'aucun autre test ne voit : plantage d'un composant sur
 * une donnée réelle, erreur d'import, exception non gérée, page blanche, écran
 * de chargement qui ne se termine jamais.
 *
 * Chaque route est montée dans un **processus séparé** : c'est le seul moyen
 * d'obtenir une isolation totale. Un DOM partagé laisse traîner les rendus et
 * les requêtes de la page précédente, qui viennent polluer la suivante.
 *
 * Usage (serveur démarré, interface compilée) :
 *   node scripts/smoke_render.mjs
 *   node scripts/smoke_render.mjs --verbose
 *   FASOTURF_API=http://127.0.0.1:8000 node scripts/smoke_render.mjs
 */

import { readFileSync, readdirSync } from "node:fs";
import { spawn } from "node:child_process";
import path from "node:path";
import { pathToFileURL } from "node:url";

const ROOT = path.resolve(import.meta.dirname, "..");
const DIST = path.join(ROOT, "dist");
const BASE = process.env.FASOTURF_API ?? "http://127.0.0.1:8000";
const VERBOSE = process.argv.includes("--verbose");

/** Marqueur de fin de sortie du processus enfant, pour un parsing fiable. */
const RESULT_PREFIX = "__FASOTURF_RESULT__";

// ==========================================================================
// Mode enfant : monter UNE route, rendre compte, quitter
// ==========================================================================

async function renderSingleRoute(route, marker, timeoutMs) {
  const { JSDOM, VirtualConsole } = await import("jsdom");

  const html = readFileSync(path.join(DIST, "index.html"), "utf8");
  const assetsDir = path.join(DIST, "assets");
  const bundleFile = readdirSync(assetsDir).find((name) => /^index-.*\.js$/.test(name));
  const bundleHref = pathToFileURL(path.join(assetsDir, bundleFile)).href;

  const errors = [];

  const virtualConsole = new VirtualConsole();
  virtualConsole.on("jsdomError", (error) => errors.push(`jsdomError: ${error.message}`));
  virtualConsole.on("error", (...args) => errors.push(`console.error: ${args.join(" ")}`));
  virtualConsole.on("warn", (...args) => errors.push(`console.warn: ${args.join(" ")}`));

  const dom = new JSDOM(html, {
    url: `${BASE}${route}`,
    pretendToBeVisual: true,
    virtualConsole,
  });
  const { window } = dom;

  // --- Exposition du DOM au bundle (qui attend un environnement navigateur) ---
  // NOTE : `performance` est volontairement absent. Remplacer le `performance`
  // global de Node par celui de jsdom provoque une récursion infinie
  // (`Performance.now()` de jsdom se rappelle lui-même). Node en fournit un.
  const globalKeys = [
    "window", "document", "HTMLElement", "HTMLInputElement", "HTMLSelectElement",
    "HTMLAnchorElement", "Element", "Node", "Text", "Event", "CustomEvent",
    "PopStateEvent", "MouseEvent", "KeyboardEvent", "DOMException", "SVGElement",
    "getComputedStyle", "requestAnimationFrame", "cancelAnimationFrame",
    "matchMedia", "MutationObserver", "localStorage", "sessionStorage",
    "history", "location", "DOMParser", "FormData", "Blob",
  ];
  for (const key of globalKeys) {
    if (key in window) {
      Object.defineProperty(globalThis, key, {
        value: window[key],
        configurable: true,
        writable: true,
      });
    }
  }

  // `fetch` : le bundle appelle des chemins relatifs (`/api/...`), qui n'ont pas
  // de sens dans Node. On les résout contre l'adresse du serveur.
  const nodeFetch = globalThis.fetch;
  const boundFetch = (input, init) =>
    nodeFetch(typeof input === "string" ? new URL(input, BASE).href : input, init);
  Object.defineProperty(globalThis, "fetch", {
    value: boundFetch,
    configurable: true,
    writable: true,
  });
  Object.defineProperty(window, "fetch", { value: boundFetch, configurable: true, writable: true });

  process.on("unhandledRejection", (reason) => errors.push(`unhandledRejection: ${reason}`));
  process.on("uncaughtException", (error) => errors.push(`uncaughtException: ${error.message}`));

  const root = window.document.getElementById("root");
  const text = () => root?.textContent?.replace(/\s+/g, " ").trim() ?? "";

  try {
    await import(bundleHref);
  } catch (error) {
    errors.push(`import du bundle : ${error?.message ?? error}`);
  }

  // On attend le **marqueur de la page**, pas simplement « du texte » : le
  // gabarit (menu latéral) s'affiche avant que les données n'arrivent.
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (text().includes(marker)) break;
    await new Promise((resolve) => setTimeout(resolve, 200));
  }

  const rendered = text();
  return {
    route,
    marker,
    length: rendered.length,
    markerFound: rendered.includes(marker),
    errors,
    excerpt: rendered.slice(0, 240),
  };
}

// ==========================================================================
// Mode orchestrateur : une route par processus enfant
// ==========================================================================

async function api(pathname) {
  const response = await fetch(`${BASE}${pathname}`);
  if (!response.ok) throw new Error(`${pathname} → HTTP ${response.status}`);
  return response.json();
}

function runChild(route, marker, timeoutMs) {
  return new Promise((resolve) => {
    const child = spawn(
      process.execPath,
      [import.meta.filename, "--child", "--route", route, "--marker", marker, "--timeout", String(timeoutMs)],
      { cwd: ROOT, env: process.env, stdio: ["ignore", "pipe", "pipe"] },
    );

    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => (stdout += chunk));
    child.stderr.on("data", (chunk) => (stderr += chunk));

    const hardKill = setTimeout(() => child.kill("SIGKILL"), timeoutMs + 20_000);

    child.on("close", (code) => {
      clearTimeout(hardKill);
      const line = stdout.split("\n").find((row) => row.startsWith(RESULT_PREFIX));
      if (!line) {
        resolve({
          route,
          marker,
          length: 0,
          markerFound: false,
          errors: [`processus enfant terminé (code ${code}) sans résultat`, stderr.slice(0, 300)],
          excerpt: "",
        });
        return;
      }
      try {
        resolve(JSON.parse(line.slice(RESULT_PREFIX.length)));
      } catch (error) {
        resolve({
          route,
          marker,
          length: 0,
          markerFound: false,
          errors: [`résultat enfant illisible : ${error.message}`],
          excerpt: "",
        });
      }
    });
  });
}

async function main() {
  console.log("=".repeat(74));
  console.log("  TEST DE RENDU — pages FasoTurf (bundle compilé + API réelle)");
  console.log("=".repeat(74));

  try {
    readFileSync(path.join(DIST, "index.html"), "utf8");
  } catch {
    console.log("\nInterface non compilée : lancer `npm run build` puis relancer.\n");
    process.exit(1);
  }

  // ------------------------------------------------------------------
  // Hygiène du bundle : aucune origine d'API absolue.
  //
  // L'API doit toujours être appelée en URL **relative** (`/api/...`) : elle
  // est résolue par le proxy Vite (développement 5173 et prévisualisation
  // 4173) ou par le backend qui sert `dist/` sur la même origine.
  //
  // Une origine figée (ex. « si port 5173 alors 127.0.0.1:8000 ») casse
  // silencieusement dès que l'interface est servie sur un autre port : le
  // serveur de fichiers statiques répond alors 404 sur `/api/...` et le
  // tableau de bord reste vide. Aucun outil ne signale cette régression.
  // ------------------------------------------------------------------
  const bundleName = readdirSync(path.join(DIST, "assets")).find((n) => /^index-.*\.js$/.test(n));
  const bundleSource = readFileSync(path.join(DIST, "assets", bundleName), "utf8");
  const originsFichees = ["http://127.0.0.1:", "http://localhost:", "http://0.0.0.0:"].filter((o) =>
    bundleSource.includes(o),
  );
  if (originsFichees.length > 0) {
    console.log(
      `\n[FAIL ] origine d'API figée dans le bundle : ${originsFichees.join(", ")}\n` +
        "         L'API doit rester en URL relative (voir src/lib/apiBase.ts).\n",
    );
    process.exit(1);
  }
  console.log(`[  OK ] bundle sans origine figée — API appelée en URL relative (${bundleName})`);

  const health = await fetch(`${BASE}/api/health`).catch(() => null);
  if (!health?.ok) {
    console.log(`\nServeur injoignable sur ${BASE} : démarrer l'application d'abord.\n`);
    process.exit(1);
  }
  const healthBody = await health.json();
  const coverage = healthBody.coverage ?? {};
  console.log(
    `[  OK ] serveur joignable — ${healthBody.database} · ` +
      `${coverage.exploitableRaces ?? "?"} courses exploitables · ` +
      `${coverage.runners ?? "?"} partants`,
  );

  const [races, horses, jockeys, trainers] = await Promise.all([
    api("/api/races/summary?limit=1"),
    api("/api/horses?q=ganass&limit=1"),
    api("/api/jockeys?limit=1"),
    api("/api/trainers?limit=1"),
  ]);

  /**
   * Chaque route est associée à un marqueur qui n'existe **que** sur cette page
   * (et non dans le menu latéral, présent partout) : sans cela, le test
   * passerait même si la page ne s'affichait pas.
   */
  const routes = [
    { route: "/", marker: "Programme officiel", label: "page publique" },
    { route: "/dashboard", marker: "Top 5 des pronostics", label: "tableau de bord", timeout: 60_000 },
    { route: "/courses", marker: "au moins 8 partants", label: "programme" },
    { route: "/pronostics", marker: "Ce que ce classement est", label: "pronostics", timeout: 60_000 },
    { route: "/chevaux", marker: "Un même nom peut désigner", label: "recherche chevaux" },
    { route: "/jockeys", marker: "Voir les entraîneurs", label: "jockeys" },
    { route: "/entraineurs", marker: "Voir les jockeys", label: "entraîneurs" },
    { route: "/analyses", marker: "Courses analysables", label: "analyses" },
    { route: "/statistiques", marker: "Traçabilité de la donnée", label: "statistiques" },
  ];

  if (races?.[0]?.id) {
    routes.push({ route: `/courses/${races[0].id}`, marker: "Partants (", label: "fiche course" });
  }
  if (horses?.[0]?.id) {
    routes.push({ route: `/chevaux/${horses[0].id}`, marker: "Statistiques réelles", label: "fiche cheval" });
  }
  if (jockeys?.[0]?.id) {
    routes.push({ route: `/jockeys/${jockeys[0].id}`, marker: "Statistiques réelles", label: "fiche jockey" });
  }
  if (trainers?.[0]?.id) {
    routes.push({
      route: `/entraineurs/${trainers[0].id}`,
      marker: "Statistiques réelles",
      label: "fiche entraîneur",
    });
  }

  console.log("");
  let failures = 0;

  for (const { route, marker, label, timeout } of routes) {
    const started = Date.now();
    const result = await runChild(route, marker, timeout ?? 30_000);
    const elapsed = ((Date.now() - started) / 1000).toFixed(1);

    const substantial = result.length > 400;
    const ok = result.markerFound && substantial && result.errors.length === 0;
    if (!ok) failures += 1;

    const reasons = [
      !result.markerFound && `marqueur « ${marker} » absent`,
      !substantial && `texte trop court (${result.length})`,
      result.errors.length > 0 && `${result.errors.length} erreur(s) : ${result.errors[0].slice(0, 150)}`,
    ].filter(Boolean);

    console.log(
      `[${ok ? "  OK " : "FAIL "}] ${label} (${route}) — ` +
        (ok ? `${result.length} caractères en ${elapsed}s` : reasons.join(" · ")),
    );

    if (VERBOSE) {
      if (result.excerpt) console.log(`         extrait : ${result.excerpt}…`);
      for (const error of result.errors.slice(0, 4)) {
        console.log(`         ${error.slice(0, 260)}`);
      }
    }
  }

  console.log("");
  console.log("=".repeat(74));
  console.log(
    failures === 0
      ? `  ${routes.length} pages montées et rendues sans erreur`
      : `  ${failures} page(s) en échec sur ${routes.length}`,
  );
  console.log("=".repeat(74));
  process.exit(failures === 0 ? 0 : 1);
}

// ==========================================================================
// Aiguillage
// ==========================================================================

const argv = process.argv;
if (argv.includes("--child")) {
  const route = argv[argv.indexOf("--route") + 1];
  const marker = argv[argv.indexOf("--marker") + 1];
  const timeout = Number(argv[argv.indexOf("--timeout") + 1]) || 30_000;
  const result = await renderSingleRoute(route, marker, timeout);
  process.stdout.write(`\n${RESULT_PREFIX}${JSON.stringify(result)}\n`);
  process.exit(0);
} else {
  await main();
}
