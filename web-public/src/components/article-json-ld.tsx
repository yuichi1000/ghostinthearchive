/**
 * Article JSON-LD 構造化データコンポーネント
 * 記事詳細ページに配置して Google リッチリザルトに対応
 */

interface ArticleJsonLdProps {
  title: string
  description: string
  url: string
  datePublished?: string
  dateModified?: string
  imageUrl?: string
  lang: string
}

export function ArticleJsonLd({
  title,
  description,
  url,
  datePublished,
  dateModified,
  imageUrl,
  lang,
}: ArticleJsonLdProps) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Article",
    headline: title,
    description,
    url,
    inLanguage: lang,
    ...(datePublished && { datePublished }),
    ...(dateModified && { dateModified }),
    ...(imageUrl && { image: imageUrl }),
    author: {
      "@type": "Organization",
      name: "Ghost in the Archive",
    },
    publisher: {
      "@type": "Organization",
      name: "Ghost in the Archive",
      url: "https://ghostinthearchive.ai",
    },
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
  )
}
