import { formatDelta } from "../../lib/formatters";
import { cn } from "../../lib/utils";
import type { UserPerformance } from "../../types/performance";
import { Tooltip } from "../ui/Tooltip";

/**
 * Définition des métriques portée par infobulle (spec §24).
 *
 * Tant que le backend n'a pas arrêté le calcul exact, la définition le dit
 * explicitement — on ne présente pas une statistique comme fiable sans méthode.
 */
const DEFINITIONS = {
  successRate:
    "Part de vos sélections évaluées comme réussies, selon la définition de performance FasoTurf. " +
    "Définition de calcul non encore arrêtée côté moteur.",
  top3: "Part de vos sélections dont le cheval termine dans les trois premiers.",
  analyzed: "Nombre de courses que vous avez analysées sur la période affichée.",
} as const;

function MetricTile({
  label,
  value,
  delta,
  caption,
  definition,
}: {
  label: string;
  value: string;
  delta?: number;
  caption: string;
  definition: string;
}) {
  return (
    <div className="rounded-[10px] border border-[#EFF3F1] bg-[#FAFBFB] px-2.5 py-2.5">
      <Tooltip label={definition} side="bottom">
        <span className="block truncate text-[10.5px] font-medium leading-none text-faso-muted underline decoration-dotted decoration-faso-border underline-offset-[3px]">
          {label}
        </span>
      </Tooltip>

      <div className="mt-1.5 flex items-baseline gap-1">
        <span className="text-[23px] font-bold leading-none tracking-[-0.4px] text-faso-text">
          {value}
        </span>
        {delta !== undefined && (
          <span
            className={cn(
              "text-[10px] font-bold leading-none",
              delta >= 0 ? "text-faso-green" : "text-faso-red",
            )}
          >
            ({formatDelta(delta)})
          </span>
        )}
      </div>

      <div className="mt-1.5 truncate text-[10px] leading-none text-faso-muted">{caption}</div>
    </div>
  );
}

/** Trois KPI utilisateur (spec §23). */
export function PerformanceMetrics({ performance }: { performance: UserPerformance }) {
  return (
    <div className="grid grid-cols-3 gap-2">
      <MetricTile
        label="Taux de réussite"
        value={`${performance.successRate}%`}
        delta={performance.successRateDelta}
        caption="sur 30 jours"
        definition={DEFINITIONS.successRate}
      />
      <MetricTile
        label="Top 3"
        value={`${performance.top3Rate}%`}
        delta={performance.top3Delta}
        caption="sur 30 jours"
        definition={DEFINITIONS.top3}
      />
      <MetricTile
        label="Courses analysées"
        value={String(performance.racesAnalyzed)}
        caption="ce mois"
        definition={DEFINITIONS.analyzed}
      />
    </div>
  );
}
