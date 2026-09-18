# FasoTurf — Home / Login
## Frontend Design Specification v1.0

> Spécification frontend de référence pour reproduire la maquette de la page d'accueil / connexion FasoTurf.
> Stack : React + TypeScript + Tailwind CSS + Lucide React + Inter.

---

# 1. Référence visuelle

## Artboard

- Width : `1536px`
- Height : `1024px`

La page est conçue en priorité pour un desktop `1536 × 1024`, puis doit être responsive.

## Technologies

```text
React
TypeScript
Tailwind CSS
Lucide React
Inter
```

## Icônes

Utiliser exclusivement Lucide React :

```tsx
import {
  Search,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  Bell,
  MapPin,
  Clock3,
  ChevronLeft,
  ChevronRight,
  Database,
  BrainCircuit,
  BarChart3,
  BellRing,
  CircleCheck,
  Menu
} from "lucide-react";
```

Ne pas utiliser Font Awesome.

---

# 2. Structure globale

```text
App
└── LoginHomePage
    ├── Background
    ├── Header
    ├── HeroContent
    │   ├── Brand
    │   ├── HeroTitle
    │   ├── HeroDescription
    │   ├── FeatureList
    │   └── Tagline
    ├── LoginCard
    └── LatestRacesSection
        ├── SectionHeader
        ├── RaceCarousel
        │   ├── RaceCard
        │   ├── RaceCard
        │   ├── RaceCard
        │   ├── RaceCard
        │   └── RaceCard
        └── CarouselControls
```

---

# 3. Page principale

La page entière utilise une image de course en background.

```css
min-height: 100vh;
width: 100%;
```

Tailwind :

```tsx
<div className="relative min-h-screen w-full overflow-hidden">
```

## Background

```tsx
<div className="absolute inset-0">
  <img
    src="/images/fasoturf-racing-bg.jpg"
    className="h-full w-full object-cover"
    alt=""
  />
</div>
```

---

# 4. Overlay du background

Le background doit être sombre afin de garantir la lisibilité.

```tsx
<div className="absolute inset-0 bg-[#001B16]/70" />

<div className="absolute inset-0 bg-gradient-to-r
  from-[#001B16]/95
  via-[#003D2A]/65
  to-[#001B16]/45"
/>
```

Objectif : le cheval doit rester visible au centre, mais le texte blanc doit toujours être parfaitement lisible.

---

# 5. Couleurs

```text
Faso Green       #087F3E
Faso Green Dark  #05632F
Faso Green Deep  #003D2A
Faso Accent      #0BAF58
Faso Gold        #F2C94C
Faso Red         #D64545

White            #FFFFFF
Text Dark        #17221C
Muted            #68736D
Border           #DCE3DF
Page Background  #F7F9F8
```

---

# 6. Header

## Dimensions

```text
top: 0
left: 0
right: 0
height: 96px
```

Container :

```tsx
<header className="
  relative
  z-20
  mx-auto
  flex
  h-[96px]
  max-w-[1396px]
  items-center
  justify-between
  px-0
">
```

À `1536px` :

```text
max-width : 1396px
marges horizontales ≈ 70px
```

---

# 7. Logo

Composition :

```text
Horse icon
+
FasoTurf
+
La data des courses
```

## Dimensions

```text
Logo total : environ 400px × 100px

Horse icon
Width  : 110px
Height : 100px

FasoTurf
Font size : 58px
Weight    : 700

Subtitle
Font size : 24px
Weight    : 400
```

## Texte

```text
FasoTurf
La data des courses
```

## Couleurs

```text
Faso → #FFFFFF
Turf → #0BAF58
Subtitle → #FFFFFF
```

---

# 8. Navigation

Position approximative :

```text
X ≈ 560px
Y ≈ 72px
```

Items :

```text
Accueil
Fonctionnalités
Tarifs
À propos
```

## Style

```text
font-size : 14px
font-weight : 400
color : white
```

Gap :

```text
36px
```

Tailwind :

```tsx
<nav className="flex items-center gap-9">
```

---

# 9. Navigation active

`Accueil` possède une petite ligne sous le texte.

```text
width  : 48px
height : 1px
color  : white
```

```tsx
<div className="relative pb-4">
  Accueil

  <span className="
    absolute
    bottom-0
    left-0
    h-px
    w-12
    bg-white
  " />
</div>
```

---

# 10. Hero layout

Le hero occupe environ :

