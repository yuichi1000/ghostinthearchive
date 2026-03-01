"use client"

import { ExternalLink, FileText } from "lucide-react"
import type { Evidence } from "../types/mystery"
import { cn } from "../lib/utils"
import { getArchiveName } from "../lib/archive-name"

interface EvidenceLabels {
  source?: string
  view?: string
  originalText?: string
}

interface EvidenceBlockProps {
  evidence: Evidence
  label?: string
  translatedExcerpt?: string
  labels?: EvidenceLabels
  className?: string
}

export function EvidenceBlock({ evidence, label, translatedExcerpt, labels, className }: EvidenceBlockProps) {
  const sourceLabel = labels?.source ?? "Source:"
  const viewLabel = labels?.view ?? "View"
  const originalTextLabel = labels?.originalText ?? "Original text"

  // 空 excerpt のフォールバック: テキスト部分を非表示にする（既存 Firestore データ対応）
  const hasExcerpt = !!evidence.relevant_excerpt?.trim()
  const hasTranslatedExcerpt = !!translatedExcerpt?.trim()
  const archiveName = getArchiveName(evidence)

  return (
    <figure className={cn("relative group", className)}>
      {label && (
        <div className="mb-2 text-xs font-mono uppercase tracking-wider text-muted-foreground">
          {label}
        </div>
      )}

      <blockquote
        className="relative bg-gradient-to-br from-paper via-paper-light to-paper p-5 border border-border rounded-sm transform rotate-[-0.3deg] hover:rotate-0 transition-transform duration-300 shadow-lg"
      >
        {/* Top edge wear effect */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-b from-parchment/10 to-transparent" />

        {/* Date badge + Quote marks row */}
        <div className="flex items-start justify-between mb-1">
          {(hasExcerpt || hasTranslatedExcerpt) && (
            <div className="text-4xl text-parchment/20 font-serif leading-none" aria-hidden="true">
              &ldquo;
            </div>
          )}
          {evidence.source_date && (
            <div className={cn(
              "px-2 py-0.5 bg-blood-red/20 border border-blood-red/30 rounded-sm shrink-0",
              !(hasExcerpt || hasTranslatedExcerpt) && "ml-auto"
            )}>
              <span className="text-xs font-mono text-[#ff6b6b]">{evidence.source_date}</span>
            </div>
          )}
        </div>

        {/* Evidence text: 翻訳があればメインに、原文はサブに。空 excerpt は非表示。 */}
        {hasTranslatedExcerpt ? (
          <div className="relative pl-6">
            <p className="text-sm text-foreground/90 leading-relaxed font-mono whitespace-pre-wrap">
              {translatedExcerpt}
            </p>
            {hasExcerpt && (
              <div className="mt-3 pt-3 border-t border-border/30">
                <p className="text-xs text-muted-foreground/60 mb-1 font-mono uppercase tracking-wider">
                  {originalTextLabel}
                </p>
                <p className="text-xs text-foreground/50 leading-relaxed font-mono whitespace-pre-wrap">
                  {evidence.relevant_excerpt}
                </p>
              </div>
            )}
          </div>
        ) : hasExcerpt ? (
          <p className="relative text-sm text-foreground/90 leading-relaxed pl-6 font-mono whitespace-pre-wrap">
            {evidence.relevant_excerpt}
          </p>
        ) : null}
      </blockquote>

      {/* Source citation */}
      <figcaption className="mt-3 flex items-start justify-between gap-4 px-2">
        <div className="flex items-start gap-2 flex-1 min-w-0">
          <FileText className="w-4 h-4 text-gold shrink-0 mt-0.5" />
          <p className="text-xs text-muted-foreground leading-relaxed">
            <span className="text-parchment/80 font-medium">{sourceLabel} </span>
            {archiveName && (
              <>
                <span className="text-gold/70">{archiveName}</span>
                <span className="text-muted-foreground/40"> — </span>
              </>
            )}
            {evidence.source_title}
          </p>
        </div>
        {evidence.source_url && (
          <a
            href={evidence.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-gold hover:text-parchment transition-colors shrink-0 no-underline"
          >
            {viewLabel}
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </figcaption>
    </figure>
  )
}
