import rawRaces from "./realRaces.json";

export type Runner = {
  number: number;
  name: string;
  age: number;
  music: string;
  jockey: string;
  trainer: string;
  odds: number;
  marketProb: number | null;
  marketRank: number;
  isWinner: boolean;
  position: number | null;
};

export type Race = {
  id: string;
  date: string;
  reunion: string;
  course: string;
  hippodrome: string;
  title: string;
  discipline: string;
  distance: string;
  /** État du terrain — non exposé par l'API PMU, donc null (jamais inventé). */
  terrain?: string | null;
  /** Météo réelle de la réunion (API PMU). */
  meteo?: {
    temperature: number | null;
    nebulosite: string | null;
    ventForce: number | null;
    ventDirection: string | null;
  } | null;
  starters: number;
  time: string;
  status: string;
  hasResult: boolean;
  favoriteOdds: number;
  /** couleur d'accent du petit cheval (Burkina palette) */
  accent: "green" | "gold" | "red";
  /** true = course officielle LONAB du jour (Quinté+ / Quarté+ / Tiercé) */
  isLonab?: boolean;
  /** libellé du pari LONAB, ex. "Quinté+ / Quarté+ / Tiercé" */
  lonabBet?: string | null;
  /** pari mis en avant par le journal officiel LONAB ce jour-là : "4+1", "QUARTE", "TIERCE" */
  lonabJournalBet?: string | null;
  lonabJournalVenue?: string | null;
  /** ordre d'arrivée officiel, ex. "3-9-13-2-5" */
  arrivee?: string | null;
  /**
   * Provenance de `arrivee` :
   * - "lonab"     = arrivée officielle du socle LONAB (source de vérité)
   * - "positions" = ordre dérivé des positions des partants au socle
   * - null        = aucune arrivée collectée (course non encore courue)
   */
  arriveeSource?: "lonab" | "positions" | null;
  /** dividende Quinté+ pour 1 € */
  quinteDividende?: number | null;
  quinteGagnants?: number | null;
  runners: Runner[];
};

export const races: Race[] = rawRaces as Race[];