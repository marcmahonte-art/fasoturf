# Mémoire d'exécution — automation 17358277

## 2026-09-16 (3e passage) — « poursuite de la conversation »

**Tâche réellement exécutée** : ce run n'a PAS exécuté la mesure du mouvement des cotes
(Phase 12). La consigne reçue était de poursuivre les travaux en cours : la connexion du
Dashboard FasoTurf à la base réelle (PROMPT MAÎTRE), et surtout la **preuve que les pages
s'affichent vraiment**.

**Ce qui a été fait** :
- Exécution du test de rendu `fasoturf/scripts/smoke_render.mjs` (jsdom + API réelle,
  un processus enfant par route) → **13/13 pages montées et rendues sans erreur** :
  `/`, `/dashboard`, `/courses`, `/pronostics`, `/chevaux`, `/jockeys`, `/entraineurs`,
  `/analyses`, `/statistiques`, + 4 fiches de détail sur identifiants réels.
- Correctif mineur dans ce script : il lisait `exploitable_races` alors que `/api/health`
  expose `coverage.exploitableRaces` (camelCase imbriqué) → en-tête désormais renseigné
  (1173 courses exploitables · 18879 partants).
- Batterie complète rejouée : `test_api.py` **41/41** · `check_dashboard_contract.mjs`
  **43 vérifications, CONTRAT CONFORME** · `tsc -b` 0 erreur · `oxlint` 0 warning (76 fichiers).
- **SHA-256 du socle LONAB inchangé** : `d71f6a01…f41d2cdb42` (revérifié indépendamment).
- Nettoyage de `.workbuddy-ai/memory/MEMORY.md` (16,3 → 14,2 Ko) : fusion des avertissements
  dupliqués en une section « Honnêteté de la donnée », renvoi vers `PHASEN_*.md` pour les
  chiffres par phase et vers `src/App.tsx` pour le mapping des routes.

**État de la Phase 12 (mouvement des cotes)** : **inchangé** — 1er test non significatif
(p=0,3779), capture forward à accumuler. Aucune donnée nouvelle collectée lors de ce run.

**Prochaine exécution** : si la consigne redevient la mesure du mouvement des cotes, reprendre la
séquence Phase 12 (`--backfill-results` → capture 2 h → `--fetch-results` → analyse poolée
**sans** `--date`), hors sandbox pour l'accès réseau. Sinon, les seuls écrans encore en attente
côté FasoTurf sont `/abonnement`, `/profile` et `/settings`, qui exigeraient une couche de comptes
utilisateurs inexistante en base (décision humaine requise avant de la créer).
