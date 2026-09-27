import { useCallback, useEffect, useState } from "react";
import { X } from "lucide-react";
import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { SidebarMenuContext } from "./sidebarMenu";
import type { DataStatus } from "../../types/performance";

/**
 * Gabarit du Dashboard (spec §3 et §4).
 *
 * Desktop : sidebar fixe de 245 px + main en `calc(100vw - 245px)`.
 * Le contenu est centré dans `min(100% - 48px, 1280px)`.
 * Sous 1024 px : la sidebar devient un tiroir accessible au clavier.
 */
export function DashboardLayout({
  dataStatus,
  children,
}: {
  dataStatus: DataStatus;
  children: ReactNode;
}) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const openMenu = useCallback(() => setDrawerOpen(true), []);
  const closeMenu = useCallback(() => setDrawerOpen(false), []);

  useEffect(() => {
    if (!drawerOpen) return;

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") closeMenu();
    }

    document.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
    };
  }, [drawerOpen, closeMenu]);

  return (
    <SidebarMenuContext.Provider value={openMenu}>
      <div className="min-h-screen bg-faso-bg">
        {/* Sidebar desktop — fixe, 245 px */}
        <Sidebar
          dataStatus={dataStatus}
          className="fixed left-0 top-0 z-40 hidden h-screen lg:flex"
        />

        {/* Tiroir mobile / tablette */}
        {drawerOpen && (
          <div
            className="fixed inset-0 z-50 lg:hidden"
            role="dialog"
            aria-modal="true"
            aria-label="Menu de navigation"
          >
            <button
              type="button"
              aria-label="Fermer le menu"
              onClick={closeMenu}
              className="absolute inset-0 h-full w-full cursor-default bg-black/45"
            />
            <div className="relative h-full w-[245px] animate-fade-in shadow-lift">
              <Sidebar dataStatus={dataStatus} className="h-full" />
              <button
                type="button"
                aria-label="Fermer le menu"
                onClick={closeMenu}
                className="absolute right-3 top-4 grid h-8 w-8 place-items-center rounded-[8px] bg-white/10 text-white transition-colors duration-150 ease-out hover:bg-white/20"
              >
                <X size={16} aria-hidden="true" />
              </button>
            </div>
          </div>
        )}

        {/* Main — décalé de la largeur de la sidebar */}
        <div className="lg:pl-[245px]">
          <div className="mx-auto w-[min(calc(100%_-_48px),1280px)] pb-8">{children}</div>
        </div>
      </div>
    </SidebarMenuContext.Provider>
  );
}
