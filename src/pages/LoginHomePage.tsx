import { useState, useEffect } from "react";
import { Header } from "../components/landing/Header";
import { HeroBackground } from "../components/landing/HeroBackground";
import { HeroContent } from "../components/landing/HeroContent";
import { LoginCard } from "../components/landing/LoginCard";
import { LatestRaces } from "../components/landing/LatestRaces";
import { RaceDetailModal } from "../components/landing/RaceDetailModal";
import { races as defaultRaces, type Race } from "../data/races";
import { fetchRaces } from "../services/api";

export function LoginHomePage() {
  const [selectedRace, setSelectedRace] = useState<Race | null>(null);
  const [racesList, setRacesList] = useState<Race[]>(defaultRaces);
  const [isLive, setIsLive] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    fetchRaces(30).then((result) => {
      if (mounted && result.races.length > 0) {
        setRacesList(result.races);
        setIsLive(result.isLive);
      }
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

      <LatestRaces
        races={racesList}
        isLive={isLive}
        onSelectRace={(race) => setSelectedRace(race)}
      />

      {/* Modale détaillée de la course et des partants */}
      <RaceDetailModal
        race={selectedRace}
        onClose={() => setSelectedRace(null)}
      />
    </div>
  );
}