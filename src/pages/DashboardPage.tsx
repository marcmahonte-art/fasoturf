import { AlertTriangle, RefreshCw } from "lucide-react";
import { DashboardLayout } from "../components/dashboard/DashboardLayout";
import { Topbar } from "../components/dashboard/Topbar";
import { WelcomeHero } from "../components/dashboard/WelcomeHero";
import { PerformanceCard } from "../components/dashboard/PerformanceCard";
import { FollowedRaces } from "../components/dashboard/FollowedRaces";
import { AlertsCard } from "../components/dashboard/AlertsCard";
import { PredictionTop5 } from "../components/dashboard/PredictionTop5";
import { QuickAccess } from "../components/dashboard/QuickAccess";
import { ProBanner } from "../components/dashboard/ProBanner";
import { Button } from "../components/ui/Button";
import {
  HeroSkeleton,
  PerformanceSkeleton,
  RaceCardSkeleton,
  RailCardSkeleton,
} from "../components/ui/Skeleton";
import { useDashboardData } from "../lib/useDashboardData";
import type { DataStatus as DataStatusModel } from "../types/performance";

/** Statut provisoire affiché tant que la source n'a pas répondu. */
function pendingStatus(): DataStatusModel {
  return {
    status: "SYNCING",
    lastUpdatedAt: new Date().toISOString(),
    source: "Socle LONAB",
    raceCount: 0,
    origin: "real",
  };
}

const GRID = "grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_390px]";

/**
 * Page /dashboard (spec §47).
 *
 * Ordre de rendu : gabarit → topbar → hero + performances → courses à suivre →
 * colonne de droite (alertes, top 5, accès rapides) → bandeau Pro.
 * Les états loading / success / empty / error sont gérés explicitement ;
 * aucune valeur de remplacement n'est affichée en cas d'erreur (spec §40).
 */
export function DashboardPage() {
  const { state, reload } = useDashboardData();

  if (state.status === "loading") {
    return (
      <DashboardLayout dataStatus={pendingStatus()}>
        <div className="flex h-[68px] items-center">
          <div className="h-[34px] w-full max-w-[481px] animate-pulse rounded-[9px] bg-faso-field" />
        </div>

        <main className="flex flex-col gap-[18px]">
          <div className={`${GRID} items-stretch`}>
            <HeroSkeleton />
            <PerformanceSkeleton />
          </div>

          <div className={GRID}>
            <div className="flex flex-col gap-1.5">
              <div className="mb-3.5 h-6 w-48 animate-pulse rounded-[8px] bg-faso-border-soft" />
              {[0, 1, 2, 3].map((index) => (
                <RaceCardSkeleton key={index} />
              ))}
            </div>
            <div className="flex flex-col gap-6 xl:pt-3">
              <RailCardSkeleton height={104} />
              <RailCardSkeleton height={300} />
              <RailCardSkeleton height={180} />
            </div>
          </div>
        </main>
      </DashboardLayout>
    );
  }

  if (state.status === "error") {
    return (
      <DashboardLayout dataStatus={{ ...pendingStatus(), status: "ERROR" }}>
        <div className="h-[68px]" />

        <main className="flex min-h-[440px] items-center justify-center rounded-[12px] border border-faso-border bg-white p-8">
          <div className="max-w-[430px] text-center">
            <span
              aria-hidden="true"
              className="mx-auto grid h-11 w-11 place-items-center rounded-full bg-faso-danger-soft"
            >
              <AlertTriangle size={20} className="text-faso-red" />
            </span>
            <h1 className="mt-3 text-[16px] font-bold text-faso-text">
              Impossible de charger le tableau de bord
            </h1>
            <p className="mt-1.5 text-[12.5px] leading-[19px] text-faso-muted">
              {state.message} Aucun chiffre n'est affiché tant que la source n'est pas disponible.
            </p>
            <Button variant="primary" className="mt-4" onClick={reload}>
              <RefreshCw size={14} aria-hidden="true" />
              Réessayer
            </Button>
          </div>
        </main>
      </DashboardLayout>
    );
  }

  const data = state.data;
  const searchableRaces = [data.nextRace, ...data.followedRaces].filter(
    (race): race is NonNullable<typeof race> => race !== null,
  );

  return (
    <DashboardLayout dataStatus={data.dataStatus}>
      <Topbar
        user={data.user}
        subscription={data.subscription}
        notifications={data.notifications}
        races={searchableRaces}
      />

      <main className="flex flex-col gap-[18px]">
        {/* Hero + Mes performances */}
        <div className={`${GRID} items-stretch`}>
          <WelcomeHero user={data.user} nextRace={data.nextRace} />
          <PerformanceCard
            performance={data.performance}
            performanceUnavailableReason={data.performanceUnavailableReason}
            subscription={data.subscription}
          />
        </div>

        {/* Courses à suivre + colonne de droite */}
        <div className={GRID}>
          <div className="flex flex-col gap-[18px]">
            <FollowedRaces races={data.followedRaces} />
            <ProBanner />
          </div>

          <aside aria-label="Informations complémentaires" className="flex flex-col gap-6 xl:pt-3">
            {/* Sous 1280 px, le Top 5 remonte avant les alertes (spec §59) */}
            <div className="order-2 xl:order-none">
              <AlertsCard notifications={data.notifications} />
            </div>
            <div className="order-1 xl:order-none">
              <PredictionTop5
                predictions={data.topPredictions}
                context={data.predictionContext}
                unavailableReason={data.predictionUnavailableReason}
              />
            </div>
            <div className="order-3 xl:order-none">
              <QuickAccess />
            </div>
          </aside>
        </div>
      </main>
    </DashboardLayout>
  );
}
