import type { Transition, Variants } from "framer-motion";

/** Duration tokens in milliseconds. Prefer these over ad-hoc timings. */
export const motionDuration = {
  fast: 150,
  standard: 200,
  card: 250,
  dropdown: 200,
  sidebar: 280,
  modal: 220,
  section: 550,
  hero: 700,
  chart: 800,
} as const;

export const motionEase = [0.22, 1, 0.36, 1] as const;

export const entranceTransition: Transition = {
  duration: motionDuration.section / 1000,
  ease: motionEase,
};

export const heroTransition: Transition = {
  duration: motionDuration.hero / 1000,
  ease: motionEase,
};

export const fadeUp = (delay = 0, duration = motionDuration.section): Variants => ({
  hidden: { opacity: 0, y: 16 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: duration / 1000, ease: motionEase, delay },
  },
});

export const fadeIn = (delay = 0, duration = motionDuration.standard): Variants => ({
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { duration: duration / 1000, ease: motionEase, delay },
  },
});

export const scaleIn = (delay = 0): Variants => ({
  hidden: { opacity: 0, scale: 0.96, y: 12 },
  show: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { duration: motionDuration.hero / 1000, ease: motionEase, delay },
  },
});

export const staggerContainer = (stagger = 0.08, delayChildren = 0): Variants => ({
  hidden: {},
  show: {
    transition: { staggerChildren: stagger, delayChildren },
  },
});

export const heroContainer: Variants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.1, delayChildren: 0.05 },
  },
};

export const modalVariants: Variants = {
  hidden: { opacity: 0, scale: 0.96, y: 8 },
  show: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: { duration: motionDuration.modal / 1000, ease: motionEase },
  },
  exit: {
    opacity: 0,
    scale: 0.98,
    y: 6,
    transition: { duration: motionDuration.fast / 1000, ease: motionEase },
  },
};

export const overlayVariants: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: motionDuration.modal / 1000 } },
  exit: { opacity: 0, transition: { duration: motionDuration.fast / 1000 } },
};

export const drawerVariants: Variants = {
  hidden: { x: "-100%" },
  show: {
    x: 0,
    transition: { duration: motionDuration.sidebar / 1000, ease: motionEase },
  },
  exit: {
    x: "-100%",
    transition: { duration: motionDuration.sidebar / 1000, ease: motionEase },
  },
};

export const dropdownVariants: Variants = {
  hidden: { opacity: 0, y: -6, scale: 0.98 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: motionDuration.dropdown / 1000, ease: motionEase },
  },
  exit: {
    opacity: 0,
    y: -4,
    transition: { duration: motionDuration.fast / 1000, ease: motionEase },
  },
};

export const kpiVariants: Variants = fadeUp(0, motionDuration.section);

export const reducedFade: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { duration: 0.01 } },
};

export function withReducedMotion(reduce: boolean | null, variants: Variants): Variants {
  if (reduce) return reducedFade;
  return variants;
}
