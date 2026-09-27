import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown, CreditCard, LogOut, Settings, UserCircle } from "lucide-react";
import { initials as toInitials } from "../../lib/utils";
import type { SubscriptionSummary, UserSummary } from "../../types/user";
import { Avatar } from "../ui/Avatar";
import { cn } from "../../lib/utils";

const MENU = [
  { label: "Mon profil", to: "/profile", icon: UserCircle },
  { label: "Paramètres", to: "/settings", icon: Settings },
  { label: "Abonnement", to: "/abonnement", icon: CreditCard },
];

/**
 * Bloc utilisateur de la topbar (spec §16).
 * Le statut affiché provient de `subscription.plan` — pas d'un libellé figé.
 *
 * Tant qu'aucune authentification n'est branchée, `user` vaut `null` : le bloc
 * affiche alors un état « non connecté » explicite, sans nom ni forfait inventés.
 */
export function UserMenu({
  user,
  subscription,
}: {
  user: UserSummary | null;
  subscription: SubscriptionSummary;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const isAuthenticated = user !== null;
  const fullName = user ? `${user.firstName} ${user.lastName}`.trim() : "Non connecté";
  const statusLabel = user ? user.statusLabel : "Aucun compte utilisateur";

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={isAuthenticated ? `Compte de ${fullName}` : "Compte utilisateur"}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex items-center gap-2.5 rounded-[10px] py-1 pl-1 pr-2 transition-colors duration-150 ease-out hover:bg-faso-field",
          open && "bg-faso-field",
        )}
      >
        <Avatar
          src={user?.avatarUrl}
          initials={user ? toInitials(user.firstName, user.lastName) : "?"}
          alt={fullName}
          size="md"
        />
        <span className="hidden text-left leading-tight sm:block">
          <span className="flex items-center gap-1.5">
            <span className="text-[13px] font-bold text-faso-text">{fullName}</span>
            {subscription.configured && subscription.plan === "PRO" && (
              <span className="rounded-[5px] bg-faso-gold px-1.5 py-[1px] text-[9.5px] font-bold leading-none text-faso-green-deep">
                Pro
              </span>
            )}
          </span>
          <span className="mt-0.5 block text-[11px] text-faso-muted">{statusLabel}</span>
        </span>
        <ChevronDown
          size={15}
          aria-hidden="true"
          className={cn(
            "shrink-0 text-faso-muted transition-transform duration-150 ease-out",
            open && "rotate-180",
          )}
        />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 top-[52px] z-50 w-[224px] animate-fade-in overflow-hidden rounded-[12px] border border-faso-border bg-white py-1 shadow-lift"
        >
          <div className="border-b border-faso-border-soft px-4 py-2.5">
            <p className="truncate text-[12.5px] font-semibold text-faso-text">{fullName}</p>
            <p className="mt-0.5 truncate text-[11px] text-faso-muted">{statusLabel}</p>
          </div>

          {MENU.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                to={item.to}
                role="menuitem"
                onClick={() => setOpen(false)}
                className="flex items-center gap-3 px-4 py-2 text-[12.5px] font-medium text-faso-text transition-colors duration-150 hover:bg-faso-bg"
              >
                <Icon size={15} aria-hidden="true" className="text-faso-muted" />
                {item.label}
              </Link>
            );
          })}

          <div className="my-1 border-t border-faso-border-soft" />

          {isAuthenticated ? (
            <button
              type="button"
              role="menuitem"
              className="flex w-full items-center gap-3 px-4 py-2 text-left text-[12.5px] font-medium text-faso-red transition-colors duration-150 hover:bg-faso-danger-soft"
            >
              <LogOut size={15} aria-hidden="true" />
              Déconnexion
            </button>
          ) : (
            <p className="px-4 py-2 text-[11px] leading-[16px] text-faso-muted">
              La connexion n'est pas encore disponible : aucun compte utilisateur n'existe
              côté backend.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
