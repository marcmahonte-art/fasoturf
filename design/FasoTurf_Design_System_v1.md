# FasoTurf — Design System v1.0

> **La data des courses**
>
> Design system minimaliste, moderne et premium pour la plateforme FasoTurf.

---

## 1. Vision

FasoTurf est une plateforme d'analyse et de données hippiques.

### Piliers
- **PRONO** — sélections et analyses du jour
- **DATA** — historique, chevaux, jockeys, entraîneurs, hippodromes
- **ANALYTICS** — modèles ML, probabilités, IA, backtesting
- **PRO / API / B2B** — monétisation et services professionnels

### Principes UX
1. Simple
2. Data-first
3. Fiable
4. Local mais moderne
5. Mobile-first
6. Explicable

---

## 2. Architecture produit

```text
                         FASOTURF
                    La data des courses
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
      PRONO              DATA             ANALYTICS
        │                  │                  │
  Sélections du jour   Historique          Modèles ML
  Courses à suivre    Chevaux              Probabilités
  Sélections          Jockeys              IA
  Classements         Entraîneurs           Backtesting
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │ FASOTURF PRO│
                    │ Abonnement  │
                    └──────┬──────┘
                           │
                     ┌─────▼─────┐
                     │ API / B2B │
                     └───────────┘
```

---

## 3. Identité

**Nom :** FasoTurf  
**Signature :** La data des courses

Ton : professionnel, accessible, précis, moderne, local, jamais sensationnaliste.

À éviter :
- « GAIN GARANTI ! »
- « CHEVAL SÛR À 100 % »
- « JACKPOT !!! »

---

## 4. Palette

| Token | Hex | Usage |
|---|---|---|
| `--ft-green` | `#087F3E` | marque, CTA, éléments actifs |
| `--ft-green-dark` | `#05632F` | hover, navigation |
| `--ft-gold` | `#F2C94C` | accent, PRO, highlights |
| `--ft-red` | `#D64545` | alertes, négatif, risque |
| `--ft-bg` | `#F7F9F8` | fond général |
| `--ft-white` | `#FFFFFF` | cartes et surfaces |
| `--ft-text` | `#17221C` | texte principal |
| `--ft-muted` | `#68736D` | texte secondaire |
| `--ft-border` | `#E4E9E6` | bordures |

### Règle 80 / 15 / 5
- 80 % neutres
- 15 % vert FasoTurf
- 5 % jaune / rouge

Le vert est la signature, pas le fond de toute l'application.

---

## 5. Couleurs sémantiques

```css
--success: #087F3E;
--success-soft: #E8F6EF;
--warning: #D99A00;
--warning-soft: #FFF6D9;
--danger: #D64545;
--danger-soft: #FDECEC;
--info: #2878C8;
--info-soft: #EAF3FC;
```

Les couleurs indiquent un état ou un signal du modèle, jamais une garantie de résultat.

---

## 6. Typographie

Police : **Inter**

```css
font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont,
  "Segoe UI", sans-serif;
```

| Élément | Taille | Poids |
|---|---:|---:|
| H1 | 32px | 700 |
| H2 | 24px | 600 |
| H3 | 18px | 600 |
| H4 | 16px | 600 |
| Body | 14–16px | 400 |
| Small | 12px | 400 |
| Data | 14px | 500 |
| KPI | 28–36px | 700 |

---

## 7. Espacements

Échelle 4px :

`4 · 8 · 12 · 16 · 20 · 24 · 32 · 40 · 48 · 64`

---

## 8. Border radius

```text
radius-sm    6px
radius-md    8px
radius-lg    12px
radius-xl    16px
radius-full  999px
```

Boutons : 8px  
Cards : 12px  
Grands blocs : 16px  
Badges : full

---

## 9. Ombres

Interface légère :

```css
--shadow-sm: 0 1px 3px rgba(23, 34, 28, 0.06);
--shadow-md: 0 4px 12px rgba(23, 34, 28, 0.08);
```

---

## 10. Layout

Desktop :

