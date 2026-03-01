import { notFound } from "next/navigation"
import { ResponsiveHeroImage } from "@/components/responsive-hero-image"
import { Header } from "@/components/header"
import { PublicFooter } from "@/components/public-footer"
import { MysteryArticle } from "@/components/mystery/mystery-article"
import type { MysteryArticleLabels } from "@ghost/shared/src/components/mystery/mystery-article"
import { Breadcrumb } from "@/components/breadcrumb"
import { RelatedArticles } from "@/components/related-articles"
import { ShareButtons } from "@/components/share-buttons"
import { ArticleJsonLd } from "@/components/article-json-ld"
import { MysteryPageTracker } from "@/components/trackers/mystery-page-tracker"
import { getMysteryById, getPublishedMysteryIds, getAllPublishedMysteriesMap } from "@ghost/shared/src/lib/firestore/queries"
import { Share2 } from "lucide-react"
import { localizeMystery, getTranslatedExcerpt } from "@ghost/shared/src/lib/localize"
import { SUPPORTED_LANGS, isValidLang } from "@/lib/i18n/config"
import type { SupportedLang } from "@/lib/i18n/config"
import { getDictionary } from "@/lib/i18n/dictionaries"
import { findRelatedArticles } from "@/lib/related-articles"
import { getSiteUrl } from "@/lib/site-url"
import { buildOgpMetadata, buildAlternates } from "@/lib/seo"

export async function generateStaticParams() {
  let ids: string[]
  try {
    ids = await getPublishedMysteryIds()
  } catch (error) {
    console.error("[SSG] Firestore クエリ失敗:", error)
    throw new Error(`[SSG] Firestore から記事IDを取得できませんでした: ${error}`)
  }
  console.log(`[SSG] 公開済み記事: ${ids.length} 件 (${ids.join(", ")})`)
  return SUPPORTED_LANGS.flatMap((lang) =>
    ids.map((id) => ({ lang, id }))
  )
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string; id: string }>
}) {
  const { lang, id } = await params
  if (!isValidLang(lang)) return {}

  // React.cache により SSG ビルド中は全ページで同一データを共有
  const mysteriesMap = await getAllPublishedMysteriesMap()
  const mystery = mysteriesMap.get(id) ?? await getMysteryById(id)

  if (!mystery) {
    return { title: "Mystery Not Found | Ghost in the Archive" }
  }

  const { title, summary } = localizeMystery(mystery, lang)

  const pageUrl = `${getSiteUrl()}/${lang}/mystery/${id}/`

  // hero 画像がある場合のみ images を設定
  const heroUrl = mystery.images?.hero
  const images = heroUrl ? [{ url: heroUrl, alt: title }] : undefined

  return {
    title: `${title} | Ghost in the Archive`,
    description: summary,
    alternates: {
      canonical: pageUrl,
      ...buildAlternates(`mystery/${id}`),
    },
    ...buildOgpMetadata(lang, {
      title,
      description: summary,
      path: `mystery/${id}`,
      type: "article",
      images,
    }),
  }
}

/**
 * i18n 辞書から MysteryArticleLabels を構築するヘルパー
 */
function buildLabels(dict: Awaited<ReturnType<typeof getDictionary>>): MysteryArticleLabels {
  return {
    publishedLabel: dict.detail.published,
    storytellerBylineLabel: dict.detail.storytoldBy,
    confidence: dict.confidence,
    classification: dict.classification,
    tableOfContents: dict.detail.tableOfContents,
    tocNarrative: dict.detail.tocNarrative,
    tocDiscrepancy: dict.detail.tocDiscrepancy,
    tocEvidence: dict.detail.tocEvidence,
    tocHypothesis: dict.detail.tocHypothesis,
    tocHistoricalContext: dict.detail.tocHistoricalContext,
    archivalData: dict.detail.archivalData,
    discoveredDiscrepancy: dict.detail.discoveredDiscrepancy,
    archivalEvidence: dict.detail.archivalEvidence,
    primarySource: dict.detail.primarySource,
    contrastingSource: dict.detail.contrastingSource,
    additionalEvidence: dict.detail.additionalEvidence,
    evidence: dict.evidence,
    hypothesis: dict.detail.hypothesis,
    alternativeHypotheses: dict.detail.alternativeHypotheses,
    historicalContext: dict.detail.historicalContext,
    relatedEvents: dict.detail.relatedEvents,
    keyFigures: dict.detail.keyFigures,
    storyAngles: dict.detail.storyAngles,
    classificationNotice: dict.detail.classificationNotice,
    sourceCoverage: dict.sourceCoverage,
  }
}

