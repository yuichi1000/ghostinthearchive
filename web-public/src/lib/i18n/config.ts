export const SUPPORTED_LANGS = ["en", "ja", "es", "de"] as const;
export type SupportedLang = (typeof SUPPORTED_LANGS)[number];
export const DEFAULT_LANG: SupportedLang = "en";
export const LANG_NAMES: Record<SupportedLang, string> = {
  en: "English",
  ja: "日本語",
  es: "Español",
  de: "Deutsch",
};

export function isValidLang(lang: string): lang is SupportedLang {
  return (SUPPORTED_LANGS as readonly string[]).includes(lang);
}
