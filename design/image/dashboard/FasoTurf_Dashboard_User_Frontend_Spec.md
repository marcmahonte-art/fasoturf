# FasoTurf --- Spécification Frontend --- Dashboard User

**Document:** spécification fonctionnelle et UI/UX du Dashboard
utilisateur\
**Produit:** FasoTurf --- *La data des courses*\
**Type:** application SaaS d'analyse hippique\
**Audience:** développeur Frontend senior / équipe produit\
**Référence visuelle:** maquette fournie `DASHBOARD USER.png` --- 1536 ×
1024 px\
**Stack cible:** React + TypeScript + Tailwind CSS + Lucide React\
**Police:** Inter\
**Statut:** spécification de référence pour implémentation

------------------------------------------------------------------------

## 1. Objectif de la page

Le Dashboard User est la page d'accueil authentifiée de FasoTurf.

Il doit permettre à un utilisateur connecté de comprendre en quelques
secondes :

1.  où il se trouve dans l'application ;
2.  quelles courses sont disponibles ;
3.  quelles courses il suit ;
4.  quelles analyses/pronostics sont disponibles ;
5.  comment évoluent ses performances ;
6.  quels résultats récents sont disponibles ;
7.  quel est son statut d'abonnement ;
8.  quelles fonctionnalités principales sont accessibles.

La page ne doit pas ressembler à un bookmaker ou à un casino.
L'interface doit communiquer :

-   data ;
-   analyse ;
-   intelligence artificielle ;
-   précision ;
-   confiance ;
-   produit SaaS premium.

Le ton visuel doit rester **sobre, professionnel, sportif et
technologique**.

------------------------------------------------------------------------

# 2. Principes UX

## 2.1 Hiérarchie

La hiérarchie principale est :

**Navigation → contexte utilisateur → prochaine course → performances →
courses à suivre → pronostics → résultats → accès rapides →
abonnement.**

Le Dashboard doit privilégier les informations actionnables.

## 2.2 Actions principales

Les CTA les plus importants :

-   `Voir la course`
-   `Voir l'analyse`
-   `Voir les pronostics`
-   `Voir toutes les courses`
-   `Voir le détail`
-   `Gérer`
-   `Découvrir FasoTurf Pro`

## 2.3 Règle importante

Les données de démonstration de la maquette ne doivent pas être
présentées comme des résultats réels.

Le frontend doit distinguer clairement :

-   données réelles ;
-   prédictions ;
-   résultats officiels ;
-   données de démonstration ;
-   statistiques utilisateur.

Le moteur Hippo Engine impose notamment une séparation stricte entre
donnée réelle, démonstration, prédiction et résultat.

------------------------------------------------------------------------

# 3. Architecture générale

``` text
┌────────────────────────────────────────────────────────────────────┐
│ SIDEBAR 245 px │                  TOPBAR                           │
│                │                                                    │
│ Logo           │ Search                         Notification User  │
│                ├────────────────────────────────────────────────────┤
│ Dashboard      │                                                    │
│ Pronostics     │ Hero / prochaine course       Performances        │
│ Courses        │                                                    │
│ Chevaux        │                                                    │
│ Jockeys        │                                                    │
│ Statistiques   │                                                    │
│ Analyses IA    │                                                    │
│ Abonnement     │                                                    │
│                │                                                    │
│ Pro Card       │ Courses à suivre              Alerts / Top 5       │
│                │                                                    │
│ Data status    │ CTA Pro                       Accès rapides       │
└────────────────────────────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 4. Dimensions de référence

La maquette de référence est en **1536 × 1024 px**.

## 4.1 Layout desktop

``` text
Viewport
├── Sidebar: 245 px
└── Main: calc(100vw - 245px)
```

Sidebar :

-   largeur : `245px`
-   hauteur : `100vh`
-   position : `fixed`
-   `left: 0`
-   `top: 0`
-   `overflow-y: auto`

Main :

-   `margin-left: 245px`
-   largeur : `calc(100vw - 245px)`
-   min-height : `100vh`

Contenu principal :

``` css
max-width: 1280px;
margin: 0 auto;
padding: 0 24px 32px;
```

À 1536 px :

``` text
245 sidebar
+
24 left
+
1280 content
+
24 right
=
1573
```

En pratique, le container doit utiliser :

``` css
width: min(100% - 48px, 1280px);
```

et s'adapter dynamiquement.

------------------------------------------------------------------------

# 5. Design tokens

## 5.1 Couleurs

### Brand

``` text
Faso Green       #087F3E
Faso Green Dark  #05632F
Deep Green       #003D2A
Accent Green     #0BAF58
```

### Accents

``` text
Gold             #F2C94C
Red              #D64545
```

### Interface

``` text
Text             #17221C
Muted            #68736D
Border           #DCE3DF
Page background  #F7F9F8
White            #FFFFFF
```

### États

``` text
Success:
  background: #E7F7EE
  text: #087F3E

