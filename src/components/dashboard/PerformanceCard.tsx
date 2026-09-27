import { Link } from "react-router-dom";
import { ArrowRight, ChartNoAxesColumnIncreasing, Crown, Info } from "lucide-react";
import { buttonClass } from "../ui/buttonStyles";
import { Card } from "../ui/Card";
import { DataOriginBadge } from "../ui/DataOriginBadge";
import { PerformanceMetrics } from "./PerformanceMetrics";
import { formatDateShort } from "../../lib/formatters";
import type { UserPerformance } from "../../types/performance";
import type { SubscriptionSummary } from "../../types/user";

/**
 * Carte « Mes performances » (spec §22 et §23).
 *
 * Note de vocabulaire : on affiche « Mon abonnement » et non « Mon solde »,
 * FasoTurf n'étant pas un portefeuille de paris (spec §22).
 *
 * `performance` vaut `null` tant que le backend n'expose pas de métriques
 * personnelles (elles exigent un historique de paris lié à un compte). Dans ce
 * cas la carte affiche **la raison** de l'indisponibilité — jamais des chiffres
 * de remplacement (spec §40).
 */
export function PerformanceCard({
  performance,
  performanceUnavailableReason,
  subscription,
}: {
  performance: UserPerformance | null;
  performanceUnavailableReason: string | null;
  subscription: SubscriptionSummary;
}) {
  const isPro = subscription.configured && subscription.plan === "PRO";

  return (
    <Card className="flex h-full flex-col" padding="md">
      <header className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ChartNoAxesColumnIncreasing
            size={16}
            strokeWidth={2.2}
            aria-hidden="true"
            className="text-faso-green"
          />
          <h2 className="text-[15px] font-bold leading-5 text-faso-text">Mes performances</h2>
        </div>
        <div className="flex items-center gap-2">
          {/* Aucun badge d'origine quand il n'y a rien à attribuer. */}
          {performance && <DataOriginBadge origin={performance.origin} />}
          <Link
            to="/statistiques"
            className="inline-flex items-center gap-1 text-[12px] font-semibold text-faso-green hover:text-faso-green-dark"
          >
            Voir le détail
            <ArrowRight size={12} aria-hidden="true" />
          </Link>
        </div>
      </header>

      <div className="mt-3">
        {performance ? (
          <PerformanceMetrics performance={performance} />
        ) : (
          <div className="flex items-start gap-2 rounded-[10px] border border-faso-border bg-faso-bg px-3 py-3">
            <Info
              size={13}
              aria-hidden="true"
              className="mt-[2px] shrink-0 text-faso-muted"
            />
            <div className="min-w-0">
              <p className="text-[12px] font-semibold leading-tight text-faso-text">
                Métriques personnelles indisponibles
              </p>
              <p className="mt-1 text-[11px] leading-[16px] text-faso-muted">
                {performanceUnavailableReason ??
                  "Aucune statistique personnelle n'est enregistrée pour le moment."}
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="mt-auto pt-3">
        <p className="text-[11.5px] font-medium text-faso-muted">Mon abonnement</p>

        <div className="mt-2 flex items-center gap-3 rounded-[10px] border border-faso-border px-2.5 py-2">
          <span
            aria-hidden="true"
            className="grid h-9 w-9 shrink-0 place-items-center rounded-[9px] bg-faso-gold"
          >
            <Crown size={17} className="text-white" />
          </span>

          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] font-bold leading-tight text-faso-text">
              {subscription.configured
                ? `FasoTurf ${isPro ? "Pro" : "Découverte"}`
                : "Aucun abonnement actif"}
            </p>
            <p className="mt-0.5 truncate text-[11px] leading-none text-faso-muted">
              {subscription.configured
                ? subscription.expiresAt
                  ? `Actif jusqu'au ${formatDateShort(subscription.expiresAt)}`
                  : "Aucune échéance enregistrée"
                : "La gestion d'abonnement n'est pas encore ouverte"}
            </p>
          </div>

          <Link to="/abonnement" className={buttonClass("primary", "sm")}>
            Gérer
            <ArrowRight size={12} aria-hidden="true" />
          </Link>
        </div>
      </div>
    </Card>
  );
}
