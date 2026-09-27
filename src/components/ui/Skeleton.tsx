import { cn } from "../../lib/utils";

export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn("animate-pulse rounded-[8px] bg-faso-border-soft", className)}
    />
  );
}

/** Squelette du hero — reprend la structure exacte du bloc (spec §41). */
export function HeroSkeleton() {
  return (
    <div className="h-[266px] w-full animate-pulse rounded-[12px] bg-[#0B2B21] p-6">
      <Skeleton className="h-3.5 w-40 bg-white/10" />
      <Skeleton className="mt-3 h-6 w-72 bg-white/10" />
      <Skeleton className="mt-2 h-7 w-40 bg-white/10" />
      <Skeleton className="mt-4 h-3 w-80 bg-white/10" />
      <div className="mt-14 flex gap-5">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="flex items-center gap-2">
            <Skeleton className="h-7 w-7 rounded-full bg-white/10" />
            <Skeleton className="h-3 w-20 bg-white/10" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Squelette de la carte « Mes performances ». */
export function PerformanceSkeleton() {
  return (
    <div className="h-full rounded-[12px] border border-faso-border bg-white p-4">
      <Skeleton className="h-4 w-40" />
      <div className="mt-3 grid grid-cols-3 gap-2">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-[74px]" />
        ))}
      </div>
      <Skeleton className="mt-4 h-3 w-32" />
      <Skeleton className="mt-2 h-[52px]" />
    </div>
  );
}

/** Squelette d'une carte de course. */
export function RaceCardSkeleton() {
  return (
    <div className="rounded-[12px] border border-faso-border bg-white p-3.5">
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <Skeleton className="h-5 w-16 rounded-full" />
          <Skeleton className="mt-2.5 h-4 w-40" />
          <Skeleton className="mt-2.5 h-3 w-52" />
        </div>
        <Skeleton className="h-3 w-12" />
        <Skeleton className="h-[52px] w-[92px]" />
        <Skeleton className="h-8 w-[140px]" />
      </div>
    </div>
  );
}

/** Squelette d'une ligne du Top 5. */
export function PredictionRowSkeleton() {
  return (
    <div className="flex items-center gap-3 py-2.5">
      <Skeleton className="h-[26px] w-[26px] rounded-full" />
      <Skeleton className="h-7 w-7 rounded-full" />
      <div className="flex-1">
        <Skeleton className="h-3.5 w-28" />
        <Skeleton className="mt-1.5 h-2.5 w-36" />
      </div>
      <Skeleton className="h-6 w-11" />
    </div>
  );
}

/** Squelette d'une carte de la colonne de droite. */
export function RailCardSkeleton({ height = 160 }: { height?: number }) {
  return (
    <div
      className="rounded-[12px] border border-faso-border bg-white p-4"
      style={{ minHeight: height }}
    >
      <Skeleton className="h-4 w-44" />
      <div className="mt-4 space-y-3">
        <Skeleton className="h-3.5 w-full" />
        <Skeleton className="h-3.5 w-4/5" />
        <Skeleton className="h-3.5 w-3/5" />
      </div>
    </div>
  );
}