export default async function MysteryDetailPage({
  params,
}: {
  params: Promise<{ lang: string; id: string }>
}) {
  const { lang, id } = await params
  if (!isValidLang(lang)) notFound()

  // React.cache により SSG ビルド中は全ページで同一データを共有
  const mysteriesMap = await getAllPublishedMysteriesMap()
  const mystery = mysteriesMap.get(id) ?? await getMysteryById(id)

  if (!mystery || mystery.status !== "published") {
    notFound()
  }

  const dict = await getDictionary(lang)
  const localized = localizeMystery(mystery, lang)

  // 証拠の翻訳済み抜粋テキスト
  const translatedExcerpts = {
    a: getTranslatedExcerpt(mystery, "a", lang),
    b: getTranslatedExcerpt(mystery, "b", lang),
    additional: mystery.additional_evidence.map((_, i) => getTranslatedExcerpt(mystery, i, lang)),
  }

  // シェアボタン用の URL
  const shareUrl = `${getSiteUrl()}/${lang}/mystery/${id}/`

  // 関連記事の取得（SSG ビルド時は React.cache で共有済み）
  const relatedArticles = findRelatedArticles(
    mystery,
    Array.from(mysteriesMap.values())
  )

  // ヒーロー画像（公開ページ固有: ResponsiveHeroImage）
  const heroImage = mystery.images?.hero ? (
    <figure className="mx-auto max-w-2xl">
      <div className="aged-card letterpress-border rounded-sm overflow-hidden">
        <ResponsiveHeroImage
          hero={mystery.images.hero}
          variants={mystery.images.variants}
          alt={localized.title}
          priority
          className="w-full h-auto"
        />
      </div>
    </figure>
  ) : undefined

  // compact シェアボタン（CaseFileHeader 直後）
  const afterHeader = (
    <div className="flex items-center gap-4 mb-8">
      <div className="h-px flex-1 bg-border" />
      <ShareButtons url={shareUrl} title={localized.title} variant="compact" labels={dict.share} />
      <div className="h-px flex-1 bg-border" />
    </div>
  )

  // full シェアボタン（メインカラム末尾）
  const mainColumnFooter = (
    <section className="pt-4">
      <div className="flex items-center gap-3 mb-6">
        <Share2 className="w-5 h-5 text-gold" />
        <h2 className="font-serif text-xl text-parchment">{dict.share.shareThisArticle}</h2>
      </div>
      <ShareButtons url={shareUrl} title={localized.title} variant="full" labels={dict.share} />
    </section>
  )

  return (
    <div className="min-h-screen flex flex-col film-grain">
      <Header lang={lang} nav={dict.nav} />

      <main className="flex-1 py-8 md:py-12">
        <div className="container mx-auto px-4">
          {/* パンくずリスト */}
          <Breadcrumb
            lang={lang}
            title={localized.title}
            labels={{
              home: dict.detail.breadcrumbHome,
              archive: dict.nav.archive,
            }}
          />

          {/* Article 構造化データ */}
          <ArticleJsonLd
            title={localized.title}
            description={localized.summary}
            url={shareUrl}
            datePublished={mystery.publishedAt?.toISOString()}
            dateModified={mystery.updatedAt?.toISOString()}
            imageUrl={mystery.images?.hero}
            lang={lang}
          />

          <MysteryPageTracker
            mysteryId={mystery.mystery_id}
            classification={mystery.mystery_id.slice(0, 3).toUpperCase()}
            confidenceLevel={mystery.confidence_level}
            lang={lang}
          />

          <MysteryArticle
            mystery={mystery}
            localized={localized}
            lang={lang}
            labels={buildLabels(dict)}
            translatedExcerpts={translatedExcerpts}
            heroImage={heroImage}
            publishedAt={mystery.publishedAt}
            afterHeader={afterHeader}
            mainColumnFooter={mainColumnFooter}
          />

          {/* 関連記事 */}
          <RelatedArticles
            articles={relatedArticles}
            lang={lang as SupportedLang}
            heading={dict.detail.relatedArticles}
            classificationLabels={dict.classification}
            confidenceLabels={dict.confidence}
          />
        </div>
      </main>

      <PublicFooter lang={lang} dict={dict} />
    </div>
  )
}
