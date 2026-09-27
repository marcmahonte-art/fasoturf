import { useCallback } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowRight, BrainCircuit, Info, ShieldAlert, Trophy } from "lucide-react";
import { PageShell } from "../components/dashboard/PageShell";
import { PageEmpty, PageError, SkeletonRows } from "../components/dashboard/states";
import { Card } from "../components/ui/Card";
import { DataOriginBadge } from "../components/ui/DataOriginBadge";
import { Tooltip } from "../components/ui/Tooltip";
import { buttonClass } from "../components/ui/buttonStyles";
import { fetchAvailableDates, fetchFeaturedPredictions, type FeaturedPredictions } from "../lib/api";
import { useAsyncData } from "../lib/useAsyncData";
import { formatDateShort, formatOdds, formatPercent } from "../lib/formatters";
import type { DateItem } from "../types/race";

const PREDICTION_LIMIT = 10;

/**
 * Avertissement de performance.
 *
 * Les valeurs citées sont **mesurées** sur le socle lors des phases
 * d'évaluation du projet : le classement produit par le moteur reproduit
 * nettement moins bien les arrivées que la cote du marché. Publier un
 * classement sans cet avertissement reviendrait à laisser croire à un avantage
 * qui n'a pas été démontré (spec §2.3, §32, §53).
 */
function PerformanceDisclaimer() {
  return (
    <Card padding="md">
      <header className="flex items-center gap-2">
        <ShieldAlert size={15} aria-hidden="true" className="text-faso-warning-text" />
        <h2 className="text-[13.5px] font-bold text-faso-text">
          Ce que ce classement est — et n'est pas
        </h2>
      </header>

      <ul className="mt-2.5 space-y-1.5">
        <li className="flex items-start gap-1.5 text-[11px] leading-[16px] text-faso-muted">
          <span aria-hidden="true" className="mt-[6px] h-[3px] w-[3px] shrink-0 rounded-full bg-faso-muted" />
          <span>
            Il s'agit d'une <strong className="font-semibold text-faso-text">lecture assistée</strong>{" "}
            des données de la course, pas d'une prédiction d'arrivée.
          </span>
        </li>
        <li className="flex items-start gap-1.5 text-[11px] leading-[16px] text-faso-muted">
          <span aria-hidden="true" className="mt-[6px] h-[3px] w-[3px] shrink-0 rounded-full bg-faso-muted" />
          <span>
            Évalué sur le socle, le classement du moteur reproduit les arrivées avec un AUC de{" "}
            <strong className="font-semibold text-faso-text">0,686</strong>, contre{" "}
            <strong className="font-semibold text-faso-text">0,756</strong> pour la seule cote du
            marché. <strong className="font-semibold text-faso-text">La cote reste plus informative
            que le modèle.</strong>
          </span>
        </li>
        <li className="flex items-start gap-1.5 text-[11px] leading-[16px] text-faso-muted">
          <span aria-hidden="true" className="mt-[6px] h-[3px] w-[3px] shrink-0 rounded-full bg-faso-muted" />
          <span>
            Les écarts entre la probabilité du moteur et celle du marché ont été testés comme signal
            de pari : le résultat n'est pas distinguable du hasard. Aucun rendement positif n'est
            revendiqué.
          </span>
        </li>
        <li className="flex items-start gap-1.5 text-[11px] leading-[16px] text-faso-muted">
          <span aria-hidden="true" className="mt-[6px] h-[3px] w-[3px] shrink-0 rounded-full bg-faso-muted" />
          <span>
            Les probabilités affichées sont produites par le moteur sur les données disponibles ;
            elles ne constituent ni un conseil de pari, ni une garantie de résultat.
          </span>
        </li>
      </ul>

      <footer className="mt-3 flex flex-wrap items-center gap-2 border-t border-faso-border-soft pt-2.5">
        <Link to="/statistiques" className={buttonClass("secondary", "sm")}>
          Voir les mesures et leurs méthodes
          <ArrowRight size={12} aria-hidden="true" />
        </Link>
      </footer>
    </Card>
  );
}

/**
 * Page `/pronostics` — sortie réelle du moteur Hippo Engine.
 *
 * Les pronostics proviennent de `GET /api/predictions/featured`, qui interroge
 * le moteur pour une course rattachée à un document source. Lorsque le moteur ne
 * peut rien produire, la page affiche la raison exacte : aucune liste de
 * remplacement n'est fabriquée (spec §40).
 */
