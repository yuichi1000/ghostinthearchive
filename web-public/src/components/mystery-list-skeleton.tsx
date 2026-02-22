import { FeaturedMysteryCardSkeleton } from "@/components/featured-mystery-card-skeleton"
import { MysteryCardSkeleton } from "@/components/mystery-card-skeleton"

/**
 * ホームページ用スケルトン — Featured カード + グリッド
 */
export function MysteryListSkeleton() {
  return (
    <>
      <div className="mb-12">
        <FeaturedMysteryCardSkeleton />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <MysteryCardSkeleton key={i} />
        ))}
      </div>
    </>
  )
}

/**
 * アーカイブページ用スケルトン — グリッドのみ
 */
export function MysteryGridSkeleton({ count = 12 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(count)].map((_, i) => (
        <MysteryCardSkeleton key={i} />
      ))}
    </div>
  )
}
