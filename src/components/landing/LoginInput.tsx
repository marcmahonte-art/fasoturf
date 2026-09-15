import { forwardRef, useState, type InputHTMLAttributes, type ReactNode } from "react";
import { Eye, EyeOff } from "lucide-react";

type Props = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  leftIcon?: ReactNode;
};

export const LoginInput = forwardRef<HTMLInputElement, Props>(function LoginInput(
  { label, leftIcon, placeholder, type = "text", id, ...rest },
  ref,
) {
  const reactId = id ?? rest.name ?? `login-${label.replace(/\s+/g, "-").toLowerCase()}`;
  const isPassword = type === "password";
  const [visible, setVisible] = useState(false);
  const effectiveType = isPassword && visible ? "text" : type;

  return (
    <div>
      <label
        htmlFor={reactId}
        className="mb-[7px] block text-[12px] font-medium text-faso-text"
      >
        {label}
      </label>
      <div className="relative">
        {leftIcon && (
          <span
            className="pointer-events-none absolute left-[14px] top-1/2 -translate-y-1/2 text-faso-muted"
            aria-hidden="true"
          >
            {leftIcon}
          </span>
        )}
        <input
          ref={ref}
          id={reactId}
          name={rest.name ?? reactId}
          type={effectiveType}
          placeholder={placeholder}
          {...rest}
          className={
            "h-[50px] w-full rounded-[8px] border border-faso-border bg-white " +
            (leftIcon ? "pl-[42px] " : "pl-4 ") +
            (isPassword ? "pr-[44px] " : "pr-4 ") +
            "text-[14px] text-faso-text placeholder:text-[#94A29A] outline-none transition " +
            "focus:border-faso-green focus:ring-2 focus:ring-faso-green/10"
          }
        />
        {isPassword && (
          <button
            type="button"
            aria-label={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
            aria-pressed={visible}
            onClick={() => setVisible((v) => !v)}
            className="absolute right-[10px] top-1/2 -translate-y-1/2 inline-flex h-8 w-8 items-center justify-center rounded text-faso-muted hover:text-faso-green"
          >
            {visible ? (
              <EyeOff size={18} strokeWidth={1.8} />
            ) : (
              <Eye size={18} strokeWidth={1.8} />
            )}
          </button>
        )}
      </div>
    </div>
  );
});