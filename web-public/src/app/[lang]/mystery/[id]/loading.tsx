/**
 * 記事詳細ページのローディング UI
 * 言語切り替え時のページ遷移中に表示される
 */
export default function MysteryDetailLoading() {
  return (
    <div className="min-h-screen flex flex-col film-grain">
      {/* Header skeleton */}
      <div className="h-16 border-b border-border/50" />

      <main className="flex-1 py-8 md:py-12">
        <div className="container mx-auto px-4">
          {/* Back link skeleton */}
          <div className="h-5 w-40 bg-muted/20 rounded-sm mb-8 animate-pulse" />

          {/* Case file header skeleton */}
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-6">
              <div className="h-8 w-48 bg-muted/20 rounded-sm animate-pulse" />
            </div>
            <div className="h-10 w-3/4 bg-muted/20 rounded-sm mb-4 animate-pulse" />
            <div className="h-6 w-1/2 bg-muted/20 rounded-sm animate-pulse" />
          </div>

          {/* Hero image skeleton */}
          <div className="mb-12 rounded-sm border border-border aspect-video bg-muted/10 animate-pulse" />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 lg:gap-12">
            {/* Main content skeleton */}
            <div className="lg:col-span-2 space-y-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="h-4 bg-muted/15 rounded-sm animate-pulse" style={{ width: `${85 + Math.random() * 15}%` }} />
              ))}
            </div>

            {/* Sidebar skeleton */}
            <div className="lg:col-span-1">
              <div className="h-48 bg-muted/10 rounded-sm animate-pulse" />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
