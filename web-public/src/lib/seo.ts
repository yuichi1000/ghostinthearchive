/**
 * SEO 共通ユーティリティ
 * OGP メタデータ・hreflang alternates の生成ヘルパー
 */

import type { Metadata } from "next"
import { SUPPORTED_LANGS, DEFAULT_LANG } from "@/lib/i18n/config"
import type { SupportedLang } from "@/lib/i18n/config"
import { getSiteUrl } from "@/lib/site-url"

// og:locale マッピング（各言語 → OpenGraph ロケール形式）
export const OG_LOCALE_MAP: Record<SupportedLang, string> = {
  en: "en_US",
  ja: "ja_JP",
  es: "es_ES",
  de: "de_DE",
  fr: "fr_FR",
  nl: "nl_NL",
  pt: "pt_BR",
}

/**
 * OGP + Twitter Card メタデータを生成
 */
export function buildOgpMetadata(
  lang: SupportedLang,
  options: {
    title: string
    description: string
    path: string
    type?: "website" | "article"
    images?: { url: string; alt: string }[]
  }
): Pick<Metadata, "openGraph" | "twitter"> {
  const { title, description, path, type = "website", images } = options
  const pageUrl = `${getSiteUrl()}/${lang}${path ? `/${path}` : ""}/`
  const ogLocale = OG_LOCALE_MAP[lang]
  const alternateLocales = SUPPORTED_LANGS
    .filter((l) => l !== lang)
    .map((l) => OG_LOCALE_MAP[l])

  return {
    openGraph: {
      title,
      description,
      url: pageUrl,
      type,
      locale: ogLocale,
      alternateLocale: alternateLocales,
      ...(images && { images }),
    },
    twitter: {
      title,
      description,
      ...(images && { images }),
    },
  }
}

/**
 * hreflang alternates を生成（x-default 込み）
 */
export function buildAlternates(
  path: string
): Metadata["alternates"] {
  const prefix = path ? `/${path}` : ""
  return {
    languages: {
      ...Object.fromEntries(
        SUPPORTED_LANGS.map((l) => [l, `/${l}${prefix}/`])
      ),
      "x-default": `/${DEFAULT_LANG}${prefix}/`,
    },
  }
}
