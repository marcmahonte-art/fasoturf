import { useEffect } from "react";
import { X, MapPin, Calendar, Compass, Trophy, TrendingUp, User } from "lucide-react";
import type { Race } from "../../data/races";

interface RaceDetailModalProps {
  race: Race | null;
  onClose: () => void;
}

export function RaceDetailModal({ race, onClose }: RaceDetailModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!race) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-3 sm:p-6 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className="relative flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-white/15 bg-[#063228] text-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header de la modale */}
        <div className="relative border-b border-white/10 bg-[#04241D] p-5 sm:p-6">
          <button
            onClick={onClose}
            aria-label="Fermer la fenêtre"
            className="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-white/80 transition hover:bg-white/20 hover:text-white"
          >
            <X size={18} strokeWidth={2.5} />
          </button>

          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded bg-faso-green/30 px-2 py-0.5 text-xs font-bold text-faso-accent">
              {race.reunion}
            </span>
            <span className="rounded bg-faso-green/20 px-2 py-0.5 text-xs font-bold text-white/90">
              {race.course}
            </span>
            <span className="rounded-full bg-faso-gold/20 px-2.5 py-0.5 text-xs font-semibold text-faso-gold">
              {race.discipline}
            </span>
            {race.hasResult && (
              <span className="flex items-center gap-1 rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">
                <Trophy size={12} />
                Arrivée officielle
              </span>
            )}
          </div>

          <h2 className="mt-2 text-xl sm:text-2xl font-bold tracking-tight text-white">
            {race.title}
          </h2>

          <div className="mt-3 flex flex-wrap items-center gap-y-2 gap-x-5 text-xs sm:text-sm text-white/70">
            <span className="flex items-center gap-1.5 font-medium text-white/90">
              <MapPin size={15} className="text-faso-gold" />
              {race.hippodrome}
            </span>
            <span className="flex items-center gap-1.5">
              <Calendar size={14} />
              {race.date} · {race.time}
            </span>
            <span className="flex items-center gap-1.5">
              <Compass size={14} />
              {race.distance} ({race.terrain})
            </span>
            <span className="flex items-center gap-1.5 text-faso-accent font-semibold">
              <TrendingUp size={14} />
              Favori : {race.favoriteOdds.toFixed(1)}/1
            </span>
          </div>
        </div>

        {/* Corps de la modale avec liste des partants */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          <div className="mb-3 flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-white/60">
            <span>Partants officiels ({race.starters})</span>
            <span>Cote PMU & Marché</span>
          </div>

          <div className="divide-y divide-white/10 rounded-xl border border-white/10 bg-[#032019]/70 overflow-hidden">
            {race.runners.map((runner) => (
              <div
                key={runner.number}
                className={`flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 transition hover:bg-white/5 ${
                  runner.isWinner ? "bg-emerald-950/40 border-l-4 border-l-emerald-400" : ""
                }`}
              >
                {/* Dossard + Cheval + Jockey */}
                <div className="flex items-start sm:items-center gap-3">
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-extrabold ${
                      runner.isWinner
                        ? "bg-emerald-500 text-black shadow-lg shadow-emerald-500/20"
                        : "bg-white/10 text-white"
                    }`}
                  >
                    {runner.number}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm sm:text-base font-bold text-white tracking-wide">
                        {runner.name}
                      </span>
                      {runner.isWinner && (
                        <span className="flex items-center gap-1 rounded bg-emerald-500/20 px-1.5 py-0.5 text-[10px] font-bold text-emerald-300">
                          <Trophy size={10} /> Gagnant
                        </span>
                      )}
                      {runner.marketRank === 1 && !runner.isWinner && (
                        <span className="rounded bg-faso-gold/20 px-1.5 py-0.5 text-[10px] font-bold text-faso-gold">
                          Favori
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-white/60 mt-0.5">
                      <span className="flex items-center gap-1">
                        <User size={11} /> {runner.jockey}
                      </span>
                      <span>·</span>
                      <span className="truncate max-w-[160px] sm:max-w-[200px]">
                        Entr. {runner.trainer}
                      </span>
                      {runner.music && runner.music !== "N/A" && (
                        <>
                          <span>·</span>
                          <span className="font-mono text-[11px] text-white/80">
                            Musique : {runner.music}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* Cotes & Probabilités */}
                <div className="flex items-center justify-between sm:justify-end gap-5 pl-11 sm:pl-0 border-t sm:border-t-0 border-white/5 pt-2 sm:pt-0">
                  {runner.marketProb !== null && (
                    <div className="text-left sm:text-right">
                      <div className="text-xs text-white/50 font-medium">Prob. estimée</div>
                      <div className="text-sm font-semibold text-faso-accent">
                        {runner.marketProb}%
                      </div>
                    </div>
                  )}

                  <div className="text-right min-w-[70px]">
                    <div className="text-xs text-white/50 font-medium">Cote directe</div>
                    <div className="text-base font-bold text-white tabular-nums">
                      {runner.odds ? runner.odds.toFixed(1) : "—"}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer de la modale */}
        <div className="flex items-center justify-between border-t border-white/10 bg-[#04241D] px-6 py-4">
          <p className="text-xs text-white/50">
            Données authentifiées du socle LONAB / PMU · Cotes directes du marché
          </p>
          <button
            onClick={onClose}
            className="rounded-lg bg-white/10 px-4 py-2 text-xs font-semibold text-white transition hover:bg-white/20"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}
