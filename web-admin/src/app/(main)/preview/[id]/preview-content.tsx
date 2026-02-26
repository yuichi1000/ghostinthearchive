"use client"

import Link from "next/link"
import Image from "next/image"
import { EvidenceBlock } from "@ghost/shared/src/components/evidence-block"
import { CaseFileHeader } from "@ghost/shared/src/components/mystery/case-file-header"
import { NarrativeSection } from "@ghost/shared/src/components/mystery/narrative-section"
import { DiscrepancySection } from "@ghost/shared/src/components/mystery/discrepancy-section"
import { HypothesisSection } from "@ghost/shared/src/components/mystery/hypothesis-section"
import { HistoricalContextSection } from "@ghost/shared/src/components/mystery/historical-context-section"
import { DetailSidebar } from "@ghost/shared/src/components/mystery/detail-sidebar"
import { TableOfContents } from "@ghost/shared/src/components/table-of-contents"
import { SECTION_IDS, type TocSection } from "@ghost/shared/src/lib/toc-config"
import { extractHeadings } from "@ghost/shared/src/lib/markdown-headings"
import { stripLeadingH1 } from "@ghost/shared/src/lib/utils"
import { localizeMystery, getTranslatedExcerpt } from "@ghost/shared/src/lib/localize"
import { LanguageSelector } from "@/components/language-selector"
import { useLanguage } from "@/contexts/language-context"
import type { FirestoreMystery } from "@ghost/shared/src/types/mystery"
import { ArrowLeft, FileText, Eye } from "lucide-react"

// 管理画面は英語固定のため、i18n 辞書の代わりにハードコード定数を使用
const PREVIEW_LABELS = {
  confidence: { confirmedGhost: "Confirmed Ghost", suspectedGhost: "Suspected Ghost", archivalEcho: "Archival Echo" },
  classification: { HIS: "History", FLK: "Folklore", ANT: "Anthropology", OCC: "Occult", URB: "Urban Legend", CRM: "Crime", REL: "Religion", LOC: "Locus" } as Record<string, string>,
  sourceCoverage: { heading: "Ghost Assessment" },
}

/**
 * Date は Server→Client シリアライズで string になるため、
 * toLocaleDateString を安全に呼ぶヘルパー
 */
function formatDate(d: Date | string | undefined): string {
  if (!d) return ""
  const date = typeof d === "string" ? new Date(d) : d
  return date.toLocaleDateString()
}

interface PreviewContentProps {
  mystery: FirestoreMystery
}

