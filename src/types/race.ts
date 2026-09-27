import type { DataOrigin } from "./common";

/**
 * Résumé d'une course tel que consommé par le Dashboard.
 *
 * Le frontend ne déduit JAMAIS le type de pari du nombre de partants (spec §27) :
 * `betType` provient de la donnée ou reste indéfini.
 */
export type RaceStatus = "upcoming" | "live" | "finished" | "suspended";

export interface RaceSummary {
  id: string;
  /** Numéro de réunion (R1, R2…). */
  meetingNumber: number;
  /** Numéro de course dans la réunion (C1, C2…). */
  raceNumber: number;
  hippodrome: string;
  participantCount: number;
  distanceMeters: number;
  /** Heure de départ au format « 13h55 ». */
  startTime: string;
  betType?: string;
  discipline?: string;
  imageUrl?: string;
  status: RaceStatus;
  /** Date ISO (YYYY-MM-DD) — utile pour distinguer aujourd'hui / archive. */
  date: string;
  /** Vrai si la course appartient au programme officiel LONAB. */
  isLonab?: boolean;
  /** Provenance de l'enregistrement affiché. */
  origin: DataOrigin;
}

/** Journée de courses disponible (`GET /api/dates`). */
export interface DateItem {
  date: string;
  label: string;
  count: number;
  isToday: boolean;
}

/** Partant tel que renvoyé par `GET /api/races/{id}`. */
export interface RaceRunner {
  number: number;
  name: string;
  age: number | null;
  music: string;
  jockey: string;
  trainer: string;
  /** Cote décimale réelle — `null` si absente du socle. */
  odds: number | null;
  /** Probabilité implicite du marché, en pourcentage. */
  marketProb: number | null;
  marketRank: number | null;
  isWinner: boolean;
  position: number | null;
}

export interface RaceMeteo {
  temperature: number | null;
  nebulosite: string | null;
  ventForce: number | null;
  ventDirection: string | null;
}

/**
 * Détail complet d'une course (`GET /api/races/{id}`).
 *
 * `terrain` vaut toujours `null` : la source ne l'expose pas, et le backend
 * refuse de l'inventer. L'interface affiche « — » dans ce cas.
 */
export interface RaceDetail {
  id: string;
  date: string;
  reunion: string;
  course: string;
  hippodrome: string;
  title: string;
  discipline: string;
  distance: string;
  terrain: string | null;
  starters: number;
  time: string;
  status: string;
  hasResult: boolean;
  favoriteOdds: number;
  accent: string;
  runners: RaceRunner[];
  meteo: RaceMeteo | null;
  isLonab: boolean;
  lonabBet: string | null;
  lonabJournalBet: string | null;
  lonabJournalVenue: string | null;
  /** Ordre d'arrivée réel, `null` s'il n'est pas publié. */
  arrivee: string | null;
  /** « lonab » (arrivée officielle) ou « positions » (déduite des positions). */
  arriveeSource: string | null;
  quinteDividende: number | null;
  quinteGagnants: number | null;
}
