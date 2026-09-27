import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

/**
 * Adresse du backend FasoTurf.
 *
 * Surchargeable par la variable d'environnement `FASOTURF_API` (utile si le
 * backend tourne ailleurs).
 */
const BACKEND = process.env.FASOTURF_API ?? "http://127.0.0.1:8000";

/**
 * Les appels d'API sont **relatifs** dans le code du frontend (`/api/...`).
 * Ce proxy est ce qui les rend valides quel que soit le port qui sert
 * l'interface :
 *
 *   - `npm run dev`     → 5173 (serveur de développement) ;
 *   - `npm run preview` → 4173 (prévisualisation du build) ;
 *   - backend FastAPI   → 8000 (sert `dist/` et l'API sur la même origine).
 *
 * ⚠️ Ne JAMAIS remplacer ce proxy par une énumération de ports côté client.
 * Une première version ne traitait que le port 5173 : sur 4173, l'URL restait
 * relative, `/api/dashboard` était donc servi par le serveur de fichiers
 * statiques, qui répondait **404** — et le tableau de bord restait vide.
 * Un port oublié ne produit aucune erreur visible à la compilation.
 */
const proxy = {
  "/api": {
    target: BACKEND,
    changeOrigin: true,
  },
};

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: { proxy },
  preview: { proxy },
});
