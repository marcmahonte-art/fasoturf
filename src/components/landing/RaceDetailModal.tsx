import { useEffect } from "react";
import { X, MapPin, Calendar, Compass, Trophy, TrendingUp, User, Star, CloudSun } from "lucide-react";
import type { Race } from "../../data/races";
import { todayIso } from "../../lib/formatters";

const MONTHS_FULL: Record<string, string> = {
  "01": "Janvier", "02": "Février", "03": "Mars", "04": "Avril",
  "05": "Mai", "06": "Juin", "07": "Juil", "08": "Août",
  "09": "Septembre", "10": "Octobre", "11": "Novembre", "12": "Décembre"
};

function formatFullDate(dateStr: string) {
  if (!dateStr) return "Date officielle";
  // Comparaison à la date **locale** courante (jamais une constante, jamais l'UTC).
  const isToday = dateStr.slice(0, 10) === todayIso();
  const parts = dateStr.split("-");
  if (parts.length === 3) {
    const day = parseInt(parts[2], 10);
    const month = MONTHS_FULL[parts[1]] || parts[1];
    const base = `${day} ${month} ${parts[0]}`;
    return isToday ? `Aujourd'hui · ${base}` : base;
  }
  return dateStr;
}

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
            <span className="rounded-full border border-white/[0.12] bg-white/[0.08] px-2.5 py-0.5 text-xs font-medium text-white/70">
              {race.discipline}
            </span>
            {race.isLonab && (
              <span
                title={
                  race.lonabJournalBet
                    ? `Pari du jour au journal officiel LONAB : ${race.lonabJournalBet}`
                    : "Course LONAB"
                }
                className="flex items-center gap-1 rounded-full border border-faso-gold/45 px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide text-faso-gold/90"
              >
                <Star size={12} className="fill-faso-gold/70" />
                Course LONAB
                {race.lonabJournalBet ? ` · ${race.lonabJournalBet}` : ""}
              </span>
            )}
            {race.hasResult && (
              <span className="flex items-center gap-1 rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">
                <Trophy size={12} />
                {race.arriveeSource === "lonab"
                  ? "Arrivée officielle"
                  : "Résultat de la course"}
              </span>
            )}
          </div>

          <h2 className="mt-2 text-xl sm:text-2xl font-bold tracking-tight text-white">
            {race.title}
          </h2>

          {race.hasResult && race.arrivee && (
            <div className="mt-3 flex flex-wrap items-center gap-2 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-2">
              <span className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wider text-emerald-400">
                <Trophy size={13} />
                Arrivée en direct
              </span>
              <span className="flex flex-wrap items-center gap-1">
                {race.arrivee.split("-").map((n, i) => (
                  <span
                    key={`${n}-${i}`}
                    className={`inline-flex h-6 min-w-6 items-center justify-center rounded px-1.5 text-xs font-black ${
                      i === 0
                        ? "bg-faso-gold text-slate-950"
                        : "bg-white/15 text-white"
                    }`}
                  >
                    {n}
                  </span>
                ))}
              </span>
              {race.quinteDividende ? (
                <span className="ml-auto text-[11px] font-bold text-emerald-300">
                  Quinté+ : {race.quinteDividende.toLocaleString("fr-FR")} € / 1 €
                </span>
              ) : race.arriveeSource === "positions" ? (
                <span className="ml-auto text-[10px] font-medium uppercase tracking-wider text-white/45">
                  d'après les positions au poteau
                </span>
              ) : null}
            </div>
          )}

          <div className="mt-3 flex flex-wrap items-center gap-2 sm:gap-3">
            {/* Date de la course */}
            <span className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.12] bg-white/[0.08] px-3 py-1 text-xs font-semibold text-white/90 sm:text-sm">
              <Calendar size={15} className="text-faso-accent" />
              {formatFullDate(race.date)} · {race.time}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-white/[0.08] px-3 py-1 text-xs font-medium text-white/85 sm:text-sm">
              <MapPin size={14} className="text-white/45" />
              {race.hippodrome}
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-white/[0.08] px-3 py-1 text-xs font-medium text-white/70 sm:text-sm">
              <Compass size={14} />
              {race.distance}
            </span>
            {race.meteo && (
              <span
                title={
                  `Météo réunion${race.meteo.ventForce != null ? ` · vent ${race.meteo.ventForce} km/h ${race.meteo.ventDirection ?? ""}` : ""}`
                }
                className="inline-flex items-center gap-1.5 rounded-lg bg-white/[0.08] px-3 py-1 text-xs font-medium text-white/70 sm:text-sm"
              >
                <CloudSun size={14} className="text-white/45" />
                {race.meteo.temperature != null ? `${race.meteo.temperature}°` : ""}
                {race.meteo.nebulosite ? ` ${race.meteo.nebulosite}` : ""}
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/15 px-3 py-1 text-xs font-semibold text-emerald-300 sm:text-sm">
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
                        <span className="rounded border border-white/[0.12] bg-white/[0.08] px-1.5 py-0.5 text-[10px] font-semibold text-white/65">
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
