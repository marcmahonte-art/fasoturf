import type { SVGProps } from "react";

/**
 * Icône « cheval ».
 *
 * Lucide React (v1.46) ne fournit pas d'icône `Horse`. La spec autorise
 * explicitement une icône sémantiquement proche ; plutôt qu'un pictogramme
 * approximatif, on réutilise la silhouette de cheval déjà présente dans les
 * assets du projet (`src/assets/horse-runner.svg`), inlinée ici pour pouvoir
 * hériter de `currentColor` comme les icônes Lucide voisines.
 */
export function HorseIcon({ size = 16, ...rest }: SVGProps<SVGSVGElement> & { size?: number }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 32 24"
      width={size}
      height={size * (24 / 32)}
      fill="currentColor"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      <path d="M3 14 C3 11 5 9 8 8 L11 7 L14 6 L17 5 L20 5 L23 6 L25 7 L27 6 L29 4 L30 6 L28 9 L25 11 L23 10 L20 11 L17 12 L14 13 L11 13 L8 12 L5 13 L4 15 Z M16 8 L17 6 L19 5 L20 7 L19 9 Z M11 14 L12 17 L10 19 L9 17 Z M20 13 L21 16 L19 18 L18 16 Z" />
    </svg>
  );
}