Warning:
  background: #FFF7DF
  text: #9A7212

Danger:
  background: #FDECEC
  text: #D64545

Info:
  background: #EAF4FF
```

Ne pas multiplier les couleurs. Le vert FasoTurf doit rester dominant.

------------------------------------------------------------------------

# 6. Typographie

Police :

``` text
Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

## Échelle

``` text
Page title       32px / 38px / 700
Section title    20px / 26px / 700
Card title       15-16px / 20px / 650
Body             14px / 20px / 400
Small            12px / 17px / 400
Micro            11px / 15px / 500
Metric           25-28px / 32px / 700
```

La maquette utilise une typographie compacte afin de conserver beaucoup
de données sans donner une sensation de surcharge.

------------------------------------------------------------------------

# 7. Spacing system

Utiliser une grille basée sur 4 px :

``` text
4
8
12
16
20
24
32
40
48
64
```

Espacements principaux :

``` text
Topbar → hero                 26px
Hero → section                18px
Section → section              18px
Card padding                  16-24px
Element interne               8-16px
```

------------------------------------------------------------------------

# 8. Border radius

``` text
Small controls     8px
Buttons            9-10px
Cards              10-14px
Hero               10px
Badges             999px
Avatar             50%
```

Les cartes doivent être légèrement arrondies, mais pas excessivement «
mobile app ».

------------------------------------------------------------------------

# 9. Ombres

Utiliser des ombres très légères.

``` css
box-shadow:
  0 2px 8px rgba(0,0,0,.03),
  0 8px 24px rgba(0,61,42,.04);
```

Éviter les ombres fortes.

------------------------------------------------------------------------

# 10. Sidebar

## 10.1 Structure

La sidebar contient :

1.  Logo ;
2.  navigation ;
3.  bloc FasoTurf Pro ;
4.  statut des données.

``` text
SIDEBAR
│
├── Logo
│
├── Navigation
│   ├── Tableau de bord
│   ├── Pronostics
│   ├── Courses du jour
│   ├── Chevaux
│   ├── Jockeys / Entraîneurs
│   ├── Statistiques
│   ├── Analyses IA
│   └── Abonnement
│
├── Pro promotion
│
└── Data status
```

## 10.2 Logo

Zone :

``` text
~210px × 60px
```

Contenu :

-   icône cheval/logo FasoTurf ;
-   texte `FasoTurf` ;
-   baseline `La data des courses`.

Le logo doit être un composant réutilisable :

``` tsx
<FasoTurfLogo variant="sidebar" />
```

------------------------------------------------------------------------

# 11. Navigation

## 11.1 Items

``` text
Tableau de bord
Pronostics
Courses du jour
Chevaux
Jockeys / Entraîneurs
Statistiques
Analyses IA
Abonnement
```

## 11.2 Icônes Lucide

Utiliser uniquement Lucide React.

Suggestions :

``` text
Tableau de bord       House
Pronostics            Target
Courses du jour       CalendarDays
Chevaux               Horse
Jockeys / Entraîneurs UsersRound
Statistiques          ChartNoAxesColumnIncreasing
Analyses IA           BrainCircuit
Abonnement            Crown
```

Si une icône `Horse` n'est pas disponible dans la version Lucide
installée, utiliser une icône Lucide sémantiquement proche.

Ne pas utiliser :

-   Font Awesome ;
-   emojis ;
-   SVG décoratifs provenant de bibliothèques externes sans nécessité.

## 11.3 Item actif

Fond :

``` text
#087F3E
```

Texte :

``` text
#FFFFFF
```

Radius :

``` text
8px
```

Padding :

``` text
10px 12px
```

L'item actif doit être clairement identifiable.

------------------------------------------------------------------------

# 12. Bloc FasoTurf Pro

Position :

bas de sidebar, avant le statut des données.

Structure :

``` text
┌─────────────────────────────┐
│ 👑  FasoTurf Pro            │
│                             │
│ Accédez aux analyses        │
│ avancées, des pronostics    │
│ et plus encore.             │
│                             │
│ [ Découvrir → ]             │
└─────────────────────────────┘
```

Le rendu final doit utiliser l'icône `Crown` et non un emoji.

Style :

``` text
border: 1px solid #087F3E
background: transparent / deep green sidebar
```

CTA :

``` text
background: #087F3E
text: white
```

------------------------------------------------------------------------

# 13. Data status

En bas :

``` text
● Données mises à jour
  Aujourd'hui 10:24
  Base LONAB · 711 courses
```

Le nombre doit provenir de l'API.

Ne jamais hardcoder `711` en production.

