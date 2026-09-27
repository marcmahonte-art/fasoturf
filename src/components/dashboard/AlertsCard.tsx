import { Link } from "react-router-dom";
import { ArrowRight, Bell, Info } from "lucide-react";
import { DataOriginBadge } from "../ui/DataOriginBadge";
import type { NotificationSummary } from "../../types/performance";

/**
 * Carte « Alertes » de la colonne de droite (spec §48).
 *
 * Le compteur provient de `notifications.unreadCount`. Tant qu'aucun compte
 * utilisateur n'existe, le bloc est **indisponible** — ce n'est pas la même
 * chose qu'un compteur à zéro, et l'interface le dit (spec §40).
 */
export function AlertsCard({ notifications }: { notifications: NotificationSummary }) {
  const count = notifications.unreadCount;
  const unavailable = !notifications.configured;

  return (
    <section
      aria-labelledby="alerts-title"
      className="rounded-[12px] border border-faso-danger-line bg-[#FDF3F3] p-4"
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <span
            aria-hidden="true"
            className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-faso-danger-soft"
          >
            <Bell size={16} strokeWidth={2.1} className="text-faso-red" />
          </span>
          <h2 id="alerts-title" className="text-[14px] font-bold leading-none text-faso-text">
            Alertes
          </h2>
        </div>
        {!unavailable && <DataOriginBadge origin={notifications.origin} />}
      </div>

      {unavailable ? (
        <>
          <p className="mt-2.5 flex items-start gap-2 text-[11.5px] leading-[17px] text-faso-muted">
            <Info size={12} aria-hidden="true" className="mt-[3px] shrink-0 text-faso-muted" />
            <span>
              Les alertes sont rattachées à un compte utilisateur, qui n'existe pas encore.
              Aucun compteur n'est affiché tant que cette fonction n'est pas branchée.
            </span>
          </p>

          <Link
            to="/dashboard"
            className="mt-3 inline-flex items-center gap-1 text-[12px] font-semibold text-faso-muted hover:text-faso-text"
          >
            En savoir plus
            <ArrowRight size={12} aria-hidden="true" />
          </Link>
        </>
      ) : (
        <>
          <p className="mt-2.5 text-[26px] font-bold leading-none tracking-[-0.6px] text-faso-text">
            {count}
          </p>
          <p className="mt-1.5 text-[12px] text-faso-muted">
            {count > 1 ? "Nouvelles notifications" : "Nouvelle notification"}
          </p>

          <Link
            to="/dashboard"
            className="mt-2.5 inline-flex items-center gap-1 text-[12px] font-semibold text-faso-red hover:brightness-90"
          >
            Voir mes alertes
            <ArrowRight size={12} aria-hidden="true" />
          </Link>
        </>
      )}
    </section>
  );
}
