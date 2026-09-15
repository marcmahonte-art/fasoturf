import { Menu } from "lucide-react";
import { BrandLogo } from "./BrandLogo";

const NAV = [
  { label: "Accueil", href: "#", active: true },
  { label: "Fonctionnalités", href: "#fonctionnalites", active: false },
  { label: "Tarifs", href: "#tarifs", active: false },
  { label: "À propos", href: "#a-propos", active: false },
];

export function Header() {
  return (
    <header className="relative z-20 mx-auto flex h-[96px] max-w-[1396px] items-center justify-between px-4 sm:px-0">
      <BrandLogo />

      {/* Navigation desktop */}
      <nav
        aria-label="Navigation principale"
        className="hidden md:flex items-center gap-9 text-[14px] font-normal text-white"
      >
        {NAV.map((item) => (
          <a
            key={item.label}
            href={item.href}
            aria-current={item.active ? "page" : undefined}
            className="relative pb-4 transition hover:text-white/80"
          >
            {item.label}
            {item.active && (
              <span
                aria-hidden="true"
                className="absolute bottom-0 left-0 h-px w-12 bg-white"
              />
            )}
          </a>
        ))}
      </nav>

      {/* Bouton menu mobile */}
      <button
        type="button"
        aria-label="Ouvrir le menu"
        className="md:hidden inline-flex h-10 w-10 items-center justify-center rounded-lg text-white/90 hover:bg-white/10"
      >
        <Menu size={22} strokeWidth={2} />
      </button>
    </header>
  );
}