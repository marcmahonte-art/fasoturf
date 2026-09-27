import { useId } from "react";
import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

export type TooltipSide = "top" | "bottom" | "right";

const SIDE_CLASS: Record<TooltipSide, string> = {
  top: "bottom-full left-1/2 mb-1.5 -translate-x-1/2",
  bottom: "top-full left-1/2 mt-1.5 -translate-x-1/2",
  right: "left-full top-1/2 ml-2 -translate-y-1/2",
};

/**
 * Infobulle accessible : déclenchée au survol ET au focus clavier.
 * Utilisée notamment pour porter la définition des métriques (spec §24)
 * et l'origine des données (spec §2.3).
 */
export function Tooltip({
  label,
  side = "top",
  className,
  children,
}: {
  label: ReactNode;
  side?: TooltipSide;
  className?: string;
  children: ReactNode;
}) {
  const id = useId();

  return (
    <span className="group/tt relative inline-flex">
      <span
        tabIndex={0}
        aria-describedby={id}
        className={cn("inline-flex cursor-help rounded-[4px]", className)}
      >
        {children}
      </span>
      <span
        id={id}
        role="tooltip"
        className={cn(
          "pointer-events-none absolute z-50 w-max max-w-[250px] whitespace-normal rounded-[8px]",
          "bg-faso-green-deep px-2.5 py-1.5 text-left text-[11px] font-medium leading-[15px] text-white",
          "opacity-0 shadow-lift transition-opacity duration-150 ease-out",
          "group-hover/tt:opacity-100 group-focus-within/tt:opacity-100",
          SIDE_CLASS[side],
        )}
      >
        {label}
      </span>
    </span>
  );
}
