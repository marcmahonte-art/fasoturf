import { useState, useEffect } from "react";
import { Header } from "../components/landing/Header";
import { HeroBackground } from "../components/landing/HeroBackground";
import { HeroContent } from "../components/landing/HeroContent";
import { LoginCard } from "../components/landing/LoginCard";
import { LatestRaces } from "../components/landing/LatestRaces";
import { RaceDetailModal } from "../components/landing/RaceDetailModal";
import type { Race } from "../data/races";
import {
  fetchRaces,
  fetchDates,
  type DateItem,
  type RaceFeedSource,
} from "../services/api";

/**
 * Page publique `/` — présentation + connexion, avec le programme réel.
 *
 * Le programme n'est **jamais** pré-rempli par un fichier local : il démarre
 * vide et n'affiche que ce que l'API renvoie. Si l'API est injoignable, la
 * bande du bas le dit explicitement et affiche l'instantané local avec sa date
 * de capture — un repli déclaré, pas un repli silencieux.
 */
export function LoginHomePage() {
  const [selectedRace, setSelectedRace] = useState<Race | null>(null);
  const [racesList, setRacesList] = useState<Race[]>([]);
  const [availableDates, setAvailableDates] = useState<DateItem[]>([]);
  const [isLive, setIsLive] = useState<boolean>(false);
  const [source, setSource] = useState<RaceFeedSource | null>(null);
  const [snapshotDate, setSnapshotDate] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    fetchRaces(50).then((result) => {
      if (!mounted) return;
      setRacesList(result.races);
      setIsLive(result.isLive);
      setSource(result.source);
      setSnapshotDate(result.snapshotDate);
    });

    fetchDates().then((dates) => {
      if (mounted) setAvailableDates(dates);
    });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-faso-green-deep">
      <HeroBackground />

      {/* Header (logo + nav) */}
      <div className="relative z-20 pt-3 sm:pt-0">
        <Header />
      </div>

      {/* Hero : 2 colonnes desktop, 1 colonne mobile */}
      <main className="relative z-10 mx-auto max-w-[1396px] px-4 pb-[300px] sm:px-8 sm:pb-[340px] lg:px-0">
        <div className="grid grid-cols-1 gap-10 lg:grid-cols-[58%_42%] lg:gap-8 lg:pt-6">
          <section aria-label="Présentation FasoTurf" className="lg:pt-8">
            <HeroContent />
          </section>

          <section aria-label="Connexion" className="flex justify-center lg:justify-end lg:pt-2">
            <LoginCard />
          </section>
        </div>
      </main>

      {/* Bandeau Programme officiel & Arrivées */}
      <LatestRaces
        races={racesList}
        isLive={isLive}
        source={source}
        snapshotDate={snapshotDate}
        availableDates={availableDates}
        onSelectRace={(race) => setSelectedRace(race)}
      />

      {/* Modale détaillée de la course et des partants */}
      <RaceDetailModal race={selectedRace} onClose={() => setSelectedRace(null)} />
    </div>
  );
}
