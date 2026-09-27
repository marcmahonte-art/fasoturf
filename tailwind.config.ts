import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        faso: {
          /* Brand */
          green: "#087F3E",
          "green-dark": "#05632F",
          "green-deep": "#003D2A",
          accent: "#0BAF58",

          /* Accents */
          gold: "#F2C94C",
          red: "#D64545",

          /* Interface */
          bg: "#F7F9F8",
          surface: "#FFFFFF",
          text: "#17221C",
          muted: "#68736D",
          border: "#DCE3DF",
          "border-soft": "#E9EDEB",
          field: "#EEF2F0",

          /* Sidebar */
          sidebar: "#001C18",
          "sidebar-raised": "#0A2E24",

          /* États — fonds doux */
          "success-soft": "#E7F7EE",
          "warning-soft": "#FFF7DF",
          "warning-text": "#9A7212",
          "danger-soft": "#FDECEC",
          "danger-line": "#F7DCDC",
          "info-soft": "#EAF4FF",
          "info-text": "#2878C8",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
      },
      borderRadius: {
        card: "12px",
        button: "8px",
      },
      boxShadow: {
        /* conservée pour la landing existante */
        card: "0 20px 60px rgba(0,0,0,.20)",
        /* interface dashboard — ombres volontairement très légères */
        panel: "0 2px 8px rgba(0,0,0,.03), 0 8px 24px rgba(0,61,42,.04)",
        soft: "0 1px 3px rgba(23,34,28,.06)",
        lift: "0 4px 14px rgba(0,61,42,.08)",
      },
      keyframes: {
        marquee: {
          from: { transform: "translateX(0)" },
          to: { transform: "translateX(-50%)" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(4px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        marquee: "marquee 35s linear infinite",
        "fade-in": "fade-in 200ms ease-out both",
      },
    },
  },
  plugins: [],
} satisfies Config;