```text
┌──────────────────────────────────────────────────────┐
│ Logo       Recherche              🔔   PRO   Profil  │
├──────────────┬───────────────────────────────────────┤
│ Accueil      │                                       │
│ Courses      │             CONTENU                   │
│ Analyses     │                                       │
│ Data         │                                       │
│ Chevaux      │                                       │
│ Jockeys      │                                       │
│ Entraîneurs  │                                       │
│ Résultats    │                                       │
└──────────────┴───────────────────────────────────────┘
```

Sidebar : 240px  
Content : max-width 1440px  
Padding : 24–32px

---

## 11. Navigation

```text
🏠 Accueil
🏇 Courses
📊 Analyses
🗄 Data
🐎 Chevaux
👤 Jockeys
👤 Entraîneurs
🏆 Résultats
```

Secondaire :

```text
⭐ FasoTurf Pro
⚙ Paramètres
```

---

## 12. Header

```text
Logo | Recherche | Notifications | PRO | Profil
```

Placeholder recherche :

> Rechercher une course, un cheval, un jockey...

---

## 13. Boutons

### Primary
`[ Voir l'analyse → ]`

Vert, texte blanc, radius 8px.

### Secondary
`[ Voir le profil ]`

Blanc + bordure verte.

### PRO
`[ ⭐ Passer à PRO ]`

Vert avec accent jaune discret.

### Ghost
`Voir tout →`

---

## 14. Cards

```css
background: #FFFFFF;
border: 1px solid #E4E9E6;
border-radius: 12px;
padding: 20px;
```

Éviter les grosses ombres, gradients excessifs et bordures épaisses.

---

## 15. Dashboard

```text
Bonjour 👋
Voici un aperçu des courses et analyses du jour.

┌────────────┐ ┌────────────┐ ┌────────────┐
│ Courses    │ │ Analyses   │ │ Résultats  │
│ 24         │ │ 18         │ │ 12         │
└────────────┘ └────────────┘ └────────────┘

Courses à suivre

R1 · C4
Paris-Vincennes
14 partants · 2 700 m
                         [Voir l'analyse]

R2 · C3
Lyon-Parilly
16 partants · 2 400 m
                         [Voir l'analyse]
```

Les chiffres ci-dessus sont des exemples UI uniquement.

---

## 16. Carte Course

```text
┌────────────────────────────────────────────┐
│ R1 · C4                         Aujourd'hui │
│                                            │
│ Paris-Vincennes                            │
│ 14 partants · 2 700 m                      │
│                                            │
│ 13h55                         [Analyser →] │
└────────────────────────────────────────────┘
```

Priorité : course, hippodrome, partants, distance, heure, type, disponibilité de l'analyse.

---

## 17. Composant Cheval

```text
┌──────────────────────────────────────────┐
│  8   NOM DU CHEVAL              82 %     │
│      Jockey · Entraîneur                  │
│                                          │
│  Forme       █████████░  88              │
│  Cote        3.40                         │
│  Top 3       71 %                         │
│                                          │
│                [Voir le profil]          │
└──────────────────────────────────────────┘
```

Le numéro du cheval doit être très visible.

---

## 18. Score / Probabilité

Toujours indiquer la nature de la métrique :

```text
Score modèle       82 / 100
Probabilité Top 3  71 %
Indice de forme    88 / 100
```

Ne jamais présenter un score comme une certitude.

---

## 19. Analyse IA

```text
┌────────────────────────────────────────────┐
│ 🧠 Analyse FasoTurf                        │
│                                            │
│ Le cheval ressort grâce à sa régularité,  │
│ son profil sur la distance et les données │
│ historiques disponibles.                  │
│                                            │
│ Facteurs principaux                        │
│ ✓ Forme récente                            │
│ ✓ Distance                                 │
│ ✓ Jockey                                   │
│ ⚠ Données limitées                         │
└────────────────────────────────────────────┘
```

L'IA explique les données du moteur. Elle ne doit pas inventer de statistiques.

---

## 20. Badges

```text
🟢 Analyse disponible
🟡 Analyse en cours
🔴 Signal faible
⭐ PRO
```

