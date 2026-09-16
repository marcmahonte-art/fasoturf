import type { Race } from "../data/races";
import fallbackRaces from "../data/realRaces.json";

const API_BASE_URL = "http://127.0.0.1:8000";

export interface DateItem {
  date: string;
  label: string;
  count: number;
  isToday: boolean;
}

/**
 * Récupère les courses récentes depuis l'API FastAPI (avec filtre par date optionnel)
 * Avec repli automatique sur le fichier local si l'API n'est pas démarrée.
 */
export async function fetchRaces(
  limit: number = 40,
  date?: string
): Promise<{ races: Race[]; isLive: boolean }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const query = date ? `limit=${limit}&date=${date}` : `limit=${limit}`;
    const response = await fetch(`${API_BASE_URL}/api/races?${query}`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        return { races: data as Race[], isLive: true };
      }
    }
  } catch {
    // API hors ligne ou injoignable, bascule transparente sur le cache local
  }

  let filtered = fallbackRaces as Race[];
  if (date) {
    filtered = filtered.filter((r) => r.date === date);
  }
  return { races: filtered, isLive: false };
}

/**
 * Récupère les courses du jour (date du jour ou date la plus récente)
 */
export async function fetchTodayRaces(): Promise<{ races: Race[]; isLive: boolean; todayDate?: string }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const response = await fetch(`${API_BASE_URL}/api/races/today`, {
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      if (Array.isArray(data) && data.length > 0) {
        return { races: data as Race[], isLive: true, todayDate: data[0]?.date };
      }
    }
  } catch {
    // repli
  }

  const all = fallbackRaces as Race[];
  const todayDate = all[0]?.date || "2026-09-16";
  const todayOnly = all.filter((r) => r.date === todayDate);
  return { races: todayOnly.length > 0 ? todayOnly : all, isLive: false, todayDate };
}

/**
 * Récupère la liste des dates de courses disponibles
 */
export async function fetchDates(): Promise<DateItem[]> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

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
    // repli
  }

  // Calcul du repli à partir de fallbackRaces
  const countMap: Record<string, number> = {};
  for (const r of fallbackRaces as Race[]) {
    countMap[r.date] = (countMap[r.date] || 0) + 1;
  }

  const dates = Object.keys(countMap).sort().reverse();
  const todayStr = dates[0] || "2026-09-16";

  const months: Record<string, string> = {
    "01": "Janv", "02": "Févr", "03": "Mars", "04": "Avr",
    "05": "Mai", "06": "Juin", "07": "Juil", "08": "Août",
    "09": "Sept", "10": "Oct", "11": "Nov", "12": "Déc"
  };

  return dates.map((d) => {
    const isToday = d === todayStr;
    const parts = d.split("-");
    const label = isToday ? "Aujourd'hui" : `${parts[2]} ${months[parts[1]] || parts[1]}`;
    return {
      date: d,
      label,
      count: countMap[d],
      isToday,
    };
  });
}
