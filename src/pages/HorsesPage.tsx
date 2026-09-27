import { useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { AlertTriangle, ArrowRight, Info, PawPrint } from "lucide-react";
import { PageShell } from "../components/dashboard/PageShell";
import { PageEmpty, PageError, SkeletonRows } from "../components/dashboard/states";
import { Card } from "../components/ui/Card";
import { DataOriginBadge } from "../components/ui/DataOriginBadge";
import { SearchField } from "../components/ui/SearchField";
import { fetchHorses } from "../lib/api";
import { useAsyncData } from "../lib/useAsyncData";
import { formatCount, formatDateShort } from "../lib/formatters";
import type { HorseSummary } from "../types/entities";

const PAGE_LIMIT = 50;

/**
 * Libellé lisible des variantes sexe/année de naissance.
 *
 * Le socle stocke `H~2017 | M~2021` : le sexe et l'année de naissance sont
 * mélangés dans une seule colonne, et plusieurs variantes peuvent coexister
 * pour un même nom (indice d'homonymie). On affiche la donnée brute, jamais une
 * déduction (spec §2.3).
 */
function formatVariants(raw: string | null): string {
  if (!raw) return "Non renseigné";
  return raw
    .split("|")
    .map((part) => part.trim())
    .filter(Boolean)
    .join(" · ");
}

/**
 * Page `/chevaux` — recherche dans les chevaux réellement référencés.
 *
 * La recherche est portée par l'URL (`?q=`) : un résultat est partageable et le
 * bouton retour du navigateur fonctionne. Aucun cheval n'est inventé : si la
 * recherche ne renvoie rien, la page le dit.
 */
export function HorsesPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";

  const loadHorses = useCallback(
    () => fetchHorses({ q: query || null, limit: PAGE_LIMIT }),
    [query],
  );

  const { state, reload } = useAsyncData<HorseSummary[]>(loadHorses);

  const horses = state.status === "success" ? state.data : [];

  const submit = useCallback(
    (next: string) => {
      const updated = new URLSearchParams(params);
      if (next) updated.set("q", next);
      else updated.delete("q");
      setParams(updated, { replace: true });
    },
    [params, setParams],
  );

  return (
    <PageShell
      title="Chevaux"
      description="Recherche dans les chevaux référencés par le socle. La recherche ignore les accents et la casse."
    >
      <Card padding="md">
        <SearchField
          value={query}
          onSubmit={submit}
          label="Rechercher un cheval par son nom"
          placeholder="Nom du cheval (ex. Ganass)"
        />

        <p className="mt-3 flex items-center gap-1.5 border-t border-faso-border-soft pt-2.5 text-[11px] text-faso-muted">
          <Info size={11} aria-hidden="true" />
          {state.status === "success" ? (
            <>
              {formatCount(horses.length)} cheval{horses.length > 1 ? "x" : ""} affiché
              {horses.length > 1 ? "s" : ""}
              {query ? ` pour « ${query} »` : " (les plus vus en premier)"}
            </>
          ) : (
            "Recherche en cours…"
          )}
        </p>
      </Card>

      {state.status === "loading" && <SkeletonRows count={8} heightClass="h-[72px]" />}

      {state.status === "error" && <PageError message={state.message} onRetry={reload} />}

      {state.status === "success" && horses.length === 0 && (
        <PageEmpty
          title={query ? "Aucun cheval ne correspond à cette recherche" : "Aucun cheval référencé"}
          description={
            query
              ? "Aucun nom ne correspond dans la base. Essayez un fragment plus court (les accents et la casse sont ignorés)."
              : "La base ne contient aucun cheval exploitable pour le moment."
          }
        />
      )}

      {state.status === "success" && horses.length > 0 && (
        <section aria-labelledby="horses-list-title">
          <header className="mb-3.5 flex items-center gap-2.5">
            <h2 id="horses-list-title" className="text-[18px] font-bold leading-6 text-faso-text">
              Résultats
            </h2>
            <DataOriginBadge origin="real" />
          </header>

          <ul className="flex flex-col gap-1.5">
            {horses.map((horse) => (
              <li key={horse.id}>
                <HorseRow horse={horse} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="flex items-start gap-1.5 text-[11px] leading-[17px] text-faso-muted">
        <AlertTriangle size={12} aria-hidden="true" className="mt-[2px] shrink-0" />
        <span>
          Un même nom peut désigner plusieurs chevaux : le socle ne fournit pas d'identifiant
          d'élevage fiable. Les fiches concernées portent un avertissement d'homonymie plutôt
          qu'une fusion silencieuse.
        </span>
      </p>
    </PageShell>
  );
}

/** Ligne de cheval : identité réelle + signal de qualité, puis lien vers la fiche. */
function HorseRow({ horse }: { horse: HorseSummary }) {
  const homonym = horse.homonymRisk === "suspected_homonym";

  return (
    <article className="flex min-h-[72px] items-center gap-4 rounded-[12px] border border-faso-border bg-white px-4 py-3 shadow-panel transition-shadow duration-200 ease-out hover:shadow-lift">
      <span
        aria-hidden="true"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-faso-bg text-faso-muted"
      >
        <PawPrint size={16} />
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="truncate text-[15px] font-bold leading-tight text-faso-text">
            {horse.name}
          </h3>
          {homonym && (
            <span className="inline-flex items-center gap-1 rounded-full bg-faso-warning-soft px-1.5 py-[2px] text-[10px] font-bold leading-none text-faso-warning-text">
              <AlertTriangle size={9} aria-hidden="true" />
              Homonymie possible
            </span>
          )}
        </div>

        <p className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11.5px] text-faso-muted">
          <span>{formatVariants(horse.sexBirthyearVariants)}</span>
          {horse.breed && <span className="truncate">{horse.breed}</span>}
          {horse.father && <span className="truncate">Père : {horse.father}</span>}
        </p>
      </div>

      <div className="hidden w-[150px] shrink-0 text-right text-[11.5px] text-faso-muted sm:block">
        <p>
          <span className="font-semibold text-faso-text">
            {horse.starts === null ? "—" : formatCount(horse.starts)}
          </span>{" "}
          partants
        </p>
        <p className="mt-1">Vu le {formatDateShort(horse.lastSeenDate)}</p>
      </div>

      <Link
        to={`/chevaux/${horse.id}`}
        className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-[9px] border border-faso-border bg-white px-3 text-[12px] font-semibold text-faso-text transition-colors duration-150 ease-out hover:bg-faso-bg"
      >
        Voir la fiche
        <ArrowRight size={13} aria-hidden="true" />
      </Link>
    </article>
  );
}
