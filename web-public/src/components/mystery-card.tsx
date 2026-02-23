import Image from "next/image"
import Link from "next/link"
import { FileText, MapPin, Calendar } from "lucide-react"
import type { FirestoreMystery } from "@ghost/shared/src/types/mystery"
import { cn } from "@ghost/shared/src/lib/utils"
import { localizeMystery } from "@ghost/shared/src/lib/localize"
import { ClassificationBadge } from "@/components/classification-badge"
import { GhostConfidenceBadge } from "@/components/ghost-confidence-badge"
import type { SupportedLang } from "@/lib/i18n/config"
import type { Dictionary } from "@/lib/i18n/dictionaries"

interface MysteryCardProps {
  mystery: FirestoreMystery
  lang?: SupportedLang
  classificationLabels: Dictionary["classification"]
  confidenceLabels: Dictionary["confidence"]
  className?: string
}

export function MysteryCard({ mystery, lang = "en", classificationLabels, confidenceLabels, className }: MysteryCardProps) {
  const { title, summary } = localizeMystery(mystery, lang)

  const locations = mystery.historical_context?.geographic_scope || []
  const timePeriod = mystery.historical_context?.time_period || ""
  const thumbnailUrl = mystery.images?.thumbnail

  return (
    <Link href={`/${lang}/mystery/${mystery.mystery_id}`} className={cn("block group no-underline", className)}>
      <article className="aged-card letterpress-border rounded-sm p-5 h-full transition-all duration-300 hover:bg-paper-light hover:border-parchment-dark/30 hover:shadow-lg hover:shadow-black/20">
        <div className={cn(thumbnailUrl && "grid grid-cols-[96px_1fr] gap-4")}>
          {/* サムネイル（あれば表示） */}
          {thumbnailUrl && (
            <div className="w-24 h-24 rounded-sm overflow-hidden flex-shrink-0 border border-border/30">
              <Image
                src={thumbnailUrl}
                alt=""
                width={96}
                height={96}
                className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
              />
            </div>
          )}

          <div className="min-w-0">
            {/* File tab decoration */}
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono uppercase tracking-wider">
                <FileText className="w-3.5 h-3.5 text-gold" />
                <span>{mystery.mystery_id}</span>
              </div>
              <time className="text-xs text-muted-foreground font-mono shrink-0">
                {mystery.publishedAt
                  ? mystery.publishedAt.toLocaleDateString()
                  : mystery.createdAt.toLocaleDateString()}
              </time>
            </div>

            {/* 分類バッジ + ゴーストレベル */}
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <ClassificationBadge mysteryId={mystery.mystery_id} labels={classificationLabels} />
              {mystery.confidence_level && (
                <GhostConfidenceBadge level={mystery.confidence_level} labels={confidenceLabels} />
              )}
            </div>

            {/* Title */}
            <h3 className="font-serif text-lg text-parchment mb-1 leading-tight group-hover:text-gold transition-colors text-balance">
              {title}
            </h3>

            {/* Summary */}
            <p className="text-sm text-foreground/80 leading-relaxed mb-4 line-clamp-3">
              {summary}
            </p>

            {/* Footer metadata */}
            <div className="flex items-center gap-3 pt-3 border-t border-border/50 text-xs text-muted-foreground">
              {locations.length > 0 && (
                <span className="flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  {locations[0]}
                  {locations.length > 1 && (
                    <span className="text-muted-foreground/70">
                      {classificationLabels.moreLocations.replace("{count}", String(locations.length - 1))}
                    </span>
                  )}
                </span>
              )}
              {timePeriod && (
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {timePeriod}
                </span>
              )}
            </div>
          </div>
        </div>
      </article>
    </Link>
  )
}