Le statut peut devenir :

``` text
Données à jour
Synchronisation...
Dernière synchronisation...
Erreur de synchronisation
```

------------------------------------------------------------------------

# 14. Topbar

Hauteur cible :

``` text
76px
```

Structure :

``` text
┌─────────────────────────────────────────────────────────────┐
│ Search                            Bell       Avatar / User │
└─────────────────────────────────────────────────────────────┘
```

## Recherche

Placeholder :

``` text
Rechercher une course, un cheval, un jockey, un entraîneur...
```

Largeur :

``` text
480-520px
```

Style :

``` text
background: #EEF2F0
border: none
radius: 9px
```

Icône :

``` text
Search
```

Fonctionnalité attendue :

Recherche globale :

``` text
course
cheval
jockey
entraîneur
hippodrome
```

Le composant doit pouvoir afficher des suggestions.

------------------------------------------------------------------------

# 15. Notification

Icône :

``` text
Bell
```

Badge :

``` text
3
```

Le badge doit être généré depuis :

``` ts
unreadNotificationsCount
```

Interactions :

-   click → panneau notifications ;
-   état lu/non lu ;
-   lien vers la page concernée.

------------------------------------------------------------------------

# 16. User profile

Zone :

``` text
Avatar
Nom
Statut
Chevron
```

Exemple de données de maquette :

``` text
Moussa TRAORE
Membre FasoTurf
Pro
```

En production :

``` ts
user.firstName
user.lastName
user.avatarUrl
subscription.plan
```

Le menu utilisateur :

``` text
Mon profil
Paramètres
Abonnement
Déconnexion
```

------------------------------------------------------------------------

# 17. Hero Dashboard

## 17.1 Position

Le hero est la zone visuelle dominante.

Disposition desktop :

``` text
┌──────────────────────────────────────────────┐
│                                              │
│ Hero                                         │
│                                              │
│ Texte                      Course suivante   │
│                                              │
└──────────────────────────────────────────────┘
```

Largeur :

``` text
~860px
```

Hauteur :

``` text
266px
```

Dans la maquette, il est placé à gauche des performances.

------------------------------------------------------------------------

# 18. Hero background

Utiliser une image de course hippique en arrière-plan.

Le traitement doit être :

``` css
background-image:
  linear-gradient(
    90deg,
    rgba(0, 61, 42, .96),
    rgba(0, 61, 42, .72),
    rgba(0, 61, 42, .35)
  ),
  url(...);
```

Objectif :

-   conserver la visibilité du cheval ;
-   garantir la lisibilité du texte ;
-   garder l'identité verte.

Ne pas transformer le hero en publicité agressive.

------------------------------------------------------------------------

# 19. Hero contenu

Texte :

``` text
Bonjour Moussa 👋

Bienvenue sur votre espace
FasoTurf

Suivez les courses, analysez les données et profitez
de nos analyses et pronostics intelligents.
```

Pour la version production :

``` tsx
Bonjour {user.firstName}
```

Titre :

``` text
Bienvenue sur votre espace
FasoTurf
```

`FasoTurf` doit être mis en avant en vert clair/brand.

------------------------------------------------------------------------

# 20. Hero feature strip

En bas du hero :

``` text
Données fiables
Analyses précises
IA prédictive
Pronostics experts
```

Icônes :

``` text
Database
ChartNoAxesCombined
BrainCircuit
Target
```

Ces éléments sont des arguments produit, pas des métriques.

------------------------------------------------------------------------

# 21. Prochaine course

Carte flottante dans le hero.

Structure :

``` text
Prochaine course

R1 · C4
Ouagadougou

14:30

[ Voir la course → ]
```

Données :

``` ts
nextRace = {
  meeting,
  raceNumber,
  hippodrome,
  startTime,
  participants,
  distance,
  discipline
}
```

CTA :

``` text
Voir la course
```

La carte doit être liée à :

``` text
/races/:raceId
```

------------------------------------------------------------------------

# 22. Carte « Mes performances »

Position :

à droite du hero.

Largeur approximative :

``` text
390px
```

Structure :

``` text
Mes performances                 Voir le détail →

┌──────────┬──────────┬──────────┐
│ Taux      │ Top 3    │ Courses  │
│ réussite  │          │ analysées│
│ 56%       │ 78%      │ 42       │
└──────────┴──────────┴──────────┘

Mon solde / Abonnement

FasoTurf Pro
Actif jusqu'au...
                         [Gérer]
```

Important : éviter « solde » si FasoTurf n'est pas un portefeuille de
paris. Dans la version produit, préférer :

``` text
Mon abonnement
```

------------------------------------------------------------------------

# 23. Métriques utilisateur

Trois KPI :

### Taux de réussite

