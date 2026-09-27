import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import type { ReactNode } from "react";
import { DashboardLayout } from "./DashboardLayout";
import { Topbar } from "./Topbar";
import { Skeleton } from "../ui/Skeleton";
import { useDashboardData } from "../../lib/useDashboardData";
import type { DataStatus as DataStatusModel } from "../../types/performance";

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

/**
 * Gabarit commun des pages internes.
 *
 * Il porte trois choses que chaque page devrait sinon dupliquer :
 *  1. le **contexte utilisateur** (sidebar, topbar, recherche) — chargé une fois
 *     par page via `useDashboardData` ;
 *  2. le **statut de la donnée** affiché dans la sidebar ;
 *  3. l'**en-tête de page** (retour, titre, description, actions).
 *
 * Les pages restent responsables de leurs propres états chargement / erreur /
 * vide : le gabarit ne masque jamais un échec.
 */
export function PageShell({
  title,
  description,
  backTo = "/dashboard",
  backLabel = "Retour au tableau de bord",
  actions,
  children,
}: {
  title?: string;
  description?: string;
  backTo?: string | null;
  backLabel?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  const shell = useDashboardData();
  const shellData = shell.state.status === "success" ? shell.state.data : null;
  const dataStatus: DataStatusModel = shellData?.dataStatus ?? pendingStatus();

  return (
    <DashboardLayout dataStatus={dataStatus}>
      {shellData ? (
        <Topbar
          user={shellData.user}
          subscription={shellData.subscription}
          notifications={shellData.notifications}
          races={[shellData.nextRace, ...shellData.followedRaces].filter(
            (race): race is NonNullable<typeof race> => race !== null,
          )}
        />
      ) : (
        <div className="flex h-[68px] items-center">
          <Skeleton className="h-[34px] w-full max-w-[481px]" />
        </div>
      )}

      <main className="flex flex-col gap-[18px]">
        {backTo && (
          <Link
            to={backTo}
            className="inline-flex w-fit items-center gap-1.5 text-[12px] font-semibold text-faso-muted hover:text-faso-text"
          >
            <ArrowLeft size={13} aria-hidden="true" />
            {backLabel}
          </Link>
        )}

        {(title || description || actions) && (
          <header className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              {title && (
                <h1 className="text-[22px] font-bold leading-tight text-faso-text">{title}</h1>
              )}
              {description && (
                <p className="mt-1 max-w-[680px] text-[12.5px] leading-[19px] text-faso-muted">
                  {description}
                </p>
              )}
            </div>
            {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
          </header>
        )}

        {children}
      </main>
    </DashboardLayout>
  );
}
