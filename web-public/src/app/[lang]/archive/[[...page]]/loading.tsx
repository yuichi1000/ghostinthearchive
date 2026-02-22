/**
 * アーカイブページのローディング UI
 * 言語切り替え時のページ遷移中に表示される
 */
import { MysteryGridSkeleton } from "@/components/mystery-list-skeleton"

export default function ArchiveLoading() {
  return (
    <div className="min-h-screen flex flex-col film-grain">
      {/* Header skeleton */}
      <div className="h-16 border-b border-border/50" />

      <main className="flex-1">
        <section className="py-16 md:py-24">
          <div className="container mx-auto px-4">
            {/* 見出しスケルトン */}
            <div className="mb-12">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-6 h-6 bg-muted/20 rounded-sm animate-pulse" />
                <div className="h-9 w-48 bg-muted/20 rounded-sm animate-pulse" />
              </div>
              <div className="h-4 w-80 bg-muted/15 rounded-sm animate-pulse" />
              <div className="mt-4 h-px bg-gradient-to-r from-border to-transparent" />
            </div>

            {/* グリッドスケルトン */}
            <MysteryGridSkeleton />
          </div>
        </section>
      </main>
    </div>
  )
}
