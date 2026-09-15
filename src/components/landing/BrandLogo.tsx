import logoHorse from "../../assets/logo-horse.svg";

type Props = {
  /** réduit le logo pour le menu mobile */
  compact?: boolean;
};

export function BrandLogo({ compact = false }: Props) {
  return (
    <div className="flex items-center gap-3">
      <img
        src={logoHorse}
        alt="FasoTurf"
        className={compact ? "h-9 w-10" : "h-[68px] w-[78px] sm:h-[88px] sm:w-[100px]"}
      />
      <div className="leading-none">
        <div
          className={
            (compact ? "text-[26px]" : "text-[42px] sm:text-[56px]") +
            " font-bold tracking-tight"
          }
        >
          <span className="text-white">Faso</span>
          <span className="text-faso-accent">Turf</span>
        </div>
        {!compact && (
          <div className="mt-1 text-[18px] sm:text-[22px] font-normal text-white/95">
            La data des courses
          </div>
        )}
      </div>
    </div>
  );
}