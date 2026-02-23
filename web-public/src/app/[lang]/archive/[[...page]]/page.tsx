import { Suspense } from "react"
import { notFound } from "next/navigation"
import { Header } from "@/components/header"
import { PublicFooter } from "@/components/public-footer"
import { MysteryCard } from "@/components/mystery-card"
import { Pagination } from "@/components/pagination"
import { ArchiveFilter } from "@/components/archive-filter"
import type { MysteryEntry } from "@/components/archive-filter"
import { getPublishedMysteries, getAllPublishedMysteriesMap } from "@ghost/shared/src/lib/firestore/queries"
import { localizeMystery } from "@ghost/shared/src/lib/localize"
import { ARCHIVE_PAGE_SIZE } from "@/lib/constants"
import { FileStack, Search } from "lucide-react"
import { isValidLang, SUPPORTED_LANGS } from "@/lib/i18n/config"
import type { SupportedLang } from "@/lib/i18n/config"
import { getDictionary } from "@/lib/i18n/dictionaries"
import { buildOgpMetadata, buildAlternates } from "@/lib/seo"

// SSG: ビルド時に生成されたページ以外は 404
export const dynamicParams = false

export async function generateStaticParams() {
  const mysteries = await getPublishedMysteries(1000)
  const totalPages = Math.max(1, Math.ceil(mysteries.length / ARCHIVE_PAGE_SIZE))

  return SUPPORTED_LANGS.flatMap((lang) => {
    // ページ 1（パスなし）
    const pages: { lang: string; page?: string[] }[] = [{ lang, page: [] }]
    // ページ 2 以降
    for (let i = 2; i <= totalPages; i++) {
      pages.push({ lang, page: [String(i)] })
    }
    return pages
  })
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string; page?: string[] }>
}) {
  const { lang, page } = await params
  if (!isValidLang(lang)) return {}

  const dict = await getDictionary(lang)
  const currentPage = page?.length ? parseInt(page[0], 10) : 1
  const pageTitle = currentPage > 1
    ? `${dict.archive.heading} - ${dict.archive.page} ${currentPage} | Ghost in the Archive`
    : dict.archive.title

  return {
    title: pageTitle,
    description: dict.seo.archiveDescription,
    alternates: buildAlternates("archive"),
    ...buildOgpMetadata(lang, {
      title: dict.archive.heading,
      description: dict.seo.archiveDescription,
      path: "archive",
    }),
  }
}

export default async function ArchivePage({
  params,
}: {
  params: Promise<{ lang: string; page?: string[] }>
}) {
  const { lang, page } = await params
  if (!isValidLang(lang)) notFound()

  const currentPage = page?.length ? parseInt(page[0], 10) : 1
  if (isNaN(currentPage) || currentPage < 1) notFound()

  const dict = await getDictionary(lang)

  // React.cache 付きで全記事を一度だけ取得
  const mysteriesMap = await getAllPublishedMysteriesMap()
  const allMysteries = Array.from(mysteriesMap.values())

  const totalPages = Math.max(1, Math.ceil(allMysteries.length / ARCHIVE_PAGE_SIZE))
  if (currentPage > totalPages) notFound()

  const startIndex = (currentPage - 1) * ARCHIVE_PAGE_SIZE
  const pageMysteries = allMysteries.slice(startIndex, startIndex + ARCHIVE_PAGE_SIZE)

  // フィルタ用の軽量データを構築（全記事・全言語の title/summary）
  const filterEntries: MysteryEntry[] = allMysteries.map((m) => {
    const i18n: Record<string, { title: string; summary: string }> = {}
    for (const l of SUPPORTED_LANGS) {
      const localized = localizeMystery(m, l)
      i18n[l] = { title: localized.title, summary: localized.summary }
    }
    return {
      id: m.mystery_id,
      classification: m.mystery_id.slice(0, 3).toUpperCase(),
      confidenceLevel: m.confidence_level,
      thumbnail: m.images?.thumbnail ?? null,
      publishedAt: m.publishedAt?.toISOString() ?? "",
      i18n,
    }
  })

  return (
    <div className="min-h-screen flex flex-col film-grain">
      <Header lang={lang as SupportedLang} nav={dict.nav} />

      <main className="flex-1">
        <section className="py-16 md:py-24">
          <div className="container mx-auto px-4">
            {/* 見出し */}
            <div className="mb-12">
              <div className="flex items-center gap-3 mb-4">
                <FileStack className="w-6 h-6 text-gold" />
                <h1 className="font-serif text-3xl md:text-4xl text-parchment">
                  {dict.archive.heading}
                </h1>
              </div>
              <p className="text-muted-foreground max-w-2xl">
                {dict.archive.description}
              </p>
              <div className="mt-4 h-px bg-gradient-to-r from-border to-transparent" />
            </div>

            {/* 分類フィルタ（?c= パラメータ使用時） */}
            <Suspense fallback={null}>
              <ArchiveFilter lang={lang as SupportedLang} dict={dict} mysteries={filterEntries} />
            </Suspense>

            {/* SSG 記事グリッド（フィルタ未使用時に表示） */}
            <div className="archive-default-content">
              {pageMysteries.length === 0 ? (
                <div className="text-center py-16">
                  <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" aria-hidden="true" />
                  <h2 className="font-serif text-xl text-parchment mb-2">
                    {dict.archive.noArticles}
                  </h2>
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {pageMysteries.map((mystery) => (
                      <MysteryCard
                        key={mystery.mystery_id}
                        mystery={mystery}
                        lang={lang as SupportedLang}
                        classificationLabels={dict.classification}
                        confidenceLabels={dict.confidence}
                      />
                    ))}
                  </div>

                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    basePath={`/${lang}/archive`}
                    labels={dict.archive}
                  />
                </>
              )}
            </div>
          </div>
        </section>
      </main>

      <PublicFooter lang={lang} dict={dict} />
    </div>
  )
}
