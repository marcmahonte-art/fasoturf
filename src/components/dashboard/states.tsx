import { AlertTriangle, Inbox, RefreshCw } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "../ui/Button";
import { Skeleton } from "../ui/Skeleton";

/**
 * États partagés par les pages internes.
 *
 * Chaque page affiche explicitement son état : **aucun état n'est masqué par
 * une valeur de remplacement**. Un échec affiche son message, un résultat vide
 * affiche une explication, jamais une liste fabriquée (spec §40).
 */

/** Échec de chargement, avec action de reprise. */
export function PageError({
  message,
  onRetry,
  title = "Impossible de charger les données",
}: {
  message: string;
  onRetry?: () => void;
  title?: string;
}) {
  return (
    <div className="flex min-h-[320px] items-center justify-center rounded-[12px] border border-faso-border bg-white p-8">
      <div className="max-w-[440px] text-center">
        <span
          aria-hidden="true"
          className="mx-auto grid h-11 w-11 place-items-center rounded-full bg-faso-danger-soft"
        >
          <AlertTriangle size={20} className="text-faso-red" />
        </span>
        <h2 className="mt-3 text-[16px] font-bold text-faso-text">{title}</h2>
        <p className="mt-1.5 text-[12.5px] leading-[19px] text-faso-muted">{message}</p>
        {onRetry && (
          <Button variant="primary" className="mt-4" onClick={onRetry}>
            <RefreshCw size={14} aria-hidden="true" />
            Réessayer
          </Button>
        )}
      </div>
    </div>
  );
}

/** Résultat vide — distinct d'une erreur : la requête a réussi, il n'y a rien. */
export function PageEmpty({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-[12px] border border-dashed border-faso-border bg-white px-6 py-12 text-center">
      <Inbox size={26} aria-hidden="true" className="text-faso-muted" />
      <p className="mt-3 text-[14px] font-semibold text-faso-text">{title}</p>
      <p className="mt-1 max-w-[420px] text-[12.5px] leading-[19px] text-faso-muted">
        {description}
      </p>
      {children && <div className="mt-4">{children}</div>}
    </div>
  );
}

/** Liste de lignes en attente de chargement. */
export function SkeletonRows({
  count = 5,
  heightClass = "h-[76px]",
}: {
  count?: number;
  heightClass?: string;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      {Array.from({ length: count }, (_, index) => (
        <Skeleton key={index} className={`w-full ${heightClass}`} />
      ))}
    </div>
  );
}
