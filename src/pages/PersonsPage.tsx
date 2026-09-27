import { useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowRight, Info, UserRound } from "lucide-react";
import { PageShell } from "../components/dashboard/PageShell";
import { PageEmpty, PageError, SkeletonRows } from "../components/dashboard/states";
import { Card } from "../components/ui/Card";
import { DataOriginBadge } from "../components/ui/DataOriginBadge";
import { SearchField } from "../components/ui/SearchField";
import { Tooltip } from "../components/ui/Tooltip";
import { buttonClass } from "../components/ui/buttonStyles";
import { fetchPersons, type PersonRole } from "../lib/api";
import { useAsyncData } from "../lib/useAsyncData";
import { formatCount, formatPercent } from "../lib/formatters";
import type { PersonSummary } from "../types/entities";

const PAGE_LIMIT = 50;

/** Configuration éditoriale propre à chaque rôle. */
const ROLE_CONFIG: Record<
  PersonRole,
  { title: string; basePath: string; searchLabel: string; placeholder: string; unit: string }
> = {
  jockey: {
    title: "Jockeys",
    basePath: "/jockeys",
    searchLabel: "Rechercher un jockey par son nom",
    placeholder: "Nom du jockey (ex. E. Raffin)",
    unit: "montes",
  },
  trainer: {
    title: "Entraîneurs",
    basePath: "/entraineurs",
    searchLabel: "Rechercher un entraîneur par son nom",
    placeholder: "Nom de l'entraîneur (ex. L.Cl. Abrivard)",
    unit: "partants",
  },
};

/**
 * Page `/jockeys` et `/entraineurs` — même écran, rôle paramétré.
 *
 * Les deux listes proviennent de `GET /api/jockeys` et `GET /api/trainers`, qui
 * lisent la même table de personnes du socle en filtrant sur le rôle. La
 * recherche est portée par l'URL (`?q=`) pour rester partageable.
 */
export function PersonsPage({ role }: { role: PersonRole }) {
  const config = ROLE_CONFIG[role];
  const [params, setParams] = useSearchParams();
  const query = params.get("q") ?? "";

  const loadPersons = useCallback(
    () => fetchPersons(role, { q: query || null, limit: PAGE_LIMIT }),
    [role, query],
  );

  const { state, reload } = useAsyncData<PersonSummary[]>(loadPersons);

  const persons = state.status === "success" ? state.data : [];

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
      title={config.title}
      description={`Recherche dans les ${config.title.toLowerCase()} référencés par le socle, avec leurs statistiques réellement calculées.`}
      actions={
        <Link
          to={role === "jockey" ? "/entraineurs" : "/jockeys"}
          className={buttonClass("secondary", "md")}
        >
          {role === "jockey" ? "Voir les entraîneurs" : "Voir les jockeys"}
          <ArrowRight size={13} aria-hidden="true" />
        </Link>
      }
    >
      <Card padding="md">
        <SearchField
          value={query}
          onSubmit={submit}
          label={config.searchLabel}
          placeholder={config.placeholder}
        />

        <p className="mt-3 flex items-center gap-1.5 border-t border-faso-border-soft pt-2.5 text-[11px] text-faso-muted">
          <Info size={11} aria-hidden="true" />
          {state.status === "success" ? (
            <>
              {formatCount(persons.length)} {role === "jockey" ? "jockey" : "entraîneur"}
              {persons.length > 1 ? "s" : ""} affiché{persons.length > 1 ? "s" : ""}
              {query ? ` pour « ${query} »` : ` (les plus actifs en premier)`}
            </>
          ) : (
            "Recherche en cours…"
          )}
        </p>
      </Card>

      {state.status === "loading" && <SkeletonRows count={8} heightClass="h-[68px]" />}

      {state.status === "error" && <PageError message={state.message} onRetry={reload} />}

      {state.status === "success" && persons.length === 0 && (
        <PageEmpty
          title={
            query
              ? "Aucun résultat pour cette recherche"
              : `Aucun ${role === "jockey" ? "jockey" : "entraîneur"} référencé`
          }
          description={
            query
              ? "Aucun nom ne correspond dans la base. Essayez un fragment plus court : les accents et la casse sont ignorés."
              : "La base ne contient aucune personne exploitable pour ce rôle."
          }
        />
      )}

      {state.status === "success" && persons.length > 0 && (
        <section aria-labelledby="persons-list-title">
          <header className="mb-3.5 flex items-center gap-2.5">
            <h2 id="persons-list-title" className="text-[18px] font-bold leading-6 text-faso-text">
              Résultats
            </h2>
            <DataOriginBadge origin="real" />
          </header>

          <ul className="flex flex-col gap-1.5">
            {persons.map((person) => (
              <li key={person.id}>
                <PersonRow person={person} basePath={config.basePath} unit={config.unit} />
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="flex items-start gap-1.5 text-[11px] leading-[17px] text-faso-muted">
        <Info size={12} aria-hidden="true" className="mt-[2px] shrink-0" />
        <span>
          La résolution des noms de personnes est imparfaite dans la source : certaines entrées
          proviennent de libellés mal découpés. Le socle enregistre un indice de confiance de
          résolution, affiché tel quel sur chaque ligne — il n'est jamais masqué.
        </span>
      </p>
    </PageShell>
  );
}

/** Ligne de personne : nom, volume d'apparitions, confiance de résolution, lien fiche. */
function PersonRow({
  person,
  basePath,
  unit,
}: {
  person: PersonSummary;
  basePath: string;
  unit: string;
}) {
  const lowConfidence = person.resolutionConfidence !== null && person.resolutionConfidence < 1;

  return (
    <article className="flex min-h-[68px] items-center gap-4 rounded-[12px] border border-faso-border bg-white px-4 py-3 shadow-panel transition-shadow duration-200 ease-out hover:shadow-lift">
      <span
        aria-hidden="true"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-faso-bg text-faso-muted"
      >
        <UserRound size={16} />
      </span>

      <div className="min-w-0 flex-1">
        <h3 className="truncate text-[15px] font-bold leading-tight text-faso-text">
          {person.name}
        </h3>
        <p className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11.5px] text-faso-muted">
          <span>
            {person.appearances === null ? "—" : formatCount(person.appearances)} {unit} enregistrés
          </span>
          {person.resolutionConfidence !== null && (
            <Tooltip
              label="Indice de confiance de la résolution du nom dans la source. En dessous de 100 %, l'entrée peut regrouper ou scinder des personnes distinctes."
              side="top"
            >
              <span className={lowConfidence ? "text-faso-warning-text" : undefined}>
                Résolution {formatPercent(person.resolutionConfidence)}
              </span>
            </Tooltip>
          )}
        </p>
      </div>

      <Link
        to={`${basePath}/${person.id}`}
        className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-[9px] border border-faso-border bg-white px-3 text-[12px] font-semibold text-faso-text transition-colors duration-150 ease-out hover:bg-faso-bg"
      >
        Voir la fiche
        <ArrowRight size={13} aria-hidden="true" />
      </Link>
    </article>
  );
}
