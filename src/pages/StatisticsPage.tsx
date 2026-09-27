import { useCallback } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, ArrowLeft, Info, RefreshCw } from "lucide-react";
import { DashboardLayout } from "../components/dashboard/DashboardLayout";
import { Topbar } from "../components/dashboard/Topbar";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { DataOriginBadge } from "../components/ui/DataOriginBadge";
import { Skeleton } from "../components/ui/Skeleton";
import { fetchStatistics } from "../lib/api";
import { useAsyncData } from "../lib/useAsyncData";
import { useDashboardData } from "../lib/useDashboardData";
import { formatCount, formatPercent } from "../lib/formatters";
import type { DataStatus as DataStatusModel } from "../types/performance";
import type { Measure, StatisticsOverview } from "../types/statistics";

function pendingStatus(): DataStatusModel {
  return {
    status: "SYNCING",
    lastUpdatedAt: new Date().toISOString(),
    source: "Socle LONAB",
    raceCount: 0,
    origin: "real",
  };
}

/**
 * Tuile de mesure.
 *
 * La **méthode de calcul est toujours affichée** sous la valeur : une
 * statistique publiée sans son mode de calcul n'est pas publiable (spec §52).
 */
function MeasureTile({ title, measure }: { title: string; measure: Measure }) {
  const hasValue = measure.value !== null;

  return (
    <Card padding="md">
      <header className="flex items-start justify-between gap-2">
        <h3 className="text-[13px] font-bold leading-tight text-faso-text">{title}</h3>
        <DataOriginBadge origin="real" />
      </header>

      <p className="mt-2.5 text-[26px] font-bold leading-none tracking-[-0.6px] text-faso-text">
        {hasValue ? formatPercent(measure.value, 1) : "—"}
      </p>

      <p className="mt-1.5 text-[11px] text-faso-muted">
        {measure.numerator !== null && measure.denominator !== null
          ? `${formatCount(measure.numerator)} sur ${formatCount(measure.denominator)}`
          : "Volume insuffisant"}
      </p>

      <p className="mt-2 border-t border-faso-border-soft pt-2 text-[10.5px] leading-[15px] text-faso-muted">
        {measure.method}
      </p>
      {measure.period && (
        <p className="mt-1 text-[10px] text-faso-muted">Période : {measure.period}</p>
      )}
    </Card>
  );
}

