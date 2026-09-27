import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";import { CalendarDays, Filter, Trophy, X } from "lucide-react";
import { PageShell } from "../components/dashboard/PageShell";
import { RaceFollowCard } from "../components/dashboard/RaceFollowCard";
import { PageEmpty, PageError, SkeletonRows } from "../components/dashboard/states";
import { Card } from "../components/ui/Card";
import { DataOriginBadge } from "../components/ui/DataOriginBadge";
import { buttonClass } from "../components/ui/buttonStyles";
import { fetchAvailableDates, fetchDisciplines, fetchRaceSummaries } from "../lib/api";
import { useAsyncData } from "../lib/useAsyncData";
import { cn } from "../lib/utils";
import type { DateItem, RaceSummary } from "../types/race";

const PAGE_LIMIT = 60;

/**
 * Page `/courses` — programme réel des courses.
 *
 * Les filtres sont portés par l'**URL** (`?date=`, `?hippodrome=`,
 * `?discipline=`), ce qui rend un résultat partageable et rechargeable. La
 * recherche globale pointe déjà vers cette page avec ces paramètres.
 *
 * Aucune course n'est inventée : si un filtre ne renvoie rien, la page le dit.
 */
export function CoursesPage() {
  const [params, setParams] = useSearchParams();

  const date = params.get("date");
  const hippodrome = params.get("hippodrome");
  const discipline = params.get("discipline");

  const hasFilters = Boolean(date || hippodrome || discipline);

  const loadRaces = useCallback(
    () => fetchRaceSummaries({ date, hippodrome, discipline, limit: PAGE_LIMIT }),
    [date, hippodrome, discipline],
  );
  const loadDates = useCallback(() => fetchAvailableDates(60), []);
  const loadDisciplines = useCallback(() => fetchDisciplines(), []);

  const { state, reload } = useAsyncData<RaceSummary[]>(loadRaces);
  const { state: datesState } = useAsyncData<DateItem[]>(loadDates);
  const { state: disciplinesState } = useAsyncData<string[]>(loadDisciplines);

  const dates = datesState.status === "success" ? datesState.data : [];
  const disciplines = disciplinesState.status === "success" ? disciplinesState.data : [];

  const updateParam = useCallback(
    (key: string, value: string | null) => {
      const next = new URLSearchParams(params);
      if (value) next.set(key, value);
      else next.delete(key);
      setParams(next, { replace: true });
    },
    [params, setParams],
  );

  const clearFilters = useCallback(() => setParams(new URLSearchParams(), { replace: true }), [setParams]);

  /** Hippodromes réellement présents dans la liste courante (pour le filtre). */
  const hippodromes = useMemo(() => {
    if (state.status !== "success") return [];
    const names = new Set(state.data.map((race) => race.hippodrome));
    return [...names].sort((a, b) => a.localeCompare(b, "fr"));
  }, [state]);

  const races = state.status === "success" ? state.data : [];
  const lonabCount = races.filter((race) => race.isLonab).length;

  return (
    <PageShell
      title="Courses du jour"
      description="Programme réellement présent dans la base. Filtrez par journée, hippodrome ou discipline : le filtre est conservé dans l'adresse de la page."
    >
      {/* Barre de filtres */}
      <Card padding="md">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex min-w-[168px] flex-1 flex-col gap-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-faso-muted">
              Journée
            </span>
            <select
              value={date ?? ""}
              onChange={(event) => updateParam("date", event.target.value || null)}
              className="h-[36px] rounded-[9px] border border-faso-border bg-white px-2.5 text-[12.5px] text-faso-text focus:border-faso-green/40 focus:outline-none"
            >
              <option value="">Toutes les journées disponibles</option>
              {dates.map((item) => (
                <option key={item.date} value={item.date}>
                  {item.label} — {item.count} courses
                </option>
              ))}
            </select>
          </label>

          <label className="flex min-w-[168px] flex-1 flex-col gap-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-faso-muted">
              Hippodrome
            </span>
            <select
              value={hippodrome ?? ""}
              onChange={(event) => updateParam("hippodrome", event.target.value || null)}
              disabled={hippodromes.length === 0}
              className="h-[36px] rounded-[9px] border border-faso-border bg-white px-2.5 text-[12.5px] text-faso-text focus:border-faso-green/40 focus:outline-none disabled:bg-faso-bg disabled:text-faso-muted"
            >
              <option value="">
                {hippodromes.length === 0 ? "Chargement…" : "Tous les hippodromes"}
              </option>
              {hippodromes.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>

          <label className="flex min-w-[168px] flex-1 flex-col gap-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-faso-muted">
              Discipline
            </span>
            <select
              value={discipline ?? ""}
              onChange={(event) => updateParam("discipline", event.target.value || null)}
              className="h-[36px] rounded-[9px] border border-faso-border bg-white px-2.5 text-[12.5px] text-faso-text focus:border-faso-green/40 focus:outline-none"
            >
              <option value="">Toutes les disciplines</option>
              {disciplines.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>

          {hasFilters && (
            <button
              type="button"
              onClick={clearFilters}
              className={cn(buttonClass("secondary", "md"), "h-[36px]")}
            >
              <X size={13} aria-hidden="true" />
              Réinitialiser
            </button>
          )}
        </div>

        <p className="mt-3 flex items-center gap-1.5 border-t border-faso-border-soft pt-2.5 text-[11px] text-faso-muted">
          <Filter size={11} aria-hidden="true" />
          {state.status === "success" ? (
            <>
              {races.length} course{races.length > 1 ? "s" : ""} affichée
              {races.length > 1 ? "s" : ""}
              {lonabCount > 0 && ` · ${lonabCount} au programme LONAB`}
            </>
          ) : (
            "Chargement du programme…"
          )}
        </p>
      </Card>

      {state.status === "loading" && <SkeletonRows count={6} heightClass="h-[104px]" />}

      {state.status === "error" && (
        <PageError message={state.message} onRetry={reload} />
      )}

      {state.status === "success" && races.length === 0 && (
        <PageEmpty
          title="Aucune course ne correspond à ces filtres"
          description={
            hasFilters
              ? "La base ne contient aucune course pour cette combinaison. Élargissez la recherche ou réinitialisez les filtres."
              : "La base ne contient aucune course exploitable pour le moment."
          }
        >
          {hasFilters && (
            <button type="button" onClick={clearFilters} className={buttonClass("secondary", "md")}>
              Réinitialiser les filtres
            </button>
          )}
        </PageEmpty>
      )}

      {state.status === "success" && races.length > 0 && (
        <section aria-labelledby="races-list-title">
          <header className="mb-3.5 flex items-center gap-2.5">
            <h2 id="races-list-title" className="text-[18px] font-bold leading-6 text-faso-text">
              Programme
            </h2>
            <DataOriginBadge origin="real" />
          </header>

          <ul className="flex flex-col gap-1.5">
            {races.map((race) => (
              <li key={race.id}>
                <RaceFollowCard race={race} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="flex items-start gap-1.5 text-[11px] leading-[17px] text-faso-muted">
        <CalendarDays size={12} aria-hidden="true" className="mt-[2px] shrink-0" />
        <span>
          Seules les courses disposant d'au moins 8 partants enregistrés sont listées : en deçà,
          la donnée est trop incomplète pour être analysée. Le badge{" "}
          <span className="inline-flex items-center gap-1 font-semibold text-faso-warning-text">
            <Trophy size={9} aria-hidden="true" />
            LONAB
          </span>{" "}
          signale les courses couvertes par le journal officiel.
        </span>
      </p>
    </PageShell>
  );
}
