import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertTriangle, Info, PawPrint, Trophy } from "lucide-react";
import { PageShell } from "../components/dashboard/PageShell";
import { PageError } from "../components/dashboard/states";
import { Card } from "../components/ui/Card";
import { DataOriginBadge } from "../components/ui/DataOriginBadge";
import { Skeleton } from "../components/ui/Skeleton";
import { Tooltip } from "../components/ui/Tooltip";
import { buttonClass } from "../components/ui/buttonStyles";
import { fetchHorse } from "../lib/api";
import { useAsyncData } from "../lib/useAsyncData";
import { formatCount, formatDateShort, formatOdds, formatPercent } from "../lib/formatters";
import type { HorseDetail, HorseStatistics } from "../types/entities";

/**
 * Tuile de taux.
 *
 * Un taux n'est affiché que si son dénominateur est connu : sinon la tuile
 * affiche « — » et le motif, jamais un 0 % trompeur (spec §2.3).
 */
function RateTile({
  label,
  rate,
  numerator,
  denominator,
  hint,
}: {
  label: string;
  rate: number | null;
  numerator: number;
  denominator: number;
  hint: string;
}) {
  return (
    <div className="rounded-[10px] border border-faso-border-soft bg-faso-bg px-3 py-2.5">
      <p className="text-[10.5px] font-semibold uppercase tracking-wide text-faso-muted">
        {label}
      </p>
      <p className="mt-1 text-[20px] font-bold leading-none tracking-[-0.4px] text-faso-text">
        {rate === null ? "—" : formatPercent(rate, 1)}
      </p>
      <p className="mt-1 text-[10.5px] text-faso-muted">
        {denominator > 0 ? `${formatCount(numerator)} sur ${formatCount(denominator)}` : "Aucune course"}
      </p>
      <Tooltip label={hint} side="top">
        <p className="mt-1 truncate text-[10px] text-faso-muted underline decoration-dotted">
          {hint}
        </p>
      </Tooltip>
    </div>
  );
}

/** Bloc statistiques : participations connues, victoires, places, inconnues. */
function StatisticsBlock({ statistics }: { statistics: HorseStatistics }) {
  // Dénominateur des taux : seules les courses dont l'arrivée publiée cite le
  // cheval. `starts` compte toutes les participations, `unknown` celles dont la
  // position est inconnue — les taux portent sur la différence.
  const known = statistics.starts - statistics.unknown;

  return (
    <Card padding="md">
      <header className="flex items-center justify-between gap-2">
        <h2 className="text-[14.5px] font-bold text-faso-text">Statistiques réelles</h2>
        <DataOriginBadge origin="real" />
      </header>

      <div className="mt-3 grid grid-cols-2 gap-2.5 lg:grid-cols-4">
        <RateTile
          label="Victoires"
          rate={statistics.winRate}
          numerator={statistics.wins}
          denominator={known}
          hint="Calculé uniquement sur les courses dont la position est connue."
        />
        <RateTile
          label="Top 3"
          rate={statistics.top3Rate}
          numerator={statistics.top3}
          denominator={known}
          hint="Arrivées dans les trois premiers, parmi les positions connues."
        />
        <div className="rounded-[10px] border border-faso-border-soft bg-faso-bg px-3 py-2.5">
          <p className="text-[10.5px] font-semibold uppercase tracking-wide text-faso-muted">
            Top 5
          </p>
          <p className="mt-1 text-[20px] font-bold leading-none tracking-[-0.4px] text-faso-text">
            {formatCount(statistics.top5)}
          </p>
          <p className="mt-1 text-[10.5px] text-faso-muted">courses terminées dans les 5 premiers</p>
        </div>
        <div className="rounded-[10px] border border-faso-border-soft bg-faso-bg px-3 py-2.5">
          <p className="text-[10.5px] font-semibold uppercase tracking-wide text-faso-muted">
            Positions inconnues
          </p>
          <p className="mt-1 text-[20px] font-bold leading-none tracking-[-0.4px] text-faso-text">
            {formatCount(statistics.unknown)}
          </p>
          <p className="mt-1 text-[10.5px] text-faso-muted">exclues des taux ci-dessus</p>
        </div>
      </div>

      <p className="mt-3 flex items-start gap-1.5 border-t border-faso-border-soft pt-2.5 text-[10.5px] leading-[15px] text-faso-muted">
        <Info size={11} aria-hidden="true" className="mt-[2px] shrink-0" />
        <span>
          Le socle ne publie l'arrivée que sur 3 à 5 places : un cheval non cité est simplement
          « hors arrivée », ce qui est normal. Ces courses sont comptées comme positions inconnues
          et n'entrent pas dans les taux.
        </span>
      </p>
    </Card>
  );
}

/**
 * Fiche cheval `/chevaux/:horseId`.
 *
 * L'identité, les statistiques et les courses passées proviennent
 * exclusivement de `GET /api/horses/{id}` (socle LONAB). Rien n'est extrapolé :
 * un champ absent s'affiche « — ».
 */
