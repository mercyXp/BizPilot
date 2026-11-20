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
      },
    },
  },
  plugins: [],
};

export default config;
