import type { Race } from "../data/races";
import type { DateItem } from "../types/race";
import fallbackRaces from "../data/realRaces.json";
import { API_BASE_URL, API_TIMEOUT_MS } from "../lib/apiBase";
import { todayIso } from "../lib/formatters";

export type { DateItem };

/**
 * Origine **réelle** du programme affiché sur la page publique.
 *
 * - `api` : courses servies par le backend FasoTurf, donc par le socle ;
 * - `snapshot` : instantané local figé (`data/realRaces.json`), utilisé
 *   uniquement lorsque l'API est injoignable.
 *
 * L'interface doit **dire** laquelle des deux elle affiche : présenter un
 * instantané figé comme la donnée du jour serait une information trompeuse
 * (spec §2.3).
 */
export type RaceFeedSource = "api" | "snapshot";

export interface RaceFeed {
  races: Race[];
  isLive: boolean;
  source: RaceFeedSource;
  /** Date de la dernière course de l'instantané local (si `source === "snapshot"`). */
  snapshotDate: string | null;
}

/** Instantané local, avec la date qu'il couvre réellement. */
function localSnapshot(): { races: Race[]; snapshotDate: string | null } {
  const races = fallbackRaces as Race[];
  const dates = races.map((race) => race.date).filter(Boolean).sort();
  return { races, snapshotDate: dates.length > 0 ? dates[dates.length - 1] : null };
}

/**
 * Récupère les courses récentes depuis l'API FasoTurf (filtre par date optionnel).
 *
 * Si l'API est injoignable, retourne l'instantané local en le **déclarant**
 * (`source: "snapshot"` + `snapshotDate`) : le repli n'est jamais silencieux.
 */
export async function fetchRaces(limit: number = 40, date?: string): Promise<RaceFeed> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

    const query = date ? `limit=${limit}&date=${date}` : `limit=${limit}`;
    const response = await fetch(`${API_BASE_URL}/api/races?${query}`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        return { races: data as Race[], isLive: true, source: "api", snapshotDate: null };
      }
    }
  } catch {
    // API hors ligne ou injoignable : repli explicite sur l'instantané local.
  }

  const snapshot = localSnapshot();
  const races = date ? snapshot.races.filter((race) => race.date === date) : snapshot.races;
  return {
    races,
    isLive: false,
    source: "snapshot",
    snapshotDate: snapshot.snapshotDate,
  };
}

/**
 * Récupère les courses du jour.
 *
 * La « journée » est la **date courante** ; si elle est absente de la source,
 * la date la plus récente réellement disponible est retournée et signalée par
 * `todayDate` — jamais une date écrite en dur.
 */
export async function fetchTodayRaces(): Promise<{
  races: Race[];
  isLive: boolean;
  source: RaceFeedSource;
  todayDate?: string;
}> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

    const response = await fetch(`${API_BASE_URL}/api/races/today`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        return {
          races: data as Race[],
          isLive: true,
          source: "api",
          todayDate: data[0]?.date,
        };
      }
    }
  } catch {
    // repli explicite ci-dessous
  }

  const snapshot = localSnapshot();
  const current = todayIso();
  const todayOnly = snapshot.races.filter((race) => race.date === current);
  if (todayOnly.length > 0) {
    return { races: todayOnly, isLive: false, source: "snapshot", todayDate: current };
  }
  return {
    races: snapshot.races,
    isLive: false,
    source: "snapshot",
    todayDate: snapshot.snapshotDate ?? undefined,
  };
}

/**
 * Récupère la liste des dates de courses disponibles.
 *
 * `isToday` est comparé à la **date courante réelle**, jamais à une constante.
 */
export async function fetchDates(): Promise<DateItem[]> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

    const response = await fetch(`${API_BASE_URL}/api/dates`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        return data as DateItem[];
      }
    }
  } catch {
    // repli explicite ci-dessous
  }

  // Repli : dates déduites de l'instantané local.
  const snapshot = localSnapshot();
  const countMap: Record<string, number> = {};
  for (const race of snapshot.races) {
    countMap[race.date] = (countMap[race.date] || 0) + 1;
  }

  const current = todayIso();
  const dates = Object.keys(countMap).sort().reverse();
  const mostRecent = dates[0] ?? null;

  return dates.map((date) => ({
    date,
    label:
      date === current
        ? "Aujourd'hui"
        : date === mostRecent
          ? `Dernière journée (${formatShort(date)})`
          : formatShort(date),
    count: countMap[date],
    isToday: date === current,
  }));
}

/** « 2026-10-03 » → « 3 oct. 2026 » (instantané local uniquement). */
function formatShort(iso: string): string {
  const parts = iso.slice(0, 10).split("-");
  if (parts.length !== 3) return iso;
  return `${Number(parts[2])}/${parts[1]}/${parts[0]}`;
}
