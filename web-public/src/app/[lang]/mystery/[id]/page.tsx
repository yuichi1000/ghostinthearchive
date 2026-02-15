import { notFound } from "next/navigation"
import Link from "next/link"
import { ResponsiveHeroImage } from "@/components/responsive-hero-image"
import { Header } from "@/components/header"
import { Footer } from "@ghost/shared/src/components/footer"
import { EvidenceBlock } from "@ghost/shared/src/components/evidence-block"
import { CaseFileHeader } from "@/components/mystery/case-file-header"
import { NarrativeSection } from "@/components/mystery/narrative-section"
import { DiscrepancySection } from "@/components/mystery/discrepancy-section"
import { HypothesisSection } from "@/components/mystery/hypothesis-section"
import { HistoricalContextSection } from "@/components/mystery/historical-context-section"
import { DetailSidebar } from "@/components/mystery/detail-sidebar"
import { getMysteryById, getPublishedMysteryIds, getAllPublishedMysteriesMap } from "@ghost/shared/src/lib/firestore/queries"
import { ArrowLeft, FileText } from "lucide-react"
import { localizeMystery, getTranslatedExcerpt } from "@ghost/shared/src/lib/localize"
import { SUPPORTED_LANGS, isValidLang } from "@/lib/i18n/config"
import type { SupportedLang } from "@/lib/i18n/config"
import { getDictionary } from "@/lib/i18n/dictionaries"

// SSG: ビルド時に生成されたページ以外は 404
export const dynamicParams = false

export async function generateStaticParams() {
  let ids: string[]
  try {
    ids = await getPublishedMysteryIds()
  } catch (error) {
    console.error("[SSG] Firestore クエリ失敗:", error)
    throw new Error(`[SSG] Firestore から記事IDを取得できませんでした: ${error}`)
  }
  console.log(`[SSG] 公開済み記事: ${ids.length} 件 (${ids.join(", ")})`)
  return SUPPORTED_LANGS.flatMap((lang) =>
    ids.map((id) => ({ lang, id }))
  )
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string; id: string }>
}) {
  const { lang, id } = await params
  if (!isValidLang(lang)) return {}

  // React.cache により SSG ビルド中は全ページで同一データを共有
  const mysteriesMap = await getAllPublishedMysteriesMap()
  const mystery = mysteriesMap.get(id) ?? await getMysteryById(id)

  if (!mystery) {
    return { title: "Mystery Not Found | Ghost in the Archive" }
  }

  const { title, summary } = localizeMystery(mystery, lang)

  return {
    title: `${title} | Ghost in the Archive`,
    description: summary,
    alternates: {
      languages: Object.fromEntries(
        SUPPORTED_LANGS.map((l) => [l, `/${l}/mystery/${id}`])
      ),
    },
  }
}

export default async function MysteryDetailPage({
  params,
}: {
  params: Promise<{ lang: string; id: string }>
}) {
  const { lang, id } = await params
  if (!isValidLang(lang)) notFound()

  // React.cache により SSG ビルド中は全ページで同一データを共有
  const mysteriesMap = await getAllPublishedMysteriesMap()
  const mystery = mysteriesMap.get(id) ?? await getMysteryById(id)

  if (!mystery || mystery.status !== "published") {
    notFound()
  }

  const dict = await getDictionary(lang)

  const {
    title, summary, narrativeContent, discrepancyDetected,
    hypothesis, alternativeHypotheses, politicalClimate, storyHooks,
  } = localizeMystery(mystery, lang)

  const location = mystery.historical_context?.geographic_scope?.join(", ") || ""
  const timePeriod = mystery.historical_context?.time_period || ""

  // 証拠の翻訳済み抜粋テキスト
  const evidenceAExcerpt = getTranslatedExcerpt(mystery, "a", lang)
  const evidenceBExcerpt = getTranslatedExcerpt(mystery, "b", lang)

  return (
    <div className="min-h-screen flex flex-col film-grain">
      <Header lang={lang} nav={dict.nav} />

      <main className="flex-1 py-8 md:py-12">
        <div className="container mx-auto px-4">
          {/* Back link */}
          <Link
            href={`/${lang}`}
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-parchment transition-colors mb-8 no-underline"
          >
            <ArrowLeft className="w-4 h-4" />
            {dict.detail.returnToArchive}
          </Link>

          <CaseFileHeader
            mysteryId={mystery.mystery_id}
            title={title}
            location={location}
            timePeriod={timePeriod}
            publishedAt={mystery.publishedAt}
            publishedLabel={dict.detail.published}
          />

          {/* Hero image */}
          {mystery.images?.hero && (
            <div className="mb-12 rounded-sm overflow-hidden border border-border">
              <ResponsiveHeroImage
                hero={mystery.images.hero}
                variants={mystery.images.variants}
                alt={title}
                priority
              />
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
            {/* Main content */}
            <div className="lg:col-span-2 space-y-12">
              <NarrativeSection narrativeContent={narrativeContent} summary={summary} />

              {/* Divider between narrative and archival data */}
              <div className="flex items-center gap-4">
                <div className="h-px flex-1 bg-border" />
                <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">{dict.detail.archivalData}</span>
                <div className="h-px flex-1 bg-border" />
              </div>

              {discrepancyDetected && (
                <DiscrepancySection
                  discrepancyDetected={discrepancyDetected}
                  label={dict.detail.discoveredDiscrepancy}
                />
              )}

              {/* Evidence */}
              <section>
                <div className="flex items-center gap-3 mb-6">
                  <FileText className="w-5 h-5 text-gold" />
                  <h2 className="font-serif text-xl text-parchment">{dict.detail.archivalEvidence}</h2>
                </div>
                <div className="space-y-8">
                  <EvidenceBlock
                    evidence={mystery.evidence_a}
                    label={dict.detail.primarySource}
                    translatedExcerpt={evidenceAExcerpt}
                    labels={dict.evidence}
                  />
                  <EvidenceBlock
                    evidence={mystery.evidence_b}
                    label={dict.detail.contrastingSource}
                    translatedExcerpt={evidenceBExcerpt}
                    labels={dict.evidence}
                  />
                  {mystery.additional_evidence.map((ev, i) => (
                    <EvidenceBlock
                      key={i}
                      evidence={ev}
                      label={`${dict.detail.additionalEvidence} ${i + 1}`}
                      translatedExcerpt={getTranslatedExcerpt(mystery, i, lang)}
                      labels={dict.evidence}
                    />
                  ))}
                </div>
              </section>

              {hypothesis && (
                <HypothesisSection
                  hypothesis={hypothesis}
                  alternativeHypotheses={alternativeHypotheses}
                  labels={{
                    hypothesis: dict.detail.hypothesis,
                    alternativeHypotheses: dict.detail.alternativeHypotheses,
                  }}
                />
              )}

              {mystery.historical_context && (
                <HistoricalContextSection
                  historicalContext={mystery.historical_context}
                  politicalClimate={politicalClimate}
                  labels={{
                    historicalContext: dict.detail.historicalContext,
                    relatedEvents: dict.detail.relatedEvents,
                    keyFigures: dict.detail.keyFigures,
                  }}
                />
              )}
            </div>

            <DetailSidebar
              storyHooks={storyHooks}
              labels={{
                storyAngles: dict.detail.storyAngles,
                classificationNotice: dict.detail.classificationNotice,
              }}
            />
          </div>
        </div>
      </main>

      <Footer labels={dict.footer} />
    </div>
  )
}
