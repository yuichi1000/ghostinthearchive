/**
 * トップページのローディング UI
 * 言語切り替え時のページ遷移中に表示される
 */
export default function HomeLoading() {
  return (
    <div className="min-h-screen flex flex-col film-grain">
      {/* Header skeleton */}
      <div className="h-16 border-b border-border/50" />

      <main className="flex-1">
        {/* Hero skeleton */}
        <div className="py-16 md:py-24 text-center">
          <div className="h-6 w-64 bg-muted/20 rounded-sm mx-auto mb-4 animate-pulse" />
          <div className="h-12 w-96 bg-muted/20 rounded-sm mx-auto mb-6 animate-pulse" />
          <div className="h-4 w-80 bg-muted/15 rounded-sm mx-auto animate-pulse" />
        </div>

        {/* Mystery cards skeleton */}
        <section className="py-16 md:py-24">
          <div className="container mx-auto px-4">
            <div className="h-8 w-64 bg-muted/20 rounded-sm mb-12 animate-pulse" />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="border border-border rounded-sm p-6 space-y-4 animate-pulse">
                  <div className="h-5 w-3/4 bg-muted/20 rounded-sm" />
                  <div className="h-4 w-full bg-muted/15 rounded-sm" />
                  <div className="h-4 w-2/3 bg-muted/15 rounded-sm" />
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