export function PronosticsPage() {
  const [params, setParams] = useSearchParams();
  const date = params.get("date");

  const loadFeatured = useCallback(
    () => fetchFeaturedPredictions(date, PREDICTION_LIMIT),
    [date],
  );
  const loadDates = useCallback(() => fetchAvailableDates(60), []);

  const { state, reload } = useAsyncData<FeaturedPredictions>(loadFeatured);
  const { state: datesState } = useAsyncData<DateItem[]>(loadDates);

  const dates = datesState.status === "success" ? datesState.data : [];
  const featured = state.status === "success" ? state.data : null;
  const predictions = featured?.predictions ?? [];
  const hasPredictions = predictions.length > 0;

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
      title="Pronostics"
      description="Classement produit par le moteur Hippo Engine sur une course réellement présente dans la base, accompagné de ses conditions d'obtention."
    >
      <Card padding="md">
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex min-w-[220px] flex-1 flex-col gap-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wide text-faso-muted">
              Journée demandée
            </span>
            <select
              value={date ?? ""}
              onChange={(event) => changeDate(event.target.value || null)}
              className="h-[36px] rounded-[9px] border border-faso-border bg-white px-2.5 text-[12.5px] text-faso-text focus:border-faso-green/40 focus:outline-none"
            >
              <option value="">Course la plus récente analysable (par défaut)</option>
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
            Le moteur n'analyse que les courses rattachées à un document source. Si la journée
            demandée n'en contient aucune, la course analysable la plus récente est utilisée et le
            contexte le précise.
          </span>
        </p>
      </Card>

      {state.status === "loading" && <SkeletonRows count={6} heightClass="h-[62px]" />}

      {state.status === "error" && <PageError message={state.message} onRetry={reload} />}

      {state.status === "success" && !hasPredictions && (
        <PageEmpty
          title="Aucun pronostic disponible"
          description={
            featured?.unavailableReason ??
            "Le moteur n'a publié aucun pronostic pour cette sélection."
          }
        />
      )}

      {state.status === "success" && hasPredictions && featured && (
        <Card padding="md">
          <header className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <BrainCircuit size={16} aria-hidden="true" className="text-faso-green" />
              <h2 className="text-[14.5px] font-bold text-faso-text">
                Classement du moteur ({predictions.length})
              </h2>
            </div>
            <DataOriginBadge origin="prediction" />
          </header>

          {featured.context && (
            <p className="mt-2 text-[11px] leading-[16px] text-faso-muted">{featured.context}</p>
          )}

          <ul className="mt-3 border-t border-faso-border-soft pt-1">
            {predictions.map((prediction) => (
              <li
                key={`${prediction.rank}-${prediction.horseNumber}-${prediction.horseName}`}
                className="flex items-center gap-3 border-b border-faso-border-soft py-2.5 last:border-b-0"
              >
                <span
                  aria-hidden="true"
                  className="grid h-[26px] w-[26px] shrink-0 place-items-center rounded-full bg-faso-field text-[11px] font-bold leading-none text-faso-text"
                >
                  {prediction.rank}
                </span>

                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-semibold leading-tight text-faso-text">
                    <span className="mr-1 text-faso-muted">{prediction.horseNumber}</span>
                    {prediction.horseName}
                  </p>
                  <p className="mt-0.5 truncate text-[10.5px] leading-none text-faso-muted">
                    {prediction.raceLabel}
                  </p>
                </div>

                <Tooltip
                  label="Probabilité de victoire estimée par le moteur sur les données disponibles. Ni une garantie, ni un conseil de pari."
                  side="top"
                >
                  <div className="w-[54px] shrink-0 text-right">
                    <span className="inline-flex h-[22px] items-center rounded-[6px] bg-faso-success-soft px-1.5 text-[12px] font-bold leading-none text-faso-green">
                      {prediction.winProbability === null ||
                      prediction.winProbability === undefined
                        ? "—"
                        : formatPercent(prediction.winProbability)}
                    </span>
                    <p className="mt-1 text-[9.5px] leading-none text-faso-muted">Victoire</p>
                  </div>
                </Tooltip>

                <div className="w-[40px] shrink-0 text-right">
                  <span className="block text-[12px] font-semibold leading-none text-faso-text">
                    {formatOdds(prediction.odds)}
                  </span>
                  <p className="mt-1 text-[9.5px] leading-none text-faso-muted">Cote</p>
                </div>
              </li>
            ))}
          </ul>

          <footer className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-faso-border-soft pt-2.5">
            <span className="text-[10px] text-faso-muted">
              Modèle {predictions[0]?.modelVersion ?? "—"} · {predictions[0]?.predictionVersion ?? "—"}
            </span>
            {featured.raceId && (
              <Link to={`/analyses/${featured.raceId}`} className={buttonClass("secondary", "sm")}>
                <Trophy size={12} aria-hidden="true" />
                Voir la course analysée
              </Link>
            )}
          </footer>
        </Card>
      )}

      <PerformanceDisclaimer />

      {date && (
        <p className="text-[11px] text-faso-muted">
          Journée demandée : {formatDateShort(date)}
        </p>
      )}
    </PageShell>
  );
}
