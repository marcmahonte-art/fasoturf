import { useState, useMemo } from "react";
import { Wifi, Database, Calendar, Sparkles, Clock, ListFilter, Loader2 } from "lucide-react";
import { RaceCarousel } from "./RaceCarousel";
import type { Race } from "../../data/races";
import type { DateItem, RaceFeedSource } from "../../services/api";
import { formatDayMonthShort, formatDayMonthYear, todayIso } from "../../lib/formatters";

interface LatestRacesProps {
  races: Race[];
  isLive?: boolean;
  /** Origine réelle du programme — `null` tant que la source n'a pas répondu. */
  source?: RaceFeedSource | null;
  /** Date couverte par l'instantané local, si c'est lui qui est affiché. */
  snapshotDate?: string | null;
  availableDates?: DateItem[];
  onSelectRace?: (race: Race) => void;
}

export function LatestRaces({
  races,
  isLive = false,
  source = null,
  snapshotDate = null,
  availableDates = [],
  onSelectRace,
}: LatestRacesProps) {
  const currentDay = todayIso();

  // Journée mise en avant : la date courante si elle est présente dans les
  // données, sinon la journée la plus récente réellement disponible. La valeur
  // n'est jamais écrite en dur — elle est déduite des courses reçues.
  const todayDate = useMemo(() => {
    if (races.some((race) => race.date === currentDay)) return currentDay;
    const dates = races.map((race) => race.date).filter(Boolean).sort();
    return dates.length > 0 ? dates[dates.length - 1] : currentDay;
  }, [races, currentDay]);

  const isCurrentDay = todayDate === currentDay;

  // Mode de filtre : 'today' (défaut), 'all', ou une date précise 'YYYY-MM-DD'
  const [selectedFilter, setSelectedFilter] = useState<string>("today");

  // Courses filtrées selon la sélection
  const filteredRaces = useMemo(() => {
    if (selectedFilter === "today") {
      const todayRaces = races.filter((race) => race.date === todayDate);
      return todayRaces.length > 0 ? todayRaces : races;
    }
    if (selectedFilter === "all") {
      return races;
    }
    const byDate = races.filter((race) => race.date === selectedFilter);
    return byDate.length > 0 ? byDate : races;
  }, [races, selectedFilter, todayDate]);

  // Libellé de la date actuellement affichée
  const activeDateLabel = useMemo(() => {
    if (selectedFilter === "today") {
      return {
        formatted: formatDayMonthYear(todayDate),
        tag: isCurrentDay ? "Programme du jour" : "Dernière journée disponible",
      };
    }
    if (selectedFilter === "all") {
      return { formatted: "Toutes les dates récentes", tag: "Archives" };
    }
    const isToday = selectedFilter === currentDay;
    return {
      formatted: formatDayMonthYear(selectedFilter),
      tag: isToday ? "Programme du jour" : "Archive officielle",
    };
  }, [selectedFilter, todayDate, currentDay, isCurrentDay]);

  // Liste des dates pour les boutons de filtre rapide
  const datePills = useMemo(() => {
    if (availableDates.length > 0) {
      return availableDates.slice(0, 6);
    }
    const seen = new Set<string>();
    const list: { date: string; label: string; count: number; isToday: boolean }[] = [];
    for (const race of races) {
      if (seen.has(race.date)) continue;
      seen.add(race.date);
      const isToday = race.date === todayDate;
      list.push({
        date: race.date,
        label: isToday ? "Aujourd'hui" : formatDayMonthShort(race.date),
        count: races.filter((item) => item.date === race.date).length,
        isToday,
      });
    }
    return list.slice(0, 6);
  }, [availableDates, races, todayDate]);

  const todayCount = races.filter((race) => race.date === todayDate).length;
  const lonabCount = filteredRaces.filter((race) => race.isLonab).length;

  return (
    <section
      aria-labelledby="latest-races-title"
      className="absolute bottom-[20px] sm:bottom-[32px] left-1/2 z-20 w-[calc(100%-24px)] sm:w-[calc(100%-100px)] max-w-[1418px] -translate-x-1/2 rounded-[14px] border border-faso-green/40 bg-[#00261D]/85 p-4 backdrop-blur-md sm:p-5"
    >
      {/* En-tête : titre + statut + date active + filtres */}
      <div className="mb-3 flex flex-col gap-3 border-b border-white/10 pb-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-3 sm:items-center">
          <span
            aria-hidden="true"
            className={`relative mt-1 inline-block h-[10px] w-[10px] shrink-0 rounded-full sm:mt-0 ${
              isLive ? "bg-emerald-400" : "bg-faso-accent"
            }`}
            style={{ boxShadow: "0 0 0 4px rgba(11,175,88,.18)" }}
          />

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2
                id="latest-races-title"
                className="text-[16px] font-bold tracking-tight text-white sm:text-[17px]"
              >
                Programme officiel &amp; Arrivées
              </h2>

              {source === null ? (
                <span className="inline-flex items-center gap-1 rounded border border-white/[0.12] bg-white/[0.08] px-2 py-0.5 text-[10.5px] font-semibold text-white/65">
                  <Loader2 size={10} className="animate-spin" /> Connexion…
                </span>
              ) : source === "api" ? (
                <span className="inline-flex items-center gap-1 rounded border border-emerald-500/30 bg-emerald-500/15 px-2 py-0.5 text-[10.5px] font-semibold text-emerald-300">
                  <Wifi size={10} /> Données du socle LONAB
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded border border-amber-400/35 bg-amber-400/15 px-2 py-0.5 text-[10.5px] font-semibold text-amber-200">
                  <Database size={10} /> Instantané local
                  {snapshotDate ? ` · ${formatDayMonthShort(snapshotDate)}` : ""}
                </span>
              )}
            </div>

            <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px]">
              <span className="inline-flex items-center gap-1.5 text-white/85">
                <Calendar size={13} className="text-faso-accent" />
                <span className="font-semibold">{activeDateLabel.formatted}</span>
              </span>

              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-faso-accent">
                ● {activeDateLabel.tag}
              </span>

              <span className="text-[11.5px] text-white/50">
                · {filteredRaces.length} course{filteredRaces.length > 1 ? "s" : ""}
                {lonabCount > 0 && (
                  <span className="text-white/65"> dont {lonabCount} LONAB</span>
                )}
              </span>
            </div>
          </div>
        </div>

        {/* Filtres */}
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setSelectedFilter("today")}
            className={`inline-flex items-center gap-1.5 rounded-[8px] px-3 py-1.5 text-[12px] font-semibold transition-colors ${
              selectedFilter === "today"
                ? "bg-faso-green text-white"
                : "bg-white/[0.08] text-white/75 hover:bg-white/[0.14] hover:text-white"
            }`}
          >
            <Sparkles size={13} />
            Programme du jour
            <span
              className={`ml-0.5 rounded px-1.5 py-0.5 text-[10px] font-bold ${
                selectedFilter === "today" ? "bg-black/25 text-white" : "bg-black/20 text-white/70"
              }`}
            >
              {todayCount}
            </span>
          </button>

          {datePills.map((dp) => {
            if (dp.isToday) return null; // déjà couvert par « Programme du jour »
            const isActive = selectedFilter === dp.date;
            return (
              <button
                key={dp.date}
                onClick={() => setSelectedFilter(dp.date)}
                className={`inline-flex items-center gap-1 rounded-[8px] px-2.5 py-1.5 text-[12px] font-medium transition-colors ${
                  isActive
                    ? "bg-faso-green text-white"
                    : "border border-white/10 bg-white/[0.06] text-white/65 hover:bg-white/[0.12] hover:text-white"
                }`}
              >
                <Calendar size={11} />
                {dp.label}
              </button>
            );
          })}

          <button
            onClick={() => setSelectedFilter("all")}
            className={`inline-flex items-center gap-1 rounded-[8px] px-2.5 py-1.5 text-[12px] font-medium transition-colors ${
              selectedFilter === "all"
                ? "bg-faso-green text-white"
                : "border border-white/10 bg-white/[0.06] text-white/65 hover:bg-white/[0.12] hover:text-white"
            }`}
          >
            <ListFilter size={12} />
            Toutes
          </button>
        </div>
      </div>

      {/* Carrousel */}
      {source === null ? (
        <div className="flex h-[132px] w-full items-center justify-center rounded-[8px] border border-white/10 bg-black/20 text-white/60">
          <p className="inline-flex items-center gap-2 text-sm">
            <Loader2 size={14} className="animate-spin" />
            Chargement du programme…
          </p>
        </div>
      ) : (
        <RaceCarousel
          races={filteredRaces}
          onSelectRace={onSelectRace}
          showDate={selectedFilter === "all"}
        />
      )}

      {/* Indicateur inférieur */}
      <div className="mt-2.5 flex flex-col gap-1 px-1 text-[11px] text-white/45 sm:flex-row sm:items-center sm:justify-between">
        <span className="flex items-start gap-1 sm:items-center">
          <Clock size={11} className="mt-[3px] shrink-0 text-white/35 sm:mt-0" />
          {source === "api"
            ? "Courses lues dans le socle LONAB via l'API FasoTurf."
            : source === "snapshot"
              ? `API FasoTurf injoignable : affichage d'un instantané local${
                  snapshotDate ? ` du ${formatDayMonthYear(snapshotDate)}` : ""
                }.`
              : "Connexion à l'API FasoTurf en cours."}
        </span>
        <span className="hidden sm:inline">
          Cliquez sur une course pour voir partants, cotes &amp; arrivée
        </span>
      </div>
    </section>
  );
}
