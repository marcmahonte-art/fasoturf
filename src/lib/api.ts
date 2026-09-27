import { API_BASE_URL, API_DASHBOARD_TIMEOUT_MS, API_TIMEOUT_MS } from "./apiBase";
import type { DashboardData } from "../types/dashboard";
import type { DateItem, RaceDetail, RaceSummary } from "../types/race";
import type { Prediction } from "../types/prediction";
import type { RacePrediction, PredictionUnavailable, StatisticsOverview } from "../types/statistics";
import type {
  HorseDetail,
  HorseSummary,
  PersonDetail,
  PersonSummary,
} from "../types/entities";
import type { CoverageStats, DataStatus, NotificationSummary } from "../types/performance";
import type { SubscriptionSummary, UserSummary } from "../types/user";

/**
 * Client de l'API FasoTurf.
 *
 * Le frontend **ne touche jamais** la base : il consomme uniquement les
 * endpoints REST exposés par `backend/`, qui agrègent côté serveur la donnée du
 * socle LONAB et les sorties du moteur Hippo Engine.
 *
 * Aucune donnée n'est inventée ici. Ce qui n'existe pas côté backend arrive en
 * `null` accompagné de sa raison, et l'interface l'affiche tel quel (spec §2.3).
 */

/** Réponse brute du backend (contrat `backend/schemas/dashboard.py`). */
interface DashboardResponse {
  targetDate: string | null;
  user: UserSummary | null;
  subscription: SubscriptionSummary;
  nextRace: RaceSummary | null;
  followedRaces: RaceSummary[];
  topPredictions: Prediction[];
  predictionContext: string | null;
  predictionUnavailableReason: string | null;
  performance: null;
  performanceUnavailableReason: string | null;
  coverage: CoverageStats;
  notifications: NotificationSummary;
  dataStatus: DataStatus;
  isLive: boolean;
}

/** Extrait un message d'erreur lisible d'une réponse en échec. */
async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown; hint?: unknown };
    const detail = typeof body.detail === "string" ? body.detail : null;
    const hint = typeof body.hint === "string" ? body.hint : null;
    if (detail && hint) return `${detail} ${hint}`;
    if (detail) return detail;
  } catch {
    // corps non JSON : on retombe sur le code HTTP
  }
  return `L'API a répondu ${response.status}.`;
}

/** GET JSON générique avec délai maximal et messages d'erreur explicites. */
async function apiGet<T>(path: string, timeoutMs = API_TIMEOUT_MS): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
  } catch (error) {
    clearTimeout(timeoutId);
    const aborted = error instanceof DOMException && error.name === "AbortError";
    throw new Error(
      aborted
        ? "L'API FasoTurf n'a pas répondu dans le délai imparti."
        : "L'API FasoTurf est injoignable. Démarrez le backend puis réessayez.",
    );
  }
  clearTimeout(timeoutId);

  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as T;
}

/**
 * Charge l'ensemble des données du Dashboard.
 *
 * @throws Error si l'API est injoignable ou répond une erreur — l'interface
 *         affiche alors un état d'erreur plutôt que de fabriquer des chiffres
 *         (spec §40).
 */
export async function fetchDashboard(date?: string): Promise<DashboardData> {
  const query = date ? `?date=${encodeURIComponent(date)}` : "";
  const payload = await apiGet<DashboardResponse>(
    `/api/dashboard${query}`,
    API_DASHBOARD_TIMEOUT_MS,
  );

  return {
    targetDate: payload.targetDate ?? null,
    user: payload.user ?? null,
    subscription: payload.subscription,
    nextRace: payload.nextRace ?? null,
    followedRaces: payload.followedRaces ?? [],
    topPredictions: payload.topPredictions ?? [],
    predictionContext: payload.predictionContext ?? null,
    predictionUnavailableReason: payload.predictionUnavailableReason ?? null,
    // Le backend renvoie toujours null : aucune métrique personnelle n'existe
    // en base. On ne substitue jamais une valeur de démonstration.
    performance: null,
    performanceUnavailableReason: payload.performanceUnavailableReason ?? null,
    coverage: payload.coverage,
    notifications: payload.notifications,
    dataStatus: payload.dataStatus,
    isLive: payload.isLive,
  };
}

/** Détail réel d'une course (partants, cotes, arrivée). */
export async function fetchRace(raceId: string): Promise<RaceDetail> {
  return apiGet<RaceDetail>(`/api/races/${encodeURIComponent(raceId)}`);
}

