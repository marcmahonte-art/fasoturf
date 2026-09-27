/**
 * Vérifie que TOUTE classe Tailwind utilisée dans `src/` est réellement
 * générée dans le CSS compilé.
 *
 * Pourquoi ce test existe :
 *
 * Tailwind ne génère une classe que si sa valeur existe dans le thème. Une
 * classe écrite « à peu près » — typiquement un modificateur d'opacité hors
 * échelle comme `text-white/72` (l'échelle va de 5 en 5) — ne produit
 * **aucune règle CSS**. Elle est alors silencieusement inerte :
 *
 *   - `text-white/72` → aucune couleur appliquée → le texte HÉRITE du noir du
 *     `body` (`#17221c`) et devient invisible sur la sidebar sombre (`#001c18`).
 *
 * Ni `tsc`, ni `oxlint`, ni `npm run build` ne signalent ce problème : la
 * compilation réussit, la classe est simplement absente du CSS. C'est un
 * défaut **invisible en développement** et **catastrophique en rendu**.
 *
 * Usage (après `npm run build`) :
 *   node scripts/check_tailwind_classes.mjs
 *   node scripts/check_tailwind_classes.mjs --verbose
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";

const ROOT = path.resolve(import.meta.dirname, "..");
const SRC = path.join(ROOT, "src");
const DIST_ASSETS = path.join(ROOT, "dist", "assets");
const VERBOSE = process.argv.includes("--verbose");

// ==========================================================================
// 1. Extraire les classes candidates depuis les sources
// ==========================================================================

function walk(dir) {
  const out = [];
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    if (statSync(full).isDirectory()) out.push(...walk(full));
    else if (/\.(tsx?|jsx?)$/.test(full)) out.push(full);
  }
  return out;
}

/**
 * Préfixes d'utilitaires Tailwind. Sert à écarter le texte en langue naturelle :
 * sans ce filtre, « peut-être » ou « temps-réel » seraient signalés à tort.
 */
const UTILITY_PREFIXES = [
  "text", "bg", "border", "ring", "outline", "shadow", "fill", "stroke", "from", "via", "to",
  "divide", "placeholder", "decoration", "accent", "caret", "sr", "not-sr",
  "p", "px", "py", "pt", "pb", "pl", "pr", "ps", "pe",
  "m", "mx", "my", "mt", "mb", "ml", "mr", "ms", "me",
  "w", "h", "min-w", "max-w", "min-h", "max-h", "size",
  "flex", "grid", "gap", "gap-x", "gap-y", "items", "justify", "self", "place", "order",
  "col", "row", "space-x", "space-y", "basis", "grow", "shrink",
  "rounded", "font", "leading", "tracking", "uppercase", "lowercase", "capitalize",
  "truncate", "overflow", "object", "opacity", "transition", "duration", "ease", "delay",
  "animate", "transform", "scale", "rotate", "translate", "skew", "origin",
  "cursor", "select", "pointer-events", "resize", "appearance",
  "hidden", "block", "inline", "table", "contents", "flow-root",
  "relative", "absolute", "fixed", "sticky", "static",
  "inset", "top", "right", "bottom", "left", "z", "isolate", "float", "clear",
  "list", "underline", "whitespace", "break", "hyphens", "aspect", "columns",
  "backdrop", "brightness", "contrast", "drop-shadow", "grayscale", "hue-rotate",
  "invert", "saturate", "sepia", "mix-blend", "bg-blend", "will-change",
  "container", "antialiased", "subpixel-antialiased",
];

const PREFIX_RE = new RegExp(
  `^(?:${UTILITY_PREFIXES.map((p) => p.replace(/-/g, "\\-")).join("|")})(?:-|$)`,
);

/**
 * Utilitaires réellement complets en un seul mot (sans valeur).
 * Tout autre préfixe exige une valeur : sans cette liste, du texte en langue
 * naturelle (« top », « col », « text ») serait signalé à tort.
 */
const STANDALONE = new Set([
  "truncate", "hidden", "block", "inline", "flex", "grid", "table", "contents",
  "relative", "absolute", "fixed", "sticky", "static", "isolate",
  "underline", "overline", "line-through", "no-underline",
  "uppercase", "lowercase", "capitalize", "normal-case", "italic", "not-italic",
  "antialiased", "subpixel-antialiased", "container", "resize", "appearance",
  "transform", "transform-gpu", "transform-none", "grow", "shrink",
  "float-left", "float-right", "float-none", "clear-both", "clear-none",
  "sr-only", "not-sr-only", "visible", "invisible", "collapse",
  "overflow-hidden", "overflow-auto", "overflow-visible", "overflow-scroll",
  "overflow-clip", "overflow-x-hidden", "overflow-y-hidden",
  "overflow-x-auto", "overflow-y-auto", "overflow-x-visible", "overflow-y-visible",
  "w-full", "h-full", "w-auto", "h-auto", "w-fit", "h-fit",
  "h-screen", "w-screen", "min-h-screen", "min-w-0", "min-h-0",
  "flex-1", "flex-auto", "flex-none", "flex-col", "flex-row", "flex-wrap", "flex-nowrap",
  "items-center", "items-start", "items-end", "items-baseline", "items-stretch",
  "justify-center", "justify-between", "justify-start", "justify-end", "justify-around",
  "text-center", "text-left", "text-right", "text-justify",
  "whitespace-nowrap", "whitespace-normal", "whitespace-pre",
  "break-words", "break-all", "break-normal",
  "rounded-full", "rounded-none", "rounded-sm", "rounded-md", "rounded-lg", "rounded-xl",
  "pointer-events-none", "pointer-events-auto", "select-none", "select-all",
  "z-0", "z-10", "z-20", "z-30", "z-40", "z-50",
  "relative", "col-auto", "row-auto",
]);

