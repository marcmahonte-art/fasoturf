/**
 * Provenance d'une donnée affichée dans l'interface.
 *
 * Le moteur Hippo Engine impose une séparation stricte entre donnée réelle,
 * démonstration, prédiction et résultat officiel (spec Dashboard §2.3).
 * Aucune donnée de démonstration ne doit pouvoir être confondue avec un
 * résultat réel : chaque bloc de l'interface porte explicitement son origine.
 */
export type DataOrigin =
  /** Donnée réelle issue du socle LONAB / PMU. */
  | "real"
  /** Résultat officiel (arrivée validée). */
  | "official"
  /** Sortie du moteur Hippo Engine (probabilité, classement). */
  | "prediction"
  /** Statistique propre à l'utilisateur (sélections, historique). */
  | "user"
  /** Donnée de démonstration — aucune valeur métier, jamais présentée comme réelle. */
  | "demo";

/** Libellé court affiché à côté du bloc concerné. */
export const DATA_ORIGIN_LABEL: Record<DataOrigin, string> = {
  real: "Données réelles",
  official: "Résultat officiel",
  prediction: "Prédiction moteur",
  user: "Vos statistiques",
  demo: "Démonstration",
};

/** Explication affichée en infobulle — jamais de surpromesse (spec §32). */
export const DATA_ORIGIN_HINT: Record<DataOrigin, string> = {
  real: "Donnée issue du socle LONAB / PMU, sans transformation.",
  official: "Arrivée officielle publiée par l'opérateur.",
  prediction:
    "Probabilité produite par le moteur Hippo Engine. Ce n'est pas une garantie de résultat.",
  user: "Calculée à partir de vos sélections enregistrées.",
  demo:
    "Donnée de démonstration : elle ne reflète aucune course, aucun cheval et aucun résultat réel.",
};
