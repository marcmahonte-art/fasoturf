/**
 * Formatters d'affichage.
 *
 * Aucune valeur n'est inventée ici : un formatter qui ne sait pas formater
 * renvoie une chaîne vide plutôt qu'un chiffre de remplacement.
 */

const MONTHS_SHORT_FR = [
  "janv.",
  "févr.",
  "mars",
  "avr.",
  "mai",
  "juin",
  "juil.",
  "août",
  "sept.",
  "oct.",
  "nov.",
  "déc.",
];

const MONTHS_FULL_FR = [
  "Janvier",
  "Février",
  "Mars",
  "Avril",
  "Mai",
  "Juin",
  "Juillet",
  "Août",
  "Septembre",
  "Octobre",
  "Novembre",
  "Décembre",
];

/**
 * Date du jour au format `AAAA-MM-JJ`, en heure **locale**.
 *
 * Aucune date n'est écrite en dur dans l'application : une date figée dans le
 * code devient silencieusement fausse dès le lendemain.
 */
export function todayIso(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

/** « 2026-10-03 » → « 3 Octobre 2026 ». Le mois est celui de la date, jamais un mois figé. */
export function formatDayMonthYear(iso: string | null | undefined): string {
  if (!iso) return "";
  const parts = iso.slice(0, 10).split("-");
  if (parts.length !== 3) return iso;
  const month = MONTHS_FULL_FR[Number(parts[1]) - 1];
  if (!month) return iso;
  return `${Number(parts[2])} ${month} ${parts[0]}`;
}

/** « 2026-10-03 » → « 3 Oct ». */
export function formatDayMonthShort(iso: string | null | undefined): string {
  if (!iso) return "";
  const parts = iso.slice(0, 10).split("-");
  if (parts.length !== 3) return iso;
  const month = MONTHS_SHORT_FR[Number(parts[1]) - 1];
  if (!month) return iso;
  const short = month.endsWith(".") ? month.slice(0, -1) : month;
  return `${Number(parts[2])} ${short.charAt(0).toUpperCase()}${short.slice(1)}`;
}

/** 2700 → « 2 700 m ». */
export function formatDistance(meters: number | null | undefined): string {
  if (!meters || meters <= 0) return "—";
  return `${meters.toLocaleString("fr-FR").replace(/\u202f|\u00a0/g, " ")} m`;
}

/** « 13:55 » → « 13h55 ». Toute autre forme est renvoyée telle quelle. */
export function formatClock(time: string | null | undefined): string {
  if (!time) return "—";
  const match = /^(\d{1,2}):(\d{2})$/.exec(time.trim());
  if (!match) return time;
  return `${Number(match[1])}h${match[2]}`;
}

/** « 2025-12-12 » → « 12 déc. 2025 ». */
export function formatDateShort(iso: string | null | undefined): string {
  if (!iso) return "—";
  const parts = iso.slice(0, 10).split("-");
  if (parts.length !== 3) return iso;
  const month = MONTHS_SHORT_FR[Number(parts[1]) - 1];
  if (!month) return iso;
  return `${Number(parts[2])} ${month} ${parts[0]}`;
}

/** « 2026-09-16 » → « Aujourd'hui 10:24 » si c'est aujourd'hui, sinon la date. */
export function formatLastUpdate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  const time = `${String(date.getHours()).padStart(2, "0")}:${String(
    date.getMinutes(),
  ).padStart(2, "0")}`;
  const today = new Date();
  const sameDay =
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate();
  if (sameDay) return `Aujourd'hui ${time}`;
  return `${formatDateShort(iso)} ${time}`;
}

/** 1243 → « 1 243 ». */
export function formatCount(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("fr-FR").replace(/\u202f|\u00a0/g, " ");
}

/** Probabilité 0–1 ou 0–100 → « 78 % ». */
export function formatPercent(
  value: number | null | undefined,
  fractionDigits = 0,
): string {
  if (value === null || value === undefined) return "—";
  const pct = value <= 1 ? value * 100 : value;
  return `${pct.toFixed(fractionDigits).replace(".", ",")} %`;
}

/** Cote décimale → « 2,4 ». */
export function formatOdds(value: number | null | undefined): string {
  if (value === null || value === undefined || value <= 0) return "—";
  return value.toFixed(1).replace(".", ",");
}

/** +12 → « +12 % », −3 → « −3 % ». */
export function formatDelta(value: number): string {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${Math.abs(value)} %`;
}

/** Libellé « R1 · C4 ». */
export function formatMeetingLabel(meeting: number, race: number): string {
  return `R${meeting} · C${race}`;
}

/** 1536 → « 1536 px » ; utilisé uniquement en debug/QA. */
export function formatPx(value: number): string {
  return `${value} px`;
}
