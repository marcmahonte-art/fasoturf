import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { BrainCircuit, Info } from "lucide-react";
import { PageShell } from "../components/dashboard/PageShell";
import { RaceFollowCard } from "../components/dashboard/RaceFollowCard";
import { PageEmpty, PageError, SkeletonRows } from "../components/dashboard/states";
import { Card } from "../components/ui/Card";
import { DataOriginBadge } from "../components/ui/DataOriginBadge";
import { fetchAvailableDates, fetchRaceSummaries } from "../lib/api";
import { useAsyncData } from "../lib/useAsyncData";
import type { DateItem, RaceSummary } from "../types/race";

const PAGE_LIMIT = 40;

/**
 * Page `/analyses` — courses réellement analysables par le moteur.
 *
 * Seules les courses rattachées à un document source sont listées : le moteur
 * Hippo Engine raisonne sur cet identifiant, et ne peut rien produire pour les
 * courses injectées par les adapters externes. Le filtre est appliqué **côté
 * serveur** (`analysable=true`), le frontend ne devine rien.
 */
export function AnalysesPage() {
  const [params, setParams] = useSearchParams();
  const date = params.get("date");

  const loadRaces = useCallback(
    () => fetchRaceSummaries({ date, analysable: true, limit: PAGE_LIMIT }),
    [date],
  );
  const loadDates = useCallback(() => fetchAvailableDates(60), []);

  const { state, reload } = useAsyncData<RaceSummary[]>(loadRaces);
  const { state: datesState } = useAsyncData<DateItem[]>(loadDates);

  const dates = datesState.status === "success" ? datesState.data : [];
  const races = state.status === "success" ? state.data : [];

  const changeDate = useCallback(
    (next: string | null) => {
      const updated = new URLSearchParams(params);
      if (next) updated.set("date", next);
      else updated.delete("date");
      setParams(updated, { replace: true });
    },
    [params, setParams],
  );

  return (
    <PageShell
      title="Analyses IA"
      description="Courses que le moteur Hippo Engine peut réellement analyser, c'est-à-dire rattachées à un document source. Ouvrez une course pour voir le classement produit et ses conditions d'obtention."
    >
      <Card padding="md">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex min-w-[220px] flex-1 flex-col gap-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-faso-muted">
              Journée
            </span>
            <select
              value={date ?? ""}
              onChange={(event) => changeDate(event.target.value || null)}
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
        </div>

        <p className="mt-3 flex items-start gap-1.5 border-t border-faso-border-soft pt-2.5 text-[11px] leading-[16px] text-faso-muted">
          <Info size={11} aria-hidden="true" className="mt-[2px] shrink-0" />
          <span>
            {state.status === "success"
              ? `${races.length} course${races.length > 1 ? "s" : ""} analysable${races.length > 1 ? "s" : ""} affichée${races.length > 1 ? "s" : ""}.`
              : "Chargement des courses analysables…"}
          </span>
        </p>
      </Card>

      {state.status === "loading" && <SkeletonRows count={6} heightClass="h-[104px]" />}

      {state.status === "error" && <PageError message={state.message} onRetry={reload} />}

      {state.status === "success" && races.length === 0 && (
        <PageEmpty
          title="Aucune course analysable"
          description={
            date
              ? "Aucune course de cette journée n'est rattachée à un document source. Choisissez une autre journée."
              : "La base ne contient aucune course analysable par le moteur pour le moment."
          }
        />
      )}

      {state.status === "success" && races.length > 0 && (
        <section aria-labelledby="analyses-list-title">
          <header className="mb-3.5 flex items-center gap-2.5">
            <BrainCircuit size={16} aria-hidden="true" className="text-faso-green" />
            <h2 id="analyses-list-title" className="text-[18px] font-bold leading-6 text-faso-text">
              Courses analysables
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
        <Info size={12} aria-hidden="true" className="mt-[2px] shrink-0" />
        <span>
          Le classement produit par le moteur est une lecture assistée des données, pas une
          prédiction d'arrivée : évalué sur le socle, il reproduit les arrivées moins bien que la
          seule cote du marché. Aucun rendement n'est revendiqué.
        </span>
      </p>
    </PageShell>
  );
}
