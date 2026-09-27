import type { DataOrigin } from "./common";

export interface UserSummary {
  id: string;
  firstName: string;
  lastName: string;
  /** Photo de profil si disponible — sinon les initiales sont utilisées. */
  avatarUrl?: string | null;
  /** Statut affiché sous le nom dans la topbar. */
  statusLabel: string;
}

export type PlanCode = "FREE" | "PRO" | "NONE";
export type SubscriptionStatus = "ACTIVE" | "EXPIRED" | "CANCELLED" | "NONE";

export interface SubscriptionSummary {
  plan: PlanCode;
  status: SubscriptionStatus;
  /** Date ISO d'échéance, si connue. */
  expiresAt?: string | null;
  /**
   * Faux tant qu'aucun système d'abonnement n'est branché. L'interface affiche
   * alors un état explicite plutôt qu'un forfait par défaut (spec §22).
   */
  configured: boolean;
  origin?: DataOrigin;
}
