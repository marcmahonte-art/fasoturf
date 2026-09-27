import type { RaceSummary } from "./race";
import type { Prediction } from "./prediction";
import type { SubscriptionSummary, UserSummary } from "./user";
import type {
  CoverageStats,
  DataStatus,
  NotificationSummary,
  UserPerformance,
} from "./performance";

/**
 * Contrat de la page /dashboard (spec §39).
 *
 * La page ne contient aucune donnée en dur : tout provient de
 * `fetchDashboard()`, qui interroge `GET /api/dashboard`.
 *
 * Règle de séparation (spec §2.3) : ce qui n'existe pas côté backend est
 * déclaré **indisponible avec sa raison** (`*UnavailableReason`) et n'est
 * jamais remplacé par une valeur inventée.
 */
export interface DashboardData {
  /** Journée effectivement affichée — résolue par le backend. */
  targetDate: string | null;

  /** `null` tant qu'aucune authentification n'est branchée. */
  user: UserSummary | null;
  subscription: SubscriptionSummary;

  nextRace: RaceSummary | null;
  followedRaces: RaceSummary[];

  topPredictions: Prediction[];
  /** Contexte du pronostic affiché (course, modèle, qualité de donnée). */
  predictionContext: string | null;
  /** Raison affichée lorsque le moteur n'a pas pu produire de pronostic. */
  predictionUnavailableReason: string | null;

  /** Toujours `null` : aucune métrique personnelle n'existe en base. */
  performance: UserPerformance | null;
  performanceUnavailableReason: string | null;

  coverage: CoverageStats;
  notifications: NotificationSummary;
  dataStatus: DataStatus;
  /** Vrai lorsque la journée affichée est celle du jour. */
  isLive: boolean;
}

export type AsyncState<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: T };
