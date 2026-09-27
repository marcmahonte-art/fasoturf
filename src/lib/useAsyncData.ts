import { useCallback, useEffect, useState } from "react";
import type { AsyncState } from "../types/dashboard";

/**
 * Charge une ressource asynchrone et expose ses trois états.
 *
 * Le chargement est **annulable** : changer de page ou de course ne provoque
 * jamais l'écriture d'un résultat obsolète dans le state.
 *
 * Le `loader` doit être stable (enveloppé dans un `useCallback` par l'appelant) :
 * il constitue la seule dépendance de l'effet.
 */
export function useAsyncData<T>(
  loader: () => Promise<T>,
): { state: AsyncState<T>; reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({ status: "loading" });

  const run = useCallback(() => {
    let cancelled = false;

    loader()
      .then((data) => {
        if (!cancelled) setState({ status: "success", data });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          message:
            error instanceof Error ? error.message : "Erreur inattendue du chargement.",
        });
      });

    return () => {
      cancelled = true;
    };
  }, [loader]);

  // L'effet ne fait que s'abonner : aucun setState synchrone pendant le rendu.
  useEffect(run, [run]);

  const reload = useCallback(() => {
    setState({ status: "loading" });
    void run();
  }, [run]);

  return { state, reload };
}
