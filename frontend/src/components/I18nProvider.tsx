"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { apiFetch } from "@/lib/api";
import { fallbackMessages, translate, type MessageCatalog } from "@/lib/i18n";

const LOCALE_KEY = "bizpilot.locale";

type I18nState = {
  locale: string;
  messages: Record<string, string>;
  professionalKeys: string[];
  setLocale: (locale: string) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
};

const I18nContext = createContext<I18nState | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState("en");
  const [messages, setMessages] = useState<Record<string, string>>(fallbackMessages);
  const [professionalKeys, setProfessionalKeys] = useState<string[]>([]);

  const load = useCallback(async (next: string) => {
    const response = await apiFetch(`/api/v1/i18n/messages?locale=${encodeURIComponent(next)}`);
    if (!response.ok) return;
    const body = (await response.json()) as MessageCatalog;
    setMessages({ ...fallbackMessages, ...body.messages });
    setProfessionalKeys(body.professional_keys ?? []);
  }, []);

  useEffect(() => {
    const stored = window.localStorage.getItem(LOCALE_KEY) || "en";
    setLocaleState(stored);
    void load(stored);
  }, [load]);

  const setLocale = useCallback(
    (next: string) => {
      setLocaleState(next);
      window.localStorage.setItem(LOCALE_KEY, next);
      void load(next);
    },
    [load],
  );

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => translate(messages, key, vars),
    [messages],
  );

  const value = useMemo(
    () => ({ locale, messages, professionalKeys, setLocale, t }),
    [locale, messages, professionalKeys, setLocale, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nState {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return ctx;
}