``` text
56%
+12%
sur 30 jours
```

### Top 3

``` text
78%
+8%
sur 30 jours
```

### Courses analysées

``` text
42
ce mois
```

Les valeurs sont dynamiques.

Interface :

``` ts
type UserPerformance = {
  successRate: number;
  successRateDelta: number;
  top3Rate: number;
  top3Delta: number;
  racesAnalyzed: number;
  period: "7d" | "30d" | "month";
}
```

------------------------------------------------------------------------

# 24. Important --- définition des performances

Le frontend doit afficher la définition de la métrique via tooltip.

Exemple :

``` text
Taux de réussite
Proportion de sélections évaluées comme réussies
selon la définition de performance FasoTurf.
```

Ne pas appeler automatiquement une statistique « taux de réussite » si
le backend n'a pas défini précisément le calcul.

------------------------------------------------------------------------

# 25. Section « Courses à suivre »

C'est la section centrale du dashboard.

Titre :

``` text
Courses à suivre
```

Action :

``` text
Voir toutes →
```

Chaque course est représentée par une ligne/card horizontale.

------------------------------------------------------------------------

# 26. Course Follow Card

Structure :

``` text
┌─────────────────────────────────────────────────────────────┐
│ R1 · C4                                                     │
│ Paris-Vincennes                                             │
│                                                             │
│ 14 partants    2 700 m         🕘 13h55                    │
│                                Quarté                      │
│                                                             │
│                            [image] [Voir l'analyse →]       │
└─────────────────────────────────────────────────────────────┘
```

En production :

``` text
Réunion
Course
Hippodrome
Nombre de partants
Distance
Heure
Type de jeu / discipline
Image
CTA
```

------------------------------------------------------------------------

# 27. Données course

Type TypeScript :

``` ts
type RaceSummary = {
  id: string;
  meetingNumber: number;
  raceNumber: number;
  hippodrome: string;
  participantCount: number;
  distanceMeters: number;
  startTime: string;
  betType?: "Tiercé" | "Quarté" | "Quinté+" | "Couplé";
  discipline?: string;
  imageUrl?: string;
  status: "upcoming" | "live" | "finished";
};
```

Le frontend ne doit pas déduire le type de jeu à partir du nombre de
chevaux.

------------------------------------------------------------------------

# 28. États des courses

## Upcoming

``` text
Voir l'analyse
```

## Live

``` text
● EN DIRECT
Voir la course
```

## Finished

``` text
Résultat
Voir l'analyse
```

## Suspended / cancelled

``` text
Course suspendue
```

------------------------------------------------------------------------

# 29. Top 5 des pronostics du jour

La maquette affiche une colonne droite.

Titre :

``` text
Top 5 des pronostics du jour
```

Action :

``` text
Voir tous →
```

Structure :

``` text
01  Roi de Kaya        78%   P1   2.4
02  Belle du Sahel    65%   P1   3.1
03  Diamant Noir      58%   P1   4.2
04  Lady Burkina      52%   P1   5.8
05  Tchadien          48%   P1   7.0
```

------------------------------------------------------------------------

# 30. Probabilités

Le moteur Hippo Engine doit pouvoir fournir des probabilités de :

``` text
WIN
TOP3
TOP5
```

Le frontend doit afficher la métrique explicitement.

Exemple :

``` text
78%
Probabilité victoire
```

et non simplement :

``` text
78%
```

sans contexte.

------------------------------------------------------------------------

# 31. Principe de confiance

Le moteur doit exposer un niveau de confiance.

Exemple :

``` ts
type Prediction = {
  horseId: string;
  horseName: string;
  winProbability?: number;
  top3Probability?: number;
  top5Probability?: number;
  rank: number;
  confidence?: number;
  modelVersion: string;
  predictionVersion: string;
};
```

Le frontend peut afficher :

``` text
Confiance élevée
Confiance moyenne
Confiance faible
```

Uniquement si cette classification est définie côté moteur.

------------------------------------------------------------------------

# 32. Ne pas surpromettre

Le Dashboard ne doit jamais afficher :

``` text
Gagnant garanti
100% sûr
Cheval certain
Pronostic infaillible
```

Le moteur Hippo Engine indique explicitement que les statistiques
doivent porter leur période, leur volume et leur méthode et interdit la
surpromesse.

------------------------------------------------------------------------

# 33. Section CTA Pro

La maquette contient un grand bandeau :

``` text
Des données fiables.
Des analyses précises.
Des décisions éclairées.

FasoTurf, votre allié pour mieux comprendre
les courses hippiques.

[ Découvrir FasoTurf Pro → ]
```

Background :

``` text
gradient green
```

avec image cheval en transparence.

Le message doit rester orienté **analyse/data**, pas incitation directe
au pari.

