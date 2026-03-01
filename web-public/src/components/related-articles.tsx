import type { FirestoreMystery } from "@ghost/shared/src/types/mystery"
import type { SupportedLang } from "@/lib/i18n/config"
import type { Dictionary } from "@/lib/i18n/dictionaries"
import { MysteryCard } from "@/components/mystery-card"

interface RelatedArticlesProps {
  articles: FirestoreMystery[]
  lang: SupportedLang
  heading: string
  classificationLabels: Dictionary["classification"]
  confidenceLabels: Dictionary["confidence"]
}

export function RelatedArticles({ articles, lang, heading, classificationLabels, confidenceLabels }: RelatedArticlesProps) {
  if (articles.length === 0) return null

  return (
    <section className="mt-16 pt-12 border-t border-border">
      <h2 className="font-serif text-2xl text-parchment mb-8">{heading}</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {articles.map((article) => (
          <MysteryCard
            key={article.mystery_id}
            mystery={article}
            lang={lang}
            classificationLabels={classificationLabels}
            confidenceLabels={confidenceLabels}
          />
        ))}
      </div>
    </section>
  )
}
