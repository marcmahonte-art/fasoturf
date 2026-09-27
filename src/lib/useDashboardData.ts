import { useCallback, useEffect, useState } from "react";
import { fetchDashboard } from "./api";
import type { AsyncState, DashboardData } from "../types/dashboard";

/**
 * Charge les données du Dashboard et expose un état asynchrone explicite.
 *
 * Le chargement est annulable : si le composant est démonté avant la réponse,
 * l'état n'est plus mis à jour.
 */
export function useDashboardData(): {
  state: AsyncState<DashboardData>;
  reload: () => void;
} {
  const [state, setState] = useState<AsyncState<DashboardData>>({ status: "loading" });

  // Aucun setState synchrone ici : l'effet ne fait que souscrire à la source
  // externe, et l'état initial est déjà « loading ».
  const run = useCallback(() => {
    let cancelled = false;

    fetchDashboard()
      .then((data) => {
        if (!cancelled) setState({ status: "success", data });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "Impossible de charger les données du tableau de bord.",
        });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(run, [run]);

  /** Relance explicitement le chargement (bouton « Réessayer »). */
  const reload = useCallback(() => {
    setState({ status: "loading" });
    void run();
  }, [run]);

  return { state, reload };
}
