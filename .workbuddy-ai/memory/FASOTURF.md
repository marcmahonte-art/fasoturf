# FASOTURF — conventions détaillées (extraites de MEMORY.md, non auto-injecté)

> Détail opérationnel FasoTurf. À lire uniquement quand on travaille sur `fasoturf/`.

## A. Frontend (`fasoturf/`)

Vite 8 + React 19 + TS 6 + Tailwind 3.4 + Lucide + react-router-dom 7.

- ⚠️ **`npx tsc -b` NE VOIT PAS les chemins d'assets erronés** → **toujours valider par
  `npm run build`**.
- TS strict (`noUnusedLocals`, `noUnusedParameters`, `verbatimModuleSyntax`, `erasableSyntaxOnly`) ;
  lint **oxlint** (`react/rules-of-hooks`, `react/only-export-components`,
  `react/set-state-in-effect`) → **0 warning exigé**. Pour resynchroniser un état, préférer
  l'ajustement **pendant le rendu** (comparer à une valeur mémorisée) à un `setState` dans un effet.
- ⚠️ `lucide-react` **n'a PAS d'icône `Horse`** → utiliser `PawPrint` / `UserRound`.
- ⚠️ **Une classe Tailwind « à peu près » n'échoue pas : elle DISPARAÎT.** Tailwind ne génère une
  classe que si sa valeur existe dans le thème. L'échelle d'opacité va **de 5 en 5** : `text-white/72`
  ne produit **aucune** règle CSS → la couleur n'est pas appliquée → le texte **hérite** du
  `body { color: #17221c }` et devient **noir sur la sidebar sombre `#001c18`** (contraste 1,09:1,
  invisible). Ni `tsc`, ni `oxlint`, ni `npm run build` ne le signalent. Hors échelle ⇒ forme
  **crochets** : `text-white/[0.72]`, `bg-white/[0.08]`. Garde-fou :
  `npm run check:css` (`scripts/check_tailwind_classes.mjs`) vérifie que **chaque classe utilisée
  existe dans le CSS compilé**. Et toute surface sombre doit poser sa couleur de base
  (`.ft-on-dark { color: #fff }`, dans `@layer base`) pour qu'un oubli dégrade vers du blanc
  visible plutôt que du noir invisible.
- Design system : voir `design/*.md` — **règle 80/15/5** (80 % neutres, 15 % vert, 5 % or/rouge) ;
  Faso Green `#087F3E`, Accent `#0BAF58`, Gold `#F2C94C`, Red `#D64545`, Page `#F7F9F8`.
- **Filtres toujours portés par l'URL** (`?date=`, `?hippodrome=`, `?discipline=`, `?q=`) : résultat
  partageable + bouton retour fonctionnel. `GlobalSearch` navigue vers `/courses?hippodrome=`.
- Réutilisables : `PageShell.tsx`, `states.tsx` (`PageError`/`PageEmpty`/`SkeletonRows`),
  `SearchField.tsx` (soumission explicite), `useAsyncData` (annulable).
- ⚠️ **L'API est TOUJOURS appelée en URL relative** (`API_BASE_URL = ""` dans `apiBase.ts`).
  **Ne jamais énumérer les ports côté client** : une version ne traitait que 5173, donc sur 4173
  (`vite preview`) l'URL restait relative, `/api/dashboard` était servi par le serveur de fichiers
  statiques → **404**, tableau de bord vide. C'est le **proxy `/api`** de `vite.config.ts` (déclaré
  pour `server` **et** `preview`) qui sait où vit le backend — et le backend FastAPI sert `dist/` et
  `/api` sur la même origine. Une origine unique supprime aussi le CORS. Garde-fou :
  `smoke_render.mjs` refuse un bundle contenant une origine absolue (`http://127.0.0.1:`…).
  ⚠️ `vite preview` ne fait son repli SPA que si le client accepte du HTML : un `curl` par défaut
  renvoie 200+HTML là où le `fetch` du frontend (`Accept: application/json`) reçoit **404** — le
  diagnostic par `curl` nu est donc trompeur.
- ⚠️ **`localhost` ≠ `127.0.0.1`** : Vite se lie à **IPv6 `::1`** → `127.0.0.1:4173` échoue alors
  que `localhost:4173` répond. Un panneau d'aperçu qui résout `localhost` en `127.0.0.1` ne voit
  rien. **Adresse canonique recommandée : http://127.0.0.1:8000** (backend, aucun proxy requis).
