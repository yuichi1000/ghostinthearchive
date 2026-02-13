import { MapPin, Clock, Calendar, FileText } from "lucide-react"

interface CaseFileHeaderProps {
  mysteryId: string
  title: string
  location: string
  timePeriod: string
  publishedAt?: Date
  publishedLabel?: string
}

export function CaseFileHeader({
  mysteryId,
  title,
  location,
  timePeriod,
  publishedAt,
  publishedLabel = "Published:",
}: CaseFileHeaderProps) {
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
      </div>
    </div>
  )
}