function BarList({
  title,
  items,
}: {
  title: string;
  items: { label: string; value: number; hint?: string }[];
}) {
  const max = Math.max(1, ...items.map((item) => item.value));

  return (
    <Card padding="md">
      <h3 className="text-[13px] font-bold text-faso-text">{title}</h3>

      {items.length === 0 ? (
        <p className="mt-3 text-[12px] text-faso-muted">Aucune donnée disponible.</p>
      ) : (
        <ul className="mt-3 flex flex-col gap-2">
          {items.map((item) => (
            <li key={item.label}>
              <div className="flex items-baseline justify-between gap-3 text-[11.5px]">
                <span className="truncate font-medium text-faso-text">{item.label}</span>
                <span className="shrink-0 text-faso-muted">
                  {formatCount(item.value)}
                  {item.hint ? ` · ${item.hint}` : ""}
                </span>
              </div>
              <div className="mt-1 h-[6px] overflow-hidden rounded-full bg-faso-field">
                <div
                  className="h-full rounded-full bg-faso-green"
                  style={{ width: `${Math.max(4, (item.value / max) * 100)}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

/**
 * Page `/statistiques`.
 *
 * Elle expose **uniquement** des mesures réellement calculées sur la base,
 * chacune accompagnée de sa méthode, de sa période et de son volume. Les
 * métriques personnelles n'y figurent pas : elles exigent un compte utilisateur.
 */
export function StatisticsPage() {
  const shell = useDashboardData();
  const load = useCallback(() => fetchStatistics(), []);
  const { state, reload } = useAsyncData<StatisticsOverview>(load);

  const dataStatus: DataStatusModel =
    shell.state.status === "success" ? shell.state.data.dataStatus : pendingStatus();
  const shellData = shell.state.status === "success" ? shell.state.data : null;
  const data = state.status === "success" ? state.data : null;

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

        <header>
          <h1 className="text-[22px] font-bold leading-tight text-faso-text">Statistiques</h1>
          <p className="mt-1 max-w-[640px] text-[12.5px] leading-[19px] text-faso-muted">
            Mesures calculées sur la base du projet. Chaque indicateur est publié avec sa
            méthode, sa période et son volume. Aucune statistique personnelle n'y figure :
            elle exigerait un compte utilisateur.
          </p>
        </header>

        {state.status === "loading" && (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {[0, 1, 2].map((index) => (
              <Skeleton key={index} className="h-[190px] w-full" />
            ))}
          </div>
        )}

        {state.status === "error" && (
          <div className="flex min-h-[320px] items-center justify-center rounded-[12px] border border-faso-border bg-white p-8">
            <div className="max-w-[430px] text-center">
              <span
                aria-hidden="true"
                className="mx-auto grid h-11 w-11 place-items-center rounded-full bg-faso-danger-soft"
              >
                <AlertTriangle size={20} className="text-faso-red" />
              </span>
              <h2 className="mt-3 text-[16px] font-bold text-faso-text">
                Statistiques indisponibles
              </h2>
              <p className="mt-1.5 text-[12.5px] leading-[19px] text-faso-muted">
                {state.message}
              </p>
              <Button variant="primary" className="mt-4" onClick={reload}>
                <RefreshCw size={14} aria-hidden="true" />
                Réessayer
              </Button>
            </div>
          </div>
        )}

        {data && (
          <>
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
              <MeasureTile title="Taux de victoire du favori" measure={data.favouriteWinRate} />
              <MeasureTile title="Couverture des cotes" measure={data.oddsCoverage} />
              <MeasureTile title="Couverture des arrivées" measure={data.resultCoverage} />
            </div>

            <Card padding="md">
              <header className="flex items-center justify-between gap-2">
                <h3 className="text-[13px] font-bold text-faso-text">Volumes en base</h3>
                <DataOriginBadge origin="real" />
              </header>
              <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-2.5 sm:grid-cols-3 lg:grid-cols-5">
                {[
                  { label: "Courses", value: data.coverage.races },
                  { label: "Courses exploitables", value: data.coverage.exploitableRaces },
                  { label: "Courses avec arrivée", value: data.coverage.racesWithResult },
                  { label: "Partants", value: data.coverage.runners },
                  { label: "Chevaux", value: data.coverage.horses },
                  { label: "Jockeys", value: data.coverage.jockeys },
                  { label: "Entraîneurs", value: data.coverage.trainers },
                  { label: "Hippodromes", value: data.coverage.hippodromes },
                  { label: "Relevés de cotes", value: data.coverage.oddsSnapshots },
                ].map((item) => (
                  <div key={item.label}>
                    <dt className="text-[10.5px] uppercase tracking-wide text-faso-muted">
                      {item.label}
                    </dt>
                    <dd className="mt-0.5 text-[17px] font-bold text-faso-text">
                      {formatCount(item.value)}
                    </dd>
                  </div>
                ))}
              </dl>
            </Card>

            <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
              <BarList
                title="Courses par discipline"
                items={data.byDiscipline.map((item) => ({
                  label: item.discipline,
                  value: item.races,
                }))}
              />
              <BarList
                title="Hippodromes les plus actifs"
                items={data.byHippodrome.map((item) => ({
                  label: item.hippodrome,
                  value: item.races,
                  hint: `${item.days} j`,
                }))}
              />
            </div>

            <BarList
              title="Activité mensuelle"
              items={data.monthlyActivity.map((item) => ({
                label: item.month,
                value: item.races,
              }))}
            />

            <Card padding="md">
              <h3 className="text-[13px] font-bold text-faso-text">Traçabilité de la donnée</h3>
              {data.dataVersions.length === 0 ? (
                <p className="mt-3 text-[12px] text-faso-muted">
                  Aucune version de données enregistrée.
                </p>
              ) : (
                <ul className="mt-3 flex flex-col gap-2.5">
                  {data.dataVersions.map((version) => (
                    <li
                      key={`${version.scope}-${version.version}-${version.createdAt}`}
                      className="rounded-[10px] border border-faso-border px-3 py-2.5"
                    >
                      <p className="text-[12px] font-semibold text-faso-text">
                        {version.scope ?? "périmètre inconnu"} · {version.version ?? "—"}
                      </p>
                      {version.sourceSha256 && (
                        <p className="mt-1 break-all font-mono text-[10px] text-faso-muted">
                          SHA-256 : {version.sourceSha256}
                        </p>
                      )}
                      {version.notes && (
                        <p className="mt-1 text-[11px] leading-[16px] text-faso-muted">
                          {version.notes}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}

              <p className="mt-3 flex items-start gap-1.5 border-t border-faso-border-soft pt-2.5 text-[10.5px] leading-[15px] text-faso-muted">
                <Info size={11} aria-hidden="true" className="mt-[2px] shrink-0" />
                <span>
                  Le socle LONAB est ouvert en lecture seule : l'API ne peut pas le modifier.
                </span>
              </p>
            </Card>

            <p className="text-[11px] leading-[17px] text-faso-muted">
              Un taux de victoire du favori est une <strong>mesure de référence</strong>, pas une
              promesse de gain. Les travaux du projet ont montré que le marché est efficient sur
              toutes les familles de paris testées :{" "}
              <Link to="/dashboard" className="font-semibold text-faso-green">
                aucun avantage exploitable n'a été identifié
              </Link>
              .
            </p>
          </>
        )}
      </main>
    </DashboardLayout>
  );
}
