interface DetailSidebarLabels {
  storyAngles?: string
  classificationNotice?: string
}

interface DetailSidebarProps {
  storyHooks: string[]
  labels?: DetailSidebarLabels
  children?: React.ReactNode
}

export function DetailSidebar({ storyHooks, labels, children }: DetailSidebarProps) {
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
