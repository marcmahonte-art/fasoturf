import { cn } from "../../lib/utils";

export type ProgressTone = "green" | "gold" | "red" | "muted";

const TONE_CLASS: Record<ProgressTone, string> = {
  green: "bg-faso-green",
  gold: "bg-faso-gold",
  red: "bg-faso-red",
  muted: "bg-faso-border",
};

/**
 * Jauge fine (hauteur 4 px).
 * La valeur est toujours accompagnée d'un texte lisible : la couleur ne doit
 * jamais être le seul indicateur d'état (spec §42).
 */
export function Progress({
  value,
  tone = "green",
  label,
  className,
}: {
  /** Valeur en pourcentage (0–100). */
  value: number;
  tone?: ProgressTone;
  label?: string;
  className?: string;
}) {
  const safe = Math.max(0, Math.min(100, value));

  return (
    <div
      role="progressbar"
      aria-valuenow={Math.round(safe)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
      className={cn("h-1 w-full overflow-hidden rounded-full bg-faso-border-soft", className)}
    >
      <div
        className={cn("h-full rounded-full transition-[width] duration-200 ease-out", TONE_CLASS[tone])}
        style={{ width: `${safe}%` }}
      />
    </div>
  );
}
