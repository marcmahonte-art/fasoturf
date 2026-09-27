import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

export type BadgeTone = "green" | "gold" | "red" | "neutral" | "success" | "warning";
export type BadgeSize = "sm" | "md";

const TONE_CLASS: Record<BadgeTone, string> = {
  green: "bg-faso-green text-white",
  gold: "bg-faso-gold text-faso-green-deep",
  red: "bg-faso-red text-white",
  neutral: "bg-faso-bg text-faso-muted border border-faso-border-soft",
  success: "bg-faso-success-soft text-faso-green",
  warning: "bg-faso-warning-soft text-faso-warning-text",
};

const SIZE_CLASS: Record<BadgeSize, string> = {
  sm: "h-[19px] px-1.5 text-[10.5px] gap-1",
  md: "h-[22px] px-2 text-[11.5px] gap-1",
};

export function Badge({
  tone = "neutral",
  size = "md",
  icon,
  className,
  children,
}: {
  tone?: BadgeTone;
  size?: BadgeSize;
  icon?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center rounded-full font-semibold leading-none",
        TONE_CLASS[tone],
        SIZE_CLASS[size],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
}

/**
 * Pastille « R1 · C4 » utilisée en tête de carte de course.
 * Le libellé est construit par `formatMeetingLabel` — jamais déduit.
 */
export function MeetingBadge({
  meeting,
  race,
  className,
}: {
  meeting: number;
  race: number;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full bg-faso-green px-2.5 py-[3px]",
        "text-[11.5px] font-bold leading-none text-white",
        className,
      )}
    >
      R{meeting}
      <span aria-hidden="true" className="text-white/60">
        ·
      </span>
      C{race}
    </span>
  );
}
