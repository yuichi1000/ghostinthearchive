import { notFound } from "next/navigation"
import Link from "next/link"
import Image from "next/image"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { EvidenceBlock } from "@/components/evidence-block"
import { getMysteryById, getPublishedMysteryIds } from "@/lib/firestore/mysteries"
import {
  ArrowLeft,
  MapPin,
  Clock,
  Calendar,
  FileText,
  AlertTriangle,
  BookOpen,
  Lightbulb
} from "lucide-react"
import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"

export const revalidate = 86400

export async function generateStaticParams() {
  const ids = await getPublishedMysteryIds()
  return ids.map((id) => ({ id }))
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

  // Prefer English fields for public display
  const title = mystery.title_en || mystery.title
  const summary = mystery.summary_en || mystery.summary

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

  // Prefer English fields for public display
  const title = mystery.title_en || mystery.title
  const summary = mystery.summary_en || mystery.summary
  const narrativeContent = mystery.narrative_content_en || mystery.narrative_content
  const discrepancyDetected = mystery.discrepancy_detected_en || mystery.discrepancy_detected
  const hypothesis = mystery.hypothesis_en || mystery.hypothesis
  const alternativeHypotheses = mystery.alternative_hypotheses_en || mystery.alternative_hypotheses
  const politicalClimate = mystery.historical_context_en?.political_climate || mystery.historical_context?.political_climate

  const location = mystery.historical_context?.geographic_scope?.join(", ") || ""
  const timePeriod = mystery.historical_context?.time_period || ""
  const allEvidence = [mystery.evidence_a, mystery.evidence_b, ...mystery.additional_evidence]

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

          {/* Case file header */}
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center gap-2 px-3 py-1.5 border border-border bg-card rounded-sm">
                <FileText className="w-4 h-4 text-gold" />
                <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                  Case File #{mystery.mystery_id.slice(-3).padStart(4, '0')}
                </span>
              </div>
              <div className="h-px flex-1 bg-border" />
            </div>

            <h1 className="font-serif text-3xl md:text-4xl lg:text-5xl text-parchment mb-6 leading-tight text-balance">
              {title}
            </h1>

            <div className="flex flex-wrap items-center gap-6 text-sm text-muted-foreground">
              {location && (
                <span className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-gold" />
                  {location}
                </span>
              )}
              {timePeriod && (
                <span className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-gold" />
                  {timePeriod}
                </span>
              )}
              {mystery.publishedAt && (
                <span className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gold" />
                  Published: {mystery.publishedAt.toLocaleDateString()}
                </span>
              )}
            </div>
          </div>

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
              {/* Narrative Content (primary) */}
              {narrativeContent ? (
                <section className="prose prose-lg prose-invert max-w-none prose-headings:font-serif prose-headings:text-parchment prose-headings:mt-12 prose-headings:mb-4 prose-p:text-foreground/90 prose-p:leading-loose prose-p:mb-6 prose-a:text-gold prose-blockquote:border-gold/30 prose-blockquote:bg-card prose-blockquote:px-6 prose-blockquote:py-4 prose-blockquote:rounded-sm prose-blockquote:text-foreground/70 prose-blockquote:italic prose-blockquote:font-serif prose-strong:text-parchment prose-hr:border-border">
                  <Markdown remarkPlugins={[remarkGfm]}>
                    {narrativeContent.replace(/\*\*(.+?)\*\*/g, ' **$1** ')}
                  </Markdown>
                </section>
              ) : (
                /* Fallback: show summary if no narrative */
                <section>
                  <p className="text-lg text-foreground/90 leading-relaxed">
                    {summary}
                  </p>
                </section>
              )}

              {/* Divider between narrative and archival data */}
              <div className="flex items-center gap-4">
                <div className="h-px flex-1 bg-border" />
                <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">Archival Data</span>
                <div className="h-px flex-1 bg-border" />
              </div>

              {/* Discovered Discrepancy */}
              {discrepancyDetected && (
                <section>
                  <div className="flex items-center gap-3 mb-4">
                    <AlertTriangle className="w-5 h-5 text-blood-red" />
                    <h2 className="font-serif text-xl text-parchment">Discovered Discrepancy</h2>
                  </div>
                  <div className="pl-8 border-l-2 border-blood-red/30">
                    <p className="text-foreground/80 leading-relaxed">
                      {discrepancyDetected}
                    </p>
                  </div>
                </section>
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

              {/* Hypothesis */}
              {hypothesis && (
                <section>
                  <div className="flex items-center gap-3 mb-4">
                    <Lightbulb className="w-5 h-5 text-gold" />
                    <h2 className="font-serif text-xl text-parchment">Hypothesis</h2>
                  </div>
                  <div className="pl-8 border-l-2 border-gold/30">
                    <p className="text-foreground/80 leading-relaxed">
                      {hypothesis}
                    </p>
                  </div>
                  {alternativeHypotheses.length > 0 && (
                    <div className="mt-4 pl-8">
                      <p className="text-sm text-muted-foreground mb-2 font-mono uppercase tracking-wide">Alternative Hypotheses:</p>
                      <ul className="space-y-2">
                        {alternativeHypotheses.map((alt, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-foreground/70">
                            <span className="text-gold font-mono text-xs mt-0.5">{(i + 1).toString().padStart(2, '0')}.</span>
                            <span>{alt}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </section>
              )}

              {/* Historical Context */}
              {mystery.historical_context && (
                <section>
                  <div className="flex items-center gap-3 mb-4">
                    <BookOpen className="w-5 h-5 text-parchment-dark" />
                    <h2 className="font-serif text-xl text-parchment">Historical Context</h2>
                  </div>
                  <div className="pl-8 border-l-2 border-parchment/30">
                    {politicalClimate && (
                      <p className="text-foreground/80 leading-relaxed">
                        {politicalClimate}
                      </p>
                    )}
                    {mystery.historical_context.relevant_events.length > 0 && (
                      <div className="mt-4">
                        <p className="text-xs font-mono text-muted-foreground uppercase mb-2">Related Events:</p>
                        <ul className="space-y-1">
                          {mystery.historical_context.relevant_events.map((event, i) => (
                            <li key={i} className="text-sm text-foreground/70">• {event}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {mystery.historical_context.key_figures.length > 0 && (
                      <div className="mt-4">
                        <p className="text-xs font-mono text-muted-foreground uppercase mb-2">Key Figures:</p>
                        <p className="text-sm text-foreground/70">{mystery.historical_context.key_figures.join(", ")}</p>
                      </div>
                    )}
                  </div>
                </section>
              )}

            </div>

            {/* Sidebar */}
            <aside className="lg:col-span-1">
              <div className="sticky top-24 space-y-6">
                {/* Story hooks */}
                {(mystery.story_hooks_en?.length ?? mystery.story_hooks.length) > 0 && (
                  <div className="aged-card letterpress-border rounded-sm p-5">
                    <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground mb-4">
                      Story Angles
                    </h3>
                    <ul className="space-y-2">
                      {(mystery.story_hooks_en ?? mystery.story_hooks).map((hook, i) => (
                        <li key={i} className="text-sm text-gold font-mono">
                          • {hook}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Classification notice */}
                <div className="border border-blood-red/30 bg-blood-red/5 rounded-sm p-4">
                  <p className="text-xs text-muted-foreground font-mono leading-relaxed">
                    <span className="text-blood-red">NOTICE:</span> This case file represents AI-generated analysis of archival records.
                    All sources should be independently verified.
                  </p>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}
