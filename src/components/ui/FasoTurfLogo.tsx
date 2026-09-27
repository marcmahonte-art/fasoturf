import logoHorse from "../../assets/logo-horse.svg";
import { cn } from "../../lib/utils";

export type LogoVariant = "sidebar" | "compact";

/**
 * Logo FasoTurf réutilisable (spec §10.2).
 *
 * `sidebar` : version complète (icône + nom + baseline) pour la navigation.
 * `compact` : version réduite utilisée dans la topbar mobile.
 */
export function FasoTurfLogo({
  variant = "sidebar",
  className,
}: {
  variant?: LogoVariant;
  className?: string;
}) {
  const isCompact = variant === "compact";

  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <img
        src={logoHorse}
        alt=""
        aria-hidden="true"
        className={isCompact ? "h-8 w-9" : "h-9 w-10"}
      />
      <div className="min-w-0 leading-none">
        <div
          className={cn(
            "font-bold tracking-tight",
            isCompact ? "text-[18px]" : "text-[21px]",
          )}
        >
          <span className="text-white">Faso</span>
          <span className="text-faso-accent">Turf</span>
        </div>
        <div
          className={cn(
            "mt-1 font-medium text-white/55",
            isCompact ? "text-[9.5px]" : "text-[10.5px]",
          )}
        >
          La data des courses
        </div>
      </div>
    </div>
  );
}