Style : 12px, poids 500, padding 4px 8px, radius full.

---

## 21. Graphiques

Style minimaliste :
- pas de 3D
- peu de couleurs
- grille discrète
- légendes simples
- vert pour la série principale
- gris pour les séries secondaires

Graphiques utiles :
- performance historique
- évolution du score
- répartition Top 3
- comparaison des chevaux
- forme récente

Bibliothèque : **Recharts**

---

## 22. Page Analyse

```text
QUARTÉ — R1C4

Paris-Vincennes
2 700 m · 14 partants · 13h55

──────────────────────────────

SÉLECTION FASOTURF

1. Cheval A       82 %
2. Cheval B       76 %
3. Cheval C       68 %
4. Cheval D       61 %

──────────────────────────────

🧠 Analyse IA

Pourquoi cette sélection ?

──────────────────────────────

📊 Facteurs

Forme
Distance
Jockey
Entraîneur
Historique

──────────────────────────────

📰 Consensus
```

---

## 23. Page Cheval

```text
🐎 NOM DU CHEVAL

Sexe · âge · poids · gains

[Historique] [Statistiques] [Performances]

Dernières courses

Date | Hippodrome | Distance | Place | Temps

Statistiques

Taux de victoire
Top 3
Nombre de courses
Forme récente

Points forts
✓ Distance
✓ Hippodrome
✓ Forme actuelle
```

---

## 24. Page Courses

Filtres :

```text
[ Date ]
[ Hippodrome ]
[ Type ]
[ Discipline ]
[ Réunion ]
```

---

## 25. Page Résultats

```text
Résultats

14 septembre 2026

R1 · C1
8 - 5 - 12 - 3

R1 · C2
4 - 6 - 9 - 2

R2 · C1
7 - 1 - 4 - 8
```

Plus tard, comparer :
- pronostic FasoTurf
- résultat réel
- performance du modèle

---

## 26. FasoTurf Pro

```text
┌───────────────────────────────────────┐
│ ⭐ FasoTurf Pro                       │
│                                       │
│ Analyses avancées                     │
│ Modèles prédictifs                    │
│ Statistiques détaillées               │
│ Historique complet                    │
│                                       │
│ [ Découvrir FasoTurf Pro → ]          │
└───────────────────────────────────────┘
```

Le PRO doit être visible mais jamais agressif.

---

## 27. Landing / Home publique

La page publique est différente du dashboard.

```text
┌──────────────────────────────────────────┐
│ FasoTurf   Fonctionnalités  Tarifs  Login│
├──────────────────────────────────────────┤
│                                          │
│ Des données fiables.                    │
│ Des analyses précises.                  │
│ Des décisions éclairées.                │
│                                          │
│ FasoTurf est la plateforme d'analyse     │
│ et de données hippiques.                 │
│                                          │
│ [ Se connecter ] [ Découvrir ]           │
│                                          │
│                 🏇                       │
├──────────────────────────────────────────┤
│ Données │ Analyses │ IA │ Profils        │
├──────────────────────────────────────────┤
│ Comment ça marche ?                      │
├──────────────────────────────────────────┤
│ FasoTurf Pro                             │
└──────────────────────────────────────────┘
```

---

## 28. Page Connexion

```text
                 FasoTurf

              Bon retour !

      Email ou numéro de téléphone
      [___________________________]

              Mot de passe
      [___________________________]

      ☑ Se souvenir de moi

      [       Se connecter       ]

                  OU

      [   Continuer avec Google ]

      Pas encore de compte ?
             Créer un compte
```

Fond blanc ou `#F7F9F8`. Accent vert. Le jaune/rouge du drapeau reste un détail graphique.

---

## 29. Mobile

```text
┌─────────────────────────┐
│ 🏇 FasoTurf        🔔   │
│                         │
│ Courses du jour         │
│                         │
│ [ Course card ]         │
│ [ Course card ]         │
│ [ Course card ]         │
│                         │
├─────────────────────────┤
│ 🏠  🏇  📊  🐎  👤     │
└─────────────────────────┘
```

