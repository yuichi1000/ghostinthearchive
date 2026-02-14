export function FeaturedMysteryCardSkeleton() {
  return (
    <div className="aged-card letterpress-border rounded-sm overflow-hidden animate-pulse lg:grid lg:grid-cols-2">
      {/* 画像プレースホルダー */}
      <div className="h-56 sm:h-64 lg:h-auto lg:min-h-[280px] bg-muted" />

      <div className="p-6 md:p-8 lg:flex lg:flex-col lg:justify-center lg:py-10 lg:px-10">
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
