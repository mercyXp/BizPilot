"use client";

import { MotionConfig } from "framer-motion";
import type { ReactNode } from "react";

import { AuthProvider } from "@/components/AuthProvider";
import { I18nProvider } from "@/components/I18nProvider";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <MotionConfig reducedMotion="user">
      <I18nProvider>
        <AuthProvider>{children}</AuthProvider>
      </I18nProvider>
    </MotionConfig>
  );
}
