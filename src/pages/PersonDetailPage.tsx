import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { Info, Trophy, UserRound } from "lucide-react";
import { PageShell } from "../components/dashboard/PageShell";
import { PageError } from "../components/dashboard/states";
import { Card } from "../components/ui/Card";
import { DataOriginBadge } from "../components/ui/DataOriginBadge";
import { Skeleton } from "../components/ui/Skeleton";
import { Tooltip } from "../components/ui/Tooltip";
import { buttonClass } from "../components/ui/buttonStyles";
import { fetchPerson, type PersonRole } from "../lib/api";
import { useAsyncData } from "../lib/useAsyncData";
import { formatCount, formatDateShort, formatOdds, formatPercent } from "../lib/formatters";
import type { PersonDetail, PersonStatistics } from "../types/entities";

/** Libellés propres au rôle, partagés par la page liste et la fiche. */
const ROLE_LABEL: Record<PersonRole, { plural: string; unit: string; basePath: string }> = {
  jockey: { plural: "Jockeys", unit: "montes", basePath: "/jockeys" },
  trainer: { plural: "Entraîneurs", unit: "partants", basePath: "/entraineurs" },
};

/** Bloc statistiques : les taux ne sont affichés que si le dénominateur est connu. */
function StatisticsBlock({
  statistics,
  unit,
}: {
  statistics: PersonStatistics;
  unit: string;
}) {
  // Dénominateur des taux : seules les courses dont l'arrivée publiée cite la
  // personne. `mounts` compte toutes les participations, `unknown` celles dont
  // la position est inconnue.
  const known = statistics.mounts - statistics.unknown;

  const tiles: { label: string; value: string; hint: string }[] = [
    {
      label: unit === "montes" ? "Montes" : "Partants",
      value: formatCount(statistics.mounts),
      hint: `Participations enregistrées dans le socle (${unit}).`,
    },
    {
      label: "Victoires",
      value: formatCount(statistics.wins),
      hint: "Arrivées à la première place, parmi les positions connues.",
    },
    {
      label: "Top 3",
      value: formatCount(statistics.top3),
      hint: "Arrivées dans les trois premiers, parmi les positions connues.",
    },
    {
      label: "Positions inconnues",
      value: formatCount(statistics.unknown),
      hint: "Courses dont l'arrivée publiée ne cite pas cette personne.",
    },
  ];

  return (
    <Card padding="md">
      <header className="flex items-center justify-between gap-2">
        <h2 className="text-[14.5px] font-bold text-faso-text">Statistiques réelles</h2>
        <DataOriginBadge origin="real" />
      </header>

      <div className="mt-3 grid grid-cols-2 gap-2.5 lg:grid-cols-4">
        {tiles.map((tile) => (
          <Tooltip key={tile.label} label={tile.hint} side="top">
            <div className="w-full rounded-[10px] border border-faso-border-soft bg-faso-bg px-3 py-2.5">
              <p className="text-[10.5px] font-semibold uppercase tracking-wide text-faso-muted">
                {tile.label}
              </p>
              <p className="mt-1 text-[20px] font-bold leading-none tracking-[-0.4px] text-faso-text">
                {tile.value}
              </p>
            </div>
          </Tooltip>
        ))}
      </div>

      <div className="mt-3 grid grid-cols-1 gap-2.5 border-t border-faso-border-soft pt-3 sm:grid-cols-2">
        <p className="text-[11.5px] text-faso-muted">
          Taux de victoire :{" "}
          <span className="font-semibold text-faso-text">
            {statistics.winRate === null ? "—" : formatPercent(statistics.winRate, 1)}
          </span>
          {known > 0 && (
            <span className="ml-1 text-[10.5px]">
              ({formatCount(statistics.wins)} sur {formatCount(known)})
            </span>
          )}
        </p>
        <p className="text-[11.5px] text-faso-muted">
          Taux de top 3 :{" "}
          <span className="font-semibold text-faso-text">
            {statistics.top3Rate === null ? "—" : formatPercent(statistics.top3Rate, 1)}
          </span>
          {known > 0 && (
            <span className="ml-1 text-[10.5px]">
              ({formatCount(statistics.top3)} sur {formatCount(known)})
            </span>
          )}
        </p>
      </div>

      <p className="mt-3 flex items-start gap-1.5 border-t border-faso-border-soft pt-2.5 text-[10.5px] leading-[15px] text-faso-muted">
        <Info size={11} aria-hidden="true" className="mt-[2px] shrink-0" />
        <span>
          Un taux absent s'affiche « — » : il n'est jamais remplacé par 0 %. Le socle ne publie que
          3 à 5 places par course, ce qui rend une partie des positions inconnue.
        </span>
      </p>
    </Card>
  );
}

/**
 * Fiche jockey ou entraîneur (`/jockeys/:personId`, `/entraineurs/:personId`).
 *
 * Les données proviennent de `GET /api/jockeys/{id}` ou `GET /api/trainers/{id}`,
 * selon le rôle passé en paramètre de route.
 */
