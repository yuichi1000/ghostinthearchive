import { BookOpen } from "lucide-react"
import type { HistoricalContext } from "@ghost/shared/src/types/mystery"

interface HistoricalContextLabels {
  historicalContext?: string
  relatedEvents?: string
  keyFigures?: string
}

interface HistoricalContextSectionProps {
  historicalContext: HistoricalContext
  politicalClimate?: string
  labels?: HistoricalContextLabels
}

export function HistoricalContextSection({
  historicalContext,
  politicalClimate,
  labels,
}: HistoricalContextSectionProps) {
  const title = labels?.historicalContext ?? "Historical Context"
  const eventsLabel = labels?.relatedEvents ?? "Related Events:"
  const figuresLabel = labels?.keyFigures ?? "Key Figures:"

  return (
    <section id="section-historical-context" className="scroll-mt-24">
      <div className="flex items-center gap-3 mb-4">
        <BookOpen className="w-5 h-5 text-parchment-dark" />
        <h2 className="font-serif text-xl text-parchment">{title}</h2>
      </div>
      <div className="pl-8 border-l-2 border-parchment/30">
        {politicalClimate && (
          <p className="text-foreground/80 leading-relaxed">
            {politicalClimate}
          </p>
        )}
        {historicalContext.relevant_events.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-mono text-muted-foreground uppercase mb-2">{eventsLabel}</p>
            <ul className="space-y-1">
              {historicalContext.relevant_events.map((event, i) => (
                <li key={i} className="text-sm text-foreground/70">&bull; {event}</li>
              ))}
            </ul>
          </div>
        )}
        {historicalContext.key_figures.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-mono text-muted-foreground uppercase mb-2">{figuresLabel}</p>
            <p className="text-sm text-foreground/70">{historicalContext.key_figures.join(", ")}</p>
          </div>
        )}
      </div>
    </section>
  )
}
