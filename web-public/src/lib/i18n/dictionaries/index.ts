import type { SupportedLang } from "../config";
import type { Dictionary } from "./types";

const dictionaries: Record<SupportedLang, () => Promise<Dictionary>> = {
  en: () => import("./en").then((m) => m.default),
  ja: () => import("./ja").then((m) => m.default),
  es: () => import("./es").then((m) => m.default),
  de: () => import("./de").then((m) => m.default),
};

export async function getDictionary(lang: SupportedLang): Promise<Dictionary> {
  return dictionaries[lang]();
}

export type { Dictionary } from "./types";
