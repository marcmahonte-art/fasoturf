import { ArrowRight, Wifi, Database } from "lucide-react";
import { RaceCarousel } from "./RaceCarousel";
import type { Race } from "../../data/races";

interface LatestRacesProps {
  races: Race[];
  isLive?: boolean;
  onSelectRace?: (race: Race) => void;
}

export function LatestRaces({ races, isLive = false, onSelectRace }: LatestRacesProps) {
  return (
    <section
      aria-labelledby="latest-races-title"
      className="absolute bottom-[24px] sm:bottom-[38px] left-1/2 z-20 w-[calc(100%-32px)] sm:w-[calc(100%-124px)] max-w-[1418px] -translate-x-1/2 rounded-[14px] border border-faso-green/50 bg-[#00261D]/75 p-5 sm:p-6 backdrop-blur-md"
    >
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className={`relative inline-block h-[10px] w-[10px] rounded-full ${
              isLive ? "bg-emerald-400 animate-ping" : "bg-faso-accent animate-pulse"
            }`}
            style={{ boxShadow: "0 0 0 4px rgba(11,175,88,.25)" }}
          />
          <div>
            <h2
              id="latest-races-title"
              className="text-[15px] sm:text-[17px] font-bold text-white flex items-center gap-2"
            >
              Programme officiel & Arrivées en direct
              {isLive ? (
                <span className="inline-flex items-center gap-1 rounded bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400 border border-emerald-500/30">
                  <Wifi size={10} /> API Direct
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded bg-faso-gold/20 px-2 py-0.5 text-[10px] font-bold text-faso-gold border border-faso-gold/30">
                  <Database size={10} /> Socle LONAB
                </span>
              )}
            </h2>
            <p className="mt-0.5 text-[11px] sm:text-[12px] text-white/65">
              Cliquez sur une course pour consulter les partants, cotes et analyses du marché
            </p>
          </div>
        </div>

        <span className="hidden sm:inline-flex items-center gap-1 text-[12px] font-medium text-white/80">
          Courses du jour
          <ArrowRight size={14} strokeWidth={2} />
        </span>
      </div>

      <RaceCarousel races={races} onSelectRace={onSelectRace} />

      {/* indicateur de progression */}
      <div
        aria-hidden="true"
        className="mx-auto mt-4 h-[3px] w-[160px] sm:w-[300px] overflow-hidden rounded-full bg-white/15"
      >
        <span className="block h-full w-1/3 bg-faso-accent animate-pulse" />
      </div>
    </section>
  );
}