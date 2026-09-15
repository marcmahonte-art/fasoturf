/**
 * Calque d'arrière-plan :
 *  - image hippique recadrée (jockeys) depuis la maquette
 *  - overlay sombre #001B16/70 pour la lisibilité
 *  - dégradé linéaire (vert profond → transparent) pour éclairer le centre
 */
export function HeroBackground() {
  return (
    <div aria-hidden="true" className="absolute inset-0 z-0 overflow-hidden">
      <img
        src="/images/fasoturf-racing-bg.jpg"
        alt=""
        className="h-full w-full object-cover object-center"
      />
      {/* Overlay sombre uniforme */}
      <div className="absolute inset-0 bg-[#001B16]/70" />
      {/* Dégradé vert centre-droit (reprend le ton Faso) */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(90deg, rgba(0,27,22,.95) 0%, rgba(0,61,42,.55) 45%, rgba(0,27,22,.35) 100%)",
        }}
      />
      {/* Vignette bas pour ancrer la barre des dernières courses */}
      <div
        className="absolute inset-x-0 bottom-0 h-[260px]"
        style={{
          background:
            "linear-gradient(180deg, rgba(0,27,22,0) 0%, rgba(0,27,22,.85) 100%)",
        }}
      />
    </div>
  );
}