export function PreviewContent({ mystery }: PreviewContentProps) {
  const { lang, setLang } = useLanguage()

  // translations map に存在する言語
  const availableLangs = Object.keys(mystery.translations ?? {})
  // *_ja レガシーフィールドの有無
  const hasLegacyJa = !!(mystery.title_ja || mystery.narrative_content_ja)

  const {
    title, summary, narrativeContent, discrepancyDetected,
    hypothesis, alternativeHypotheses, politicalClimate, storyHooks,
    confidenceRationale,
  } = localizeMystery(mystery, lang)

  // 証拠の翻訳済み抜粋テキスト
  const evidenceAExcerpt = getTranslatedExcerpt(mystery, "a", lang)
  const evidenceBExcerpt = getTranslatedExcerpt(mystery, "b", lang)

  const location = mystery.historical_context?.geographic_scope?.join(", ") || ""
  const timePeriod = mystery.historical_context?.time_period || ""

  // 本文見出しから TOC セクションを動的構築
  const narrativeHeadings = extractHeadings(stripLeadingH1(narrativeContent || ""))
  const tocSections: TocSection[] = [
    ...(narrativeHeadings.length > 0
      ? narrativeHeadings.map(h => ({ id: h.id, label: h.text }))
      : [{ id: SECTION_IDS.narrative, label: "Narrative" }]),
    ...(discrepancyDetected ? [{ id: SECTION_IDS.discrepancy, label: "Discovered Discrepancy" }] : []),
    { id: SECTION_IDS.evidence, label: "Archival Evidence" },
    ...(hypothesis ? [{ id: SECTION_IDS.hypothesis, label: "Hypothesis" }] : []),
    ...(mystery.historical_context ? [{ id: SECTION_IDS.historicalContext, label: "Historical Context" }] : []),
  ]

  // publishedAt を安全に Date に変換
  const publishedAt = mystery.publishedAt
    ? (typeof mystery.publishedAt === "string" ? new Date(mystery.publishedAt) : mystery.publishedAt)
    : mystery.createdAt
      ? (typeof mystery.createdAt === "string" ? new Date(mystery.createdAt) : mystery.createdAt)
      : undefined

  return (
    <>
      {/* Preview Banner */}
      <div className="bg-amber-500/90 text-black py-2 px-4 text-center sticky top-16 z-40">
        <div className="container mx-auto flex items-center justify-center gap-4">
          <Eye className="w-4 h-4" />
          <span className="font-mono text-sm">
            PREVIEW MODE - Status: <span className="font-bold uppercase">{mystery.status}</span>
          </span>
          <LanguageSelector
            currentLang={lang}
            onLangChange={setLang}
            availableLangs={availableLangs}
            hasLegacyJa={hasLegacyJa}
          />
          <Link
            href="/"
            className="ml-4 px-3 py-1 bg-black/20 hover:bg-black/30 rounded text-sm no-underline transition-colors"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>

      <div className="py-8 md:py-12">
        <div className="container mx-auto px-4">
          {/* Back link */}
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-parchment transition-colors mb-8 no-underline"
          >
            <ArrowLeft className="w-4 h-4" />
            Return to Dashboard
          </Link>

          <CaseFileHeader
            mysteryId={mystery.mystery_id}
            title={title}
            location={location}
            timePeriod={timePeriod}
            publishedAt={publishedAt}
            publishedLabel={mystery.publishedAt ? "Published:" : "Created:"}
            confidenceLevel={mystery.confidence_level}
            confidenceLabels={PREVIEW_LABELS.confidence}
            classificationLabels={PREVIEW_LABELS.classification}
            storyteller={mystery.storyteller}
          />

          {/* モバイル目次 */}
          <TableOfContents sections={tocSections} heading="Table of Contents" variant="mobile" />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
            {/* Main content */}
            <div className="lg:col-span-2 space-y-12">
              {/* Hero image */}
              {mystery.images?.hero && (
                <figure className="mx-auto max-w-2xl">
                  <div className="aged-card letterpress-border rounded-sm overflow-hidden">
                    <Image
                      src={mystery.images.hero}
                      alt={title}
                      width={1200}
                      height={675}
                      className="w-full h-auto"
                      priority
                      unoptimized={mystery.images.hero.includes('localhost')}
                    />
                  </div>
                </figure>
              )}

              <NarrativeSection narrativeContent={narrativeContent} summary={summary} lang={lang} />

              {/* Divider between narrative and archival data */}
              <div className="flex items-center gap-4">
                <div className="h-px flex-1 bg-border" />
                <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">Archival Data</span>
                <div className="h-px flex-1 bg-border" />
              </div>

              {discrepancyDetected && (
                <DiscrepancySection discrepancyDetected={discrepancyDetected} />
              )}

              {/* Evidence */}
              <section id="section-evidence" className="scroll-mt-24">
                <div className="flex items-center gap-3 mb-6">
                  <FileText className="w-5 h-5 text-gold" />
                  <h2 className="font-serif text-xl text-parchment">Archival Evidence</h2>
                </div>
                <div className="space-y-8">
                  <EvidenceBlock
                    evidence={mystery.evidence_a}
                    label="Primary Source"
                    translatedExcerpt={evidenceAExcerpt}
                  />
                  <EvidenceBlock
                    evidence={mystery.evidence_b}
                    label="Contrasting Source"
                    translatedExcerpt={evidenceBExcerpt}
                  />
                  {mystery.additional_evidence.map((ev, i) => (
                    <EvidenceBlock
                      key={i}
                      evidence={ev}
                      label={`Additional Evidence ${i + 1}`}
                      translatedExcerpt={getTranslatedExcerpt(mystery, i, lang)}
                    />
                  ))}
                </div>
              </section>

              {hypothesis && (
                <HypothesisSection
                  hypothesis={hypothesis}
                  alternativeHypotheses={alternativeHypotheses}
                />
              )}

              {mystery.historical_context && (
                <HistoricalContextSection
                  historicalContext={mystery.historical_context}
                  politicalClimate={politicalClimate}
                />
              )}
            </div>

            <DetailSidebar
              storyHooks={storyHooks}
              confidenceRationale={confidenceRationale}
              sourceCoverageLabels={PREVIEW_LABELS.sourceCoverage}
            >
              {/* デスクトップ目次 */}
              <TableOfContents sections={tocSections} heading="Table of Contents" variant="desktop" />
            </DetailSidebar>
          </div>
        </div>
      </div>
    </>
  )
}
