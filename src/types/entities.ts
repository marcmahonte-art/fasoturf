/**
 * Types des entités du socle : chevaux, jockeys, entraîneurs, hippodromes.
 *
 * Miroir exact de `backend/schemas/entities.py`. Les taux ne sont renseignés
 * que si leur dénominateur est connu : un taux absent vaut `null`, jamais 0 %.
 */

export interface HorseSummary {
  id: string;
  name: string;
  starts: number | null;
  firstSeenDate: string | null;
  lastSeenDate: string | null;
  /** Variantes sexe/année de naissance rencontrées dans les sources. */
  sexBirthyearVariants: string | null;
  father: string | null;
  mother: string | null;
  coat: string | null;
  breed: string | null;
  /** Signal d'homonymie : plusieurs chevaux peuvent porter le même nom. */
  homonymRisk: string | null;
}

export interface HorseStatistics {
  starts: number;
  wins: number;
  top3: number;
  top5: number;
  /** Participations dont la position n'est pas connue (exclues des taux). */
  unknown: number;
  winRate: number | null;
  top3Rate: number | null;
}

export interface HorseRun {
  raceId: string;
  date: string;
  hippodrome: string | null;
  discipline: string | null;
  distanceMeters: number | null;
  title: string | null;
  number: number | null;
  position: number | null;
  odds: number | null;
}

export interface HorseDetail {
  horse: HorseSummary;
  statistics: HorseStatistics;
  recentRuns: HorseRun[];
}

export interface PersonSummary {
  id: string;
  name: string;
  role: string;
  appearances: number | null;
  resolutionConfidence: number | null;
}

export interface PersonStatistics {
  /** Nombre de participations (montes pour un jockey, partants pour un entraîneur). */
  mounts: number;
  wins: number;
  top3: number;
  unknown: number;
  winRate: number | null;
  top3Rate: number | null;
}

export interface PersonRun {
  raceId: string;
  date: string;
  hippodrome: string | null;
  discipline: string | null;
  distanceMeters: number | null;
  title: string | null;
  horseName: string | null;
  number: number | null;
  position: number | null;
  odds: number | null;
}

export interface PersonDetail {
  person: PersonSummary;
  statistics: PersonStatistics;
  recentRuns: PersonRun[];
}

export interface HippodromeSummary {
  id: string;
  name: string;
  country: string | null;
  races: number | null;
  isValid: boolean;
  qualityFlag: string | null;
}

export interface HippodromeDetail {
  hippodrome: HippodromeSummary;
  statistics: {
    races?: number;
    days?: number;
    avgDistance?: number | null;
    withResult?: number;
  };
}
