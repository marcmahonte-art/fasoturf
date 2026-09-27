import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

export type CardVariant = "default" | "soft" | "dark" | "hero";
export type CardPadding = "none" | "sm" | "md" | "lg";

const VARIANT_CLASS: Record<CardVariant, string> = {
  default: "bg-white border border-faso-border shadow-panel",
  soft: "bg-faso-bg border border-faso-border-soft",
  dark: "bg-faso-sidebar border border-white/10 text-white",
  hero: "bg-faso-green-deep border border-white/10 text-white",
};

const PADDING_CLASS: Record<CardPadding, string> = {
  none: "",
  sm: "p-3",
  md: "p-4",
  lg: "p-5",
};

export type CardProps = {
  variant?: CardVariant;
  padding?: CardPadding;
  interactive?: boolean;
  className?: string;
  children: ReactNode;
};

/**
 * Conteneur générique (spec §37).
 * Toutes les cartes du dashboard partagent ce composant afin de garantir
 * des rayons, bordures et ombres homogènes.
 */
export function Card({
  variant = "default",
  padding = "md",
  interactive = false,
  className,
  children,
}: CardProps) {
  return (
    <section
      className={cn(
        "rounded-[12px]",
        VARIANT_CLASS[variant],
        PADDING_CLASS[padding],
        interactive &&
          "transition-shadow duration-200 ease-out hover:shadow-lift focus-within:shadow-lift",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function CardHeader({
  title,
  icon,
  action,
  className,
}: {
  title: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <header className={cn("flex items-center justify-between gap-3", className)}>
      <div className="flex min-w-0 items-center gap-2">
        {icon}
        <h2 className="truncate text-[15px] font-bold leading-5 text-faso-text">{title}</h2>
      </div>
      {action}
    </header>
  );
}

export function CardContent({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <div className={cn("mt-3", className)}>{children}</div>;
}

export function CardFooter({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <footer className={cn("mt-3 border-t border-faso-border-soft pt-3", className)}>
      {children}
    </footer>
  );
}
