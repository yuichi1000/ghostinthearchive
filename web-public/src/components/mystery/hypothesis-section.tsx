import { Lightbulb } from "lucide-react"

interface HypothesisSectionProps {
  hypothesis: string
  alternativeHypotheses: string[]
}

export function HypothesisSection({ hypothesis, alternativeHypotheses }: HypothesisSectionProps) {
  return (
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
  )
}
