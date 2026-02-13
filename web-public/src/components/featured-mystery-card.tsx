import Link from "next/link"
import { FileText, MapPin, Calendar, Star } from "lucide-react"
import { ResponsiveHeroImage } from "@/components/responsive-hero-image"
import type { FirestoreMystery } from "@ghost/shared/src/types/mystery"
import { localizeMystery } from "@ghost/shared/src/lib/localize"
import type { SupportedLang } from "@/lib/i18n/config"

interface FeaturedMysteryCardProps {
  mystery: FirestoreMystery
  lang: SupportedLang
  label: string
}

export function FeaturedMysteryCard({ mystery, lang, label }: FeaturedMysteryCardProps) {
  const { title, summary } = localizeMystery(mystery, lang)

  const location = mystery.historical_context?.geographic_scope?.[0] || ""
  const timePeriod = mystery.historical_context?.time_period || ""

  return (
    <Link href={`/${lang}/mystery/${mystery.mystery_id}`} className="block group no-underline">
      <article className="aged-card letterpress-border rounded-sm overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-black/20">
        {/* ヒーロー画像 */}
        {mystery.images?.hero && (
          <div className="relative overflow-hidden">
            <ResponsiveHeroImage
              hero={mystery.images.hero}
              variants={mystery.images.variants}
              alt={title}
              priority
            />
            <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[hsl(var(--card))] to-transparent pointer-events-none" />
          </div>
        )}

        <div className="p-6 md:p-8">
          {/* フィーチャーバッジ */}
          <div className="flex items-center gap-2 mb-4">
            <Star className="w-4 h-4 text-gold" />
            <span className="text-xs font-mono uppercase tracking-widest text-gold">
              {label}
            </span>
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
            {location && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {location}
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
