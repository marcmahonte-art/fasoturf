import { Link } from "react-router-dom";
import { ArrowRight, BarChart3 } from "lucide-react";
import { buttonClass } from "../ui/buttonStyles";

const BANNER_IMAGE = "/images/fasoturf-racing-bg.jpg";

/**
 * Bandeau « FasoTurf Pro » (spec §33).
 *
 * Le message reste orienté analyse et données : aucune incitation directe au
 * pari, aucune promesse de gain.
 */
export function ProBanner() {
  return (
    <section
      aria-labelledby="pro-banner-title"
      className="relative h-[112px] overflow-hidden rounded-[12px]"
      style={{
        background:
          "linear-gradient(96deg, #003D2A 0%, #05632F 46%, #0E7A45 78%, #12874C 100%)",
      }}
    >
      <img
        src={BANNER_IMAGE}
        alt=""
        aria-hidden="true"
        loading="lazy"
        className="absolute inset-y-0 right-0 h-full w-[46%] object-cover object-center opacity-70"
        style={{
          maskImage: "linear-gradient(90deg, transparent 0%, rgba(0,0,0,.85) 42%, #000 100%)",
          WebkitMaskImage: "linear-gradient(90deg, transparent 0%, rgba(0,0,0,.85) 42%, #000 100%)",
        }}
      />
      <div
        aria-hidden="true"
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(90deg, rgba(0,45,32,.35) 0%, rgba(0,61,42,.1) 55%, rgba(0,61,42,0) 100%)",
        }}
      />

      <div className="relative z-10 flex h-full items-center gap-4 px-6">
        <span
          aria-hidden="true"
          className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-black/25"
        >
          <BarChart3 size={20} strokeWidth={2.2} className="text-white" />
        </span>

        <div className="min-w-0 flex-1">
          <h2 id="pro-banner-title" className="text-[14.5px] font-bold leading-[20px] text-white">
            Des données fiables. Des analyses précises.
            <br />
            Des décisions éclairées.
          </h2>
          <p className="mt-1 text-[11px] leading-none text-white/[0.72]">
            FasoTurf, votre allié pour mieux comprendre les courses hippiques.
          </p>
        </div>

        <Link to="/abonnement" className={buttonClass("gold", "md", "hidden sm:inline-flex")}>
          Découvrir FasoTurf Pro
          <ArrowRight size={14} aria-hidden="true" />
        </Link>
      </div>
    </section>
  );
}