```text
height ≈ 680px
```

Container :

```text
max-width : 1396px
margin : auto
```

Grid :

```text
colonne gauche : 58%
colonne droite : 42%
```

Tailwind :

```tsx
<div className="
  relative
  z-10
  mx-auto
  grid
  max-w-[1396px]
  grid-cols-[58%_42%]
">
```

---

# 11. Zone gauche

Position de référence :

```text
X ≈ 70px
Y ≈ 180px
Width ≈ 760px
```

---

# 12. Hero title

Texte :

```text
L’intelligence des courses
hippiques du Burkina.
```

La partie `du Burkina.` est verte.

## Dimensions

```text
font-size      : 42px
line-height    : 1.15
font-weight    : 700
letter-spacing : -0.8px
```

Tailwind :

```tsx
<h1 className="
  max-w-[720px]
  text-[42px]
  font-bold
  leading-[1.15]
  tracking-[-0.8px]
  text-white
">
  L’intelligence des courses
  <br />
  hippiques <span className="text-[#0BAF58]">du Burkina.</span>
</h1>
```

---

# 13. Hero description

Texte :

```text
FasoTurf vous offre des données fiables, des analyses précises
et des prédictions intelligentes pour mieux comprendre et
suivre les courses hippiques.
```

## Dimensions

```text
width       : 620px
font-size   : 17px
line-height : 1.55
font-weight : 400
```

Couleur :

```text
rgba(255,255,255,0.85)
```

Margin top :

```text
18px
```

---

# 14. Feature list

La liste commence environ à :

```text
Y ≈ 390px
```

Chaque feature :

```text
height ≈ 62px
```

Gap :

```text
14px
```

---

# 15. Feature icon

Dimensions :

```text
48 × 48px
border-radius : 50%
```

Exemple :

```tsx
<div className="
  flex
  h-12
  w-12
  shrink-0
  items-center
  justify-center
  rounded-full
  bg-[#087F3E]
">
```

Icon :

```text
20 × 20px
stroke-width : 2
```

---

# 16. Features

## Feature 1

Icon :

```tsx
<BarChart3 />
```

Titre :

```text
Pronostics & sélections
```

Description :

```text
Des analyses fiables pour vos jeux et vos décisions.
```

---

## Feature 2

Icon :

```tsx
<Database />
```

Couleur :

```text
#F2C94C
```

Titre :

```text
Base de données complète
```

Description :

```text
Chevaux, jockeys, entraîneurs, hippodromes...
```

---

## Feature 3

Icon :

```tsx
<BrainCircuit />
```

Titre :

```text
Analyses & IA
```

Description :

```text
Des modèles prédictifs basés sur les données et l’intelligence artificielle.
```

---

## Feature 4

Icon :

```tsx
<BellRing />
```

Couleur :

```text
#D64545
```

Titre :

```text
Alertes personnalisées
```

Description :

```text
Ne ratez plus aucune course importante.
```

---

# 17. Feature typography

Titre :

```text
font-size   : 16px
font-weight : 600
line-height : 1.3
```

Description :

```text
font-size   : 13px
font-weight : 400
line-height : 1.4
color       : rgba(255,255,255,.75)
```

---

# 18. Tagline

Position approximative :

```text
X = 70px
Y = 700px
```

Texte :

```text
Plus qu’un turf, une intelligence !
```

## Style

```text
font-size  : 25px
font-style : italic
color      : #0BAF58
```

Pour la version finale, une police script peut être utilisée uniquement pour cette phrase.

Exemple :

```css
font-family: "Dancing Script", cursive;
```

Inter reste la police principale.

---

# 19. Ligne décorative Burkina

Sous le slogan :

```text
──────────────
```

Avec trois couleurs :

```text
vert
jaune
rouge
```

Dimensions :

```text
width  : 105px
height : 3px
```

---

# 20. Login Card

Position de référence :

```text
X ≈ 968px
Y ≈ 123px
Width ≈ 510px
Height ≈ 620px
```

## Card

```tsx
<div className="
  w-[510px]
  rounded-[14px]
  bg-white
  p-[38px]
  shadow-[0_20px_60px_rgba(0,0,0,0.20)]
">
```

---

# 21. Login title

```text
Se connecter
```

Dimensions :

```text
font-size   : 29px
font-weight : 700
line-height : 1.2
```

Couleur :

```text
#17221C
```

---

# 22. Login description

