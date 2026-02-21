import Link from "next/link"
import { FileText, MapPin, Calendar, Star } from "lucide-react"
import { ResponsiveHeroImage } from "@/components/responsive-hero-image"
import type { FirestoreMystery } from "@ghost/shared/src/types/mystery"
import { localizeMystery } from "@ghost/shared/src/lib/localize"
import { cn } from "@ghost/shared/src/lib/utils"
import { ClassificationBadge } from "@/components/classification-badge"
import type { SupportedLang } from "@/lib/i18n/config"
import type { Dictionary } from "@/lib/i18n/dictionaries"

interface FeaturedMysteryCardProps {
  mystery: FirestoreMystery
  lang: SupportedLang
  label: string
  classificationLabels: Dictionary["classification"]
}

export function FeaturedMysteryCard({ mystery, lang, label, classificationLabels }: FeaturedMysteryCardProps) {
  const { title, summary } = localizeMystery(mystery, lang)

  const locations = mystery.historical_context?.geographic_scope || []
  const timePeriod = mystery.historical_context?.time_period || ""
  const hasImage = !!mystery.images?.hero

  return (
    <Link href={`/${lang}/mystery/${mystery.mystery_id}`} className="block group no-underline">
      <article className={cn(
        "aged-card letterpress-border rounded-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-black/20",
        hasImage && "lg:grid lg:grid-cols-2"
      )}>
        {/* ヒーロー画像 */}
        {hasImage && (
          <div className="relative overflow-hidden max-h-56 sm:max-h-64 lg:max-h-none lg:h-full">
            <ResponsiveHeroImage
              hero={mystery.images!.hero!}
              variants={mystery.images!.variants}
              alt={title}
              priority
              className="w-full h-full object-cover"
            />
            {/* モバイル: 下方向グラデーション */}
            <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[hsl(var(--card))] to-transparent pointer-events-none lg:hidden" />
            {/* PC: 右方向グラデーション（画像右端） */}
            <div className="hidden lg:block absolute top-0 right-0 bottom-0 w-24 bg-gradient-to-l from-[hsl(var(--card))] to-transparent pointer-events-none" />
          </div>
        )}

        <div className={cn(
          "p-6 md:p-8",
          hasImage && "lg:flex lg:flex-col lg:justify-center lg:py-10 lg:px-10"
        )}>
          {/* フィーチャーバッジ + 分類バッジ */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex items-center gap-2">
              <Star className="w-4 h-4 text-gold" />
              <span className="text-xs font-mono uppercase tracking-widest text-gold">
                {label}
              </span>
            </div>
            <ClassificationBadge mysteryId={mystery.mystery_id} labels={classificationLabels} />
          </div>

          {/* メタデータ */}
          <div className="flex items-start justify-between gap-3 mb-4">
            <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono uppercase tracking-wider">
              <FileText className="w-3.5 h-3.5 text-gold" />
              <span>{mystery.mystery_id}</span>
            </div>
            <time className="text-xs text-muted-foreground font-mono">
              {mystery.publishedAt
                ? mystery.publishedAt.toLocaleDateString()
                : mystery.createdAt.toLocaleDateString()}
            </time>
          </div>

          {/* タイトル */}
          <h3 className="font-serif text-2xl md:text-3xl lg:text-4xl text-parchment mb-3 leading-tight group-hover:text-gold transition-colors text-balance">
            {title}
          </h3>

          {/* サマリー全文 */}
          <p className="text-sm md:text-base text-foreground/80 leading-relaxed mb-6">
            {summary}
          </p>

          {/* フッターメタデータ */}
          <div className="flex items-center gap-3 pt-4 border-t border-border/50 text-xs text-muted-foreground">
            {locations.length > 0 && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {locations[0]}
                {locations.length > 1 && (
                  <span className="text-muted-foreground/70">
                    {classificationLabels.moreLocations.replace("{count}", String(locations.length - 1))}
                  </span>
                )}
              </span>
            )}
            {timePeriod && (
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {timePeriod}
              </span>
            )}
          </div>
        </div>
      </article>
    </Link>
  )
}