------------------------------------------------------------------------

# 34. Responsive

## Desktop ≥ 1280

Layout :

``` text
Sidebar
Main
  Hero + Performance
  Courses + Right rail
```

## Tablet 768--1279

Sidebar :

-   compacte ;
-   icônes + tooltip ;
-   possibilité de collapse.

Layout :

``` text
Hero
Performance
Courses
Top 5
CTA
```

## Mobile \< 768

Sidebar :

-   remplacée par header + menu drawer.

Topbar :

``` text
Logo | Search | Bell
```

Hero :

``` text
1 colonne
```

Performance :

``` text
3 KPI en grille
```

Courses :

``` text
1 colonne
```

Top 5 :

``` text
1 colonne
```

------------------------------------------------------------------------

# 35. Breakpoints Tailwind

``` text
sm: 640px
md: 768px
lg: 1024px
xl: 1280px
2xl: 1536px
```

Comportement :

``` text
< lg     → navigation compacte
< md     → layout une colonne
< sm     → cartes pleine largeur
```

------------------------------------------------------------------------

# 36. Composants React

Arborescence recommandée :

``` text
src/
├── app/
│   └── dashboard/
│       └── page.tsx
│
├── components/
│   └── dashboard/
│       ├── DashboardLayout.tsx
│       ├── Sidebar.tsx
│       ├── SidebarNav.tsx
│       ├── Topbar.tsx
│       ├── GlobalSearch.tsx
│       ├── NotificationBell.tsx
│       ├── UserMenu.tsx
│       ├── WelcomeHero.tsx
│       ├── NextRaceCard.tsx
│       ├── PerformanceCard.tsx
│       ├── PerformanceMetrics.tsx
│       ├── FollowedRaces.tsx
│       ├── RaceFollowCard.tsx
│       ├── PredictionTop5.tsx
│       ├── PredictionRow.tsx
│       ├── ProBanner.tsx
│       ├── QuickAccess.tsx
│       └── DataStatus.tsx
│
├── components/
│   └── ui/
│       ├── Button.tsx
│       ├── Card.tsx
│       ├── Badge.tsx
│       ├── Avatar.tsx
│       ├── Progress.tsx
│       └── Tooltip.tsx
│
├── lib/
│   ├── api.ts
│   ├── formatters.ts
│   └── utils.ts
│
└── types/
    ├── race.ts
    ├── prediction.ts
    ├── user.ts
    └── performance.ts
```

------------------------------------------------------------------------

# 37. Composant Card générique

Toutes les cartes doivent partager un composant :

``` tsx
<Card>
  <CardHeader />
  <CardContent />
  <CardFooter />
</Card>
```

Props :

``` ts
type CardProps = {
  variant?: "default" | "soft" | "dark" | "hero";
  padding?: "none" | "sm" | "md" | "lg";
  interactive?: boolean;
};
```

------------------------------------------------------------------------

# 38. Boutons

## Primary

``` text
background: #087F3E
color: white
```

Hover :

``` text
background: #05632F
```

## Secondary

``` text
background: #FFFFFF
border: #DCE3DF
color: #17221C
```

## Gold CTA

À réserver à :

``` text
FasoTurf Pro
premium
abonnement
```

Ne pas utiliser le jaune partout.

------------------------------------------------------------------------

# 39. Data fetching

Le Dashboard ne doit pas contenir les données en dur.

Prévoir :

``` ts
GET /api/dashboard
```

Réponse :

``` ts
type DashboardResponse = {
  user: UserSummary;
  nextRace: RaceSummary | null;
  followedRaces: RaceSummary[];
  topPredictions: Prediction[];
  performance: UserPerformance;
  notifications: NotificationSummary;
  subscription: SubscriptionSummary;
  dataStatus: DataStatus;
};
```

------------------------------------------------------------------------

# 40. États API

Chaque widget doit gérer :

### Loading

Skeleton.

### Success

Affichage normal.

### Empty

Exemple :

``` text
Aucune course à suivre
Explorez les courses du jour.
```

### Error

``` text
Impossible de charger les courses.
[ Réessayer ]
```

Ne pas afficher de faux chiffres en cas d'erreur.

------------------------------------------------------------------------

# 41. Skeleton loading

Le skeleton doit reproduire la structure de la carte.

Exemple :

``` text
Hero skeleton
Performance skeleton
Race card skeleton
Prediction row skeleton
```

Animation :

``` text
animate-pulse
```

------------------------------------------------------------------------

# 42. Accessibilité

Obligatoire :

-   navigation clavier ;
-   focus visible ;
-   contraste suffisant ;
-   labels sur boutons icon-only ;
-   `aria-label` pour notification ;
-   `aria-current="page"` pour menu actif ;
-   textes alternatifs sur images ;
-   ne pas utiliser la couleur seule pour indiquer un état.

