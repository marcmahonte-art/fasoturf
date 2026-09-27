import { Link } from "react-router-dom";
import { ArrowRight, CalendarX2 } from "lucide-react";
import { RaceFollowCard } from "./RaceFollowCard";
import { DataOriginBadge } from "../ui/DataOriginBadge";
import type { RaceSummary } from "../../types/race";

/**
 * Section « Courses à suivre » (spec §25).
 *
 * Les courses proviennent du socle LONAB. Les états vide et « aucune course
 * publiée » sont gérés explicitement — aucune ligne de remplacement n'est
 * fabriquée (spec §40).
 */
export function FollowedRaces({ races }: { races: RaceSummary[] }) {
  return (
    <section aria-labelledby="followed-races-title">
      <header className="mb-3.5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <h2 id="followed-races-title" className="text-[20px] font-bold leading-6 text-faso-text">
            Courses à suivre
          </h2>
          {races.length > 0 && <DataOriginBadge origin={races[0].origin} />}
        </div>

        <Link
          to="/courses"
          className="inline-flex shrink-0 items-center gap-1 text-[12.5px] font-semibold text-faso-green hover:text-faso-green-dark"
        >
          Voir toutes
          <ArrowRight size={13} aria-hidden="true" />
        </Link>
      </header>

      {races.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-[12px] border border-dashed border-faso-border bg-white px-6 py-12 text-center">
          <CalendarX2 size={26} aria-hidden="true" className="text-faso-muted" />
          <p className="mt-3 text-[14px] font-semibold text-faso-text">Aucune course à suivre</p>
          <p className="mt-1 text-[12.5px] text-faso-muted">
            Explorez les courses du jour pour en ajouter.
          </p>
          <Link to="/courses" className="mt-4 text-[12.5px] font-semibold text-faso-green">
            Voir les courses du jour
          </Link>
        </div>
      ) : (
        <ul className="flex flex-col gap-1.5">
          {races.map((race) => (
            <li key={race.id}>
              <RaceFollowCard race={race} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