Priorité mobile :
1. Courses
2. Analyse
3. Sélections
4. Résultats
5. Profil

---

## 30. Icônes

Bibliothèque : **Lucide Icons**

Style :
- stroke 1.8–2px
- taille 18–22px
- style cohérent

---

## 31. Illustrations et photos

Les photos de chevaux sont utilisées avec parcimonie :
- landing page
- bannière PRO
- page cheval
- contenu éditorial

Le dashboard reste data-first.

---

## 32. Responsive

```text
Mobile       < 640px
Tablet       640–1024px
Desktop      1024–1440px
Large        > 1440px
```

Sur mobile :
- sidebar → bottom navigation
- KPI → colonne ou scroll horizontal
- tables → cards
- graphiques → largeur complète
- CTA → facilement accessibles au pouce

---

## 33. États UI

### Loading
Skeleton minimal.

### Empty

```text
Aucune analyse disponible

Les données de cette course ne sont
pas encore disponibles.
```

### Error

```text
Impossible de charger les données.

[ Réessayer ]
```

### Locked / PRO

```text
⭐ Fonctionnalité PRO

Passez à FasoTurf Pro pour accéder
à cette analyse.

[ Découvrir PRO ]
```

---

## 34. Règles Data / IA

Toujours distinguer :

```text
DONNÉE
14 courses

↓

STATISTIQUE
Top 3 : 71 %

↓

MODÈLE
Score : 82 / 100

↓

IA
Explication en langage naturel
```

Préférer :
> « Le modèle classe ce cheval parmi les profils les plus favorables de la course. »

Éviter :
> « Ce cheval va gagner. »

---

## 35. Architecture technique UI

```text
Next.js
│
├── Tailwind CSS
├── shadcn/ui
├── Lucide
├── Recharts
│
├── components/
│   ├── ui/
│   ├── course/
│   ├── horse/
│   ├── analytics/
│   └── pro/
│
├── app/
│   ├── page.tsx
│   ├── login/
│   ├── dashboard/
│   ├── courses/
│   ├── analyses/
│   ├── chevaux/
│   ├── jockeys/
│   ├── entraineurs/
│   └── resultats/
│
└── lib/
```

Backend :

```text
Next.js
   ↓
FastAPI
   ↓
SQLite / PostgreSQL
   ↓
Data + ML Engine
```

---

## 36. Tokens CSS

```css
:root {
  --ft-green: #087F3E;
  --ft-green-dark: #05632F;
  --ft-gold: #F2C94C;
  --ft-red: #D64545;

  --ft-bg: #F7F9F8;
  --ft-white: #FFFFFF;

  --ft-text: #17221C;
  --ft-muted: #68736D;
  --ft-border: #E4E9E6;

  --success: #087F3E;
  --warning: #D99A00;
  --danger: #D64545;
  --info: #2878C8;

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 999px;
}
```

---

## 37. Identité Burkina

Le vert domine. Le jaune et le rouge apparaissent comme accents subtils, notamment dans :
- landing page
- footer
- bannière PRO
- écran de connexion

Ne pas utiliser les trois couleurs dans chaque composant.

---

## 38. Règles à respecter

### DO
- beaucoup d'espace blanc
- vert comme signature
- chiffres lisibles
- cartes simples
- icônes cohérentes
- mobile-first
- explication des modèles

### DON'T
- design casino
- néons
- gradients partout
- graphiques multicolores
- grosses animations
- promesses de gains garantis
- fausses probabilités
- surcharge du dashboard

---

## 39. Objectif UX

L'utilisateur doit comprendre rapidement :

1. Quelle est la course ?
2. Quels profils ressortent ?
3. Pourquoi ?
4. Quelles données soutiennent l'analyse ?
5. Que donne FasoTurf Pro ?

---

## 40. Stack UI finale

```text
FasoTurf
│
├── Next.js
├── Tailwind CSS
├── shadcn/ui
├── Lucide Icons
├── Recharts
└── Inter
```

**Version : 1.0**  
**Statut : Design System MVP**
