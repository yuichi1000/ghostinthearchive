import type { SourceCoverage, AcademicCoverage } from "@ghost/shared/src/types/mystery"
import type { Dictionary } from "@/lib/i18n/dictionaries"

interface SourceCoverageCardProps {
  sourceCoverage: SourceCoverage
  academicCoverage?: AcademicCoverage
  languagesAnalyzed?: string[]
  confidenceRationale?: string
  labels: Dictionary["sourceCoverage"]
}

export function SourceCoverageCard({
  sourceCoverage,
  academicCoverage,
  languagesAnalyzed,
  confidenceRationale,
  labels,
}: SourceCoverageCardProps) {
  return (
    <div className="aged-card letterpress-border rounded-sm p-5">
      <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground mb-4">
        {labels.heading}
      </h3>

      {/* 分析言語 */}
      {languagesAnalyzed && languagesAnalyzed.length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1.5">
            {labels.languagesAnalyzed}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {languagesAnalyzed.map((lang) => (
              <span
                key={lang}
                className="inline-flex px-1.5 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider bg-gold/10 text-gold border border-gold/20"
              >
                {lang}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 検索アーカイブ */}
      {sourceCoverage.apis_searched.length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground mb-1.5">
            {labels.apisSearched}
          </p>
          <ul className="space-y-0.5">
            {sourceCoverage.apis_searched.map((api) => (
              <li key={api} className="text-xs text-foreground/70 font-mono">
                &bull; {api}
              </li>
            ))}
          </ul>
        </div>
      )}

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

      {/* カバレッジ注記 */}
      <p className="text-[10px] text-muted-foreground/60 leading-relaxed mt-3 pt-3 border-t border-border">
        {labels.coverageNote}
      </p>
    </div>
  )
}
