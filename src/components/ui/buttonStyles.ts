import { cn } from "../../lib/utils";

export type ButtonVariant = "primary" | "secondary" | "gold" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

const VARIANT_CLASS: Record<ButtonVariant, string> = {
  primary: "bg-faso-green text-white hover:bg-faso-green-dark",
  secondary: "bg-white text-faso-text border border-faso-border hover:bg-faso-bg",
  /* Réservé à FasoTurf Pro / premium / abonnement (spec §38) */
  gold: "bg-faso-gold text-faso-green-deep hover:brightness-95",
  ghost: "bg-transparent text-faso-text hover:bg-faso-bg",
  danger: "bg-faso-red text-white hover:brightness-95",
};

const SIZE_CLASS: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-[12px] gap-1.5",
  md: "h-9 px-4 text-[13px] gap-1.5",
  lg: "h-10 px-5 text-[14px] gap-2",
};

/**
 * Classes de bouton réutilisables sur un `<a>` / `<Link>`.
 * Évite un composant polymorphe tout en garantissant un rendu identique
 * à celui du composant `Button`.
 */
export function buttonClass(
  variant: ButtonVariant = "primary",
  size: ButtonSize = "md",
  className?: string,
): string {
  return cn(
    "inline-flex shrink-0 items-center justify-center rounded-[9px] font-semibold",
    "transition-colors duration-150 ease-out",
    "focus-visible:outline-2 focus-visible:outline-offset-2",
    "disabled:cursor-not-allowed disabled:opacity-55",
    VARIANT_CLASS[variant],
    SIZE_CLASS[size],
    className,
  );
}
