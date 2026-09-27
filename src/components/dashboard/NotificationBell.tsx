import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Bell } from "lucide-react";
import { cn } from "../../lib/utils";
import type { NotificationSummary } from "../../types/performance";
import { DataOriginBadge } from "../ui/DataOriginBadge";

/**
 * Cloche de notifications (spec §15).
 * Le compteur provient de `notifications.unreadCount` — jamais codé en dur.
 */
export function NotificationBell({ notifications }: { notifications: NotificationSummary }) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const count = notifications.unreadCount;

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) setOpen(false);
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        aria-label={
          count > 0 ? `Afficher les notifications, ${count} non lues` : "Afficher les notifications"
        }
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "relative grid h-9 w-9 place-items-center rounded-[9px] text-faso-text",
          "transition-colors duration-150 ease-out hover:bg-faso-field",
          open && "bg-faso-field",
        )}
      >
        <Bell size={18} strokeWidth={1.9} aria-hidden="true" />
        {count > 0 && (
          <span
            className={cn(
              "absolute right-[3px] top-[3px] grid h-[16px] min-w-[16px] place-items-center rounded-full",
              "bg-faso-red px-1 text-[9.5px] font-bold leading-none text-white",
            )}
          >
            {count > 9 ? "9+" : count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-[46px] z-50 w-[320px] animate-fade-in overflow-hidden rounded-[12px] border border-faso-border bg-white shadow-lift">
          <div className="flex items-center justify-between border-b border-faso-border-soft px-4 py-3">
            <h3 className="text-[13.5px] font-bold text-faso-text">Notifications</h3>
            <DataOriginBadge origin={notifications.origin} />
          </div>

          {notifications.items.length === 0 ? (
            <p className="px-4 py-5 text-[12px] text-faso-muted">Aucune notification.</p>
          ) : (
            <ul className="max-h-[280px] overflow-y-auto ft-scroll-light">
              {notifications.items.map((item) => (
                <li key={item.id} className="border-b border-faso-border-soft last:border-b-0">
                  <Link
                    to={item.href ?? "/dashboard"}
                    onClick={() => setOpen(false)}
                    className="flex items-start gap-3 px-4 py-3 transition-colors duration-150 hover:bg-faso-bg"
                  >
                    <span
                      aria-hidden="true"
                      className={cn(
                        "mt-1.5 h-[7px] w-[7px] shrink-0 rounded-full",
                        item.read ? "bg-faso-border" : "bg-faso-green",
                      )}
                    />
                    <span className="min-w-0">
                      <span className="block text-[12.5px] font-medium leading-[18px] text-faso-text">
                        {item.title}
                      </span>
                      {!item.read && (
                        <span className="mt-0.5 block text-[10.5px] font-semibold text-faso-green">
                          Non lue
                        </span>
                      )}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
