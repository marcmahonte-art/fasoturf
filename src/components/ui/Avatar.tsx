import { cn } from "../../lib/utils";

export type AvatarSize = "sm" | "md" | "lg";

const SIZE_CLASS: Record<AvatarSize, string> = {
  sm: "h-7 w-7 text-[10px]",
  md: "h-9 w-9 text-[12px]",
  lg: "h-10 w-10 text-[13px]",
};

const TONE_CLASS = [
  "bg-faso-green text-white",
  "bg-faso-green-deep text-white",
  "bg-faso-gold text-faso-green-deep",
  "bg-[#0BAF58] text-white",
  "bg-[#05632F] text-white",
];

/** Couleur stable dérivée du nom — évite tout aléa entre deux rendus. */
function toneFor(seed: string): string {
  let sum = 0;
  for (let i = 0; i < seed.length; i += 1) sum += seed.charCodeAt(i);
  return TONE_CLASS[sum % TONE_CLASS.length] ?? TONE_CLASS[0];
}

export function Avatar({
  src,
  initials,
  alt,
  size = "md",
  className,
}: {
  src?: string | null;
  initials: string;
  alt: string;
  size?: AvatarSize;
  className?: string;
}) {
  if (src) {
    return (
      <img
        src={src}
        alt={alt}
        loading="lazy"
        className={cn(
          "shrink-0 rounded-full object-cover",
          SIZE_CLASS[size],
          className,
        )}
      />
    );
  }

  return (
    <span
      role="img"
      aria-label={alt}
      className={cn(
        "inline-flex shrink-0 select-none items-center justify-center rounded-full font-bold uppercase",
        SIZE_CLASS[size],
        toneFor(initials + alt),
        className,
      )}
    >
      {initials}
    </span>
  );
}
