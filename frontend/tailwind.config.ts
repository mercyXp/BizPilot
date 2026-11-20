import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "var(--color-brand)",
          deep: "var(--color-brand-deep)",
          soft: "var(--color-brand-soft)",
          50: "#F0FDFA",
          100: "#CCFBF1",
          500: "#0D9488",
          600: "#0F766E",
          700: "#115E59",
        },
        canvas: "var(--color-bg)",
        surface: "var(--color-surface)",
        border: "var(--color-border)",
        ink: {
          DEFAULT: "var(--color-text)",
          muted: "var(--color-text-secondary)",
          faint: "var(--color-muted)",
        },
        secondary: "var(--color-text-secondary)",
        muted: "var(--color-muted)",
        mint: "#D1FAE5",
        highlight: "#FDE68A",
        lavender: "#EDE9FE",
        "muted-bg": "var(--color-muted-bg)",
        success: {
          DEFAULT: "var(--color-success)",
          bg: "var(--color-success-bg)",
          border: "var(--color-success-border)",
        },
        danger: {
          DEFAULT: "var(--color-danger)",
          bg: "var(--color-danger-bg)",
          border: "var(--color-danger-border)",
        },
        warning: {
          DEFAULT: "var(--color-warning)",
          bg: "var(--color-warning-bg)",
          border: "var(--color-warning-border)",
        },
        info: {
          DEFAULT: "var(--color-info)",
          bg: "var(--color-info-bg)",
          border: "var(--color-info-border)",
        },
        ai: {
          DEFAULT: "var(--color-ai)",
          bg: "var(--color-ai-bg)",
          border: "var(--color-ai-border)",
        },
        customer: {
          DEFAULT: "var(--color-customer)",
          bg: "var(--color-customer-bg)",
          border: "var(--color-customer-border)",
        },
        chart: {
          revenue: "var(--chart-revenue)",
          expenses: "var(--chart-expenses)",
          profit: "var(--chart-profit)",
          purchases: "var(--chart-purchases)",
          customers: "var(--chart-customers)",
          sales: "var(--chart-sales)",
          outstanding: "var(--chart-outstanding)",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgb(0 0 0 / 0.04), 0 1px 3px rgb(0 0 0 / 0.06)",
        lift: "0 8px 24px rgb(15 118 110 / 0.10)",
        focus: "0 0 0 3px rgb(13 148 136 / 0.22)",
      },
      backgroundImage: {
        grid: "linear-gradient(to right, rgb(15 118 110 / 0.07) 1px, transparent 1px), linear-gradient(to bottom, rgb(15 118 110 / 0.07) 1px, transparent 1px)",
      },
      transitionTimingFunction: {
        entrance: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
      transitionDuration: {
        fast: "150ms",
        standard: "200ms",
        card: "250ms",
        dropdown: "200ms",
        sidebar: "280ms",
        modal: "220ms",
        section: "550ms",
        hero: "700ms",
        chart: "800ms",
      },
      keyframes: {
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "ai-pulse": {
          "0%, 100%": { opacity: "0.45", transform: "scale(1)" },
          "50%": { opacity: "1", transform: "scale(1.08)" },
        },
        "typing-bounce": {
          "0%, 80%, 100%": { transform: "translateY(0)", opacity: "0.4" },
          "40%": { transform: "translateY(-3px)", opacity: "1" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        "ambient-shift": {
          "0%, 100%": { transform: "translate3d(0,0,0) scale(1)" },
          "50%": { transform: "translate3d(12px, -8px, 0) scale(1.04)" },
        },
      },
      animation: {
        shimmer: "shimmer 1.4s ease-in-out infinite",
        "ai-pulse": "ai-pulse 2.4s ease-in-out infinite",
        float: "float 8s ease-in-out infinite",
        "ambient-shift": "ambient-shift 18s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
