import { Link } from "react-router-dom";
import {
  ArrowRight,
  CalendarRange,
  Clock,
  Ruler,
  ShieldAlert,
  Trophy,
} from "lucide-react";
import { MeetingBadge } from "../ui/Badge";
import { buttonClass } from "../ui/buttonStyles";
import { cn } from "../../lib/utils";
import { formatClock, formatDistance } from "../../lib/formatters";
import type { RaceSummary } from "../../types/race";

/**
 * Libellé du CTA et mention d'état selon le statut de la course (spec §28).
 * La couleur n'est jamais le seul indicateur : l'état est écrit en toutes lettres.
 */
function ctaFor(status: RaceSummary["status"]) {
  switch (status) {
    case "live":
      return { label: "Voir la course", live: true, finished: false };
    case "finished":
      return { label: "Voir l'analyse", live: false, finished: true };
    case "suspended":
      return { label: "Voir l'analyse", live: false, finished: false };
    default:
      return { label: "Voir l'analyse", live: false, finished: false };
  }
}

/**
 * Vignette de repli **décorative**.
 *
 * Le socle ne fournit pas de visuel par course. L'image affichée est une photo
 * hippique générique déjà présente dans le projet : elle est marquée
 * `aria-hidden` et ne porte aucune information (l'information est dans le texte).
 */
const DECORATIVE_THUMBNAIL = "/images/fasoturf-racing-bg.jpg";

/**
 * Ligne de course de la section « Courses à suivre » (spec §26).
 * Toutes les valeurs affichées proviennent de la donnée — le type de pari
 * n'est jamais déduit du nombre de partants (spec §27).
 */
export function RaceFollowCard({ race }: { race: RaceSummary }) {
  const cta = ctaFor(race.status);
  const isSuspended = race.status === "suspended";

  return (
    <article className="flex min-h-[104px] items-center gap-4 rounded-[12px] border border-faso-border bg-white px-4 py-3.5 shadow-panel transition-shadow duration-200 ease-out hover:shadow-lift">
      {/* Bloc principal */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <MeetingBadge meeting={race.meetingNumber} race={race.raceNumber} />
          {race.isLonab && (
            <span className="inline-flex items-center gap-1 rounded-full bg-faso-warning-soft px-1.5 py-[2px] text-[10px] font-bold leading-none text-faso-warning-text">
              <Trophy size={9} aria-hidden="true" />
              LONAB
            </span>
          )}
        </div>

        <h3 className="mt-2 truncate text-[16px] font-bold leading-tight text-faso-text">
          {race.hippodrome}
        </h3>

        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11.5px] text-faso-muted">
          <span className="inline-flex items-center gap-1.5">
            <CalendarRange size={12} aria-hidden="true" className="text-faso-muted" />
            {race.participantCount} partants
          </span>
          <span className="inline-flex items-center gap-1.5">
            <Ruler size={12} aria-hidden="true" className="text-faso-muted" />
            {formatDistance(race.distanceMeters)}
          </span>
          {race.discipline && <span className="truncate">{race.discipline}</span>}
        </div>
      </div>

      {/* Heure + type de pari */}
      <div className="hidden w-[86px] shrink-0 text-right sm:block">
        <div className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-faso-text">
          <Clock size={12} aria-hidden="true" className="text-faso-muted" />
          {formatClock(race.startTime)}
        </div>
        <div className="mt-1 truncate text-[11.5px] text-faso-muted">
          {race.betType ?? race.discipline ?? "—"}
        </div>
      </div>

      {/* Vignette illustrative (décorative : l'information est portée par le texte) */}
      <img
        src={race.imageUrl ?? DECORATIVE_THUMBNAIL}
        alt=""
        aria-hidden="true"
        loading="lazy"
        className="hidden h-[52px] w-[92px] shrink-0 rounded-[8px] object-cover md:block"
      />

      {/* CTA */}
      <div className="flex shrink-0 flex-col items-end gap-1.5">
        {cta.live && (
          <span className="inline-flex items-center gap-1 text-[10.5px] font-bold text-faso-red">
            <span aria-hidden="true" className="h-[6px] w-[6px] rounded-full bg-faso-red" />
            EN DIRECT
          </span>
        )}
        {cta.finished && (
          <span className="inline-flex items-center gap-1 text-[10.5px] font-semibold text-faso-muted">
            <Trophy size={10} aria-hidden="true" />
            Résultat
          </span>
        )}
        {isSuspended ? (
          <span className="inline-flex h-9 items-center gap-1.5 rounded-[9px] bg-faso-danger-soft px-3 text-[12px] font-semibold text-faso-red">
            <ShieldAlert size={13} aria-hidden="true" />
            Course suspendue
          </span>
        ) : (
          <Link
            to={`/analyses/${race.id}`}
            className={cn(buttonClass("primary", "md", "min-w-[144px]"))}
          >
            {cta.label}
            <ArrowRight size={13} aria-hidden="true" />
          </Link>
        )}
      </div>
    </article>
  );
}
