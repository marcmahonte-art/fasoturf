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
  terrain: "Bon" | "Souple" | "Lourd" | "Très souple" | string;
  starters: number;
  time: string;
  status: string;
  hasResult: boolean;
  favoriteOdds: number;
  /** couleur d'accent du petit cheval (Burkina palette) */
  accent: "green" | "gold" | "red";
  runners: Runner[];
};

export const races: Race[] = rawRaces as Race[];