```text
Accédez à votre espace pour consulter
les analyses et pronostics FasoTurf.
```

Dimensions :

```text
font-size   : 14px
line-height : 1.55
color       : #68736D
```

Margin :

```text
8px
```

---

# 23. Login form

Gap entre les champs :

```text
20px
```

---

# 24. Label

Exemple :

```text
Email ou numéro de téléphone
```

Dimensions :

```text
font-size   : 12px
font-weight : 500
color       : #17221C
```

Margin bottom :

```text
7px
```

---

# 25. Input

Dimensions :

```text
width  : 100%
height : 50px
```

Style :

```tsx
className="
  h-[50px]
  w-full
  rounded-[8px]
  border
  border-[#DCE3DF]
  bg-white
  px-4
  text-[14px]
  outline-none
  transition
  focus:border-[#087F3E]
  focus:ring-2
  focus:ring-[#087F3E]/10
"
```

---

# 26. Input icons

Email :

```tsx
<Mail size={18} strokeWidth={1.8} />
```

Position :

```text
left : 14px
```

Placeholder :

```text
exemple@fasoturf.bf ou 70 12 34 56
```

Couleur :

```text
#94A29A
```

---

# 27. Password

Label :

```text
Mot de passe
```

Placeholder :

```text
Votre mot de passe
```

Icon gauche :

```tsx
<Lock />
```

Icon droit :

```tsx
<Eye />
```

ou :

```tsx
<EyeOff />
```

---

# 28. Remember row

```text
margin-top : 12px
```

Layout :

```text
[✓] Se souvenir de moi              Mot de passe oublié ?
```

Font :

```text
12px
```

Checkbox :

```text
16 × 16px
```

Couleur :

```text
#087F3E
```

---

# 29. Login button

Dimensions :

```text
width  : 100%
height : 51px
```

Style :

```tsx
<button className="
  flex
  h-[51px]
  w-full
  items-center
  justify-center
  gap-2
  rounded-[8px]
  bg-[#087F3E]
  text-[14px]
  font-semibold
  text-white
  transition
  hover:bg-[#05632F]
">
  Se connecter
  <ArrowRight size={18} />
</button>
```

---

# 30. Separator

Après le bouton :

```text
────────────  OU  ────────────
```

Margin :

```text
24px 0
```

Texte :

```text
font-size : 12px
color : #9AA59F
```

---

# 31. Google button

Dimensions :

```text
height : 50px
width  : 100%
```

Style :

```text
background : white
border     : 1px solid #DCE3DF
radius     : 8px
```

Texte :

```text
Se connecter avec Google
```

---

# 32. Create account

Texte :

```text
Vous n'avez pas de compte ?
Créer un compte
```

Font :

```text
12px
```

`Créer un compte` :

```text
color       : #087F3E
font-weight : 600
```

---

# 33. Latest Races — section du bas

Cette section affiche les dernières courses disponibles.

Elle doit permettre de voir rapidement :

- Réunion
- Numéro de course
- Hippodrome
- Nombre de partants
- Heure
- Optionnellement distance et terrain

La section doit défiler horizontalement de manière continue.

## Position desktop

```text
left   : 62px
right  : 57px
bottom : 38px
height : 202px
```

Dimensions approximatives :

```text
width  ≈ 1418px
height ≈ 202px
```

---

# 34. Latest races container

```tsx
<section className="
  absolute
  bottom-[38px]
  left-1/2
  z-20
  w-[calc(100%-124px)]
  max-w-[1418px]
  -translate-x-1/2
  rounded-[14px]
  border
  border-[#087F3E]/50
  bg-[#00261D]/75
  p-6
  backdrop-blur-md
">
```

---

# 35. Section header

Structure :

```text
● Dernières courses
  En temps réel · Résultats et programmes

                                      Voir toutes les courses →
```

## Titre

```text
font-size   : 17px
font-weight : 700
color       : white
```

## Sous-titre

```text
font-size : 12px
color     : rgba(255,255,255,.65)
```

---

# 36. Green status dot

Dimensions :

```text
10 × 10px
```

Style :

```css
background: #0BAF58;
border-radius: 9999px;
box-shadow: 0 0 0 4px rgba(11,175,88,.15);
```

---

# 37. Race carousel

Sur desktop, afficher environ 5 mini-cartes.

```text
[ Course 1 ]
[ Course 2 ]
[ Course 3 ]
[ Course 4 ]
[ Course 5 ]
```