Exemple :

``` tsx
<button
  aria-label="Afficher les notifications"
>
  <Bell />
</button>
```

------------------------------------------------------------------------

# 43. Navigation

Routes recommandées :

``` text
/dashboard
/pronostics
/courses
/courses/:raceId
/chevaux
/chevaux/:horseId
/jockeys
/entraineurs
/statistiques
/analyses
/abonnement
/profile
/settings
```

CTA :

``` text
Voir la course
→ /courses/:raceId

Voir l'analyse
→ /analyses/:raceId

Voir tous les pronostics
→ /pronostics
```

------------------------------------------------------------------------

# 44. Intégration Hippo Engine

Le Dashboard doit être une couche de présentation au-dessus du moteur.

Architecture :

``` text
LONAB
  ↓
Data ingestion
  ↓
Normalization
  ↓
Master database
  ↓
Feature engineering
  ↓
Hippo Engine
  ↓
Prediction Service
  ↓
API
  ↓
FasoTurf Dashboard
```

Le README fourni indique que le moteur expose notamment :

``` text
generate_prediction(raceId)
```

et une sortie API via :

``` text
engine.as_api_payload()
```

Le frontend doit consommer le contrat API et ne jamais recalculer les
probabilités.

------------------------------------------------------------------------

# 45. Version du modèle

Pour les analyses IA, prévoir une information technique discrète :

``` text
Modèle v1.2
Données arrêtées à 10:20
```

ou dans un tooltip :

``` text
Prediction version
Model version
Timestamp
```

Le moteur prévoit déjà :

``` text
model_version
prediction_version
```

------------------------------------------------------------------------

# 46. Explicabilité IA

Une analyse détaillée doit pouvoir expliquer le classement.

Exemple :

``` text
Pourquoi ce cheval est classé #1 ?

+ Forme récente
+ Performance sur cette distance
+ Performance sur cet hippodrome
+ Jockey
+ Entraîneur
+ Historique du couple
```

Important :

les facteurs affichés doivent venir des features réellement calculées.

Ne pas inventer une explication marketing.

Le moteur Hippo Engine indique que le RANK expose ses contributions et
que les facteurs doivent être dérivés des features calculées.

------------------------------------------------------------------------

# 47. Page Dashboard --- ordre de rendu

Ordre exact recommandé :

``` text
1. DashboardLayout
2. Topbar
3. Hero + Performance
4. Courses à suivre
5. Right rail :
   - Alertes
   - Top 5 pronostics
   - Accès rapides
6. Pro banner
```

Sur desktop, la grille principale :

``` text
grid-template-columns: minmax(0, 1fr) 390px;
gap: 20px;
```

Hero :

``` text
grid-column: 1;
```

Performance :

``` text
grid-column: 2;
grid-row: 1;
```

Courses :

``` text
grid-column: 1;
```

Right rail :

``` text
grid-column: 2;
```

------------------------------------------------------------------------

# 48. Right rail

## Alertes

``` text
┌──────────────────────────┐
│ 🔔 Alertes               │
│                          │
│ 2                        │
│ Nouvelles notifications  │
│                          │
│ Voir mes alertes →       │
└──────────────────────────┘
```

## Top 5

Carte compacte.

## Accès rapides

``` text
Chevaux
Pronostics
Statistiques

Jockeys
Entraîneurs
Hippodromes
```

------------------------------------------------------------------------

# 49. Quick Access

Chaque item :

``` text
Icon
Title
Description
```

Exemples :

``` text
Chevaux
Rechercher un cheval

Pronostics
Mes sélections

Statistiques
Voir les analyses

Jockeys
Profils & stats

Entraîneurs
Profils & stats

Hippodromes
Tous les hippodromes
```

Ces cartes doivent être cliquables.

------------------------------------------------------------------------

# 50. Données et terminologie

Utiliser la terminologie métier FasoTurf :

``` text
Course
Réunion
Partants
Arrivée
Hippodrome
Cheval
Jockey
Entraîneur
Pronostic
Probabilité
Top 3
Top 5
Quinté
Quarté
Tiercé
Analyse
Historique
Performance
```

Éviter de transformer l'application en interface de bookmaker.

------------------------------------------------------------------------

# 51. Données réelles et démonstration

Le README du moteur indique actuellement :

``` text
711 courses exploitables
```

et un backtest sur :

``` text
228 courses de 2026
```

avec les résultats publiés dans le README.

Ces chiffres peuvent servir à une page interne de transparence /
statistiques, mais **ne doivent pas être injectés automatiquement dans
le Dashboard utilisateur comme des KPI personnels**.

------------------------------------------------------------------------

# 52. Performance actuelle du moteur

