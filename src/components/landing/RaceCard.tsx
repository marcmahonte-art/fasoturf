import { MapPin, Clock3, TrendingUp } from "lucide-react";
import horseRunner from "../../assets/horse-runner.svg";
import type { Race } from "../../data/races";

const ACCENT_COLOR: Record<Race["accent"], string> = {
  green: "#0BAF58",
  gold: "#F2C94C",
  red: "#D64545",
};

export function RaceCard({
  race,
  onSelect,
}: {
  race: Race;
  onSelect?: (race: Race) => void;
}) {
  const accent = ACCENT_COLOR[race.accent];

  return (
    <article
      onClick={() => onSelect?.(race)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect?.(race);
        }
      }}
      className="flex h-[124px] min-w-[240px] sm:min-w-[260px] flex-col justify-between rounded-xl border border-white/10 bg-[#06352B]/85 p-3.5 text-white transition-all duration-200 hover:scale-[1.02] hover:border-faso-gold/50 hover:bg-[#084236] hover:shadow-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-faso-gold/50"
    >
      <div className="flex items-center gap-2">
        <span className="rounded bg-faso-green/30 px-1.5 py-0.5 text-[11px] font-bold text-faso-accent">
          {race.reunion}
        </span>
        <span className="rounded bg-faso-green/20 px-1.5 py-0.5 text-[11px] font-bold">
          {race.course}
        </span>
        <span className="truncate text-[10.5px] font-medium text-white/70">
          {race.discipline}
        </span>
        <img
          src={horseRunner}
          alt=""
          aria-hidden="true"
          width={26}
          height={18}
          className="ml-auto opacity-90"
          style={{ color: accent }}
        />
      </div>

      <div className="flex flex-col">
        <div className="flex items-center gap-1 text-[13px] font-semibold">
          <MapPin size={13} strokeWidth={2} className="text-faso-gold shrink-0" />
          <span className="truncate">{race.hippodrome}</span>
        </div>
        <div className="truncate text-[11px] text-white/60">
          {race.distance} · {race.title}
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] text-white/65 pt-1 border-t border-white/10">
        <span className="flex items-center gap-1 font-medium">
          <TrendingUp size={11} className="text-faso-accent" />
          Fav. {race.favoriteOdds.toFixed(1)}
        </span>
        <span className="flex items-center gap-1 text-[11px] text-white/50">
          {race.starters} partants
        </span>
        <span className="flex items-center gap-1 text-[11px] font-medium text-white">
          <Clock3 size={11} />
          {race.time}
        </span>
      </div>
    </article>
  );
}