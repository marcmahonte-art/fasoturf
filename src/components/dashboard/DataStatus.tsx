import { AlertCircle, RefreshCw } from "lucide-react";
import { formatCount, formatLastUpdate } from "../../lib/formatters";
import { cn } from "../../lib/utils";
import { SYNC_STATUS_LABEL, type DataStatus as DataStatusModel } from "../../types/performance";

const DOT_CLASS: Record<DataStatusModel["status"], string> = {
  CURRENT: "bg-faso-accent",
  SYNCING: "bg-faso-gold",
  ERROR: "bg-faso-red",
};

/**
 * Statut des données (spec §13).
 * Le nombre de courses provient de l'API — jamais codé en dur.
 */
export function DataStatus({ status }: { status: DataStatusModel }) {
  const isError = status.status === "ERROR";

  return (
    <div className="border-t border-white/[0.07] px-4 py-3.5">
      <div className="flex items-center gap-2">
        {status.status === "SYNCING" ? (
          <RefreshCw size={11} className="shrink-0 animate-spin text-faso-gold" aria-hidden="true" />
        ) : isError ? (
          <AlertCircle size={11} className="shrink-0 text-faso-red" aria-hidden="true" />
        ) : (
          <span
            aria-hidden="true"
            className={cn("h-[7px] w-[7px] shrink-0 rounded-full", DOT_CLASS[status.status])}
            style={{ boxShadow: "0 0 0 3px rgba(11,175,88,.16)" }}
          />
        )}
        <span className="text-[11.5px] font-medium leading-none text-white/85">
          {SYNC_STATUS_LABEL[status.status]}
        </span>
      </div>

      <div className="mt-1.5 pl-[15px] text-[10.5px] leading-[16px] text-white/45">
        <div>{formatLastUpdate(status.lastUpdatedAt)}</div>
        <div className="truncate">
          {status.source}
          {/* Le volume n'est affiché que lorsqu'il est réellement connu. */}
          {status.raceCount > 0 ? ` · ${formatCount(status.raceCount)} courses` : ""}
        </div>
      </div>
    </div>
  );
}
