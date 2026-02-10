import { AlertTriangle } from "lucide-react"

interface DiscrepancySectionProps {
  discrepancyDetected: string
}

export function DiscrepancySection({ discrepancyDetected }: DiscrepancySectionProps) {
  return (
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
  )
}
