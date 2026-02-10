import { notFound } from "next/navigation"
import Link from "next/link"
import Image from "next/image"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { EvidenceBlock } from "@/components/evidence-block"
import { CaseFileHeader } from "@/components/mystery/case-file-header"
import { NarrativeSection } from "@/components/mystery/narrative-section"
import { DiscrepancySection } from "@/components/mystery/discrepancy-section"
import { HypothesisSection } from "@/components/mystery/hypothesis-section"
import { HistoricalContextSection } from "@/components/mystery/historical-context-section"
import { DetailSidebar } from "@/components/mystery/detail-sidebar"
import { getMysteryById, getPublishedMysteryIds } from "@/lib/firestore/mysteries"
import { ArrowLeft, FileText } from "lucide-react"
import { localizeMystery } from "@/lib/localize"

// SSG: ビルド時に生成されたページ以外は 404
export const dynamicParams = false

// output: "export" では generateStaticParams が空配列だとビルドエラーになる
// revalidate = 0 でこのチェックをバイパス（静的出力では実行時に影響なし）
export const revalidate = 0

export async function generateStaticParams() {
  try {
    const ids = await getPublishedMysteryIds()
    return ids.map((id) => ({ id }))
  } catch {
    return []
  }
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const mystery = await getMysteryById(id)

  if (!mystery) {
    return { title: "Mystery Not Found | Ghost in the Archive" }
  }

  const { title, summary } = localizeMystery(mystery)

  return {
    title: `${title} | Ghost in the Archive`,
    description: summary,
  }
}

export default async function MysteryDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const mystery = await getMysteryById(id)

  if (!mystery || mystery.status !== "published") {
    notFound()
  }

  const {
    title, summary, narrativeContent, discrepancyDetected,
    hypothesis, alternativeHypotheses, politicalClimate, storyHooks,
  } = localizeMystery(mystery)

  const location = mystery.historical_context?.geographic_scope?.join(", ") || ""
  const timePeriod = mystery.historical_context?.time_period || ""

  return (
    <div className="min-h-screen flex flex-col film-grain">
      <Header />

      <main className="flex-1 py-8 md:py-12">
        <div className="container mx-auto px-4">
          {/* Back link */}
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-parchment transition-colors mb-8 no-underline"
          >
            <ArrowLeft className="w-4 h-4" />
            Return to Archive
          </Link>

          <CaseFileHeader
            mysteryId={mystery.mystery_id}
            title={title}
            location={location}
            timePeriod={timePeriod}
            publishedAt={mystery.publishedAt}
          />

          {/* Hero image */}
          {mystery.images?.hero && (
            <div className="mb-12 rounded-sm overflow-hidden border border-border">
              <Image
                src={mystery.images.hero}
                alt={title}
                width={1200}
                height={675}
                className="w-full h-auto"
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
                <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">Archival Data</span>
                <div className="h-px flex-1 bg-border" />
              </div>

              {discrepancyDetected && (
                <DiscrepancySection discrepancyDetected={discrepancyDetected} />
              )}

              {/* Evidence */}
              <section>
                <div className="flex items-center gap-3 mb-6">
                  <FileText className="w-5 h-5 text-gold" />
                  <h2 className="font-serif text-xl text-parchment">Archival Evidence</h2>
                </div>
                <div className="space-y-8">
                  <EvidenceBlock evidence={mystery.evidence_a} label="Primary Source" />
                  <EvidenceBlock evidence={mystery.evidence_b} label="Contrasting Source" />
                  {mystery.additional_evidence.map((ev, i) => (
                    <EvidenceBlock key={i} evidence={ev} label={`Additional Evidence ${i + 1}`} />
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

            <DetailSidebar storyHooks={storyHooks} />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}
