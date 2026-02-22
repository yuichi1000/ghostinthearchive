import type { SourceCoverage } from "@ghost/shared/src/types/mystery"
import type { Dictionary } from "@/lib/i18n/dictionaries"
import { SourceCoverageCard } from "@/components/mystery/source-coverage-card"

interface DetailSidebarLabels {
  storyAngles?: string
  classificationNotice?: string
}

interface DetailSidebarProps {
  storyHooks: string[]
  labels?: DetailSidebarLabels
  sourceCoverage?: SourceCoverage
  languagesAnalyzed?: string[]
  confidenceRationale?: string
  sourceCoverageLabels?: Dictionary["sourceCoverage"]
  children?: React.ReactNode
}

export function DetailSidebar({
  storyHooks,
  labels,
  sourceCoverage,
  languagesAnalyzed,
  confidenceRationale,
  sourceCoverageLabels,
  children,
}: DetailSidebarProps) {
  const storyAnglesLabel = labels?.storyAngles ?? "Story Angles"
  const noticeText = labels?.classificationNotice ?? "This case file represents AI-generated analysis of archival records. All sources should be independently verified."

  return (
    <aside className="lg:col-span-1">
      <div className="sticky top-24 space-y-6">
        {/* 目次（デスクトップ版、children から受け取る） */}
        {children}

        {/* Story hooks */}
        {storyHooks.length > 0 && (
          <div className="aged-card letterpress-border rounded-sm p-5">
            <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground mb-4">
              {storyAnglesLabel}
            </h3>
            <ul className="space-y-2">
              {storyHooks.map((hook, i) => (
                <li key={i} className="text-sm text-gold font-mono">
                  &bull; {hook}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Source coverage（schema_version=2 の記事のみ表示） */}
        {sourceCoverage && sourceCoverageLabels && (
          <SourceCoverageCard
            sourceCoverage={sourceCoverage}
            languagesAnalyzed={languagesAnalyzed}
            confidenceRationale={confidenceRationale}
            labels={sourceCoverageLabels}
          />
        )}

        {/* Classification notice */}
        <div className="border border-blood-red/30 bg-blood-red/5 rounded-sm p-4">
          <p className="text-xs text-muted-foreground font-mono leading-relaxed">
            <span className="text-blood-red">NOTICE:</span> {noticeText}
          </p>
        </div>
      </div>
    </aside>
  )
}
