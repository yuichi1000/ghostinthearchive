export function MysteryCardSkeleton() {
  return (
    <div className="aged-card letterpress-border rounded-sm p-5 h-64 animate-pulse">
      <div className="h-4 bg-muted rounded w-1/3 mb-4" />
      <div className="h-6 bg-muted rounded w-2/3 mb-2" />
      <div className="h-4 bg-muted rounded w-full mb-2" />
      <div className="h-4 bg-muted rounded w-4/5 mb-4" />
      <div className="h-6 bg-muted rounded w-1/4" />
    </div>
  )
}
