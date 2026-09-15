import { useState, type FormEvent } from "react";
import { Mail, Lock, ArrowRight } from "lucide-react";
import { LoginInput } from "./LoginInput";

function GoogleIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 48 48"
      aria-hidden="true"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6.1 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C34 6 29.3 4 24 4 13 4 4 13 4 24s9 20 20 20 20-9 20-20c0-1.2-.1-2.3-.4-3.5z" />
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3 0 5.8 1.1 7.9 3l5.7-5.7C34 6 29.3 4 24 4 16.4 4 9.7 8.3 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.3l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.2-4.2 5.6l6.2 5.2c-.4.4 6.7-4.9 6.7-14.8 0-1.2-.1-2.3-.4-3.5z" />
    </svg>
  );
}

export function LoginCard() {
  const [remember, setRemember] = useState(true);

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    // premier jet : pas de backend, on ne fait que signaler la structure
    e.preventDefault();
    // console.debug("[FasoTurf] login submit (mock)");
  };

  return (
    <aside
      aria-labelledby="login-title"
      className="w-full max-w-[510px] rounded-[14px] bg-white p-7 sm:p-[38px] shadow-card"
    >
      <h2
        id="login-title"
        className="text-[25px] sm:text-[29px] font-bold leading-[1.2] text-faso-text"
      >
        Se connecter
      </h2>
      <p className="mt-2 text-[14px] leading-[1.55] text-faso-muted">
        Accédez à votre espace pour consulter
        les analyses et pronostics FasoTurf.
      </p>

      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-5" noValidate>
        <LoginInput
          label="Email ou numéro de téléphone"
          name="identifier"
          type="text"
          placeholder="exemple@fasoturf.bf ou 70 12 34 56"
          autoComplete="username"
          leftIcon={<Mail size={18} strokeWidth={1.8} />}
        />

        <LoginInput
          label="Mot de passe"
          name="password"
          type="password"
          placeholder="Votre mot de passe"
          autoComplete="current-password"
          leftIcon={<Lock size={18} strokeWidth={1.8} />}
        />

        <div className="mt-3 flex items-center justify-between text-[12px]">
          <label className="flex items-center gap-2 text-faso-text cursor-pointer select-none">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              className="h-4 w-4 rounded border-faso-border accent-faso-green"
            />
            Se souvenir de moi
          </label>
          <a href="#mot-de-passe-oublie" className="font-medium text-faso-green hover:underline">
            Mot de passe oublié&nbsp;?
          </a>
        </div>

        <button
          type="submit"
          className="mt-2 flex h-[51px] w-full items-center justify-center gap-2 rounded-[8px] bg-faso-green text-[14px] font-semibold text-white transition hover:bg-faso-green-dark focus:outline-none focus:ring-2 focus:ring-faso-green/30"
        >
          Se connecter
          <ArrowRight size={18} strokeWidth={2} />
        </button>

        <div className="my-3 flex items-center gap-4 text-[12px] text-[#9AA59F]">
          <span className="h-px flex-1 bg-faso-border" />
          OU
          <span className="h-px flex-1 bg-faso-border" />
        </div>

        <button
          type="button"
          className="flex h-[50px] w-full items-center justify-center gap-3 rounded-[8px] border border-faso-border bg-white text-[14px] font-medium text-faso-text transition hover:bg-faso-bg focus:outline-none focus:ring-2 focus:ring-faso-green/20"
        >
          <GoogleIcon />
          Se connecter avec Google
        </button>
      </form>

      <p className="mt-6 text-center text-[12px] text-faso-muted">
        Vous n'avez pas de compte&nbsp;?{" "}
        <a href="#creer-un-compte" className="font-semibold text-faso-green hover:underline">
          Créer un compte
        </a>
      </p>

      {/* Petite décoration sous "Créer un compte" (ligne drapeau + étoile) */}
      <div className="mx-auto mt-4 flex h-[2px] w-[120px] overflow-hidden rounded-sm">
        <span className="flex-[2] bg-faso-green" />
        <span className="flex-1 bg-faso-gold" />
        <span className="flex-1 bg-faso-red" />
      </div>
      <div
        aria-hidden="true"
        className="mx-auto mt-2 h-[10px] w-[10px] rotate-45 bg-faso-gold"
      />
    </aside>
  );
}