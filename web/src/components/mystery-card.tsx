import Link from "next/link"
import { FileText, MapPin, Calendar } from "lucide-react"
import type { FirestoreMystery } from "@/types/mystery"
import { cn } from "@/lib/utils"

interface MysteryCardProps {
  mystery: FirestoreMystery
  className?: string
}

export function MysteryCard({ mystery, className }: MysteryCardProps) {
  // Prefer English fields for public display
  const title = mystery.title_en || mystery.title
  const summary = mystery.summary_en || mystery.summary

  const location = mystery.historical_context?.geographic_scope?.[0] || ""
  const timePeriod = mystery.historical_context?.time_period || ""

  return (
    <Link href={`/mystery/${mystery.mystery_id}`} className={cn("block group no-underline", className)}>
      <article className="aged-card letterpress-border rounded-sm p-5 h-full transition-all duration-300 hover:bg-paper-light hover:border-parchment-dark/30 hover:shadow-lg hover:shadow-black/20">
        {/* File tab decoration */}
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono uppercase tracking-wider">
            <FileText className="w-3.5 h-3.5 text-gold" />
            <span>{mystery.mystery_id}</span>
          </div>
          <time className="text-xs text-muted-foreground font-mono">
            {mystery.publishedAt
              ? mystery.publishedAt.toLocaleDateString()
              : mystery.createdAt.toLocaleDateString()}
          </time>
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
          {location && (
            <span className="flex items-center gap-1">
              <MapPin className="w-3 h-3" />
              {location}
            </span>
          )}
          {timePeriod && (
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {timePeriod}
            </span>
          )}
        </div>
      </article>
    </Link>
  )
}