Le README fournit les mesures suivantes :

``` text
Gagnant trouvé
18.0 %

Favori marché
23.2 %

Précision Top 3
33.0 %

Favori marché
36.0 %

Brier Top3
0.146
```

Validation :

``` text
WIN
ROC-AUC  0.677
Brier    0.062
Log loss 0.236

TOP3
ROC-AUC  0.675
Brier    0.148
Log loss 0.464

TOP5
ROC-AUC  0.658
Brier    0.208
Log loss 0.603
```

Ces chiffres sont des mesures du moteur, pas des promesses commerciales.

Ils doivent être présentés avec :

-   période ;
-   volume ;
-   méthode ;
-   statut hors-échantillon.

------------------------------------------------------------------------

# 53. Ce que le Dashboard ne doit PAS faire

Ne pas afficher :

``` text
✓ Gain garanti
✓ Pari gagnant garanti
✓ 95% de réussite sans définition
✓ Le meilleur cheval garanti
✓ IA infaillible
✓ Vous allez gagner
```

Ne pas créer une esthétique :

``` text
casino
bookmaker
machine à sous
jackpot
```

FasoTurf doit être positionné comme :

``` text
data + analytics + intelligence hippique
```

------------------------------------------------------------------------

# 54. Performance frontend

Objectifs :

``` text
LCP < 2.5s
CLS < 0.1
INP < 200ms
```

Techniques :

-   images WebP/AVIF ;
-   lazy loading des images hors viewport ;
-   éviter les grosses images non compressées ;
-   code splitting ;
-   cache API ;
-   skeleton plutôt que blocage ;
-   ne pas charger les charts avant leur visibilité.

------------------------------------------------------------------------

# 55. Images

Les images de chevaux doivent être :

``` text
object-fit: cover;
border-radius: 8px;
```

Ratio recommandé pour les miniatures :

``` text
16:9
```

Hero :

``` text
cover
center
```

Ne jamais étirer une image.

------------------------------------------------------------------------

# 56. Animations

Animations très discrètes.

Autorisé :

``` text
hover card
button hover
skeleton
dropdown
notification badge
```

Durée :

``` text
150–250ms
```

Easing :

``` text
ease-out
```

Éviter :

-   animations permanentes ;
-   gros zoom ;
-   bounce ;
-   effets casino ;
-   glow excessif.

------------------------------------------------------------------------

# 57. Exemple de structure JSX

``` tsx
export default function DashboardPage() {
  return (
    <DashboardLayout>
      <Topbar />

      <main className="space-y-5">
        <section className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_390px] gap-5">
          <WelcomeHero />
          <PerformanceCard />
        </section>

        <section className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_390px] gap-5">
          <div className="space-y-5">
            <FollowedRaces />
            <ProBanner />
          </div>

          <aside className="space-y-5">
            <AlertsCard />
            <PredictionTop5 />
            <QuickAccess />
          </aside>
        </section>
      </main>
    </DashboardLayout>
  );
}
```

------------------------------------------------------------------------

# 58. Exemple de modèle de données

``` ts
interface DashboardData {
  user: {
    id: string;
    firstName: string;
    lastName: string;
    avatarUrl?: string;
  };

  subscription: {
    plan: "FREE" | "PRO";
    status: "ACTIVE" | "EXPIRED" | "CANCELLED";
    expiresAt?: string;
  };

  nextRace: RaceSummary | null;

  followedRaces: RaceSummary[];

  predictions: Prediction[];

  performance: UserPerformance;

  alerts: {
    unreadCount: number;
    items: Notification[];
  };

  dataStatus: {
    status: "CURRENT" | "SYNCING" | "ERROR";
    lastUpdatedAt: string;
    source: string;
    raceCount: number;
  };
}
```

------------------------------------------------------------------------

# 59. Responsive mobile --- ordre

Sur mobile :

``` text
Header
↓
Hero
↓
Performance
↓
Prochaine course
↓
Courses à suivre
↓
Top 5 pronostics
↓
Alertes
↓
Accès rapides
↓
Pro banner
```

Les cartes doivent prendre :

``` text
width: 100%;
```

Les tableaux doivent devenir des cards.

------------------------------------------------------------------------

# 60. Gestion des erreurs

Erreur globale :

``` text
Une erreur est survenue.

Nous n'avons pas pu charger votre tableau de bord.

[ Réessayer ]
```

Erreur d'un widget :

``` text
Impossible de charger cette section.
[ Réessayer ]
```

Ne jamais faire échouer toute la page si une seule API secondaire est
indisponible.

------------------------------------------------------------------------

# 61. Tests frontend

Tests minimum :

### Navigation

-   Dashboard actif ;
-   routes correctes ;
-   menu mobile.

### Courses

