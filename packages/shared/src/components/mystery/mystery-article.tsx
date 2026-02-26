// 共有記事レンダラー
// 管理画面プレビューと公開ページの両方から使用する。
// "use client" なし — サーバーコンポーネント互換（子コンポーネントが個別に "use client" を持つ）
import type { ReactNode } from "react"
import { FileText } from "lucide-react"
import { EvidenceBlock } from "../evidence-block"
import { CaseFileHeader } from "./case-file-header"
import { NarrativeSection } from "./narrative-section"
import { DiscrepancySection } from "./discrepancy-section"
import { HypothesisSection } from "./hypothesis-section"
import { HistoricalContextSection } from "./historical-context-section"
import { DetailSidebar } from "./detail-sidebar"
import { TableOfContents } from "../table-of-contents"
import { SECTION_IDS, type TocSection } from "../../lib/toc-config"
import { extractHeadings } from "../../lib/markdown-headings"
import { stripLeadingH1 } from "../../lib/utils"
import type { FirestoreMystery } from "../../types/mystery"
import type { LocalizedMystery } from "../../lib/localize"

// --- ラベル型定義 ---

export interface MysteryArticleLabels {
  // CaseFileHeader
  publishedLabel: string
  storytellerBylineLabel: string
  confidence: { confirmedGhost: string; suspectedGhost: string; archivalEcho: string }
  classification: Record<string, string>
  // TableOfContents
  tableOfContents: string
  // TOC セクションラベル
  tocNarrative: string
  tocDiscrepancy: string
  tocEvidence: string
  tocHypothesis: string
  tocHistoricalContext: string
  // 各セクション
  archivalData: string
  discoveredDiscrepancy: string
  archivalEvidence: string
  primarySource: string
  contrastingSource: string
  additionalEvidence: string
  evidence: { source: string; view: string; originalText: string }
  hypothesis: string
  alternativeHypotheses: string
  historicalContext: string
  relatedEvents: string
  keyFigures: string
  storyAngles: string
  classificationNotice: string
  sourceCoverage: { heading: string }
}

// --- Props ---

export interface MysteryArticleProps {
  mystery: FirestoreMystery
  localized: LocalizedMystery
  lang: string
  labels: MysteryArticleLabels
  translatedExcerpts: { a?: string; b?: string; additional: (string | undefined)[] }
  heroImage?: ReactNode
  publishedAt?: Date
  afterHeader?: ReactNode
  mainColumnFooter?: ReactNode
}

// --- コンポーネント ---

export function MysteryArticle({
  mystery,
  localized,
  lang,
  labels,
  translatedExcerpts,
  heroImage,
  publishedAt,
  afterHeader,
  mainColumnFooter,
}: MysteryArticleProps) {
  const {
    title, summary, narrativeContent, discrepancyDetected,
    hypothesis, alternativeHypotheses, politicalClimate, storyHooks,
    confidenceRationale,
  } = localized

  const location = mystery.historical_context?.geographic_scope?.join(", ") || ""
  const timePeriod = mystery.historical_context?.time_period || ""

  // 本文見出しから TOC セクションを動的構築（1回だけ計算）
  const narrativeHeadings = extractHeadings(stripLeadingH1(narrativeContent || ""))
  const precomputedHeadingIds = narrativeHeadings.map(h => h.id)

  const tocSections: TocSection[] = [
    ...(narrativeHeadings.length > 0
      ? narrativeHeadings.map(h => ({ id: h.id, label: h.text }))
      : [{ id: SECTION_IDS.narrative, label: labels.tocNarrative }]),
    ...(discrepancyDetected ? [{ id: SECTION_IDS.discrepancy, label: labels.tocDiscrepancy }] : []),
    { id: SECTION_IDS.evidence, label: labels.tocEvidence },
    ...(hypothesis ? [{ id: SECTION_IDS.hypothesis, label: labels.tocHypothesis }] : []),
    ...(mystery.historical_context ? [{ id: SECTION_IDS.historicalContext, label: labels.tocHistoricalContext }] : []),
  ]

  return (
    <>
      <CaseFileHeader
        mysteryId={mystery.mystery_id}
        title={title}
        location={location}
        timePeriod={timePeriod}
        publishedAt={publishedAt}
        publishedLabel={labels.publishedLabel}
        confidenceLevel={mystery.confidence_level}
        confidenceLabels={labels.confidence}
        classificationLabels={labels.classification}
        storyteller={mystery.storyteller}
        storytellerBylineLabel={labels.storytellerBylineLabel}
      />

      {afterHeader}

      {/* モバイル目次 */}
      <TableOfContents sections={tocSections} heading={labels.tableOfContents} variant="mobile" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
        {/* メインコンテンツ */}
        <div className="lg:col-span-2 space-y-12">
          {/* ヒーロー画像（アプリ固有コンポーネントを slot で受け取る） */}
          {heroImage}

          <NarrativeSection
            narrativeContent={narrativeContent}
            summary={summary}
            lang={lang}
            precomputedHeadingIds={precomputedHeadingIds}
          />

          {/* 本文とアーカイブデータの区切り */}
          <div className="flex items-center gap-4">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">{labels.archivalData}</span>
            <div className="h-px flex-1 bg-border" />
          </div>

          {discrepancyDetected && (
            <DiscrepancySection discrepancyDetected={discrepancyDetected} label={labels.discoveredDiscrepancy} />
          )}

          {/* 証拠セクション */}
          <section id="section-evidence" className="scroll-mt-24">
            <div className="flex items-center gap-3 mb-6">
              <FileText className="w-5 h-5 text-gold" />
              <h2 className="font-serif text-xl text-parchment">{labels.archivalEvidence}</h2>
            </div>
            <div className="space-y-8">
              <EvidenceBlock
                evidence={mystery.evidence_a}
                label={labels.primarySource}
                translatedExcerpt={translatedExcerpts.a}
                labels={labels.evidence}
              />
              <EvidenceBlock
                evidence={mystery.evidence_b}
                label={labels.contrastingSource}
                translatedExcerpt={translatedExcerpts.b}
                labels={labels.evidence}
              />
              {mystery.additional_evidence.map((ev, i) => (
                <EvidenceBlock
                  key={i}
                  evidence={ev}
                  label={`${labels.additionalEvidence} ${i + 1}`}
                  translatedExcerpt={translatedExcerpts.additional[i]}
                  labels={labels.evidence}
                />
              ))}
            </div>
          </section>

          {hypothesis && (
            <HypothesisSection
              hypothesis={hypothesis}
              alternativeHypotheses={alternativeHypotheses}
              labels={{ hypothesis: labels.hypothesis, alternativeHypotheses: labels.alternativeHypotheses }}
            />
          )}

          {mystery.historical_context && (
            <HistoricalContextSection
              historicalContext={mystery.historical_context}
              politicalClimate={politicalClimate}
              labels={{
                historicalContext: labels.historicalContext,
                relatedEvents: labels.relatedEvents,
                keyFigures: labels.keyFigures,
              }}
            />
          )}

          {mainColumnFooter}
        </div>

        <DetailSidebar
          storyHooks={storyHooks}
          labels={{
            storyAngles: labels.storyAngles,
            classificationNotice: labels.classificationNotice,
          }}
          confidenceRationale={confidenceRationale}
          sourceCoverageLabels={labels.sourceCoverage}
        >
          {/* デスクトップ目次（サイドバー内） */}
          <TableOfContents sections={tocSections} heading={labels.tableOfContents} variant="desktop" />
        </DetailSidebar>
      </div>
    </>
  )
}