/** Variantes (`hover:`, `md:`, `group-hover:`…) à retirer avant le test de préfixe. */
function stripVariants(token) {
  const parts = token.split(":");
  return parts[parts.length - 1];
}

function looksLikeUtility(token) {
  if (!token || token.length > 120) return false;
  if (/[\s'"`${}]/.test(token)) return false;
  if (!/^[a-zA-Z0-9:\/\[\]\.\-%()#!&*+~<>=_,]+$/.test(token)) return false;

  const base = stripVariants(token);
  // Un utilitaire est complet s'il porte une valeur (`-`), un modificateur
  // d'opacité (`/`) ou une valeur arbitraire (`[...]`).
  if (base.includes("-") || base.includes("/") || base.includes("[")) {
    return PREFIX_RE.test(base);
  }
  // Sinon il doit figurer dans la liste des utilitaires d'un seul mot.
  return STANDALONE.has(base);
}

function extractCandidates(source) {
  // Littéraux de chaîne : "…", '…', `…` (les gabarits interpolés sont écartés).
  const literals = source.match(/(?:"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*'|`(?:[^`\\]|\\.)*`)/g) ?? [];
  const tokens = new Set();
  for (const literal of literals) {
    if (literal.includes("${")) continue;
    for (const raw of literal.slice(1, -1).split(/\s+/)) {
      const token = raw.trim();
      if (looksLikeUtility(token)) tokens.add(token);
    }
  }
  return tokens;
}

// ==========================================================================
// 2. Indexer les classes réellement présentes dans le CSS compilé
// ==========================================================================

/** Échappement CSS appliqué par Tailwind aux caractères spéciaux d'un nom de classe. */
function cssEscape(name) {
  return name.replace(/[\[\]().\/%#,:'"!*+~<>=&;{}]/g, (ch) => `\\${ch}`);
}

function readCompiledCss() {
  const files = readdirSync(DIST_ASSETS).filter((f) => f.endsWith(".css"));
  if (files.length === 0) return null;
  return files.map((f) => readFileSync(path.join(DIST_ASSETS, f), "utf8")).join("\n");
}

function isGenerated(css, token) {
  const escaped = cssEscape(token);
  // Un vrai sélecteur se termine par `{`, `,`, `:`, un combinateur ou un espace.
  // Le lookahead évite qu'un préfixe (`text-white`) ne soit déclaré présent
  // parce qu'une classe plus longue (`text-white\/70`) existe.
  const re = new RegExp(`\\.${escaped.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?=[{,:>~+ )\\n}])`);
  return re.test(css);
}

// ==========================================================================
// 3. Rapport
// ==========================================================================

const css = readCompiledCss();
if (!css) {
  console.log("\nCSS compilé introuvable : lancer `npm run build` puis relancer.\n");
  process.exit(1);
}

const byFile = new Map();
for (const file of walk(SRC)) {
  const tokens = extractCandidates(readFileSync(file, "utf8"));
  const missing = [...tokens].filter((t) => !isGenerated(css, t)).sort();
  if (missing.length > 0) byFile.set(path.relative(ROOT, file).replace(/\\/g, "/"), missing);
}

console.log("=".repeat(74));
console.log("  CLASSES TAILWIND NON GÉNÉRÉES (inertes au rendu)");
console.log("=".repeat(74));

if (byFile.size === 0) {
  console.log("\n  Aucune — toutes les classes utilisées existent dans le CSS compilé.\n");
  process.exit(0);
}

let total = 0;
for (const [file, missing] of [...byFile.entries()].sort()) {
  total += missing.length;
  console.log(`\n${file}`);
  for (const token of missing) console.log(`    ${token}`);
}

console.log("");
console.log("=".repeat(74));
console.log(`  ${total} classe(s) inerte(s) dans ${byFile.size} fichier(s)`);
console.log("=".repeat(74));
if (!VERBOSE) {
  console.log("\n  Rappel : une classe inerte n'applique AUCUN style. Pour un modificateur");
  console.log("  d'opacité hors échelle (l'échelle va de 5 en 5), utiliser la forme");
  console.log("  entre crochets : text-white/[0.72] au lieu de text-white/72.");
}
process.exit(1);
