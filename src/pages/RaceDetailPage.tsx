import { useCallback } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertTriangle,
  ArrowLeft,
  BrainCircuit,
  Clock,
  Info,
  RefreshCw,
  Ruler,
  Trophy,
  Users,
} from "lucide-react";
import { DashboardLayout } from "../components/dashboard/DashboardLayout";
import { Topbar } from "../components/dashboard/Topbar";
import { Card } from "../components/ui/Card";
import { MeetingBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { DataOriginBadge } from "../components/ui/DataOriginBadge";
import { Tooltip } from "../components/ui/Tooltip";
import { Skeleton } from "../components/ui/Skeleton";
import { buttonClass } from "../components/ui/buttonStyles";
import { fetchRace, fetchRacePrediction } from "../lib/api";
import { useAsyncData } from "../lib/useAsyncData";
import { useDashboardData } from "../lib/useDashboardData";
import { cn } from "../lib/utils";
import { formatOdds, formatPercent } from "../lib/formatters";
import type { DataStatus as DataStatusModel } from "../types/performance";
import type { RaceDetail } from "../types/race";
import type { RacePrediction, PredictionUnavailable } from "../types/statistics";

/** Statut affiché tant que la source n'a pas répondu. */
function pendingStatus(): DataStatusModel {
  return {
    status: "SYNCING",
    lastUpdatedAt: new Date().toISOString(),
    source: "Socle LONAB",
    raceCount: 0,
    origin: "real",
  };
}

function isUnavailable(
  value: RacePrediction | PredictionUnavailable,
): value is PredictionUnavailable {
  return (value as PredictionUnavailable).available === false;
}

const GRID = "grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_390px]";

/** Ligne de partant : toutes les valeurs proviennent de la donnée, jamais d'une estimation. */
function RunnerRow({ runner }: { runner: RaceDetail["runners"][number] }) {
  return (
    <tr className="border-b border-faso-border-soft last:border-b-0">
      <td className="py-2.5 pr-2 text-center">
        <span
          className={cn(
            "inline-grid h-[24px] w-[24px] place-items-center rounded-full text-[11px] font-bold",
            runner.isWinner ? "bg-faso-gold text-faso-green-deep" : "bg-faso-field text-faso-text",
          )}
        >
          {runner.number}
        </span>
      </td>
      <td className="py-2.5 pr-3">
        <span className="block truncate text-[13px] font-semibold text-faso-text">
          {runner.name}
        </span>
        <span className="mt-0.5 block truncate text-[10.5px] text-faso-muted">
          {runner.jockey || "Jockey non renseigné"}
          {runner.trainer ? ` · ${runner.trainer}` : ""}
        </span>
      </td>
      <td className="hidden py-2.5 pr-3 text-right text-[12px] text-faso-muted sm:table-cell">
        {runner.age ?? "—"}
      </td>
      <td className="hidden py-2.5 pr-3 text-right text-[12px] text-faso-muted md:table-cell">
        {runner.music || "—"}
      </td>
      <td className="py-2.5 pr-3 text-right text-[12px] font-semibold text-faso-text">
        {formatOdds(runner.odds)}
      </td>
      <td className="py-2.5 pr-3 text-right text-[12px] text-faso-muted">
        {runner.marketProb === null ? "—" : formatPercent(runner.marketProb)}
      </td>
      <td className="py-2.5 text-right text-[12px] font-semibold text-faso-text">
        {runner.position ?? "—"}
      </td>
    </tr>
  );
}

/** Bloc « analyse du moteur » : pronostic réel ou indisponibilité explicite. */
function EnginePanel({
  prediction,
  raceId,
}: {
  prediction: RacePrediction | PredictionUnavailable | null;
  raceId: string;
}) {
  if (prediction === null) {
    return (
      <Card padding="md">
        <div className="flex flex-col gap-2">
          <Skeleton className="h-5 w-40" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </Card>
    );
  }

  if (isUnavailable(prediction)) {
    return (
      <Card padding="md">
        <header className="flex items-center gap-2">
          <BrainCircuit size={16} aria-hidden="true" className="text-faso-muted" />
          <h2 className="text-[14.5px] font-bold text-faso-text">Analyse du moteur</h2>
        </header>
        <div className="mt-3 flex items-start gap-2 rounded-[10px] border border-faso-border bg-faso-bg px-3 py-3">
          <Info size={13} aria-hidden="true" className="mt-[2px] shrink-0 text-faso-muted" />
          <div>
            <p className="text-[12px] font-semibold leading-tight text-faso-text">
              Pronostic indisponible
            </p>
            <p className="mt-1 text-[11px] leading-[16px] text-faso-muted">{prediction.reason}</p>
          </div>
        </div>
        <p className="mt-3 text-[10.5px] leading-[15px] text-faso-muted">
          Aucune probabilité n'est affichée en remplacement. Le moteur ne produit un
          pronostic que pour les courses rattachées à un document source.
        </p>
      </Card>
    );
  }

  return (
    <Card padding="md">
      <header className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <BrainCircuit size={16} aria-hidden="true" className="text-faso-green" />
          <h2 className="text-[14.5px] font-bold text-faso-text">Analyse du moteur</h2>
        </div>
        <DataOriginBadge origin="prediction" />
      </header>

      <p className="mt-2 text-[11px] leading-[16px] text-faso-muted">
        {prediction.modelVersion} · {prediction.predictionVersion}
        {prediction.dataQuality ? ` · qualité ${prediction.dataQuality.toLowerCase().replace(/_/g, " ")}` : ""}
        {prediction.confidence ? ` · confiance ${prediction.confidence.toLowerCase()}` : ""}
      </p>

      {prediction.confidenceReasons.length > 0 && (
        <ul className="mt-2 space-y-1">
          {prediction.confidenceReasons.map((reason) => (
            <li key={reason} className="flex items-start gap-1.5 text-[10.5px] leading-[15px] text-faso-muted">
              <span aria-hidden="true" className="mt-[6px] h-[3px] w-[3px] shrink-0 rounded-full bg-faso-muted" />
              {reason}
            </li>
          ))}
        </ul>
      )}

      {prediction.runners.length > 0 && (
        <ul className="mt-3 border-t border-faso-border-soft pt-1">
          {prediction.runners.slice(0, 6).map((item) => (
            <li
              key={`${item.horseNumber}-${item.rank}`}
              className="flex items-center gap-2.5 border-b border-faso-border-soft py-2 last:border-b-0"
            >
              <span className="w-5 shrink-0 text-center text-[11px] font-bold text-faso-muted">
                {item.rank}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-[12.5px] font-semibold text-faso-text">
                  <span className="mr-1 text-faso-muted">{item.horseNumber}</span>
                  {item.horseName}
                </p>
                {item.factorsPositive && item.factorsPositive.length > 0 && (
                  <p className="mt-0.5 truncate text-[10px] text-faso-muted">
                    {item.factorsPositive[0]}
                  </p>
                )}
              </div>
              <Tooltip label="Probabilité de victoire estimée par le moteur. Ce n'est pas une garantie." side="top">
                <span className="shrink-0 rounded-[6px] bg-faso-success-soft px-1.5 py-[3px] text-[11.5px] font-bold text-faso-green">
                  {formatPercent(item.winProbability)}
                </span>
              </Tooltip>
              <span className="w-[34px] shrink-0 text-right text-[11.5px] font-semibold text-faso-text">
                {formatOdds(item.odds)}
              </span>
            </li>
          ))}
        </ul>
      )}

      <footer className="mt-3 border-t border-faso-border-soft pt-2.5">
        <p className="text-[10px] leading-[15px] text-faso-muted">
          Probabilités produites par le moteur Hippo Engine à partir des données
          disponibles. Ce n'est pas une garantie de résultat.
        </p>
        <Link
          to={`/analyses/${raceId}`}
          className="mt-2 inline-flex text-[11.5px] font-semibold text-faso-green hover:text-faso-green-dark"
        >
          Voir l'analyse détaillée
        </Link>
      </footer>
    </Card>
  );
}

/**
 * Fiche course `/courses/:raceId` (spec §43).
 *
 * Toutes les valeurs proviennent de `GET /api/races/{id}` (socle LONAB) et de
 * `GET /api/predictions/race/{id}` (moteur Hippo Engine). Le terrain, l'arrivée
 * et les cotes absents restent affichés « — » : rien n'est inventé.
 */
export function RaceDetailPage() {
  const { raceId = "" } = useParams<{ raceId: string }>();
  const shell = useDashboardData();

  const loadRace = useCallback(() => fetchRace(raceId), [raceId]);
  const loadPrediction = useCallback(() => fetchRacePrediction(raceId), [raceId]);

  const { state: raceState, reload: reloadRace } = useAsyncData(loadRace);
  const { state: predictionState } = useAsyncData(loadPrediction);

  const dataStatus: DataStatusModel =
    shell.state.status === "success" ? shell.state.data.dataStatus : pendingStatus();

  const shellData = shell.state.status === "success" ? shell.state.data : null;
  const race = raceState.status === "success" ? raceState.data : null;

  return (
    <DashboardLayout dataStatus={dataStatus}>
      {shellData ? (
        <Topbar
          user={shellData.user}
          subscription={shellData.subscription}
          notifications={shellData.notifications}
          races={[shellData.nextRace, ...shellData.followedRaces].filter(
            (race): race is NonNullable<typeof race> => race !== null,
          )}
        />
      ) : (
        <div className="flex h-[68px] items-center">
          <Skeleton className="h-[34px] w-full max-w-[481px]" />
        </div>
      )}

      <main className="flex flex-col gap-[18px]">
        <Link
          to="/dashboard"
          className="inline-flex w-fit items-center gap-1.5 text-[12px] font-semibold text-faso-muted hover:text-faso-text"
        >
          <ArrowLeft size={13} aria-hidden="true" />
          Retour au tableau de bord
        </Link>

        {raceState.status === "loading" && (
          <div className={GRID}>
            <div className="flex flex-col gap-3">
              <Skeleton className="h-[112px] w-full" />
              <Skeleton className="h-[380px] w-full" />
            </div>
            <Skeleton className="h-[320px] w-full" />
          </div>
        )}

        {raceState.status === "error" && (
          <div className="flex min-h-[360px] items-center justify-center rounded-[12px] border border-faso-border bg-white p-8">
            <div className="max-w-[430px] text-center">
              <span
                aria-hidden="true"
                className="mx-auto grid h-11 w-11 place-items-center rounded-full bg-faso-danger-soft"
              >
                <AlertTriangle size={20} className="text-faso-red" />
              </span>
              <h1 className="mt-3 text-[16px] font-bold text-faso-text">
                Course introuvable
              </h1>
              <p className="mt-1.5 text-[12.5px] leading-[19px] text-faso-muted">
                {raceState.message}
              </p>
              <div className="mt-4 flex justify-center gap-2">
                <Button variant="primary" onClick={reloadRace}>
                  <RefreshCw size={14} aria-hidden="true" />
                  Réessayer
                </Button>
                <Link to="/dashboard" className={buttonClass("secondary", "md")}>
                  Tableau de bord
                </Link>
              </div>
            </div>
          </div>
        )}

        {race && (
          <>
            {/* En-tête de course */}
            <Card padding="md">
              <div className="flex flex-wrap items-center gap-2">
                <MeetingBadge
                  meeting={Number(race.reunion.replace(/\D/g, "")) || 0}
                  race={Number(race.course.replace(/\D/g, "")) || 0}
                />
                {race.isLonab && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-faso-warning-soft px-2 py-[3px] text-[10px] font-bold leading-none text-faso-warning-text">
                    <Trophy size={9} aria-hidden="true" />
                    Programme LONAB
                  </span>
                )}
                <DataOriginBadge origin="real" />
              </div>

              <h1 className="mt-2.5 text-[22px] font-bold leading-tight text-faso-text">
                {race.hippodrome}
              </h1>
              <p className="mt-1 text-[13px] text-faso-muted">{race.title}</p>

              <dl className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-[12px] text-faso-muted">
                <div className="inline-flex items-center gap-1.5">
                  <Clock size={12} aria-hidden="true" />
                  <dt className="sr-only">Heure de départ</dt>
                  <dd>{race.time || "—"}</dd>
                </div>
                <div className="inline-flex items-center gap-1.5">
                  <Ruler size={12} aria-hidden="true" />
                  <dt className="sr-only">Distance</dt>
                  <dd>{race.distance || "—"}</dd>
                </div>
                <div className="inline-flex items-center gap-1.5">
                  <Users size={12} aria-hidden="true" />
                  <dt className="sr-only">Partants</dt>
                  <dd>{race.starters} partants</dd>
                </div>
                <div>
                  <dt className="sr-only">Discipline</dt>
                  <dd>{race.discipline}</dd>
                </div>
                <div>
                  <dt className="sr-only">Statut</dt>
                  <dd>{race.status}</dd>
                </div>
              </dl>

              <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1.5 border-t border-faso-border-soft pt-3 text-[11.5px]">
                <span className="text-faso-muted">
                  Date : <span className="font-semibold text-faso-text">{race.date}</span>
                </span>
                <span className="text-faso-muted">
                  Terrain : <span className="font-semibold text-faso-text">{race.terrain ?? "—"}</span>
                </span>
                <span className="text-faso-muted">
                  Arrivée :{" "}
                  <span className="font-semibold text-faso-text">{race.arrivee ?? "non publiée"}</span>
                  {race.arriveeSource === "positions" && (
                    <Tooltip
                      label="Ordre reconstitué à partir des positions enregistrées, faute d'arrivée officielle."
                      side="top"
                    >
                      <span className="ml-1 underline decoration-dotted">(reconstituée)</span>
                    </Tooltip>
                  )}
                </span>
                {race.meteo?.temperature !== null && race.meteo?.temperature !== undefined && (
                  <span className="text-faso-muted">
                    Météo :{" "}
                    <span className="font-semibold text-faso-text">
                      {race.meteo.temperature} °C
                      {race.meteo.nebulosite ? ` · ${race.meteo.nebulosite}` : ""}
                    </span>
                  </span>
                )}
              </div>

              <p className="mt-3 flex items-start gap-1.5 text-[10.5px] leading-[15px] text-faso-muted">
                <Info size={11} aria-hidden="true" className="mt-[2px] shrink-0" />
                <span>
                  Le terrain et la météo ne sont affichés que s'ils figurent réellement dans la
                  source : aucune valeur n'est estimée.
                </span>
              </p>
            </Card>

            <div className={GRID}>
              {/* Partants */}
              <Card padding="md">
                <header className="flex items-center justify-between gap-2">
                  <h2 className="text-[14.5px] font-bold text-faso-text">
                    Partants ({race.runners.length})
                  </h2>
                  <DataOriginBadge origin="real" />
                </header>

                {race.runners.length === 0 ? (
                  <p className="mt-4 text-[12px] text-faso-muted">
                    Aucun partant enregistré pour cette course.
                  </p>
                ) : (
                  <div className="mt-2 overflow-x-auto ft-scroll-light">
                    <table className="w-full min-w-[520px] border-collapse">
                      <thead>
                        <tr className="border-b border-faso-border text-left text-[10.5px] uppercase tracking-wide text-faso-muted">
                          <th scope="col" className="pb-2 pr-2 text-center font-semibold">
                            N°
                          </th>
                          <th scope="col" className="pb-2 pr-3 font-semibold">
                            Cheval
                          </th>
                          <th scope="col" className="hidden pb-2 pr-3 text-right font-semibold sm:table-cell">
                            Âge
                          </th>
                          <th scope="col" className="hidden pb-2 pr-3 text-right font-semibold md:table-cell">
                            Musique
                          </th>
                          <th scope="col" className="pb-2 pr-3 text-right font-semibold">
                            Cote
                          </th>
                          <th scope="col" className="pb-2 pr-3 text-right font-semibold">
                            Prob. marché
                          </th>
                          <th scope="col" className="pb-2 text-right font-semibold">
                            Arrivée
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {race.runners.map((runner) => (
                          <RunnerRow key={runner.number} runner={runner} />
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <p className="mt-3 border-t border-faso-border-soft pt-2.5 text-[10.5px] leading-[15px] text-faso-muted">
                  « Prob. marché » est la probabilité implicite déduite des cotes présentes en
                  base. « — » signale une donnée absente de la source, jamais une valeur estimée.
                </p>
              </Card>

              <aside aria-label="Analyse" className="flex flex-col gap-6">
                <EnginePanel
                  prediction={
                    predictionState.status === "success"
                      ? predictionState.data
                      : predictionState.status === "error"
                        ? { available: false, reason: predictionState.message }
                        : null
                  }
                  raceId={raceId}
                />
              </aside>
            </div>
          </>
        )}
      </main>
    </DashboardLayout>
  );
}
