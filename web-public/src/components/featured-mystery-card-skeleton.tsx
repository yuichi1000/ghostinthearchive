export function FeaturedMysteryCardSkeleton() {
  return (
    <div className="aged-card letterpress-border rounded-sm overflow-hidden animate-pulse">
      {/* 画像プレースホルダー */}
      <div className="h-64 md:h-80 bg-muted" />

      <div className="p-6 md:p-8">
        <div className="h-3 bg-muted rounded w-1/4 mb-4" />
        <div className="h-4 bg-muted rounded w-1/3 mb-4" />
        <div className="h-8 bg-muted rounded w-3/4 mb-3" />
        <div className="h-4 bg-muted rounded w-full mb-2" />
        <div className="h-4 bg-muted rounded w-5/6 mb-6" />
        <div className="h-6 bg-muted rounded w-1/4" />
      </div>
    </div>
  )
}
