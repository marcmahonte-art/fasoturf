import type { DataOrigin } from "./common";
import type { Prediction } from "./prediction";
import type { CoverageStats } from "./performance";

/** Réponse de `GET /api/predictions/race/{id}` lorsque le moteur est indisponible. */
export interface PredictionUnavailable {
  available: false;
  reason: string;
}

/**
 * Pronostic complet d'une course, produit par le moteur Hippo Engine.
 *
 * Le frontend n'en dérive aucun chiffre : tout est affiché tel quel (spec §44).
 */
export interface RacePrediction {
  raceId: string;
  raceLabel: string;
  modelVersion: string;
  predictionVersion: string;
  dataTimestamp: string | null;
  /** Ex. « DATA_PARTIAL », « DATA_FULL ». */
  dataQuality: string | null;
  confidence: string | null;
  confidenceReasons: string[];
  /** Numéros des chevaux par catégorie, tels que classés par le moteur. */
  bases: number[];
  chances: number[];
  outsiders: number[];
  quinte: number[];
  tierce: number[];
  quarte: number[];
  runners: Prediction[];
  origin: DataOrigin;
}

/**
 * Mesure statistique accompagnée de **son mode de calcul**.
 *
 * Une mesure n'est jamais publiée sans méthode, période et volume : c'est une
 * exigence du moteur (spec §52).
 */
export interface Measure {
  value: number | null;
  numerator: number | null;
  denominator: number | null;
  unit: string;
  method: string;
  period: string | null;
  volume: number;
}

export interface DisciplineStat {
  discipline: string;
  races: number;
  avgDistance: number | null;
}

export interface HippodromeStat {
  hippodrome: string;
  races: number;
  days: number;
}

export interface MonthStat {
  month: string;
  races: number;
}

export interface DataVersionItem {
  scope: string | null;
  version: string | null;
  sourceSha256: string | null;
  createdAt: string | null;
  notes: string | null;
}

/** Réponse de `GET /api/statistics`. */
export interface StatisticsOverview {
  coverage: CoverageStats;
  favouriteWinRate: Measure;
  oddsCoverage: Measure;
  resultCoverage: Measure;
  byDiscipline: DisciplineStat[];
  byHippodrome: HippodromeStat[];
  monthlyActivity: MonthStat[];
  dataVersions: DataVersionItem[];
}
