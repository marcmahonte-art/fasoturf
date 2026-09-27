import { Link } from "react-router-dom";
import { ArrowRight, Info, Trophy } from "lucide-react";
import { Card } from "../ui/Card";
import { DataOriginBadge } from "../ui/DataOriginBadge";
import { PredictionRow } from "./PredictionRow";
import { Tooltip } from "../ui/Tooltip";
import type { Prediction } from "../../types/prediction";

/**
 * « Top 5 des pronostics » (spec §29 et §31).
 *
 * Les probabilités proviennent du moteur **Hippo Engine** via l'API ; le
 * frontend ne les recalcule jamais (spec §44).
 *
 * `context` nomme la course et le modèle effectivement utilisés. Lorsque le
 * moteur n'a pas pu produire de pronostic, `unavailableReason` est affichée
 * telle quelle : aucune liste de remplacement n'est fabriquée (spec §40).
 */
export function PredictionTop5({
  predictions,
  context,
  unavailableReason,
}: {
  predictions: Prediction[];
  context: string | null;
  unavailableReason: string | null;
}) {
  const hasPredictions = predictions.length > 0;
  const isDemo = predictions.some((p) => p.origin === "demo");

  return (
    <Card padding="md">
      <header className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Trophy size={16} strokeWidth={2.1} aria-hidden="true" className="text-faso-green" />
          <h2 className="text-[14.5px] font-bold leading-5 text-faso-text">
            Top 5 des pronostics
          </h2>
        </div>
        <Link
          to="/pronostics"
          className="inline-flex shrink-0 items-center gap-1 text-[12px] font-semibold text-faso-green hover:text-faso-green-dark"
        >
          Voir tous
          <ArrowRight size={12} aria-hidden="true" />
        </Link>
      </header>

      {context && (
        <p className="mt-2 truncate text-[11px] leading-[16px] text-faso-muted" title={context}>
          {context}
        </p>
      )}

      {isDemo && (
        <div className="mt-2.5 flex items-start gap-2 rounded-[8px] bg-faso-warning-soft px-2.5 py-2">
          <Info size={12} aria-hidden="true" className="mt-[2px] shrink-0 text-faso-warning-text" />
          <p className="text-[10.5px] leading-[15px] text-faso-warning-text">
            Classement de démonstration : aucune probabilité réelle n'est affichée.
          </p>
        </div>
      )}

      {hasPredictions ? (
        <ul className="mt-1.5">
          {predictions.map((prediction) => (
            <PredictionRow key={`${prediction.raceId}-${prediction.horseId}-${prediction.rank}`} prediction={prediction} />
          ))}
        </ul>
      ) : (
        <div className="mt-3 flex items-start gap-2 rounded-[10px] border border-faso-border bg-faso-bg px-3 py-3">
          <Info size={13} aria-hidden="true" className="mt-[2px] shrink-0 text-faso-muted" />
          <div className="min-w-0">
            <p className="text-[12px] font-semibold leading-tight text-faso-text">
              Aucun pronostic disponible
            </p>
            <p className="mt-1 text-[11px] leading-[16px] text-faso-muted">
              {unavailableReason ?? "Le moteur n'a publié aucun pronostic."}
            </p>
          </div>
        </div>
      )}

      <footer className="mt-2 flex items-center justify-between gap-2 border-t border-faso-border-soft pt-2.5">
        {hasPredictions ? (
          <DataOriginBadge origin={isDemo ? "demo" : (predictions[0]?.origin ?? "prediction")} />
        ) : (
          <span className="text-[10px] text-faso-muted">Moteur non disponible</span>
        )}
        <Tooltip
          label="Version du modèle et horodatage de la prédiction — fournis par le moteur."
          side="top"
        >
          <span className="text-[10px] text-faso-muted">
            Modèle {predictions[0]?.modelVersion ?? "—"}
          </span>
        </Tooltip>
      </footer>
    </Card>
  );
}
