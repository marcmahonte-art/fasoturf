import type { DataOrigin } from "./common";

export type PerformancePeriod = "7d" | "30d" | "month";

/**
 * Performances affichées à l'utilisateur.
 *
 * Le backend n'expose **pas** encore cette donnée : elle exige un historique de
 * paris lié à un compte utilisateur, qui n'existe pas dans la base. L'interface
 * reçoit donc `null` et affiche un état explicitement indisponible plutôt
 * qu'un chiffre inventé (spec §24 et §40).
 */
export interface UserPerformance {
  successRate: number;
  successRateDelta: number;
  top3Rate: number;
  top3Delta: number;
  racesAnalyzed: number;
  period: PerformancePeriod;
  origin: DataOrigin;
}

export interface NotificationItem {
  id: string;
  title: string;
  createdAt: string;
  read: boolean;
  href?: string;
}

export interface NotificationSummary {
  unreadCount: number;
  items: NotificationItem[];
  /**
   * Faux tant qu'aucun compte utilisateur n'existe : les notifications ne sont
   * pas « vides », elles sont **indisponibles**. La distinction est affichée.
   */
  configured: boolean;
  origin: DataOrigin;
}

export type SyncStatus = "CURRENT" | "SYNCING" | "ERROR";

export const SYNC_STATUS_LABEL: Record<SyncStatus, string> = {
  CURRENT: "Données mises à jour",
  SYNCING: "Synchronisation…",
  ERROR: "Erreur de synchronisation",
};

export interface DataStatus {
  status: SyncStatus;
  /** Horodatage ISO de la dernière consolidation connue. */
  lastUpdatedAt: string;
  source: string;
  /** Nombre de courses réellement disponibles pour la journée affichée. */
  raceCount: number;
  origin: DataOrigin;
}

/** Volumes réellement présents dans la base (exposés par /api/statistics). */
export interface CoverageStats {
  races: number;
  exploitableRaces: number;
  racesWithResult: number;
  runners: number;
  horses: number;
  jockeys: number;
  trainers: number;
  hippodromes: number;
  oddsSnapshots: number;
}
