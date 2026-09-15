import type { LucideIcon } from "lucide-react";

type Props = {
  icon: LucideIcon;
  title: string;
  description: string;
  iconBg?: string; // ex: "#087F3E"
};

export function FeatureItem({ icon: Icon, title, description, iconBg = "#087F3E" }: Props) {
  return (
    <div className="flex items-center gap-4">
      <div
        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full"
        style={{ backgroundColor: iconBg }}
        aria-hidden="true"
      >
        <Icon size={20} strokeWidth={2} className="text-white" />
      </div>
      <div className="leading-tight">
        <div className="text-[16px] font-semibold text-white">{title}</div>
        <div className="mt-1 text-[13px] font-normal leading-snug text-white/75">
          {description}
        </div>
      </div>
    </div>
  );
}