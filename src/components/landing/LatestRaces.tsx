import { useState, useMemo } from "react";
import { Wifi, Database, Calendar, Sparkles, Clock, ListFilter } from "lucide-react";
import { RaceCarousel } from "./RaceCarousel";
import type { Race } from "../../data/races";
import type { DateItem } from "../../services/api";

const MONTHS_FULL: Record<string, string> = {
  "01": "Janvier", "02": "Février", "03": "Mars", "04": "Avril",
  "05": "Mai", "06": "Juin", "07": "Juil", "08": "Août",
  "09": "Septembre", "10": "Octobre", "11": "Novembre", "12": "Décembre"
};

function formatHeaderDate(dateStr: string) {
  if (!dateStr) return "Programme officiel";
  const parts = dateStr.split("-");
  if (parts.length === 3) {
    const day = parseInt(parts[2], 10);
    const month = MONTHS_FULL[parts[1]] || parts[1];
    return `${day} ${month} ${parts[0]}`;
  }
  return dateStr;
}

interface LatestRacesProps {
  races: Race[];
  isLive?: boolean;
  availableDates?: DateItem[];
  onSelectRace?: (race: Race) => void;
}

export function LatestRaces({
  races,
  isLive = false,
  availableDates = [],
  onSelectRace,
}: LatestRacesProps) {
  // Trouver la date d'aujourd'hui ou la plus récente parmi les courses
  const todayDate = useMemo(() => {
    const todayMatch = races.find((r) => r.date === "2026-09-16");
    if (todayMatch) return "2026-09-16";
    return races[0]?.date || "2026-09-16";
  }, [races]);

  // Mode de filtre : 'today' (défaut), 'all', ou une date précise 'YYYY-MM-DD'
  const [selectedFilter, setSelectedFilter] = useState<string>("today");

  // Courses filtrées selon la sélection
  const filteredRaces = useMemo(() => {
    if (selectedFilter === "today") {
      const todayRaces = races.filter((r) => r.date === todayDate);
      return todayRaces.length > 0 ? todayRaces : races;
    }
    if (selectedFilter === "all") {
      return races;
    }
    // Date précise
    const byDate = races.filter((r) => r.date === selectedFilter);
    return byDate.length > 0 ? byDate : races;
  }, [races, selectedFilter, todayDate]);

  // Libellé de la date actuellement affichée
  const activeDateLabel = useMemo(() => {
    if (selectedFilter === "today") {
      return {
        formatted: formatHeaderDate(todayDate),
        isToday: true,
        tag: "PROGRAMME DU JOUR",
      };
    }
    if (selectedFilter === "all") {
      return {
        formatted: "Toutes les dates récentes (Archives)",
        isToday: false,
        tag: "ARCHIVES COMPLÈTES",
      };
    }
    const isToday = selectedFilter === todayDate;
    return {
      formatted: formatHeaderDate(selectedFilter),
      isToday,
      tag: isToday ? "PROGRAMME DU JOUR" : "ARCHIVE OFFICIELLE",
    };
  }, [selectedFilter, todayDate]);

  // Liste des dates pour les boutons de filtre rapide
  const datePills = useMemo(() => {
    if (availableDates.length > 0) {
      return availableDates.slice(0, 6);
    }
    // Calculer depuis les courses
    const seen = new Set<string>();
    const list: { date: string; label: string; count: number; isToday: boolean }[] = [];
    for (const r of races) {
      if (!seen.has(r.date)) {
        seen.add(r.date);
        const isToday = r.date === todayDate;
        const parts = r.date.split("-");
        const count = races.filter((x) => x.date === r.date).length;
        list.push({
          date: r.date,
          label: isToday ? "Aujourd'hui" : `${parts[2]} Sept`,
          count,
          isToday,
        });
      }
    }
    return list.slice(0, 6);
  }, [availableDates, races, todayDate]);

  return (
    <section
      aria-labelledby="latest-races-title"
      className="absolute bottom-[20px] sm:bottom-[32px] left-1/2 z-20 w-[calc(100%-24px)] sm:w-[calc(100%-100px)] max-w-[1418px] -translate-x-1/2 rounded-[16px] border border-faso-green/60 bg-[#00241B]/90 p-4 sm:p-5 backdrop-blur-md shadow-2xl"
    >
      {/* Ligne 1 : Titre + Statut API + Date Principale Bien Visible */}
      <div className="mb-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3 border-b border-white/10 pb-3">
        <div className="flex items-start sm:items-center gap-3">
          <span
            aria-hidden="true"
            className={`mt-1 sm:mt-0 relative inline-block h-[11px] w-[11px] rounded-full shrink-0 ${
              isLive ? "bg-emerald-400 animate-ping" : "bg-faso-accent animate-pulse"
            }`}
            style={{ boxShadow: "0 0 0 4px rgba(11,175,88,.3)" }}
          />

          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h2
                id="latest-races-title"
                className="text-[16px] sm:text-[18px] font-black text-white tracking-tight"
              >
                Programme officiel & Arrivées en direct
              </h2>

              {isLive ? (
                <span className="inline-flex items-center gap-1 rounded bg-emerald-500/20 px-2 py-0.5 text-[10.5px] font-bold text-emerald-400 border border-emerald-500/30">
                  <Wifi size={10} /> API Direct
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 rounded bg-faso-gold/20 px-2 py-0.5 text-[10.5px] font-bold text-faso-gold border border-faso-gold/30">
                  <Database size={10} /> Socle LONAB
                </span>
              )}
            </div>

            {/* BANNIÈRE DATE TRÈS VISIBLE DIRECTEMENT */}
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
              <span className="inline-flex items-center gap-1.5 rounded-md bg-amber-400/20 border border-amber-400/50 px-2.5 py-0.5 font-black text-amber-300 shadow-sm">
                <Calendar size={13} className="text-amber-400" />
                {activeDateLabel.formatted}
              </span>

              {activeDateLabel.isToday && (
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/25 border border-emerald-400/50 px-2 py-0.5 text-[11px] font-extrabold text-emerald-300 animate-pulse">
                  ● {activeDateLabel.tag}
                </span>
              )}

              <span className="text-white/60 text-[11.5px] hidden sm:inline">
                · {filteredRaces.length} course{filteredRaces.length > 1 ? "s" : ""} affichée{filteredRaces.length > 1 ? "s" : ""}
              </span>
            </div>
          </div>
        </div>

        {/* FILTRES INTERACTIFS : PROGRAMME DU JOUR & DATES */}
        <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
          {/* Bouton phare : Programme du Jour */}
          <button
            onClick={() => setSelectedFilter("today")}
            className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-black transition-all shadow-sm ${
              selectedFilter === "today"
                ? "bg-amber-400 text-slate-950 ring-2 ring-amber-300 font-black scale-105"
                : "bg-white/10 text-white/90 hover:bg-white/20 hover:text-white"
            }`}
          >
            <Sparkles size={13} className={selectedFilter === "today" ? "text-slate-950" : "text-amber-300"} />
            Programme du Jour
            <span
              className={`ml-1 rounded px-1.5 py-0.2 text-[10px] font-extrabold ${
                selectedFilter === "today" ? "bg-black/25 text-white" : "bg-amber-400/20 text-amber-300"
              }`}
            >
              {races.filter((r) => r.date === todayDate).length || 8}
            </span>
          </button>

          {/* Boutons de dates individuelles */}
          {datePills.map((dp) => {
            if (dp.isToday) return null; // déjà géré par "Programme du Jour"
            const isActive = selectedFilter === dp.date;
            return (
              <button
                key={dp.date}
                onClick={() => setSelectedFilter(dp.date)}
                className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-bold transition ${
                  isActive
                    ? "bg-faso-accent text-slate-950 font-black"
                    : "bg-black/30 text-white/70 hover:bg-white/10 hover:text-white border border-white/10"
                }`}
              >
                <Calendar size={11} />
                {dp.label}
              </button>
            );
          })}

          {/* Bouton Toutes les courses */}
          <button
            onClick={() => setSelectedFilter("all")}
            className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-semibold transition ${
              selectedFilter === "all"
                ? "bg-faso-accent text-slate-950 font-bold"
                : "bg-black/30 text-white/60 hover:bg-white/10 hover:text-white border border-white/5"
            }`}
          >
            <ListFilter size={12} />
            Toutes
          </button>
        </div>
      </div>

      {/* Carrousel des courses du jour / sélectionnées */}
      <RaceCarousel races={filteredRaces} onSelectRace={onSelectRace} />

      {/* Indicateur inférieur */}
      <div className="mt-2.5 flex items-center justify-between text-[11px] text-white/55 px-1">
        <span className="flex items-center gap-1">
          <Clock size={11} className="text-faso-gold" />
          Mise à jour en temps réel selon les publications officielles LONAB / PMU
        </span>
        <span className="hidden sm:inline">
          Cliquez sur une course pour voir partants, cotes & pronostics
        </span>
      </div>
    </section>
  );
}