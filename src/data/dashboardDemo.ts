import type { Prediction } from "../types/prediction";
import type { NotificationSummary, UserPerformance } from "../types/performance";
import type { SubscriptionSummary, UserSummary } from "../types/user";

/**
 * ⚠️ DONNÉES DE DÉMONSTRATION — AUCUNE VALEUR MÉTIER.
 *
 * ⚠️ **Ce module n'est plus consommé par le Dashboard.** Depuis la connexion à
 * l'API réelle, `/dashboard` reçoit ses données de `GET /api/dashboard`.
 * Le fichier est conservé comme référence visuelle (il reproduit la maquette)
 * et comme filet de secours documenté — il ne doit jamais être réintroduit
 * silencieusement dans un chemin d'affichage.
 *
 * Le backend FasoTurf n'expose pas encore :
 *  - le profil utilisateur et son abonnement ;
 *  - les statistiques personnelles (définitions de « taux de réussite »
 *    et « Top 3 » non arrêtées côté moteur) ;
 *  - les notifications (rattachées à un compte).
 *
 * Ces valeurs portent toutes l'origine « demo ». Elles ne doivent JAMAIS être
 * présentées comme des résultats réels (spec §2.3, §51, §53).
 */

export const DEMO_USER: UserSummary = {
  id: "demo-user",
  firstName: "Moussa",
  lastName: "TRAORE",
  avatarUrl: null,
  statusLabel: "Membre FasoTurf",
};

export const DEMO_SUBSCRIPTION: SubscriptionSummary = {
  plan: "PRO",
  status: "ACTIVE",
  expiresAt: "2025-12-12",
  configured: false,
  origin: "demo",
};

export const DEMO_PERFORMANCE: UserPerformance = {
  successRate: 56,
  successRateDelta: 12,
  top3Rate: 78,
  top3Delta: 8,
  racesAnalyzed: 42,
  period: "30d",
  origin: "demo",
};

export const DEMO_NOTIFICATIONS: NotificationSummary = {
  unreadCount: 2,
  items: [
    {
      id: "demo-notif-1",
      title: "Le programme du jour est disponible",
      createdAt: "2026-09-16T08:10:00.000Z",
      read: false,
    },
    {
      id: "demo-notif-2",
      title: "Les arrivées de la réunion précédente sont publiées",
      createdAt: "2026-09-15T18:40:00.000Z",
      read: false,
    },
  ],
  configured: false,
  origin: "demo",
};

/** Top 5 de la maquette — noms et probabilités fictifs. */
export const DEMO_PREDICTIONS: Prediction[] = [
  {
    horseId: "demo-h-1",
    horseName: "Roi de Kaya",
    horseNumber: 4,
    winProbability: 78,
    rank: 1,
    confidence: "high",
    modelVersion: "v1.0-demo",
    predictionVersion: "demo",
    raceLabel: "R1 C4 · Ouagadougou",
    odds: 2.4,
    origin: "demo",
  },
  {
    horseId: "demo-h-2",
    horseName: "Belle du Sahel",
    horseNumber: 7,
    winProbability: 65,
    rank: 2,
    confidence: "high",
    modelVersion: "v1.0-demo",
    predictionVersion: "demo",
    raceLabel: "R2 C3 · Bobo-Dioulasso",
    odds: 3.1,
    origin: "demo",
  },
  {
    horseId: "demo-h-3",
    horseName: "Diamant Noir",
    horseNumber: 2,
    winProbability: 58,
    rank: 3,
    confidence: "medium",
    modelVersion: "v1.0-demo",
    predictionVersion: "demo",
    raceLabel: "R3 C5 · Koudougou",
    odds: 4.2,
    origin: "demo",
  },
  {
    horseId: "demo-h-4",
    horseName: "Lady Burkina",
    horseNumber: 9,
    winProbability: 52,
    rank: 4,
    confidence: "medium",
    modelVersion: "v1.0-demo",
    predictionVersion: "demo",
    raceLabel: "R4 C2 · Tenkodogo",
    odds: 5.8,
    origin: "demo",
  },
  {
    horseId: "demo-h-5",
    horseName: "Tchadien",
    horseNumber: 11,
    winProbability: 48,
    rank: 5,
    confidence: "low",
    modelVersion: "v1.0-demo",
    predictionVersion: "demo",
    raceLabel: "R5 C6 · Ouagadougou",
    odds: 7.0,
    origin: "demo",
  },
];
