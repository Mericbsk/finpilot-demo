"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { DEFAULT_LANG, TRANSLATIONS, type Lang } from "./translations";

const STORAGE_KEY = "finpilot_ledger_lang";

interface LanguageContextValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

/** Scoped to the Ledger landing/demo — does not affect the dashboard. */
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(DEFAULT_LANG);

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY) as Lang | null;
      // Deliberate: restoring a persisted preference on mount. Doing this in
      // the lazy useState initializer instead would cause an SSR/client
      // hydration mismatch (localStorage isn't available on the server).
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (saved && saved in TRANSLATIONS) setLangState(saved);
    } catch {
      /* ignore */
    }
  }, []);

  // A11y/SEO: keep <html lang> in sync with the actually displayed language.
  // SSR default stays "en" (correct for the default render); this updates the
  // attribute client-side when a saved/selected TR/DE preference is applied.
  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = lang;
    }
  }, [lang]);

  const setLang = (l: Lang) => {
    setLangState(l);
    try {
      localStorage.setItem(STORAGE_KEY, l);
    } catch {
      /* ignore */
    }
  };

  const value = useMemo<LanguageContextValue>(
    () => ({
      lang,
      setLang,
      t: (key: string) => TRANSLATIONS[lang][key] ?? TRANSLATIONS[DEFAULT_LANG][key] ?? key,
    }),
    [lang],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

/** Must be used within <LanguageProvider>. Falls back to English/no-op if not. */
export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (ctx) return ctx;
  return {
    lang: DEFAULT_LANG,
    setLang: () => {},
    t: (key: string) => TRANSLATIONS[DEFAULT_LANG][key] ?? key,
  };
}
