import { Suspense } from "react"
import { notFound } from "next/navigation"
import { Header } from "@/components/header"
import { Footer } from "@ghost/shared/src/components/footer"
import { FeaturedMysteryCard } from "@/components/featured-mystery-card"
import { FeaturedMysteryCardSkeleton } from "@/components/featured-mystery-card-skeleton"
import { MysteryCard } from "@/components/mystery-card"
import { MysteryCardSkeleton } from "@/components/mystery-card-skeleton"
import { getPublishedMysteries } from "@ghost/shared/src/lib/firestore/queries"
import { HOMEPAGE_MYSTERY_LIMIT } from "@/lib/constants"
import Link from "next/link"
import { FileStack, Search } from "lucide-react"
import { SiteIntro } from "@/components/site-intro"
import { ClassificationGuide } from "@/components/classification-guide"
import { isValidLang } from "@/lib/i18n/config"
import type { SupportedLang } from "@/lib/i18n/config"
import { getDictionary } from "@/lib/i18n/dictionaries"
import type { Dictionary } from "@/lib/i18n/dictionaries"

async function MysteryList({ lang, dict }: { lang: SupportedLang; dict: Dictionary }) {
  let mysteries: Awaited<ReturnType<typeof getPublishedMysteries>> = []
  try {
    mysteries = await getPublishedMysteries(HOMEPAGE_MYSTERY_LIMIT)
  } catch (error) {
    console.error("[MysteryList] Firestore クエリ失敗:", error)
    // SSG ビルドエラーの診断用に詳細を出力
    if (error instanceof Error) {
      console.error("[MysteryList] Stack:", error.stack)
    }
  }

  if (mysteries.length === 0) {
    return (
      <div className="text-center py-16">
        <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" aria-hidden="true" />
        <h2 className="font-serif text-xl text-parchment mb-2">
          {dict.home.noMysteries}
        </h2>
        <p className="text-muted-foreground">
          {dict.home.noMysteriesDesc}
        </p>
      </div>
    )
  }

  const [featured, ...rest] = mysteries

  return (
    <>
      {/* フィーチャー記事 */}
      <div className="mb-12">
        <FeaturedMysteryCard
          mystery={featured}
          lang={lang}
          label={dict.home.featuredStory}
          classificationLabels={dict.classification}
        />
      </div>

      {/* グリッド */}
      {rest.length > 0 && (
        <>
          <div className="flex items-center gap-4 mb-8">
            <div className="flex items-center gap-3">
              <FileStack className="w-5 h-5 text-gold" />
              <h2 className="font-serif text-2xl md:text-3xl text-parchment">
                {dict.home.latestDiscoveries}
              </h2>
            </div>
            <div className="flex-1 h-px bg-gradient-to-r from-border to-transparent" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {rest.map((mystery) => (
              <MysteryCard key={mystery.mystery_id} mystery={mystery} lang={lang} classificationLabels={dict.classification} />
            ))}
          </div>
        </>
      )}
    </>
  )
}

function MysteryListSkeleton() {
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

export default async function HomePage({
  params,
}: {
  params: Promise<{ lang: string }>
}) {
  const { lang } = await params
  if (!isValidLang(lang)) notFound()

  const dict = await getDictionary(lang)

  return (
    <div className="min-h-screen flex flex-col film-grain">
      <Header lang={lang} nav={dict.nav} />

      <main className="flex-1">
        {/* サイトイントロ */}
        <SiteIntro dict={dict} />

        {/* 記事一覧 */}
        <section className="pb-16 md:pb-24">
          <div className="container mx-auto px-4">
            <Suspense fallback={<MysteryListSkeleton />}>
              <MysteryList lang={lang} dict={dict} />
            </Suspense>
          </div>
        </section>

        {/* 分類インデックス */}
        <ClassificationGuide lang={lang} dict={dict} />

        {/* アーカイブ導線 */}
        <section className="pb-16">
          <div className="container mx-auto px-4 text-center">
            <Link
              href={`/${lang}/archive`}
              className="inline-block text-sm font-mono text-muted-foreground hover:text-gold transition-colors no-underline"
            >
              <span className="redacted">████</span> {dict.home.viewAllArticles} → <span className="redacted">████</span>
            </Link>
          </div>
        </section>
      </main>

      <Footer
        labels={dict.footer}
        siteLinks={[
          { label: dict.footer.home, href: `/${lang}` },
          { label: dict.footer.archive, href: `/${lang}/archive` },
          { label: dict.footer.about, href: `/${lang}/about` },
        ]}
      />
    </div>
  )
}
