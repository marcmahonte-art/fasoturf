import { Avatar } from "../ui/Avatar";
import { Tooltip } from "../ui/Tooltip";
import { cn } from "../../lib/utils";
import { formatOdds, formatPercent } from "../../lib/formatters";
import type { Prediction } from "../../types/prediction";

/** Rang 1 à 5 — le rang 1 est le seul emploi du doré (règle 80/15/5). */
const RANK_CLASS: Record<number, string> = {
  1: "bg-faso-gold text-faso-green-deep",
  2: "bg-[#E3E8E6] text-faso-text",
  3: "bg-[#EFDCC2] text-faso-text",
};

function rankClass(rank: number): string {
  return RANK_CLASS[rank] ?? "bg-[#F0F3F2] text-faso-muted";
}

/**
 * Ligne du Top 5 (spec §29 et §30).
 *
 * La métrique affichée est nommée explicitement (« Victoire ») : une
 * probabilité n'est jamais présentée seule, sans son contexte.
 *
 * `winProbability` arrive du moteur sous forme de **ratio** (0–1) : la mise en
 * forme passe par `formatPercent`, qui ne fait aucune conversion métier.
 */
export function PredictionRow({ prediction }: { prediction: Prediction }) {
  const probability = prediction.winProbability;

  return (
    <li className="flex items-center gap-2.5 border-b border-faso-border-soft py-2.5 last:border-b-0">
      <span
        aria-hidden="true"
        className={cn(
          "grid h-[26px] w-[26px] shrink-0 place-items-center rounded-full text-[11px] font-bold leading-none",
          rankClass(prediction.rank),
        )}
      >
        {prediction.rank}
      </span>

      <Avatar
        initials={prediction.horseName.slice(0, 2)}
        alt={`Partant ${prediction.horseName}`}
        size="sm"
      />

      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-semibold leading-tight text-faso-text">
          <span className="mr-1 text-faso-muted">{prediction.horseNumber}</span>
          {prediction.horseName}
        </p>
        <p className="mt-0.5 truncate text-[10.5px] leading-none text-faso-muted">
          {prediction.raceLabel}
        </p>
      </div>

      <div className="w-[52px] shrink-0 text-right">
        <span
          className={cn(
            "inline-flex h-[22px] items-center rounded-[6px] px-1.5 text-[12px] font-bold leading-none",
            probability === null || probability === undefined
              ? "bg-faso-bg text-faso-muted"
              : "bg-faso-success-soft text-faso-green",
          )}
        >
          {probability === null || probability === undefined ? "—" : formatPercent(probability)}
        </span>
        <p className="mt-1 text-[9.5px] leading-none text-faso-muted">Victoire</p>
      </div>

      <div className="w-[38px] shrink-0 text-right">
        <Tooltip label="Cote de référence — information, pas une garantie de résultat." side="top">
          <span className="block text-[12px] font-semibold leading-none text-faso-text">
            {formatOdds(prediction.odds)}
          </span>
        </Tooltip>
        <p className="mt-1 text-[9.5px] leading-none text-faso-muted">Cote</p>
      </div>
    </li>
  );
}
