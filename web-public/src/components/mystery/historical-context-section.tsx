import { BookOpen } from "lucide-react"
import type { HistoricalContext } from "@/types/mystery"

interface HistoricalContextSectionProps {
  historicalContext: HistoricalContext
  politicalClimate?: string
}

export function HistoricalContextSection({
  historicalContext,
  politicalClimate,
}: HistoricalContextSectionProps) {
  return (
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
        {historicalContext.relevant_events.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-mono text-muted-foreground uppercase mb-2">Related Events:</p>
            <ul className="space-y-1">
              {historicalContext.relevant_events.map((event, i) => (
                <li key={i} className="text-sm text-foreground/70">• {event}</li>
              ))}
            </ul>
          </div>
        )}
        {historicalContext.key_figures.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-mono text-muted-foreground uppercase mb-2">Key Figures:</p>
            <p className="text-sm text-foreground/70">{historicalContext.key_figures.join(", ")}</p>
          </div>
        )}
      </div>
    </section>
  )
}
