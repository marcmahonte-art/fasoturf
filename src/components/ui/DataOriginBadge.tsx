import { Info } from "lucide-react";
import { cn } from "../../lib/utils";
import { DATA_ORIGIN_HINT, DATA_ORIGIN_LABEL, type DataOrigin } from "../../types/common";
import { Tooltip } from "./Tooltip";

const ORIGIN_CLASS: Record<DataOrigin, string> = {
  real: "bg-faso-success-soft text-faso-green",
  official: "bg-faso-success-soft text-faso-green",
  prediction: "bg-faso-info-soft text-faso-info-text",
  user: "bg-faso-bg text-faso-muted",
  demo: "bg-faso-warning-soft text-faso-warning-text",
};

/**
 * Marque explicitement l'origine d'un bloc de données (spec §2.3).
 *
 * Un bloc de démonstration ne doit jamais pouvoir être pris pour un résultat
 * réel : la pastille est toujours visible, et l'infobulle explique la provenance.
 */
export function DataOriginBadge({
  origin,
  className,
}: {
  origin: DataOrigin;
  className?: string;
}) {
  return (
    <Tooltip label={DATA_ORIGIN_HINT[origin]} side="bottom">
      <span
        className={cn(
          "inline-flex items-center gap-1 rounded-full px-1.5 py-[2px]",
          "text-[10px] font-semibold leading-none",
          ORIGIN_CLASS[origin],
          className,
        )}
      >
        <Info size={9} aria-hidden="true" />
        {DATA_ORIGIN_LABEL[origin]}
      </span>
    </Tooltip>
  );
}
