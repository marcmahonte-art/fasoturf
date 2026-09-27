/**
 * Adresse de l'API FasoTurf.
 *
 * Le frontend ne touche **jamais** la base de données : toutes les données
 * passent par cette API (architecture imposée : React → API → Service →
 * Repository → Database). Ce module est le seul endroit où l'adresse est
 * définie.
 *
 * L'adresse est **relative** — l'API est toujours sur la même origine que
 * l'interface. C'est vrai dans les trois façons de servir l'application :
 *
 *   - backend FastAPI (8000) : il sert `dist/` **et** `/api` ;
 *   - serveur de développement Vite (5173) : proxy `/api` (vite.config.ts) ;
 *   - prévisualisation Vite (4173) : même proxy.
 *
 * ⚠️ Ne JAMAIS réintroduire ici une liste de ports (« si 5173 alors
 * 127.0.0.1:8000 »). Une version précédente ne traitait que 5173 : ouverte sur
 * 4173, la page gardait une URL relative, `/api/dashboard` était alors servi
 * par le serveur de fichiers statiques — qui répond **404** — et le tableau de
 * bord affichait « L'API a répondu 404 ».
 *
 * Le proxy Vite rend cette énumération inutile : c'est lui qui sait où vit le
 * backend, et il s'applique aux deux serveurs. Une origine unique supprime au
 * passage toute dépendance au CORS.
 */
export const API_BASE_URL = "";

/**
 * Délai maximal d'une requête de lecture courante (ms).
 * Court, car un repli existe : mieux vaut un repli rapide qu'une page figée.
 */
export const API_TIMEOUT_MS = 4000;

/**
 * Délai accordé à l'endpoint agrégé du Dashboard.
 * Plus long : le backend peut avoir à exécuter le moteur de pronostics.
 */
export const API_DASHBOARD_TIMEOUT_MS = 45000;