/**
 * Pronostic du moteur Hippo Engine pour une course.
 *
 * Retourne soit le pronostic, soit une indisponibilité **explicite** : on ne
 * remplace jamais une absence de pronostic par une estimation locale.
 */
export async function fetchRacePrediction(
  raceId: string,
): Promise<RacePrediction | PredictionUnavailable> {
  return apiGet<RacePrediction | PredictionUnavailable>(
    `/api/predictions/race/${encodeURIComponent(raceId)}`,
    API_DASHBOARD_TIMEOUT_MS,
  );
}

/** Statistiques réellement disponibles, chacune avec sa méthode de calcul. */
export async function fetchStatistics(): Promise<StatisticsOverview> {
  return apiGet<StatisticsOverview>("/api/statistics", 15000);
}

/** Journées de courses réellement présentes dans la base. */
export async function fetchAvailableDates(limit = 60): Promise<DateItem[]> {
  return apiGet<DateItem[]>(`/api/dates?limit=${limit}`);
}

/** Disciplines réellement présentes en base (pour alimenter un filtre). */
export async function fetchDisciplines(): Promise<string[]> {
  return apiGet<string[]>("/api/disciplines");
}

export interface RaceSummaryQuery {
  date?: string | null;
  hippodrome?: string | null;
  discipline?: string | null;
  onlyLonab?: boolean;
  /** Ne garder que les courses analysables par le moteur (document source présent). */
  analysable?: boolean;
  limit?: number;
  offset?: number;
}

/** Liste légère des courses, filtrable (pages /courses et /analyses). */
export async function fetchRaceSummaries(query: RaceSummaryQuery = {}): Promise<RaceSummary[]> {
  const params = new URLSearchParams();
  if (query.date) params.set("date", query.date);
  if (query.hippodrome) params.set("hippodrome", query.hippodrome);
  if (query.discipline) params.set("discipline", query.discipline);
  if (query.onlyLonab) params.set("only_lonab", "true");
  if (query.analysable) params.set("analysable", "true");
  params.set("limit", String(query.limit ?? 40));
  if (query.offset) params.set("offset", String(query.offset));
  return apiGet<RaceSummary[]>(`/api/races/summary?${params.toString()}`);
}

// --------------------------------------------------------------------------
// Chevaux / personnes
// --------------------------------------------------------------------------

export interface HorseSearchQuery {
  q?: string | null;
  limit?: number;
  offset?: number;
}

/** Recherche de chevaux (page /chevaux). */
export async function fetchHorses(query: HorseSearchQuery = {}): Promise<HorseSummary[]> {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  params.set("limit", String(query.limit ?? 40));
  if (query.offset) params.set("offset", String(query.offset));
  return apiGet<HorseSummary[]>(`/api/horses?${params.toString()}`, 12000);
}

/** Fiche complète d'un cheval. */
export async function fetchHorse(horseId: string): Promise<HorseDetail> {
  return apiGet<HorseDetail>(`/api/horses/${encodeURIComponent(horseId)}`, 12000);
}

export type PersonRole = "jockey" | "trainer";

export interface PersonSearchQuery {
  q?: string | null;
  limit?: number;
  offset?: number;
}

/** Recherche de jockeys ou d'entraîneurs. */
export async function fetchPersons(
  role: PersonRole,
  query: PersonSearchQuery = {},
): Promise<PersonSummary[]> {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  params.set("limit", String(query.limit ?? 40));
  if (query.offset) params.set("offset", String(query.offset));
  const path = role === "jockey" ? "jockeys" : "trainers";
  return apiGet<PersonSummary[]>(`/api/${path}?${params.toString()}`, 12000);
}

/** Fiche complète d'un jockey ou d'un entraîneur. */
export async function fetchPerson(role: PersonRole, personId: string): Promise<PersonDetail> {
  const path = role === "jockey" ? "jockeys" : "trainers";
  return apiGet<PersonDetail>(`/api/${path}/${encodeURIComponent(personId)}`, 12000);
}

/** Pronostics mis en avant pour une journée (page /pronostics). */
export interface FeaturedPredictions {
  raceId: string | null;
  context: string | null;
  predictions: Prediction[];
  unavailableReason: string | null;
}

export async function fetchFeaturedPredictions(
  date?: string | null,
  limit = 10,
): Promise<FeaturedPredictions> {
  const params = new URLSearchParams();
  if (date) params.set("date", date);
  params.set("limit", String(limit));
  return apiGet<FeaturedPredictions>(
    `/api/predictions/featured?${params.toString()}`,
    API_DASHBOARD_TIMEOUT_MS,
  );
}

