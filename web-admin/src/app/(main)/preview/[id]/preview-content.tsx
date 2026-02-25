"use client"

import Link from "next/link"
import Image from "next/image"
import { EvidenceBlock } from "@ghost/shared/src/components/evidence-block"
import { localizeMystery, getTranslatedExcerpt } from "@ghost/shared/src/lib/localize"
import { LanguageSelector, type PreviewLang } from "@/components/language-selector"
import { useLanguage } from "@/contexts/language-context"
import type { FirestoreMystery } from "@ghost/shared/src/types/mystery"
import { ConfidenceBadge } from "@/components/status-badge"
import {
  ArrowLeft,
  MapPin,
  Clock,
  Calendar,
  FileText,
  AlertTriangle,
  BookOpen,
  Lightbulb,
  Eye
} from "lucide-react"
import Markdown, { type Components } from "react-markdown"
import remarkGfm from "remark-gfm"
import { rehypeUnwrapImages } from "@ghost/shared/src/lib/rehype-unwrap-images"
import { normalizeImagePlacement } from "@ghost/shared/src/lib/normalize-image-placement"
import { stripLeadingH1 } from "@ghost/shared/src/lib/utils"
import { useState } from "react"

/**
 * Date は Server→Client シリアライズで string になるため、
 * toLocaleDateString を安全に呼ぶヘルパー
 */
function formatDate(d: Date | string | undefined): string {
  if (!d) return ""
  const date = typeof d === "string" ? new Date(d) : d
  return date.toLocaleDateString()
}

function PreviewArchiveImage({ src, alt }: { src?: string; alt?: string }) {
  const [hasError, setHasError] = useState(false)
  if (!src || hasError) return null
  return (
    <figure className="not-prose my-8 flex flex-col items-center">
      <img
        src={src}
        alt={alt || "Archival Image"}
        loading="lazy"
        onError={() => setHasError(true)}
        className="h-auto max-w-full"
      />
      {alt && (
        <figcaption className="mt-2 text-center text-xs font-mono text-muted-foreground/70 leading-relaxed">
          <span className="uppercase tracking-wider text-gold/60">Archival Image</span>
          {" — "}
          {alt}
        </figcaption>
      )}
    </figure>
  )
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
  } = localizeMystery(mystery, lang)

  // 証拠の翻訳済み抜粋テキスト
  const evidenceAExcerpt = getTranslatedExcerpt(mystery, "a", lang)
  const evidenceBExcerpt = getTranslatedExcerpt(mystery, "b", lang)

  const location = mystery.historical_context?.geographic_scope?.join(", ") || ""
  const timePeriod = mystery.historical_context?.time_period || ""

  // Status badge color
  const statusColors: Record<string, string> = {
    pending: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    translating: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    published: "bg-green-500/20 text-green-400 border-green-500/30",
    archived: "bg-gray-500/20 text-gray-400 border-gray-500/30",
    error: "bg-red-500/20 text-red-400 border-red-500/30",
  }

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

          {/* Case file header */}
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center gap-2 px-3 py-1.5 border border-border bg-card rounded-sm">
                <FileText className="w-4 h-4 text-gold" />
                <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                  Case File #{mystery.mystery_id.slice(-3).padStart(4, '0')}
                </span>
              </div>
              <div className={`px-3 py-1.5 border rounded-sm text-xs font-mono uppercase ${statusColors[mystery.status] || statusColors.pending}`}>
                {mystery.status}
              </div>
              <ConfidenceBadge level={mystery.confidence_level} />
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
              {mystery.createdAt && (
                <span className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gold" />
                  Created: {formatDate(mystery.createdAt)}
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
            {/* Main content */}
            <div className="lg:col-span-2 space-y-12">
              {/* Hero image — 学術書の図版のようなフレーミング */}
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

              {/* Narrative Content (primary) */}
              {narrativeContent ? (
                <section className="prose prose-lg prose-invert max-w-none prose-headings:font-serif prose-headings:text-parchment prose-headings:mt-12 prose-headings:mb-4 prose-p:text-foreground/90 prose-p:leading-loose prose-p:mb-6 prose-a:text-gold prose-blockquote:border-gold/30 prose-blockquote:bg-card prose-blockquote:px-6 prose-blockquote:py-4 prose-blockquote:rounded-sm prose-blockquote:text-foreground/70 prose-blockquote:italic prose-blockquote:font-serif prose-strong:text-parchment prose-hr:border-border">
                  <Markdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeUnwrapImages]}
                    components={{
                      img: ({ src, alt }) => <PreviewArchiveImage src={src} alt={alt} />,
                    }}
                  >
                    {normalizeImagePlacement(stripLeadingH1(narrativeContent).replace(/\*\*(.+?)\*\*/g, ' **$1** '))}
                  </Markdown>
                </section>
              ) : (
                /* Fallback: show summary if no narrative */
                <section>
                  <div className="border border-amber-500/30 bg-amber-500/5 rounded-sm p-4 mb-6">
                    <p className="text-xs text-amber-400 font-mono">
                      No narrative content yet. Showing summary only.
                    </p>
                  </div>
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
                            <li key={i} className="text-sm text-foreground/70">{event}</li>
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
                {storyHooks.length > 0 && (
                  <div className="aged-card letterpress-border rounded-sm p-5">
                    <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground mb-4">
                      Story Angles
                    </h3>
                    <ul className="space-y-2">
                      {storyHooks.map((hook, i) => (
                        <li key={i} className="text-sm text-gold font-mono">
                          &bull; {hook}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Preview notice */}
                <div className="border border-amber-500/30 bg-amber-500/5 rounded-sm p-4">
                  <p className="text-xs text-amber-400 font-mono leading-relaxed">
                    <span className="font-bold">PREVIEW:</span> This is a preview of the article before publication.
                    Content may change before final publication.
                  </p>
                </div>

                {/* Source coverage */}
                {mystery.source_coverage && (
                  <div className="aged-card letterpress-border rounded-sm p-5">
                    <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground mb-4">
                      Investigation Scope
                    </h3>

                    {mystery.languages_analyzed && mystery.languages_analyzed.length > 0 && (
                      <div className="mb-3">
                        <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1.5">
                          Languages Analyzed
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {mystery.languages_analyzed.map((lang) => (
                            <span
                              key={lang}
                              className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-gold/10 text-gold border border-gold/20"
                            >
                              {lang}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {mystery.source_coverage.apis_searched.length > 0 && (
                      <div className="mb-3">
                        <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1.5">
                          Archives Searched
                        </p>
                        <ul className="space-y-0.5">
                          {mystery.source_coverage.apis_searched.map((api) => (
                            <li key={api} className="text-xs text-foreground/70 font-mono">
                              &bull; {api}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {mystery.confidence_rationale && (
                      <div className="mb-3">
                        <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1.5">
                          Assessment Rationale
                        </p>
                        <p className="text-xs text-foreground/70 leading-relaxed">
                          {mystery.confidence_rationale}
                        </p>
                      </div>
                    )}

                    <p className="text-[10px] text-muted-foreground/60 leading-relaxed mt-3 pt-3 border-t border-border">
                      This analysis is based on materials available through the digital archive APIs listed above.
                    </p>
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
      </div>
    </>
  )
}
