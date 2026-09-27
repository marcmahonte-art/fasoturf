import { Link } from "react-router-dom";
import { ArrowLeft, Construction } from "lucide-react";
import { DashboardLayout } from "../components/dashboard/DashboardLayout";
import { Topbar } from "../components/dashboard/Topbar";
import { buttonClass } from "../components/ui/buttonStyles";
import { useDashboardData } from "../lib/useDashboardData";
import { Skeleton } from "../components/ui/Skeleton";
import type { DataStatus as DataStatusModel } from "../types/performance";

function pendingStatus(): DataStatusModel {
  return {
    status: "SYNCING",
    lastUpdatedAt: new Date().toISOString(),
    source: "Socle LONAB",
    raceCount: 0,
    origin: "real",
  };
}

/**
 * Écran d'attente pour les routes déclarées mais non encore implémentées
 * (`/pronostics`, `/chevaux`, `/jockeys`, `/statistiques`, `/analyses`…).
 *
 * Il conserve le gabarit et la navigation afin qu'aucun lien de la sidebar
 * ne mène à une page blanche ou à une 404.
 */
export function ComingSoonPage({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  const { state } = useDashboardData();

  const dataStatus: DataStatusModel =
    state.status === "success" ? state.data.dataStatus : pendingStatus();

  return (
    <DashboardLayout dataStatus={dataStatus}>
      {state.status === "success" ? (
        <Topbar
          user={state.data.user}
          subscription={state.data.subscription}
          notifications={state.data.notifications}
          races={[state.data.nextRace, ...state.data.followedRaces].filter(
            (race): race is NonNullable<typeof race> => race !== null,
          )}
        />
      ) : (
        <div className="flex h-[68px] items-center">
          <Skeleton className="h-[34px] w-full max-w-[481px]" />
        </div>
      )}

      <main className="flex min-h-[440px] items-center justify-center rounded-[12px] border border-faso-border bg-white p-8">
        <div className="max-w-[460px] text-center">
          <span
            aria-hidden="true"
            className="mx-auto grid h-11 w-11 place-items-center rounded-full bg-faso-success-soft"
          >
            <Construction size={20} className="text-faso-green" />
          </span>
          <h1 className="mt-3 text-[20px] font-bold leading-6 text-faso-text">{title}</h1>
          <p className="mt-2 text-[12.5px] leading-[19px] text-faso-muted">{description}</p>
          <Link to="/dashboard" className={buttonClass("secondary", "md", "mt-5")}>
            <ArrowLeft size={14} aria-hidden="true" />
            Retour au tableau de bord
          </Link>
        </div>
      </main>
    </DashboardLayout>
  );
}
