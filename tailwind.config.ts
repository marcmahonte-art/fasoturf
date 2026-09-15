import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        faso: {
          green: "#087F3E",
          "green-dark": "#05632F",
          "green-deep": "#003D2A",
          accent: "#0BAF58",
          gold: "#F2C94C",
          red: "#D64545",
          bg: "#F7F9F8",
          text: "#17221C",
          muted: "#68736D",
          border: "#E4E9E6",
        },
      },
      borderRadius: {
        card: "12px",
        button: "8px",
      },
      boxShadow: {
        card: "0 20px 60px rgba(0,0,0,.20)",
      },
      keyframes: {
        marquee: {
          from: { transform: "translateX(0)" },
          to: { transform: "translateX(-50%)" },
        },
      },
      animation: {
        marquee: "marquee 35s linear infinite",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;