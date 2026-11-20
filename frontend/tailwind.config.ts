import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F1F5F9",
        surface: "#FFFFFF",
        ink: {
          DEFAULT: "#0F172A",
          muted: "#334155",
          faint: "#475569",
        },
        brand: {
          50: "#F0FDFA",
          100: "#CCFBF1",
          500: "#0D9488",
          600: "#0F766E",
          700: "#115E59",
        },
        mint: "#D1FAE5",
        info: "#DBEAFE",
        highlight: "#FDE68A",
        blush: "#FCE7F3",
        lavender: "#EDE9FE",
      },
      boxShadow: {
        card: "0 12px 40px -20px rgba(15, 23, 42, 0.25)",
      },
      backgroundImage: {
        grid: "linear-gradient(to right, rgba(15, 118, 110, 0.07) 1px, transparent 1px), linear-gradient(to bottom, rgba(15, 118, 110, 0.07) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};

export default config;
