import { useState, useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { RaceCard } from "./RaceCard";
import type { Race } from "../../data/races";

interface RaceCarouselProps {
  races: Race[];
  onSelectRace?: (race: Race) => void;
  /** Transmis aux cartes : affiche la date quand les dates sont mélangées. */
  showDate?: boolean;
}

export function RaceCarousel({ races, onSelectRace, showDate = false }: RaceCarouselProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isPaused, setIsPaused] = useState(false);

  if (!races || races.length === 0) {
    return (
      <div className="flex h-[132px] w-full items-center justify-center rounded-[8px] border border-white/10 bg-black/20 text-white/60">
        <p className="text-sm">Aucune course enregistrée pour cette sélection.</p>
      </div>
    );
  }

  // Si on a plus d'une course, on duplique pour un défilement infini fluide
  const displayRaces = races.slice(0, 15);
  const loop = displayRaces.length > 2 ? [...displayRaces, ...displayRaces] : displayRaces;

  const scroll = (direction: "left" | "right") => {
    if (containerRef.current) {
      const offset = direction === "left" ? -320 : 320;
      containerRef.current.scrollBy({ left: offset, behavior: "smooth" });
    }
  };

  return (
    <div
      className="relative group/carousel"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {/* Flèche gauche cliquable */}
      <button
        onClick={() => scroll("left")}
        aria-label="Faire défiler vers la gauche"
        className="absolute -left-2 sm:-left-4 top-1/2 z-20 hidden sm:flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-[#03241c]/90 border border-white/15 text-white/85 backdrop-blur-md transition-colors hover:bg-faso-green hover:border-faso-green hover:text-white focus:outline-none"
      >
        <ChevronLeft size={18} strokeWidth={2.5} />
      </button>

      {/* Piste animée / défilante */}
      <div
        ref={containerRef}
        className="overflow-x-auto no-scrollbar py-1 scroll-smooth"
      >
        <div
          className={`flex w-max gap-[14px] ${
            !isPaused && displayRaces.length > 2 ? "animate-marquee" : ""
          } hover:[animation-play-state:paused] motion-reduce:animate-none`}
        >
          {loop.map((r, i) => (
            <RaceCard
              key={`${r.id}-${i}`}
              race={r}
              onSelect={onSelectRace}
              showDate={showDate}
            />
          ))}
        </div>
      </div>

      {/* Flèche droite cliquable */}
      <button
        onClick={() => scroll("right")}
        aria-label="Faire défiler vers la droite"
        className="absolute -right-2 sm:-right-4 top-1/2 z-20 hidden sm:flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-[#03241c]/90 border border-white/15 text-white/85 backdrop-blur-md transition-colors hover:bg-faso-green hover:border-faso-green hover:text-white focus:outline-none"
      >
        <ChevronRight size={18} strokeWidth={2.5} />
      </button>
    </div>
  );
}