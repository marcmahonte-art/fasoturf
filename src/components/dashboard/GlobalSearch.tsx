import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CalendarDays, Search, Users, X } from "lucide-react";
import { cn } from "../../lib/utils";
import type { RaceSummary } from "../../types/race";

type Suggestion = {
  id: string;
  kind: "course" | "hippodrome" | "discipline";
  label: string;
  hint: string;
  href: string;
};

/** Construit les suggestions à partir des courses réellement chargées. */
function buildSuggestions(races: RaceSummary[], query: string): Suggestion[] {
  const q = query.trim().toLowerCase();
  if (q.length < 2) return [];

  const out: Suggestion[] = [];
  const seen = new Set<string>();

  for (const race of races) {
    const raceLabel = `R${race.meetingNumber} C${race.raceNumber} · ${race.hippodrome}`;
    const haystacks = [
      race.hippodrome,
      race.discipline ?? "",
      raceLabel,
    ].join(" ").toLowerCase();

    if (!haystacks.includes(q)) continue;

    if (!seen.has(`course-${race.id}`)) {
      seen.add(`course-${race.id}`);
      out.push({
        id: `course-${race.id}`,
        kind: "course",
        label: raceLabel,
        hint: `${race.participantCount} partants · ${race.startTime}`,
        href: `/courses/${race.id}`,
      });
    }
  }

  const hippodromes = new Set<string>();
  for (const race of races) {
    if (!race.hippodrome.toLowerCase().includes(q)) continue;
    if (hippodromes.has(race.hippodrome)) continue;
    hippodromes.add(race.hippodrome);
    out.push({
      id: `hippo-${race.hippodrome}`,
      kind: "hippodrome",
      label: race.hippodrome,
      hint: "Hippodrome",
      href: `/courses?hippodrome=${encodeURIComponent(race.hippodrome)}`,
    });
  }

  return out.slice(0, 6);
}

/**
 * Recherche globale (spec §14).
 *
 * Périmètre couvert : course, hippodrome, discipline — à partir des données
 * réellement chargées. Les chevaux, jockeys et entraîneurs nécessitent une
 * recherche côté backend qui n'est pas encore exposée : aucune suggestion
 * n'est inventée pour ces catégories.
 */
export function GlobalSearch({ races }: { races: RaceSummary[] }) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const suggestions = useMemo(() => buildSuggestions(races, query), [races, query]);

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const showPanel = open && query.trim().length >= 2;

  return (
    <div ref={containerRef} className="relative w-full max-w-[481px]">
      <div className="relative">
        <Search
          size={15}
          aria-hidden="true"
          className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-faso-muted"
        />
        <input
          type="search"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder="Rechercher une course, un cheval, un jockey, un entraîneur..."
          aria-label="Recherche globale"
          aria-expanded={showPanel}
          aria-controls="global-search-results"
          role="combobox"
          className={cn(
            "h-[34px] w-full rounded-[9px] border border-transparent bg-faso-field pl-10 pr-9",
            "text-[13px] text-faso-text placeholder:text-faso-muted",
            "transition-colors duration-150 ease-out focus:border-faso-green/30 focus:bg-white",
            "[&::-webkit-search-cancel-button]:hidden",
          )}
        />
        {query && (
          <button
            type="button"
            aria-label="Effacer la recherche"
            onClick={() => {
              setQuery("");
              setOpen(false);
            }}
            className="absolute right-2.5 top-1/2 grid h-5 w-5 -translate-y-1/2 place-items-center rounded-full text-faso-muted hover:bg-faso-border-soft hover:text-faso-text"
          >
            <X size={12} aria-hidden="true" />
          </button>
        )}
      </div>

      {showPanel && (
        <div
          id="global-search-results"
          role="listbox"
          className="absolute left-0 right-0 top-[42px] z-50 animate-fade-in overflow-hidden rounded-[10px] border border-faso-border bg-white shadow-lift"
        >
          {suggestions.length === 0 ? (
            <p className="px-4 py-3 text-[12px] text-faso-muted">
              Aucun résultat pour « {query.trim()} ».
            </p>
          ) : (
            <ul className="max-h-[280px] overflow-y-auto ft-scroll-light py-1">
              {suggestions.map((s) => (
                <li key={s.id}>
                  <button
                    type="button"
                    role="option"
                    aria-selected="false"
                    onClick={() => {
                      setOpen(false);
                      navigate(s.href);
                    }}
                    className="flex w-full items-center gap-3 px-3 py-2 text-left transition-colors duration-150 hover:bg-faso-bg"
                  >
                    <span className="grid h-7 w-7 shrink-0 place-items-center rounded-[8px] bg-faso-success-soft text-faso-green">
                      {s.kind === "hippodrome" ? (
                        <Users size={13} aria-hidden="true" />
                      ) : (
                        <CalendarDays size={13} aria-hidden="true" />
                      )}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-[12.5px] font-semibold text-faso-text">
                        {s.label}
                      </span>
                      <span className="block truncate text-[11px] text-faso-muted">{s.hint}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
