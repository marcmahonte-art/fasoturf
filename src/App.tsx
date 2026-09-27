import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { LoginHomePage } from "./pages/LoginHomePage";
import { DashboardPage } from "./pages/DashboardPage";
import { RaceDetailPage } from "./pages/RaceDetailPage";
import { StatisticsPage } from "./pages/StatisticsPage";
import { CoursesPage } from "./pages/CoursesPage";
import { AnalysesPage } from "./pages/AnalysesPage";
import { PronosticsPage } from "./pages/PronosticsPage";
import { HorsesPage } from "./pages/HorsesPage";
import { HorseDetailPage } from "./pages/HorseDetailPage";
import { PersonsPage } from "./pages/PersonsPage";
import { PersonDetailPage } from "./pages/PersonDetailPage";
import { ComingSoonPage } from "./pages/ComingSoonPage";

/**
 * Routage de l'application FasoTurf.
 *
 * Toutes ces routes sont alimentées par l'API (`fasoturf/backend/`) : le
 * frontend ne lit jamais la base directement.
 *
 * `/`                     landing publique + connexion (inchangée)
 * `/dashboard`            tableau de bord (GET /api/dashboard)
 * `/pronostics`           sortie du moteur Hippo Engine (GET /api/predictions/featured)
 * `/courses`              programme filtrable (GET /api/races/summary)
 * `/courses/:id`          fiche course (GET /api/races/{id})
 * `/chevaux`              recherche de chevaux (GET /api/horses)
 * `/chevaux/:id`          fiche cheval (GET /api/horses/{id})
 * `/jockeys`              recherche de jockeys (GET /api/jockeys)
 * `/jockeys/:id`          fiche jockey (GET /api/jockeys/{id})
 * `/entraineurs`          recherche d'entraîneurs (GET /api/trainers)
 * `/entraineurs/:id`      fiche entraîneur (GET /api/trainers/{id})
 * `/statistiques`         mesures réellement calculées (GET /api/statistics)
 * `/analyses`             courses analysables par le moteur
 * `/analyses/:id`         fiche course + panneau du moteur
 *
 * Les routes encore non implémentées sont déclarées explicitement afin
 * qu'aucun lien de la navigation ne mène à une page blanche : elles affichent
 * un écran d'attente qui dit ce qui manque.
 */
const PENDING_ROUTES: { path: string; title: string; description: string }[] = [
  {
    path: "/abonnement",
    title: "Abonnement",
    description:
      "La gestion de l'abonnement FasoTurf Pro n'est pas encore implémentée : aucun plan ni paiement n'existe côté serveur.",
  },
  {
    path: "/profile",
    title: "Mon profil",
    description:
      "La gestion du profil utilisateur n'est pas encore implémentée : la base ne contient aucune donnée de compte.",
  },
  {
    path: "/settings",
    title: "Paramètres",
    description:
      "Les paramètres du compte ne sont pas encore implémentés : la base ne contient aucune préférence utilisateur.",
  },
];

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginHomePage />} />
        <Route path="/dashboard" element={<DashboardPage />} />

        <Route path="/pronostics" element={<PronosticsPage />} />

        <Route path="/courses" element={<CoursesPage />} />
        <Route path="/courses/:raceId" element={<RaceDetailPage />} />

        <Route path="/chevaux" element={<HorsesPage />} />
        <Route path="/chevaux/:horseId" element={<HorseDetailPage />} />

        <Route path="/jockeys" element={<PersonsPage role="jockey" />} />
        <Route path="/jockeys/:personId" element={<PersonDetailPage role="jockey" />} />
        <Route path="/entraineurs" element={<PersonsPage role="trainer" />} />
        <Route path="/entraineurs/:personId" element={<PersonDetailPage role="trainer" />} />

        <Route path="/statistiques" element={<StatisticsPage />} />

        <Route path="/analyses" element={<AnalysesPage />} />
        {/* L'analyse d'une course s'appuie sur la même fiche, qui contient déjà
            le panneau du moteur Hippo Engine. */}
        <Route path="/analyses/:raceId" element={<RaceDetailPage />} />

        {PENDING_ROUTES.map((route) => (
          <Route
            key={route.path}
            path={route.path}
            element={<ComingSoonPage title={route.title} description={route.description} />}
          />
        ))}

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
