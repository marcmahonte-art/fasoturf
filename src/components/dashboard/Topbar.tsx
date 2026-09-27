import { Menu } from "lucide-react";
import { FasoTurfLogo } from "../ui/FasoTurfLogo";
import { GlobalSearch } from "./GlobalSearch";
import { NotificationBell } from "./NotificationBell";
import { UserMenu } from "./UserMenu";
import { useOpenSidebarMenu } from "./sidebarMenu";
import type { NotificationSummary } from "../../types/performance";
import type { SubscriptionSummary, UserSummary } from "../../types/user";
import type { RaceSummary } from "../../types/race";

/**
 * Barre supérieure (spec §14).
 *
 * Contient la recherche globale, la cloche de notifications et le menu
 * utilisateur. Sous 1024 px, la sidebar est remplacée par un tiroir : la
 * topbar accueille alors le logo et le bouton d'ouverture (spec §34).
 */
export function Topbar({
  user,
  subscription,
  notifications,
  races,
}: {
  user: UserSummary | null;
  subscription: SubscriptionSummary;
  notifications: NotificationSummary;
  races: RaceSummary[];
}) {
  const openMenu = useOpenSidebarMenu();

  return (
    <header className="flex h-[68px] items-center gap-3">
      <button
        type="button"
        aria-label="Ouvrir le menu de navigation"
        onClick={openMenu}
        className="grid h-9 w-9 shrink-0 place-items-center rounded-[9px] text-faso-text transition-colors duration-150 ease-out hover:bg-faso-field lg:hidden"
      >
        <Menu size={19} aria-hidden="true" />
      </button>

      <div className="shrink-0 lg:hidden">
        <FasoTurfLogo variant="compact" />
      </div>

      <div className="hidden min-w-0 flex-1 md:block">
        <GlobalSearch races={races} />
      </div>

      <div className="ml-auto flex shrink-0 items-center gap-1.5 sm:gap-3">
        <NotificationBell notifications={notifications} />
        <UserMenu user={user} subscription={subscription} />
      </div>
    </header>
  );
}
