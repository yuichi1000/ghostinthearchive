interface SourceCoverageLabels {
  heading: string
}

interface SourceCoverageCardProps {
  confidenceRationale?: string
  labels: SourceCoverageLabels
}

export function SourceCoverageCard({
  confidenceRationale,
  labels,
}: SourceCoverageCardProps) {
  return (
    <div className="aged-card letterpress-border rounded-sm p-5">
      <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground mb-4">
        {labels.heading}
      </h3>
      {confidenceRationale && (
        <p className="text-xs text-foreground/70 leading-relaxed">
          {confidenceRationale}
        </p>
      )}
    </div>
  )
}
