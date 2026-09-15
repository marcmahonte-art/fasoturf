import { ChevronLeft, ChevronRight } from "lucide-react";
import { RaceCard } from "./RaceCard";
import type { Race } from "../../data/races";

interface RaceCarouselProps {
  races: Race[];
  onSelectRace?: (race: Race) => void;
}

export function RaceCarousel({ races, onSelectRace }: RaceCarouselProps) {
  const displayRaces = races.slice(0, 15);
  const loop = [...displayRaces, ...displayRaces];

  return (
    <div className="relative">
      {/* flèche gauche informative */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-[-6px] sm:-left-5 top-1/2 z-10 hidden h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-md sm:inline-flex opacity-70"
      >
        <ChevronLeft size={18} strokeWidth={2} />
      </div>

      {/* piste animée */}
      <div className="overflow-hidden py-1">
        <div className="flex w-max animate-marquee gap-[14px] hover:[animation-play-state:paused] motion-reduce:animate-none">
          {loop.map((r, i) => (
            <RaceCard
              key={`${r.id}-${i}`}
              race={r}
              onSelect={onSelectRace}
            />
          ))}
        </div>
      </div>

      {/* flèche droite informative */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute right-[-6px] sm:-right-5 top-1/2 z-10 hidden h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-white/10 text-white backdrop-blur-md sm:inline-flex opacity-70"
      >
        <ChevronRight size={18} strokeWidth={2} />
      </div>
    </div>
  );
}