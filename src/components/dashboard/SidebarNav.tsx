import { NavLink } from "react-router-dom";
import {
  BrainCircuit,
  CalendarDays,
  ChartNoAxesColumnIncreasing,
  Crown,
  House,
  Target,
  UsersRound,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { cn } from "../../lib/utils";
import { HorseIcon } from "./icons";

type NavItem = {
  label: string;
  to: string;
  icon: LucideIcon;
  /** Icône alternative (silhouette cheval) — cf. `icons.tsx`. */
  customIcon?: "horse";
};

/** Items de navigation (spec §11.1) et icônes Lucide associées (spec §11.2). */
const NAV_ITEMS: NavItem[] = [
  { label: "Tableau de bord", to: "/dashboard", icon: House },
  { label: "Pronostics", to: "/pronostics", icon: Target },
  { label: "Courses du jour", to: "/courses", icon: CalendarDays },
  { label: "Chevaux", to: "/chevaux", icon: Target, customIcon: "horse" },
  { label: "Jockeys / Entraîneurs", to: "/jockeys", icon: UsersRound },
  { label: "Statistiques", to: "/statistiques", icon: ChartNoAxesColumnIncreasing },
  { label: "Analyses IA", to: "/analyses", icon: BrainCircuit },
  { label: "Abonnement", to: "/abonnement", icon: Crown },
];

function ItemIcon({ item, active }: { item: NavItem; active: boolean }) {
  if (item.customIcon === "horse") {
    return <HorseIcon size={17} className={cn("shrink-0", active ? "opacity-100" : "opacity-80")} />;
  }
  const Icon = item.icon;
  return (
    <Icon
      size={17}
      strokeWidth={active ? 2.2 : 1.9}
      aria-hidden="true"
      className={cn("shrink-0", active ? "opacity-100" : "opacity-80")}
    />
  );
}

export function SidebarNav() {
  return (
    <nav aria-label="Navigation principale" className="px-3.5">
      <ul className="flex flex-col gap-[3px]">
        {NAV_ITEMS.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              end={item.to === "/dashboard"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-[8px] px-3 py-[9px] text-[13.5px] transition-colors duration-150 ease-out",
                  isActive
                    ? "bg-faso-green-dark font-semibold text-white"
                    : "font-medium text-white/[0.72] hover:bg-white/[0.06] hover:text-white",
                )
              }
            >
              {({ isActive }) => (
                <>
                  <ItemIcon item={item} active={isActive} />
                  <span className="truncate">{item.label}</span>
                  {isActive && <span className="sr-only">(page active)</span>}
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
