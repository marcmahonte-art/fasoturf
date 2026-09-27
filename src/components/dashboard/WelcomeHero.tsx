import { BrainCircuit, ChartNoAxesCombined, Database, Target } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NextRaceCard } from "./NextRaceCard";
import type { RaceSummary } from "../../types/race";
import type { UserSummary } from "../../types/user";

/** Arguments produit affichés en bas du hero (spec §20) — pas des métriques. */
const FEATURES: { icon: LucideIcon; label: string }[] = [
  { icon: Database, label: "Données fiables" },
  { icon: ChartNoAxesCombined, label: "Analyses précises" },
  { icon: BrainCircuit, label: "IA prédictive" },
  { icon: Target, label: "Pronostics experts" },
];

const HERO_IMAGE = "/images/fasoturf-racing-bg.jpg";

/**
 * Hero du Dashboard (spec §17–§20).
 *
 * Traitement de l'image : dégradé vert profond de gauche à droite afin de
 * garantir la lisibilité du texte tout en laissant le cheval visible.
 *
 * `user` est `null` tant qu'aucune authentification n'est branchée : le
 * message d'accueil reste alors générique plutôt que d'afficher un nom inventé.
 */
export function WelcomeHero({
  user,
  nextRace,
}: {
  user: UserSummary | null;
  nextRace: RaceSummary | null;
}) {
  return (
    <section
      aria-labelledby="hero-title"
      className="relative h-[266px] overflow-hidden rounded-[12px] bg-faso-green-deep"
    >
      <img
        src={HERO_IMAGE}
        alt=""
        aria-hidden="true"
        className="absolute inset-0 h-full w-full object-cover object-center"
      />
      <div
        aria-hidden="true"
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(90deg, rgba(0,16,13,.98) 0%, rgba(0,24,19,.94) 34%, rgba(0,30,23,.66) 62%, rgba(0,34,26,.34) 100%)",
        }}
      />

      <div className="relative z-10 flex h-full flex-col justify-between px-6 py-5">
        <div className="max-w-[430px]">
          <p className="text-[13px] font-semibold leading-none text-faso-accent">
            {user ? `Bonjour ${user.firstName}` : "Bonjour"}{" "}
            <span aria-hidden="true">👋</span>
          </p>

          <h1
            id="hero-title"
            className="mt-2 text-[24px] font-bold leading-[1.2] tracking-[-0.2px] text-white"
          >
            Bienvenue sur votre espace
          </h1>
          <p className="text-[29px] font-bold leading-[1.15] tracking-[-0.4px] text-faso-accent">
            FasoTurf
          </p>

          <p className="mt-2.5 max-w-[340px] text-[12.5px] leading-[19px] text-white/[0.78]">
            Suivez les courses, analysez les données et profitez de nos analyses et
            pronostics intelligents.
          </p>
        </div>

        <ul className="flex flex-wrap items-center gap-x-6 gap-y-2.5">
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            return (
              <li key={feature.label} className="flex items-center gap-2">
                <span
                  aria-hidden="true"
                  className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-[#00241D]"
                >
                  <Icon size={13} strokeWidth={2} className="text-faso-accent" />
                </span>
                <span className="text-[11.5px] font-medium text-white/90">{feature.label}</span>
              </li>
            );
          })}
        </ul>
      </div>

      {nextRace && (
        <NextRaceCard race={nextRace} className="absolute right-4 top-[64px] z-20 hidden xl:block" />
      )}
    </section>
  );
}