-   liste ;
-   empty state ;
-   loading ;
-   error ;
-   course finished ;
-   course live.

### Pronostics

-   classement ;
-   probabilité ;
-   absence de données ;
-   modèle indisponible.

### User

-   FREE ;
-   PRO ;
-   abonnement expiré.

### Responsive

Tester :

``` text
375px
768px
1024px
1280px
1440px
1536px
1920px
```

------------------------------------------------------------------------

# 62. Checklist pixel-perfect

Avant livraison :

-   [ ] Sidebar = \~245 px
-   [ ] Header aligné
-   [ ] Logo correctement dimensionné
-   [ ] Navigation active verte
-   [ ] Hero correctement cropé
-   [ ] Overlay hero suffisamment sombre
-   [ ] Performance card alignée au hero
-   [ ] KPI lisibles
-   [ ] Courses correctement espacées
-   [ ] Miniatures 16:9
-   [ ] CTA verts
-   [ ] Gold uniquement pour Pro
-   [ ] Right rail aligné
-   [ ] Cards avec border subtile
-   [ ] Aucun débordement horizontal
-   [ ] Responsive mobile
-   [ ] Focus clavier
-   [ ] Skeletons
-   [ ] Empty states
-   [ ] Error states

------------------------------------------------------------------------

# 63. Checklist architecture

-   [ ] Aucun chiffre métier hardcodé
-   [ ] API séparée des composants UI
-   [ ] Types TypeScript
-   [ ] Composants réutilisables
-   [ ] Données mock séparées des données API
-   [ ] Gestion loading/error/empty
-   [ ] Aucun calcul ML dans React
-   [ ] Aucun calcul de probabilité côté client
-   [ ] `model_version` conservé
-   [ ] `prediction_version` conservé
-   [ ] timestamps conservés
-   [ ] source/provenance conservée

------------------------------------------------------------------------

# 64. Contrat visuel final

Le Dashboard FasoTurf doit donner cette impression :

``` text
PREMIUM
   +
DATA
   +
IA
   +
COURSES HIPPIQUES
```

et non :

``` text
CASINO
   +
PARIS
   +
PROMESSES DE GAINS
```

La référence esthétique est une plateforme SaaS/data moderne, avec
l'identité visuelle du Burkina Faso intégrée de manière élégante.

------------------------------------------------------------------------

# 65. Résumé pour le développeur

**Construire un dashboard SaaS desktop-first en React + TypeScript +
Tailwind + Lucide React, basé sur la maquette 1536×1024.**

Structure :

``` text
SIDEBAR
  Logo
  Navigation
  FasoTurf Pro
  Data status

TOPBAR
  Recherche
  Notifications
  Profil

MAIN
  Hero
  Performance
  Courses à suivre
  Alertes
  Top 5 pronostics
  Accès rapides
  Pro banner
```

Le frontend doit être prêt à consommer le moteur Hippo Engine via une
API.

**Le frontend présente les données ; il ne doit pas recréer la logique
ML.**

La priorité est :

1.  fidélité visuelle ;
2.  lisibilité ;
3.  données structurées ;
4.  explicabilité ;
5.  responsive ;
6.  accessibilité ;
7.  séparation stricte entre données réelles, prédictions et résultats ;
8.  absence de surpromesse.

------------------------------------------------------------------------

# 66. Référence technique du moteur

Le moteur fourni avec le projet est documenté comme :

> Hippo Engine --- moteur IA de pronostics hippiques : ingestion,
> features, modèles, value, fusion, génération de Quinté, backtest et
> traçabilité.

Il indique notamment :

``` text
RANK
TOP3
CATBOOST
Value Engine
Fusion Engine
Quinté
Tiercé / Quarté+
Confiance
Traçabilité
Backtest
API interne
```

Le Dashboard doit donc être conçu dès maintenant pour exposer ces
capacités progressivement sans devoir refaire son architecture UI.

------------------------------------------------------------------------

# 67. Definition of Done

La page est considérée terminée lorsque :

``` text
[✓] reproduit fidèlement la maquette
[✓] fonctionne en 1536×1024
[✓] fonctionne en 1280×800
[✓] fonctionne sur tablette
[✓] fonctionne sur mobile
[✓] toutes les cartes ont loading/empty/error
[✓] navigation fonctionnelle
[✓] données typées
[✓] API découplée
[✓] aucune donnée métier inventée
[✓] aucune promesse de gain
[✓] accessibilité de base validée
[✓] performance acceptable
[✓] composants réutilisables
```

**Résultat attendu :** un Dashboard User FasoTurf qui ressemble à un
produit SaaS data professionnel et qui peut évoluer directement vers les
pages Courses, Chevaux, Jockeys, Entraîneurs, Pronostics, Analyses IA et
Statistiques.
