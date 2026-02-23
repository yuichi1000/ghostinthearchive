import { MapPin, Clock, Calendar, FileText, Pen } from "lucide-react"
import type { ConfidenceLevel } from "@ghost/shared/src/types/mystery"
import { STORYTELLER_DISPLAY_NAMES } from "@ghost/shared/src/types/mystery"
import type { Dictionary } from "@/lib/i18n/dictionaries"
import { GhostConfidenceBadge } from "@/components/ghost-confidence-badge"

interface CaseFileHeaderProps {
  mysteryId: string
  title: string
  location: string
  timePeriod: string
  publishedAt?: Date
  publishedLabel?: string
  confidenceLevel?: ConfidenceLevel
  confidenceLabels?: Dictionary["confidence"]
  storyteller?: string
  storytellerBylineLabel?: string
}

export function CaseFileHeader({
  mysteryId,
  title,
  location,
  timePeriod,
  publishedAt,
  publishedLabel = "Published:",
  confidenceLevel,
  confidenceLabels,
  storyteller,
  storytellerBylineLabel = "Storytold by",
}: CaseFileHeaderProps) {
  const storytellerDisplayName = storyteller ? STORYTELLER_DISPLAY_NAMES[storyteller] || storyteller : null

  return (
    <div className="mb-12">
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center gap-2 px-3 py-1.5 border border-border bg-card rounded-sm">
          <FileText className="w-4 h-4 text-gold" />
          <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
            {mysteryId}
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
        {publishedAt && (
          <span className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gold" />
            {publishedLabel} {publishedAt.toLocaleDateString()}
          </span>
        )}
        {storytellerDisplayName && (
          <span className="flex items-center gap-2">
            <Pen className="w-4 h-4 text-gold" />
            {storytellerBylineLabel} {storytellerDisplayName}
          </span>
        )}
        {confidenceLevel && confidenceLabels && (
          <GhostConfidenceBadge level={confidenceLevel} labels={confidenceLabels} />
        )}
      </div>
    </div>
  )
}