export function HorseDetailPage() {
  const { horseId = "" } = useParams<{ horseId: string }>();

  const loadHorse = useCallback(() => fetchHorse(horseId), [horseId]);
  const { state, reload } = useAsyncData<HorseDetail>(loadHorse);

  const detail = state.status === "success" ? state.data : null;
  const horse = detail?.horse;

  return (
    <PageShell
      backTo="/chevaux"
      backLabel="Retour à la recherche"
      title={horse?.name ?? "Fiche cheval"}
      description={
        horse
          ? "Identité, statistiques et dernières courses telles qu'enregistrées dans le socle."
          : "Chargement de la fiche…"
      }
      actions={
        <Link to="/chevaux" className={buttonClass("secondary", "md")}>
          Chercher un autre cheval
        </Link>
      }
    >
      {state.status === "loading" && (
        <div className="flex flex-col gap-3">
          <Skeleton className="h-[132px] w-full" />
          <Skeleton className="h-[186px] w-full" />
          <Skeleton className="h-[260px] w-full" />
        </div>
      )}

      {state.status === "error" && (
        <PageError
          title="Cheval introuvable"
          message={state.message}
          onRetry={reload}
        />
      )}

      {detail && horse && (
        <>
          {/* Identité */}
          <Card padding="md">
            <div className="flex flex-wrap items-start gap-4">
              <span
                aria-hidden="true"
                className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-faso-bg text-faso-muted"
              >
                <PawPrint size={20} />
              </span>

              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-[20px] font-bold leading-tight text-faso-text">
                    {horse.name}
                  </h2>
                  {horse.homonymRisk === "suspected_homonym" && (
                    <span className="inline-flex items-center gap-1 rounded-full bg-faso-warning-soft px-2 py-[3px] text-[10px] font-bold leading-none text-faso-warning-text">
                      <AlertTriangle size={9} aria-hidden="true" />
                      Homonymie possible
                    </span>
                  )}
                  <DataOriginBadge origin="real" />
                </div>

                <dl className="mt-3 grid grid-cols-2 gap-x-5 gap-y-2 text-[11.5px] sm:grid-cols-3 lg:grid-cols-5">
                  <div>
                    <dt className="text-faso-muted">Sexe / année</dt>
                    <dd className="mt-0.5 font-semibold text-faso-text">
                      {horse.sexBirthyearVariants || "Non renseigné"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-faso-muted">Race</dt>
                    <dd className="mt-0.5 font-semibold text-faso-text">
                      {horse.breed ?? "Non renseigné"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-faso-muted">Robe</dt>
                    <dd className="mt-0.5 font-semibold text-faso-text">
                      {horse.coat ?? "Non renseigné"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-faso-muted">Père</dt>
                    <dd className="mt-0.5 truncate font-semibold text-faso-text">
                      {horse.father ?? "Non renseigné"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-faso-muted">Mère</dt>
                    <dd className="mt-0.5 truncate font-semibold text-faso-text">
                      {horse.mother ?? "Non renseigné"}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>

            <p className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1.5 border-t border-faso-border-soft pt-3 text-[11.5px] text-faso-muted">
              <span>
                Participations référencées :{" "}
                <span className="font-semibold text-faso-text">
                  {horse.starts === null ? "—" : formatCount(horse.starts)}
                </span>
              </span>
              <span>
                Première apparition :{" "}
                <span className="font-semibold text-faso-text">
                  {formatDateShort(horse.firstSeenDate)}
                </span>
              </span>
              <span>
                Dernière apparition :{" "}
                <span className="font-semibold text-faso-text">
                  {formatDateShort(horse.lastSeenDate)}
                </span>
              </span>
            </p>

            {horse.homonymRisk === "suspected_homonym" && (
              <p className="mt-2.5 flex items-start gap-1.5 rounded-[10px] border border-faso-border bg-faso-bg px-3 py-2.5 text-[10.5px] leading-[15px] text-faso-muted">
                <AlertTriangle size={12} aria-hidden="true" className="mt-[1px] shrink-0" />
                <span>
                  Ce nom apparaît avec plusieurs combinaisons sexe / année de naissance. Les
                  courses listées ci-dessous peuvent donc concerner plusieurs chevaux distincts :
                  aucune fusion n'est faite par le socle.
                </span>
              </p>
            )}
          </Card>

          <StatisticsBlock statistics={detail.statistics} />

          {/* Courses passées */}
          <Card padding="md">
            <header className="flex items-center justify-between gap-2">
              <h2 className="text-[14.5px] font-bold text-faso-text">
                Dernières courses ({detail.recentRuns.length})
              </h2>
              <DataOriginBadge origin="real" />
            </header>

            {detail.recentRuns.length === 0 ? (
              <p className="mt-4 text-[12px] text-faso-muted">
                Aucune course rattachée à ce cheval dans la base.
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
                        Course
                      </th>
                      <th scope="col" className="hidden pb-2 pr-3 font-semibold sm:table-cell">
                        Discipline
                      </th>
                      <th scope="col" className="hidden pb-2 pr-3 text-right font-semibold md:table-cell">
                        Distance
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
                          <Link
                            to={`/courses/${run.raceId}`}
                            className="block max-w-[260px] truncate text-[12.5px] font-semibold text-faso-text hover:text-faso-green"
                          >
                            {run.hippodrome || run.title || "Course sans hippodrome renseigné"}
                          </Link>
                          {run.title && run.hippodrome && (
                            <span className="mt-0.5 block max-w-[260px] truncate text-[10.5px] text-faso-muted">
                              {run.title}
                            </span>
                          )}
                        </td>
                        <td className="hidden py-2.5 pr-3 text-[12px] text-faso-muted sm:table-cell">
                          {run.discipline ?? "—"}
                        </td>
                        <td className="hidden py-2.5 pr-3 text-right text-[12px] text-faso-muted md:table-cell">
                          {run.distanceMeters === null
                            ? "—"
                            : `${formatCount(run.distanceMeters)} m`}
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
              Une arrivée « — » signifie que le cheval ne figure pas dans les 3 à 5 places publiées,
              pas que la course est manquante.
            </p>
          </Card>
        </>
      )}
    </PageShell>
  );
}