export function PersonDetailPage({ role }: { role: PersonRole }) {
  const label = ROLE_LABEL[role];
  const { personId = "" } = useParams<{ personId: string }>();

  const loadPerson = useCallback(() => fetchPerson(role, personId), [role, personId]);
  const { state, reload } = useAsyncData<PersonDetail>(loadPerson);

  const detail = state.status === "success" ? state.data : null;
  const person = detail?.person;

  return (
    <PageShell
      backTo={label.basePath}
      backLabel={`Retour aux ${label.plural.toLowerCase()}`}
      title={person?.name ?? `Fiche ${role === "jockey" ? "jockey" : "entraîneur"}`}
      description={
        person
          ? `Statistiques et dernières courses enregistrées pour ce ${role === "jockey" ? "jockey" : "entraîneur"}.`
          : "Chargement de la fiche…"
      }
      actions={
        <Link to={label.basePath} className={buttonClass("secondary", "md")}>
          Chercher une autre personne
        </Link>
      }
    >
      {state.status === "loading" && (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-[112px] w-full" />
          <Skeleton className="h-[186px] w-full" />
          <Skeleton className="h-[260px] w-full" />
        </div>
      )}

      {state.status === "error" && (
        <PageError
          title={role === "jockey" ? "Jockey introuvable" : "Entraîneur introuvable"}
          message={state.message}
          onRetry={reload}
        />
      )}

      {detail && person && (
        <>
          <Card padding="md">
            <div className="flex flex-wrap items-start gap-4">
              <span
                aria-hidden="true"
                className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-faso-bg text-faso-muted"
              >
                <UserRound size={20} />
              </span>

              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-[20px] font-bold leading-tight text-faso-text">
                    {person.name}
                  </h2>
                  <span className="inline-flex items-center rounded-full bg-faso-bg px-2 py-[3px] text-[10px] font-semibold leading-none text-faso-muted">
                    {role === "jockey" ? "Jockey" : "Entraîneur"}
                  </span>
                  <DataOriginBadge origin="real" />
                </div>

                <dl className="mt-3 grid grid-cols-2 gap-x-5 gap-y-2 text-[11.5px] sm:grid-cols-3">
                  <div>
                    <dt className="text-faso-muted">Apparitions enregistrées</dt>
                    <dd className="mt-0.5 font-semibold text-faso-text">
                      {person.appearances === null ? "—" : formatCount(person.appearances)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-faso-muted">Confiance de résolution du nom</dt>
                    <dd className="mt-0.5 font-semibold text-faso-text">
                      {person.resolutionConfidence === null
                        ? "Non renseignée"
                        : formatPercent(person.resolutionConfidence)}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-faso-muted">Rôle source</dt>
                    <dd className="mt-0.5 font-semibold text-faso-text">{person.role}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </Card>

          <StatisticsBlock statistics={detail.statistics} unit={label.unit} />

          <Card padding="md">
            <header className="flex items-center justify-between gap-2">
              <h2 className="text-[14.5px] font-bold text-faso-text">
                Dernières courses ({detail.recentRuns.length})
              </h2>
              <DataOriginBadge origin="real" />
            </header>

            {detail.recentRuns.length === 0 ? (
              <p className="mt-4 text-[12px] text-faso-muted">
                Aucune course rattachée à cette personne dans la base.
              </p>
            ) : (
              <div className="mt-2 overflow-x-auto ft-scroll-light">
                <table className="w-full min-w-[560px] border-collapse">
                  <thead>
                    <tr className="border-b border-faso-border text-left text-[10.5px] uppercase tracking-wide text-faso-muted">
                      <th scope="col" className="pb-2 pr-3 font-semibold">
                        Date
                      </th>
                      <th scope="col" className="pb-2 pr-3 font-semibold">
                        Cheval
                      </th>
                      <th scope="col" className="pb-2 pr-3 font-semibold">
                        Course
                      </th>
                      <th scope="col" className="pb-2 pr-3 text-right font-semibold">
                        N°
                      </th>
                      <th scope="col" className="pb-2 pr-3 text-right font-semibold">
                        Cote
                      </th>
                      <th scope="col" className="pb-2 text-right font-semibold">
                        Arrivée
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {detail.recentRuns.map((run) => (
                      <tr
                        key={`${run.raceId}-${run.number ?? "x"}`}
                        className="border-b border-faso-border-soft last:border-b-0"
                      >
                        <td className="py-2.5 pr-3 text-[12px] text-faso-muted">
                          {formatDateShort(run.date)}
                        </td>
                        <td className="py-2.5 pr-3">
                          <span className="block max-w-[180px] truncate text-[12.5px] font-semibold text-faso-text">
                            {run.horseName || "Non renseigné"}
                          </span>
                        </td>
                        <td className="py-2.5 pr-3">
                          <Link
                            to={`/courses/${run.raceId}`}
                            className="block max-w-[220px] truncate text-[12px] text-faso-muted hover:text-faso-green"
                          >
                            {run.hippodrome || run.title || "Course sans hippodrome renseigné"}
                          </Link>
                        </td>
                        <td className="py-2.5 pr-3 text-right text-[12px] text-faso-muted">
                          {run.number ?? "—"}
                        </td>
                        <td className="py-2.5 pr-3 text-right text-[12px] font-semibold text-faso-text">
                          {formatOdds(run.odds)}
                        </td>
                        <td className="py-2.5 text-right text-[12px] font-semibold text-faso-text">
                          {run.position === null ? (
                            "—"
                          ) : run.position <= 3 ? (
                            <span className="inline-flex items-center gap-1 text-faso-green">
                              <Trophy size={10} aria-hidden="true" />
                              {run.position}
                            </span>
                          ) : (
                            run.position
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <p className="mt-3 border-t border-faso-border-soft pt-2.5 text-[10.5px] leading-[15px] text-faso-muted">
              Une arrivée « — » signifie que la personne ne figure pas dans les 3 à 5 places
              publiées, pas que la course est manquante.
            </p>
          </Card>
        </>
      )}
    </PageShell>
  );
}
