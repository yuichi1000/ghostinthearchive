import React from "react"
import Link from "next/link"
import { FileText, MapPin, Clock, Ghost, FileQuestion, AlertTriangle, User, Calendar } from "lucide-react"
import type { FirestoreMystery, DiscrepancyType, ConfidenceLevel } from "@/types/mystery"
import { DISCREPANCY_TYPE_LABELS } from "@/types/mystery"
import { cn } from "@/lib/utils"

const discrepancyIcons: Record<DiscrepancyType, React.ReactNode> = {
  date_mismatch: <Clock className="w-3.5 h-3.5" />,
  person_missing: <User className="w-3.5 h-3.5" />,
  event_outcome: <AlertTriangle className="w-3.5 h-3.5" />,
  location_conflict: <MapPin className="w-3.5 h-3.5" />,
  narrative_gap: <Ghost className="w-3.5 h-3.5" />,
  name_variant: <FileQuestion className="w-3.5 h-3.5" />,
}

const discrepancyColors: Record<DiscrepancyType, string> = {
  date_mismatch: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  person_missing: "bg-gold/20 text-[#d4af37] border-gold/30",
  event_outcome: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  location_conflict: "bg-teal/20 text-[#5fb3a1] border-teal/30",
  narrative_gap: "bg-parchment/20 text-parchment border-parchment/30",
  name_variant: "bg-gold/20 text-[#d4af37] border-gold/30",
}

const confidenceColors: Record<ConfidenceLevel, string> = {
  high: "text-[#ff6b6b]",
  medium: "text-[#d4af37]",
  low: "text-muted-foreground",
}

interface MysteryCardProps {
  mystery: FirestoreMystery
  className?: string
}

export function MysteryCard({ mystery, className }: MysteryCardProps) {
  const location = mystery.historical_context?.geographic_scope?.[0] || ""
  const timePeriod = mystery.historical_context?.time_period || ""

  return (
    <Link href={`/mystery/${mystery.mystery_id}`} className={cn("block group no-underline", className)}>
      <article className="aged-card letterpress-border rounded-sm p-5 h-full transition-all duration-300 hover:bg-paper-light hover:border-parchment-dark/30 hover:shadow-lg hover:shadow-black/20">
        {/* File tab decoration */}
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono uppercase tracking-wider">
            <FileText className="w-3.5 h-3.5 text-gold" />
            <span>Case File #{mystery.mystery_id.slice(-3).padStart(4, '0')}</span>
          </div>
          <time className="text-xs text-muted-foreground font-mono">
            {mystery.publishedAt
              ? mystery.publishedAt.toLocaleDateString()
              : mystery.createdAt.toLocaleDateString()}
          </time>
        </div>

        {/* Title */}
        <h3 className="font-serif text-lg text-parchment mb-1 leading-tight group-hover:text-gold transition-colors text-balance">
          {mystery.title}
        </h3>

        {/* Summary */}
        <p className="text-sm text-foreground/80 leading-relaxed mb-4 line-clamp-3">
          {mystery.summary}
        </p>

        {/* Badges */}
        <div className="flex flex-wrap gap-2 mb-4">
          <span className={cn(
            "inline-flex items-center gap-1.5 text-xs px-2 py-1 rounded-sm border font-mono uppercase tracking-wide",
            discrepancyColors[mystery.discrepancy_type]
          )}>
            {discrepancyIcons[mystery.discrepancy_type]}
            {DISCREPANCY_TYPE_LABELS[mystery.discrepancy_type]}
          </span>
        </div>

        {/* Footer metadata */}
        <div className="flex items-center justify-between pt-3 border-t border-border/50">
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
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
          <div className="flex items-center gap-1 text-xs font-mono uppercase">
            <span className="text-muted-foreground">Confidence:</span>
            <span className={cn("font-medium", confidenceColors[mystery.confidence_level])}>
              {mystery.confidence_level}
            </span>
          </div>
        </div>
      </article>
    </Link>
  )
}
