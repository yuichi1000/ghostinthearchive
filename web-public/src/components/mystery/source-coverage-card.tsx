import type { AcademicCoverage } from "@ghost/shared/src/types/mystery"
import type { Dictionary } from "@/lib/i18n/dictionaries"

interface SourceCoverageCardProps {
  academicCoverage?: AcademicCoverage
  confidenceRationale?: string
  labels: Dictionary["sourceCoverage"]
}

export function SourceCoverageCard({
  academicCoverage,
  confidenceRationale,
  labels,
}: SourceCoverageCardProps) {
  return (
    <div className="aged-card letterpress-border rounded-sm p-5">
      <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground mb-4">
        {labels.heading}
      </h3>

      {/* 学術論文カバレッジ */}
      {academicCoverage && academicCoverage.papers_found > 0 && (
        <div className="mb-3">
          <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1.5">
            {labels.academicPapers}
          </p>
          <p className="text-xs text-foreground/70 font-mono mb-1.5">
            {academicCoverage.papers_found.toLocaleString()} papers
          </p>
          {Object.keys(academicCoverage.language_distribution).length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-1.5">
              {Object.entries(academicCoverage.language_distribution)
                .sort(([, a], [, b]) => b - a)
                .map(([lang, count]) => (
                  <span
                    key={lang}
                    className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-foreground/5 text-foreground/60 border border-border"
                  >
                    {lang}: {count}
                  </span>
                ))}
            </div>
          )}
          {academicCoverage.consensus_vs_primary && (
            <p className="text-xs text-foreground/70 leading-relaxed mt-1.5">
              {academicCoverage.consensus_vs_primary}
            </p>
          )}
        </div>
      )}

      {/* 判定根拠 */}
      {confidenceRationale && (
        <div className="mb-3">
          <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1.5">
            {labels.confidenceRationale}
          </p>
          <p className="text-xs text-foreground/70 leading-relaxed">
            {confidenceRationale}
          </p>
        </div>
      )}
    </div>
  )
}