Gap :

```text
14px
```

---

# 38. Race card

Dimensions :

```text
width  : 250px
height : 112px
```

Style :

```tsx
<div className="
  min-w-[250px]
  h-[112px]
  rounded-[8px]
  border
  border-white/10
  bg-[#06352B]/80
  p-4
">
```

---

# 39. Contenu d'une mini-course

Exemple :

```text
R1   C4

📍 Ouagadougou

12 partants

◷ 14:30
```

---

# 40. Race identifier

```text
R1
C4
```

Badge :

```text
R1 → background #087F3E/30
C4 → background #087F3E/20
```

Typography :

```text
font-size   : 11px
font-weight : 700
```

---

# 41. Hippodrome

Exemple :

```text
Ouagadougou
```

Font :

```text
font-size   : 13px
font-weight : 600
color       : white
```

Icon :

```tsx
<MapPin size={13} />
```

---

# 42. Nombre de chevaux

Afficher :

```text
12 partants
```

Préférer `partants` à `chevaux` dans l'interface.

Style :

```text
font-size : 11px
color     : rgba(255,255,255,.55)
```

---

# 43. Heure

Exemple :

```text
14:30
```

Icon :

```tsx
<Clock3 size={13} />
```

Style :

```text
font-size   : 12px
font-weight : 500
color       : white
```

---

# 44. Informations supplémentaires

Une miniature peut éventuellement afficher :

```text
R1 · C4
Ouagadougou
12 partants
1 500 m
Terrain : Bon
14:30
```

Mais ne pas surcharger la carte.

Priorité :

```text
1. R/C
2. Hippodrome
3. Partants
4. Heure
5. Distance
6. Terrain
```

---

# 45. Carousel automatique

Le carousel doit défiler horizontalement en continu.

Ne pas utiliser :

```text
slide → pause → slide → pause
```

Préférer :

```text
──────→──────→──────→──────→
```

Défilement continu, lent et linéaire.

---

# 46. Implémentation React

Exemple de données :

```tsx
const races = [
  {
    reunion: "R1",
    course: "C4",
    hippodrome: "Ouagadougou",
    starters: 12,
    distance: "1 500 m",
    terrain: "Bon",
    time: "14:30",
  },
  {
    reunion: "R2",
    course: "C3",
    hippodrome: "Bobo-Dioulasso",
    starters: 10,
    distance: "2 000 m",
    terrain: "Bon",
    time: "15:20",
  },
  {
    reunion: "R3",
    course: "C5",
    hippodrome: "Koudougou",
    starters: 14,
    distance: "1 800 m",
    terrain: "Souple",
    time: "16:10",
  },
];
```

Dupliquer le tableau pour créer une boucle :

```tsx
const infiniteRaces = [...races, ...races];
```

---

# 47. Animation CSS

```css
@keyframes marquee {
  from {
    transform: translateX(0);
  }

  to {
    transform: translateX(-50%);
  }
}

.animate-marquee {
  animation: marquee 35s linear infinite;
}
```

Utilisation :

```tsx
<div className="
  flex
  w-max
  animate-marquee
  gap-4
  hover:[animation-play-state:paused]
">
```

## Règle

Utiliser :

```text
linear
```

et non :

```text
ease-in
ease-out
```

Le défilement doit rester parfaitement régulier.

---

# 48. Carousel arrows

Flèche gauche :

```tsx
<button>
  <ChevronLeft size={18} />
</button>
```

Flèche droite :

```tsx
<button>
  <ChevronRight size={18} />
</button>
```

Dimensions :

```text
36 × 36px
```

Style :

```text
background : rgba(255,255,255,.12)
border-radius : 50%
```

---

# 49. Progress indicator

Sous les cartes :

```text
━━━━━━━━━━░░░░░░░░░
```

Dimensions :

```text
height : 3px
width  : 300px
```

Position :

```text
center
```

---

# 50. Responsive — Desktop

## ≥ 1280px

Utiliser la composition principale :

```text
Hero 2 colonnes
Login card à droite
Latest races horizontal
5 cards visibles
```

---

# 51. Responsive — Tablet

## 768px → 1279px

Réduire :

```text
Logo
Navigation
Hero title
Login width
```

Grid :

```text
55% / 45%
```

Latest races :

```text
3 cards visibles
```

---

# 52. Responsive — Mobile

## < 768px

