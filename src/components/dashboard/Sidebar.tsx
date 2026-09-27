import { Link } from "react-router-dom";
import { ArrowRight, Crown } from "lucide-react";
import { FasoTurfLogo } from "../ui/FasoTurfLogo";
import { buttonClass } from "../ui/buttonStyles";
import { SidebarNav } from "./SidebarNav";
import { DataStatus } from "./DataStatus";
import { cn } from "../../lib/utils";
import type { DataStatus as DataStatusModel } from "../../types/performance";

/**
 * Navigation latérale fixe — 245 px (spec §4.1 et §10).
 *
 * Structure : logo → navigation → promotion FasoTurf Pro → statut des données.
 * `className` permet de réutiliser le même contenu en tiroir sur mobile.
 */
export function Sidebar({
  dataStatus,
  className,
}: {
  dataStatus: DataStatusModel;
  className?: string;
}) {
  return (
    <aside
      aria-label="Navigation FasoTurf"
      className={cn(
        "ft-on-dark w-[245px] flex-col overflow-y-auto ft-scroll bg-faso-sidebar",
        className,
      )}
    >
      <div className="shrink-0 px-5 pb-5 pt-5">
        <FasoTurfLogo />
      </div>

      <div className="flex-1">
        <SidebarNav />
      </div>

      {/* Promotion FasoTurf Pro (spec §12) — icône Crown, jamais un emoji */}
      <div className="mx-3.5 mb-3 shrink-0 rounded-[12px] border border-faso-green bg-[#0A2E24] p-3.5">
        <div className="flex items-center gap-2">
          <Crown size={15} aria-hidden="true" className="shrink-0 text-faso-gold" />
          <span className="text-[13px] font-bold leading-none text-white">FasoTurf Pro</span>
        </div>
        <p className="mt-2 text-[11px] leading-[16px] text-white/60">
          Accédez à des analyses avancées, des pronostics experts et plus encore.
        </p>
        <Link to="/abonnement" className={buttonClass("primary", "sm", "mt-3 w-full")}>
          Découvrir
          <ArrowRight size={13} aria-hidden="true" />
        </Link>
      </div>

      <div className="shrink-0">
        <DataStatus status={dataStatus} />
      </div>
    </aside>
  );
}
