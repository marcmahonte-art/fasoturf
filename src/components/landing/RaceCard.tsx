import { MapPin, Clock3, TrendingUp, Calendar, CheckCircle2 } from "lucide-react";
import horseRunner from "../../assets/horse-runner.svg";
import type { Race } from "../../data/races";

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
  const isToday = dateStr === "2026-09-16" || dateStr === new Date().toISOString().split("T")[0];
  const parts = dateStr.split("-");
  if (parts.length === 3) {
    const day = parts[2];
    const month = MONTHS_FR[parts[1]] || parts[1];
    if (isToday) {
      return { label: `Aujourd'hui (${day} ${month})`, isToday: true };
    }
    return { label: `${day} ${month} ${parts[0]}`, isToday: false };
  }
  return { label: dateStr, isToday: false };
}

export function RaceCard({
  race,
  onSelect,
}: {
  race: Race;
  onSelect?: (race: Race) => void;
}) {
  const accent = ACCENT_COLOR[race.accent];
  const dateInfo = formatVisibleDate(race.date);

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
      className={`group relative flex h-[134px] min-w-[265px] sm:min-w-[285px] flex-col justify-between rounded-xl border p-3.5 text-white transition-all duration-200 hover:scale-[1.02] hover:shadow-xl cursor-pointer focus:outline-none focus:ring-2 focus:ring-faso-gold/50 ${
        dateInfo.isToday
          ? "border-faso-gold/40 bg-[#063b2f]/90 hover:border-faso-gold hover:bg-[#094739]"
          : "border-white/15 bg-[#06352B]/85 hover:border-faso-gold/40 hover:bg-[#084236]"
      }`}
    >
      {/* Ligne supérieure : Réunion/Course + Date très visible + Icône */}
      <div className="flex items-center justify-between gap-1.5">
        <div className="flex items-center gap-1.5">
          <span className="rounded bg-faso-green/40 border border-faso-accent/40 px-1.5 py-0.5 text-[11px] font-extrabold text-faso-accent">
            {race.reunion}
          </span>
          <span className="rounded bg-white/10 px-1.5 py-0.5 text-[11px] font-bold text-white">
            {race.course}
          </span>
          {/* BADGE DATE HAUTE VISIBILITÉ DIRECTEMENT SUR LA CARTE */}
          <span
            className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-[10.5px] font-black tracking-wide shadow-sm ${
              dateInfo.isToday
                ? "bg-amber-400 text-slate-950 font-black ring-1 ring-amber-300"
                : "bg-white/15 text-amber-200 border border-amber-300/30"
            }`}
          >
            <Calendar size={11} className={dateInfo.isToday ? "text-slate-950" : "text-amber-300"} />
            {dateInfo.label}
          </span>
        </div>

        <img
          src={horseRunner}
          alt=""
          aria-hidden="true"
          width={24}
          height={17}
          className="opacity-90 group-hover:scale-110 transition-transform"
          style={{ color: accent }}
        />
      </div>

      {/* Corps : Hippodrome & Titre */}
      <div className="flex flex-col my-1">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1 text-[13px] font-bold">
            <MapPin size={13} strokeWidth={2.5} className="text-faso-gold shrink-0" />
            <span className="truncate">{race.hippodrome}</span>
          </div>
          <span className="text-[10px] font-semibold text-white/70 bg-black/20 px-1.5 py-0.2 rounded border border-white/5">
            {race.discipline}
          </span>
        </div>
        <div className="truncate text-[11px] text-white/75 mt-0.5 font-medium">
          {race.distance} · {race.title}
        </div>
      </div>

      {/* Pied de carte : Favori + Partants + Heure & Statut */}
      <div className="flex items-center justify-between text-[11px] text-white/75 pt-1.5 border-t border-white/10">
        <span className="flex items-center gap-1 font-bold text-white">
          <TrendingUp size={11} className="text-faso-accent" />
          Fav. {race.favoriteOdds.toFixed(1)}
        </span>

        <span className="text-[10.5px] text-white/60">
          {race.starters} partants
        </span>

        <span className="flex items-center gap-1 text-[11px] font-bold text-faso-gold bg-black/25 px-1.5 py-0.5 rounded border border-faso-gold/20">
          <Clock3 size={11} />
          {race.time}
          {race.hasResult && (
            <span title="Arrivée validée" className="inline-flex items-center">
              <CheckCircle2 size={11} className="text-emerald-400 ml-0.5" />
            </span>
          )}
        </span>
      </div>
    </article>
  );
}