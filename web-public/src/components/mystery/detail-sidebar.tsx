interface DetailSidebarProps {
  storyHooks: string[]
}

export function DetailSidebar({ storyHooks }: DetailSidebarProps) {
  return (
    <aside className="lg:col-span-1">
      <div className="sticky top-24 space-y-6">
        {/* Story hooks */}
        {storyHooks.length > 0 && (
          <div className="aged-card letterpress-border rounded-sm p-5">
            <h3 className="font-mono text-xs uppercase tracking-wider text-muted-foreground mb-4">
              Story Angles
            </h3>
            <ul className="space-y-2">
              {storyHooks.map((hook, i) => (
                <li key={i} className="text-sm text-gold font-mono">
                  • {hook}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Classification notice */}
        <div className="border border-blood-red/30 bg-blood-red/5 rounded-sm p-4">
          <p className="text-xs text-muted-foreground font-mono leading-relaxed">
            <span className="text-blood-red">NOTICE:</span> This case file represents AI-generated analysis of archival records.
            All sources should be independently verified.
          </p>
        </div>
      </div>
    </aside>
  )
}
