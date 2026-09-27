import { Link } from "react-router-dom";
import {
  ChartNoAxesColumnIncreasing,
  LayoutGrid,
  MapPin,
  Target,
  UserRound,
  UsersRound,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Card } from "../ui/Card";
import { HorseIcon } from "./icons";

type QuickAccessItem = {
  title: string;
  description: string;
  to: string;
  icon: LucideIcon;
  customIcon?: "horse";
};

/** Six raccourcis de la colonne de droite (spec §49). */
const ITEMS: QuickAccessItem[] = [
  {
    title: "Chevaux",
    description: "Rechercher un cheval",
    to: "/chevaux",
    icon: Target,
    customIcon: "horse",
  },
  { title: "Pronostics", description: "Mes sélections", to: "/pronostics", icon: Target },
  {
    title: "Statistiques",
    description: "Voir les analyses",
    to: "/statistiques",
    icon: ChartNoAxesColumnIncreasing,
  },
  { title: "Jockeys", description: "Profils & stats", to: "/jockeys", icon: UserRound },
  { title: "Entraîneurs", description: "Profils & stats", to: "/entraineurs", icon: UsersRound },
  { title: "Hippodromes", description: "Tous les hippodromes", to: "/courses", icon: MapPin },
];

export function QuickAccess() {
  return (
    <Card padding="md">
      <div className="flex items-center gap-2">
        <LayoutGrid size={15} strokeWidth={2.1} aria-hidden="true" className="text-faso-green" />
        <h2 className="text-[14.5px] font-bold leading-5 text-faso-text">Accès rapide</h2>
      </div>

      <ul className="mt-3 grid grid-cols-3 gap-2">
        {ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <li key={item.to + item.title}>
              <Link
                to={item.to}
                className="flex h-full flex-col rounded-[10px] border border-faso-border-soft bg-white px-2.5 py-2 transition-colors duration-150 ease-out hover:border-faso-green/35 hover:bg-faso-bg"
              >
                <span className="flex items-center gap-1.5">
                  {item.customIcon === "horse" ? (
                    <HorseIcon size={14} className="shrink-0 text-faso-green" />
                  ) : (
                    <Icon
                      size={14}
                      strokeWidth={2}
                      aria-hidden="true"
                      className="shrink-0 text-faso-green"
                    />
                  )}
                  <span className="truncate text-[11.5px] font-semibold text-faso-text">
                    {item.title}
                  </span>
                </span>
                <span className="mt-1 truncate text-[10px] leading-tight text-faso-muted">
                  {item.description}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