Ne pas simplement compresser la composition desktop.

Ordre :

```text
Logo
↓
Hero
↓
Features
↓
Login
↓
Dernières courses
```

Navigation desktop remplacée par :

```text
☰
```

Logo :

```text
FasoTurf
```

Taille :

```text
32px
```

---

# 53. Mobile Hero

```text
H1 :
font-size : 30px
line-height : 1.15
```

Description :

```text
15px
```

Features :

```text
44 × 44px icons
```

---

# 54. Mobile Login

```text
width : calc(100% - 32px)
margin : 16px
```

Card :

```text
padding : 24px
```

Titre :

```text
25px
```

---

# 55. Mobile courses

Les cartes restent horizontalement scrollables.

```text
← [ Course ] [ Course ] [ Course ] →
```

Largeur :

```text
230px
```

Sur mobile, privilégier le scroll tactile. L'autoplay peut être désactivé ou ralenti.

---

# 56. Z-index

Architecture :

```text
background       z-0
overlay          z-1
hero             z-10
header           z-20
login            z-20
latest courses   z-20
```

---

# 57. Structure React recommandée

```text
src/
│
├── components/
│   │
│   ├── landing/
│   │   ├── HeroBackground.tsx
│   │   ├── Header.tsx
│   │   ├── BrandLogo.tsx
│   │   ├── HeroContent.tsx
│   │   ├── FeatureItem.tsx
│   │   ├── LoginCard.tsx
│   │   ├── LoginInput.tsx
│   │   ├── SocialLoginButton.tsx
│   │   ├── LatestRaces.tsx
│   │   ├── RaceCard.tsx
│   │   └── RaceCarousel.tsx
│   │
│   └── ui/
│       ├── Button.tsx
│       ├── Input.tsx
│       └── Badge.tsx
│
├── pages/
│   └── LoginHomePage.tsx
│
├── data/
│   └── races.ts
│
└── assets/
    └── images/
```

---

# 58. Tailwind Design Tokens

Dans `tailwind.config.ts` :

```ts
theme: {
  extend: {
    colors: {
      faso: {
        green: "#087F3E",
        "green-dark": "#05632F",
        "green-deep": "#003D2A",
        accent: "#0BAF58",
        gold: "#F2C94C",
        red: "#D64545",
        bg: "#F7F9F8",
        text: "#17221C",
        muted: "#68736D",
        border: "#E4E9E6",
      },
    },

    borderRadius: {
      card: "12px",
      button: "8px",
    },

    boxShadow: {
      card: "0 20px 60px rgba(0,0,0,.20)",
    },

    keyframes: {
      marquee: {
        from: {
          transform: "translateX(0)",
        },
        to: {
          transform: "translateX(-50%)",
        },
      },
    },

    animation: {
      marquee: "marquee 35s linear infinite",
    },
  },
}
```

---

# 59. Font

Installer Inter :

```bash
npm install @fontsource/inter
```

Puis :

```tsx
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
```

Inter est la police principale.

La police script est réservée au slogan.

---

# 60. Règles visuelles — DO / DON'T

## DO

```text
✓ Beaucoup d'espace
✓ Vert Faso comme couleur principale
✓ Blanc pour le contraste
✓ Jaune et rouge uniquement comme accents
✓ Icônes Lucide
✓ Cards avec bordures très discrètes
✓ Animations lentes
✓ Hiérarchie typographique claire
✓ Background course sombre
✓ Interface premium mais simple
```

## DON'T

```text
✗ Glassmorphism excessif
✗ Gradients violets
✗ Néons
✗ Animations agressives
✗ Cartes 3D
✗ Ombres énormes
✗ Trop de couleurs
✗ Illustrations génériques
✗ Trop de badges
✗ Texte trop petit
✗ Interface surchargée
```

Le langage visuel doit rester :

```text
FasoTurf
    ↓
Vert
    ↓
Courses
    ↓
Data
    ↓
Intelligence
    ↓
Confiance
```

---

# 61. Résumé des dimensions — Desktop 1536 × 1024