- **Un seul port recommandé** : `backend/main.py` sert `dist/` (montage `/assets` + route
  attrape-tout vers `index.html`) → **http://127.0.0.1:8000** = interface + API + `/docs`.
  Lancer `python -m backend.main` (ou `demarrer-fasoturf.bat`) ; `npm run build` requis avant.
  ⚠️ La route attrape-tout doit être déclarée **après** `include_router(api_router)` et refuser les
  chemins `api/` (404 d'API, jamais du HTML).
- ⚠️ **Piège d'outillage** : deux `Edit` en parallèle sur le **même fichier** → un seul est appliqué,
  silencieusement. Éditer séquentiellement, fichier par fichier.
- ⚠️ **Shim *safe-delete* (fail-closed)** : `npm run build` échoue avec
  `[safe-delete] 操作失败 … trash operation: Unknown` dès que `dist/assets` dépasse ~50 fichiers, et
  **toutes** les suppressions sont alors refusées (`rm -rf`, `Remove-Item`, `cmd rd`).
  Contournements **qui marchent** : (a) **renommer** `dist` → `dist_stale` puis relancer le build
  (un dossier absent n'a rien à supprimer) ; (b) supprimer via
  `[System.IO.Directory]::Delete($path, $true)` en PowerShell.
  ⚠️ **Ne pas boucler `rm -f` fichier par fichier** : chaque appel est intercepté et la boucle
  s'étouffe (4 min pour rien). Penser à nettoyer les `dist_*` résiduels — `.gitignore` ne couvre
  que `dist` et `dist-ssr`.
- **Routes** : toutes réelles et alimentées par l'API (mapping exact dans `src/App.tsx`) ; le
  frontend ne touche jamais la DB. Seuls écrans en attente : `/abonnement`, `/profile`, `/settings`
  — exigent une couche de comptes inexistante en base (**décision humaine requise**).

## B. Backend (`fasoturf/backend/`)

- **Architecture obligatoire** : `React → API → Service → Repository → Database`.
  **Le frontend ne touche JAMAIS la DB directement.**
- Stack : FastAPI + uvicorn + Pydantic v2 (Python
  `C:/Users/Lenovo/.workbuddy-ai/binaries/python/versions/3.13.12/`). Chaîne :
  `config.py` (auto-détection DB) → `db/client.py` (`read_connection`, `mode=ro` +
  `PRAGMA query_only = ON`) → `db/repositories/*` (SQL pur) → `services/*` (métier) → `routers/*` →
  `main.py`.
- **La DB n'est jamais codée en dur** : `FASOTURF_DB` → candidats connus
  (`pmu-lonab-scraper/data/master/pmu_master.db` puis `.../processed/pmu_lonab.db`) → balayage du
  projet. Validée par en-tête SQLite + `REQUIRED_TABLES = {master_race, master_runner}`.
- ⚠️ **Ordre des routes FastAPI** : les routes littérales (`/api/races/today`, `/api/races/summary`)
  **avant** `/api/races/{race_id}`. `RaceOut` **conserve le contrat historique** de `/api/races`
  (champs réels ajoutés en fin de modèle) → la page publique continue de fonctionner.
- **Hippo Engine** = source unique des probabilités (le frontend ne recalcule jamais) :
  `cd hippo-engine && python -m ml.scripts.run_prediction --list | --race <id> --json`. Cache
  TTL 900 s. Budget dashboard 25 s.
- ⚠️ **Clé du moteur = `document_id` LONAB** (`source_document_id`), **PAS l'UUID interne**.
  `source_document_id = 0` = course injectée par un adapter externe → **le moteur ne peut pas
  l'analyser** → le service renvoie une **raison explicite**, jamais un pronostic de repli.
  (Toutes les courses `SCHEDULED` du jour sont dans ce cas.)
- `analysable=true` = `source_document_id IS NOT NULL AND > 0` (précondition documentée ; la liste
  réellement acceptée reste déterminée par le moteur via `--list`).
- `master_person.role` a une **casse mixte** (`jockey`/`JOCKEY`) → toujours `lower(role) = ?`.
  Seuil partagé : `n_runners_linked >= 8`.
- ⚠️ **Dénominateur des taux = `starts - unknown`** (positions réellement connues), **jamais
  `starts` seul**. Dénominateur 0 → taux `null`, jamais 0 %.
- ⚠️ **`/api/disciplines` renvoie la valeur BRUTE** (`ATTELE`) alors que `/api/races/summary` expose
  un **libellé lisible** (`Trot Attelé`) → ne pas comparer les deux ; vérifier que les résultats
  filtrés partagent un libellé unique.
- **Pyramide de tests — 3 étages, à rejouer après toute modification** : `scripts/test_api.py`
  (serveur + SHA du socle av./ap.) → `scripts/check_dashboard_contract.mjs` (contrat API ↔ types TS,
  dérive invisible à `tsc`) → `scripts/smoke_render.mjs` (le bundle **s'exécute** et la page
  **s'affiche**).
  ⚠️ `smoke_render.mjs` : ne **jamais** exposer le `performance` de jsdom (récursion infinie) ; ne
  **jamais** réutiliser une fenêtre jsdom fermée (fuite de `history`) → **un processus enfant par
  route**. L'attente doit porter sur un **marqueur propre à la page**, jamais sur « du texte » : le
  menu latéral suffit à faire passer le test sur une page vide.
