import type { Race } from "../data/races";
import fallbackRaces from "../data/realRaces.json";

const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Récupère les courses récentes depuis l'API FastAPI
 * Avec repli automatique sur le fichier local si l'API n'est pas démarrée.
 */
export async function fetchRaces(limit: number = 25): Promise<{ races: Race[]; isLive: boolean }> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const response = await fetch(`${API_BASE_URL}/api/races?limit=${limit}`, {
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

  return { races: fallbackRaces as Race[], isLive: false };
}

/**
 * Récupère les courses de la dernière date en direct
 */
export async function fetchTodayRaces(): Promise<{ races: Race[]; isLive: boolean }> {
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
        return { races: data as Race[], isLive: true };
      }
    }
  } catch {
    // repli
  }

  return { races: fallbackRaces as Race[], isLive: false };
}
