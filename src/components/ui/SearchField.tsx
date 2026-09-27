import { Search, X } from "lucide-react";
import { useState } from "react";
import { cn } from "../../lib/utils";

/**
 * Champ de recherche avec validation explicite.
 *
 * La recherche n'est **pas** déclenchée à chaque frappe : elle part à la
 * validation (touche Entrée ou bouton), ce qui évite d'interroger l'API pour
 * des préfixes inutiles et rend l'état de chargement lisible.
 */
export function SearchField({
  value,
  onSubmit,
  placeholder,
  label,
  className,
}: {
  /** Valeur initiale (issue de l'URL, par exemple). */
  value: string;
  onSubmit: (next: string) => void;
  placeholder?: string;
  label?: string;
  className?: string;
}) {
  const [draft, setDraft] = useState(value);
  const [syncedValue, setSyncedValue] = useState(value);

  // Ajustement **pendant le rendu** (pattern officiel React) plutôt que dans un
  // effet : quand la valeur de référence change (navigation, bouton retour), le
  // champ se resynchronise sans provoquer de rendu en cascade.
  if (value !== syncedValue) {
    setSyncedValue(value);
    setDraft(value);
  }

  return (
    <form
      role="search"
      className={cn("flex items-center gap-2", className)}
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(draft.trim());
      }}
    >
      <label className="relative flex h-[36px] min-w-0 flex-1 items-center">
        {label && <span className="sr-only">{label}</span>}
        <Search
          size={13}
          aria-hidden="true"
          className="pointer-events-none absolute left-2.5 text-faso-muted"
        />
        <input
          type="search"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={placeholder}
          aria-label={label ?? placeholder ?? "Rechercher"}
          className="h-full w-full rounded-[9px] border border-faso-border bg-white pl-8 pr-8 text-[12.5px] text-faso-text placeholder:text-faso-muted focus:border-faso-green/40 focus:outline-none"
        />
        {draft.length > 0 && (
          <button
            type="button"
            onClick={() => {
              setDraft("");
              onSubmit("");
            }}
            aria-label="Effacer la recherche"
            className="absolute right-2 grid h-5 w-5 place-items-center rounded-full text-faso-muted hover:bg-faso-bg hover:text-faso-text"
          >
            <X size={12} aria-hidden="true" />
          </button>
        )}
      </label>

      <button
        type="submit"
        className="inline-flex h-[36px] shrink-0 items-center justify-center rounded-[9px] bg-faso-green px-4 text-[13px] font-semibold text-white transition-colors duration-150 ease-out hover:bg-faso-green-dark focus-visible:outline-2 focus-visible:outline-offset-2"
      >
        Rechercher
      </button>
    </form>
  );
}
