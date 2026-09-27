import { Link } from "react-router-dom";
import { ArrowRight, Clock, Crosshair } from "lucide-react";
import { buttonClass } from "../ui/buttonStyles";
import { cn } from "../../lib/utils";
import type { RaceSummary } from "../../types/race";

/**
 * Carte flottante « Prochaine course » affichée dans le hero (spec §21).
 * Le CTA pointe vers la fiche de la course concernée.
 */
export function NextRaceCard({
  race,
  className,
}: {
  race: RaceSummary;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "w-[196px] rounded-[10px] border border-white/[0.13] bg-[#04241C]/[0.88] p-3 shadow-lift backdrop-blur-md",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10.5px] font-medium leading-none text-white/60">
          Prochaine course
        </span>
        <Crosshair size={13} aria-hidden="true" className="shrink-0 text-faso-accent" />
      </div>

      <p className="mt-1.5 truncate text-[12.5px] font-bold leading-tight text-white">
        R{race.meetingNumber} · C{race.raceNumber} - {race.hippodrome}
      </p>

      <div className="mt-2.5 flex items-center gap-2 border-t border-white/10 pt-2.5">
        <Clock size={12} aria-hidden="true" className="shrink-0 text-white/55" />
        <span className="text-[12px] font-semibold leading-none text-white/90">
          {race.startTime}
        </span>
        <span aria-hidden="true" className="h-4 w-px shrink-0 bg-white/[0.13]" />
        <Link
          to={`/courses/${race.id}`}
          className={buttonClass("primary", "sm", "ml-auto h-7 px-2.5 text-[11.5px]")}
        >
          Voir la course
          <ArrowRight size={12} aria-hidden="true" />
        </Link>
      </div>
    </div>
  );
}
