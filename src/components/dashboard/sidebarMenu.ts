import { createContext, useContext } from "react";

/**
 * Contexte d'ouverture du tiroir de navigation.
 *
 * Isolé dans son propre module (et non dans `DashboardLayout.tsx`) afin que
 * le fichier du composant n'exporte que des composants — condition du
 * rafraîchissement à chaud de React.
 */
export const SidebarMenuContext = createContext<() => void>(() => {});

/** Ouvre le tiroir de navigation (sous 1024 px). */
export function useOpenSidebarMenu(): () => void {
  return useContext(SidebarMenuContext);
}
