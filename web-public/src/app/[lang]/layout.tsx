import React from "react"
import { notFound } from "next/navigation"
import { SUPPORTED_LANGS, isValidLang } from "@/lib/i18n/config"
import { buildAlternates } from "@/lib/seo"

export async function generateStaticParams() {
  return SUPPORTED_LANGS.map((lang) => ({ lang }))
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string }>
}) {
  const { lang } = await params
  if (!isValidLang(lang)) return {}

  return {
    alternates: buildAlternates(""),
  }
}

// Organization JSON-LD（全言語ページ共通）
const organizationJsonLd = {
  "@context": "https://schema.org",
  "@type": "Organization",
  name: "Ghost in the Archive",
  url: "https://ghostinthearchive.ai",
  description:
    "An autonomous AI agent system cross-analyzing the world's public digital archives through five academic disciplines — unearthing anomalies that no single record, language, or field can explain.",
}

export default async function LangLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ lang: string }>
}) {
  const { lang } = await params

  if (!isValidLang(lang)) {
    notFound()
  }

  return (
    <>
      {/* SSG では <html lang> を静的に設定できないため、同期スクリプトで即座に設定 */}
      <script
        dangerouslySetInnerHTML={{
          __html: `document.documentElement.lang="${lang}";`,
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(organizationJsonLd),
        }}
      />
      {children}
    </>
  )
}
