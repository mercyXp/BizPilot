import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#0f172a",
          800: "#1e293b",
          500: "#64748b",
        },
        brand: {
          50: "#eef2ff",
          100: "#dbe4ff",
          500: "#3b5bdb",
          600: "#2f4cd0",
          700: "#2740b0",
        },
      },
      boxShadow: {
        card: "0 12px 40px -20px rgba(15, 23, 42, 0.25)",
      },
      backgroundImage: {
        grid: "linear-gradient(to right, rgba(59, 91, 219, 0.08) 1px, transparent 1px), linear-gradient(to bottom, rgba(59, 91, 219, 0.08) 1px, transparent 1px)",
      },
    },
  },
  plugins: [],
};

export default config;
