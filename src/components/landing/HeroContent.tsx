import { BarChart3, Database, BrainCircuit, BellRing } from "lucide-react";
import { FeatureItem } from "./FeatureItem";

const FEATURES = [
  {
    icon: BarChart3,
    title: "Pronostics & sélections",
    description: "Des analyses fiables pour vos jeux et vos décisions.",
    iconBg: "#087F3E",
  },
  {
    icon: Database,
    title: "Base de données complète",
    description: "Chevaux, jockeys, entraîneurs, hippodromes…",
    iconBg: "#F2C94C",
  },
  {
    icon: BrainCircuit,
    title: "Analyses & IA",
    description:
      "Des modèles prédictifs basés sur les données et l'intelligence artificielle.",
    iconBg: "#087F3E",
  },
  {
    icon: BellRing,
    title: "Alertes personnalisées",
    description: "Ne ratez plus aucune course importante.",
    iconBg: "#D64545",
  },
];

export function HeroContent() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="max-w-[720px] text-[30px] sm:text-[36px] lg:text-[42px] font-bold leading-[1.15] tracking-[-0.8px] text-white">
        L'intelligence des courses
        <br className="hidden sm:block" />
        hippiques <span className="text-faso-accent">du Burkina.</span>
      </h1>

      <p className="max-w-[620px] text-[15px] sm:text-[17px] leading-[1.55] text-white/85">
        FasoTurf vous offre des données fiables, des analyses précises
        et des prédictions intelligentes pour mieux comprendre et
        suivre les courses hippiques.
      </p>

      <ul className="mt-2 flex flex-col gap-[14px]" id="fonctionnalites">
        {FEATURES.map((f) => (
          <li key={f.title}>
            <FeatureItem
              icon={f.icon}
              title={f.title}
              description={f.description}
              iconBg={f.iconBg}
            />
          </li>
        ))}
      </ul>

      {/* Tagline + ligne drapeau */}
      <div className="mt-6 sm:mt-10">
        <p className="text-[20px] sm:text-[25px] italic text-faso-accent leading-snug">
          Plus qu'un turf, une intelligence&nbsp;!
        </p>
        <div className="mt-2 flex h-[3px] w-[105px] overflow-hidden rounded-sm">
          <span className="flex-[2] bg-faso-green" />
          <span className="flex-1 bg-faso-gold" />
          <span className="flex-1 bg-faso-red" />
        </div>
      </div>
    </div>
  );
}