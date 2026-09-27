import type { DataOrigin } from "./common";

/**
 * Niveau de confiance du moteur (spec §31).
 * La valeur est fournie telle quelle par le moteur — le frontend ne la dérive pas.
 */
export type ConfidenceLevel = string;

/**
 * Prédiction du moteur Hippo Engine.
 *
 * Le frontend est une couche de présentation : il ne recalcule JAMAIS
 * une probabilité (spec §44). Les valeurs proviennent du contrat API.
 *
 * Unité : `winProbability`, `top3Probability`, `top5Probability` et `valueEdge`
 * sont des **ratios** (0–1), tels que produits par le moteur. La conversion en
 * pourcentage est faite au moment de l'affichage.
 */
export interface Prediction {
  horseId: string;
  horseName: string;
  /** Numéro de partant (utilisé pour l'avatar et le lien vers la course). */
  horseNumber: number;
  winProbability?: number | null;
  top3Probability?: number | null;
  top5Probability?: number | null;
  rank: number;
  confidence?: string | null;
  modelVersion: string;
  predictionVersion: string;
  /** Contexte d'affichage : réunion · course · hippodrome. */
  raceLabel: string;
  /** Identifiant de la course concernée. */
  raceId?: string;
  /** Cote de référence affichée à titre informatif. */
  odds?: number | null;
  /** Écart entre la probabilité du moteur et celle du marché (ratio). */
  valueEdge?: number | null;
  factorsPositive?: string[];
  factorsNegative?: string[];
  origin: DataOrigin;
}
