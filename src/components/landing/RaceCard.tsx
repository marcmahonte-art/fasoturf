import { MapPin, Clock3, TrendingUp, Calendar, CheckCircle2, Star } from "lucide-react";
import horseRunner from "../../assets/horse-runner.svg";
import type { Race } from "../../data/races";
import { todayIso } from "../../lib/formatters";

/**
 * Accent graphique du petit cheval — seul point de couleur chaude toléré
 * (détail graphique, cf. Design System §4 « règle 80 / 15 / 5 »).
 */
const ACCENT_COLOR: Record<Race["accent"], string> = {
  green: "#0BAF58",
  gold: "#F2C94C",
  red: "#D64545",
};

const MONTHS_FR: Record<string, string> = {
  "01": "Janv", "02": "Févr", "03": "Mars", "04": "Avr",
  "05": "Mai", "06": "Juin", "07": "Juil", "08": "Août",
  "09": "Sept", "10": "Oct", "11": "Nov", "12": "Déc"
};

function formatVisibleDate(dateStr: string): { label: string; isToday: boolean } {
  if (!dateStr) return { label: "Date N/A", isToday: false };
  // Comparaison à la date **locale** courante : `toISOString()` renvoie la date
  // UTC et peut désigner la veille ou le lendemain selon le fuseau.
  const isToday = dateStr.slice(0, 10) === todayIso();
  const parts = dateStr.split("-");
  if (parts.length === 3) {
    const day = parts[2];
    const month = MONTHS_FR[parts[1]] || parts[1];
    if (isToday) return { label: "Aujourd'hui", isToday: true };
    return { label: `${day} ${month}`, isToday: false };
  }
  return { label: dateStr, isToday: false };
}

export function RaceCard({
  race,
  onSelect,
  showDate = false,
}: {
  race: Race;
  onSelect?: (race: Race) => void;
  /** N'affiche la date que dans la vue « Toutes » (dates mélangées). */
  showDate?: boolean;
}) {
  const accent = ACCENT_COLOR[race.accent];
  const dateInfo = formatVisibleDate(race.date);
  const isToday = dateInfo.isToday;

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
      className={`group relative flex h-[132px] min-w-[262px] sm:min-w-[278px] flex-col justify-between rounded-[8px] border p-3.5 text-white transition-colors duration-200 cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-faso-accent/60 ${
        isToday
          ? "border-faso-accent/40 bg-[#07392E] hover:border-faso-accent/70"
          : "border-white/10 bg-[#06352B]/85 hover:border-faso-accent/35 hover:bg-[#084236]"
      }`}
    >
      {/* Ligne 1 : Réunion / Course + marquage LONAB (+ date en vue mixte) */}
      <div className="flex items-center justify-between gap-1.5">
        <div className="flex min-w-0 items-center gap-1.5">
          <span className="rounded bg-faso-green/30 border border-faso-green/40 px-1.5 py-0.5 text-[11px] font-bold text-white">
            {race.reunion}
          </span>
          <span className="rounded bg-faso-green/20 px-1.5 py-0.5 text-[11px] font-bold text-white/90">
            {race.course}
          </span>

          {/* Marquage LONAB — unique emploi du doré, volontairement discret */}
          {race.isLonab && (
            <span
              title={
                `Course LONAB${race.lonabJournalBet ? ` — pari du jour : ${race.lonabJournalBet}` : ""}` +
                `${race.lonabBet ? ` (${race.lonabBet})` : ""}`
              }
              className="inline-flex shrink-0 items-center gap-0.5 rounded border border-faso-gold/40 px-1.5 py-0.5 text-[9.5px] font-bold uppercase tracking-wide text-faso-gold/90"
            >
              <Star size={9} className="fill-faso-gold/70" />
              LONAB
            </span>
          )}

          {showDate && (
            <span className="inline-flex shrink-0 items-center gap-1 rounded bg-white/[0.08] px-1.5 py-0.5 text-[10px] font-medium text-white/60">
              <Calendar size={10} className="text-white/40" />
              {dateInfo.label}
            </span>
          )}
        </div>

        <img
          src={horseRunner}
          alt=""
          aria-hidden="true"
          width={24}
          height={17}
          className="shrink-0 opacity-80 transition-opacity group-hover:opacity-100"
          style={{ color: accent }}
        />
      </div>

      {/* Ligne 2 : Hippodrome + discipline */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex min-w-0 items-center gap-1.5 text-[13px] font-semibold">
          <MapPin size={13} strokeWidth={2.5} className="shrink-0 text-white/45" />
          <span className="truncate">{race.hippodrome}</span>
        </div>
        <span className="shrink-0 rounded bg-white/[0.08] px-1.5 py-0.5 text-[10px] font-medium text-white/60">
          {race.discipline}
        </span>
      </div>

      {/* Ligne 3 : distance · libellé */}
      <div className="truncate text-[11px] font-medium text-white/55">
        {race.distance} · {race.title}
      </div>

      {/* Ligne 4 : favori + partants + heure */}
      <div className="flex items-center justify-between gap-2 border-t border-white/10 pt-1.5 text-[11px]">
        <span className="flex items-center gap-1 font-semibold text-white/90">
          <TrendingUp size={11} className="text-faso-accent" />
          Fav. {race.favoriteOdds.toFixed(1)}
        </span>

        <span className="text-[10.5px] text-white/55">
          {race.starters} partants
        </span>

        <span className="flex items-center gap-1 rounded border border-white/10 bg-black/25 px-1.5 py-0.5 text-[11px] font-semibold text-white/90">
          <Clock3 size={11} className="text-white/45" />
          {race.time}
          {race.hasResult && (
            <span title="Arrivée validée" className="inline-flex items-center">
              <CheckCircle2 size={11} className="ml-0.5 text-emerald-400" />
            </span>
          )}
        </span>
      </div>
    </article>
  );
}