| Élément | Dimension |
|---|---:|
| Artboard | 1536 × 1024 |
| Header | 96px |
| Content max-width | 1396px |
| Marges horizontales | ~70px |
| Hero left | ~760px |
| Login card | 510 × 620px |
| Login radius | 14px |
| Login padding | 38px |
| Hero H1 | 42px |
| Hero description | 17px |
| Feature icon | 48 × 48px |
| Feature title | 16px |
| Feature description | 13px |
| Login title | 29px |
| Input | 50px |
| Login button | 51px |
| Latest races | ~1418 × 202px |
| Race card | 250 × 112px |
| Race gap | 14px |
| Carousel arrow | 36 × 36px |
| Main green | `#087F3E` |
| Accent green | `#0BAF58` |
| Gold | `#F2C94C` |
| Red | `#D64545` |
| Font | Inter |
| Icons | Lucide React |

---

# 62. Hiérarchie visuelle finale

```text
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  🐎 FasoTurf          Accueil  Fonctionnalités  Tarifs       │
│      La data des courses                                     │
│                                                              │
│                                                              │
│  L'intelligence des courses                 ┌──────────────┐ │
│  hippiques du Burkina.                      │              │ │
│                                             │ SE CONNECTER │ │
│  FasoTurf vous offre...                     │              │ │
│                                             │ Email        │ │
│  🟢 Pronostics & sélections                 │              │ │
│  🟡 Base de données                         │ Mot de passe │ │
│  🟢 Analyses & IA                           │              │ │
│  🔴 Alertes personnalisées                  │ [Connexion]  │ │
│                                             │              │ │
│  Plus qu'un turf, une intelligence !       │ Google       │ │
│                                             └──────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ ● Dernières courses                     Voir toutes →  │  │
│  │                                                        │  │
│  │ [R1 C4] [R2 C3] [R3 C5] [R4 C2] [R5 C6]  →→→→→       │  │
│  │                                                        │  │
│  │                 ━━━━━━━━━━━                             │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

# 63. Directive pour Antigravity

Lors de l'implémentation :

1. Reproduire la maquette en priorité à `1536 × 1024`.
2. Respecter les dimensions indiquées avant d'ajouter des améliorations visuelles.
3. Utiliser React + TypeScript.
4. Utiliser Tailwind CSS pour tout le styling.
5. Utiliser Lucide React pour les icônes.
6. Utiliser Inter comme police principale.
7. Ne pas introduire de nouvelle librairie UI sans nécessité.
8. Créer des composants réutilisables pour les éléments répétitifs.
9. Le carousel des dernières courses doit être alimenté par des données structurées, pas par du HTML codé en dur.
10. Le carousel doit pouvoir être remplacé ultérieurement par les données réelles de l'API FasoTurf.
11. Préserver l'identité visuelle FasoTurf : vert, jaune, rouge, blanc, fond hippique sombre.
12. L'interface doit rester minimaliste et professionnelle.
13. Ne pas implémenter de logique métier PMU dans cette étape.
14. Les données de course affichées actuellement peuvent être des mock data.
15. Prévoir les états `loading`, `empty`, `error` pour les dernières courses.
16. Le formulaire de connexion doit être préparé pour être connecté ultérieurement au backend.
17. Ne pas modifier la structure visuelle sans raison fonctionnelle.
18. Tester la page sur desktop, tablette et mobile.
19. Vérifier l'alignement avec une résolution de référence `1536 × 1024`.
20. Ne pas ajouter de fonctionnalités non demandées.

---

# 64. Critère de validation

La page est considérée comme conforme lorsque :

```text
✓ Le logo FasoTurf est correctement positionné
✓ Le background hippique est sombre et lisible
✓ Le hero est à gauche
✓ Le formulaire de connexion est à droite
✓ Les proportions du login card sont respectées
✓ Les couleurs FasoTurf sont respectées
✓ Les icônes proviennent de Lucide React
✓ Les boutons ont les bonnes dimensions
✓ Les inputs ont 50px de hauteur
✓ La section Dernières courses est en bas
✓ Les mini-cartes affichent R/C, hippodrome, partants et heure
✓ Le carousel défile horizontalement
✓ Le défilement est linéaire et continu
✓ La page est responsive
✓ Aucun élément ne déborde à 1536 × 1024
✓ Aucun élément visuel inutile n'a été ajouté
```

---

## Conclusion

Cette page constitue la **Landing/Login Page officielle de FasoTurf**.

Positionnement de marque :

```text
FasoTurf
La data des courses

Données
+
Historique
+
Analyses
+
IA
+
Pronostics
```

La page doit communiquer immédiatement :

> **FasoTurf est une plateforme de données et d'intelligence dédiée aux courses hippiques au Burkina Faso.**
