import { Suspense } from "react"
import { notFound } from "next/navigation"
import { Header } from "@/components/header"
import { Footer } from "@ghost/shared/src/components/footer"
import { Hero } from "@/components/hero"
import { MysteryCard } from "@/components/mystery-card"
import { MysteryCardSkeleton } from "@/components/mystery-card-skeleton"
import { getPublishedMysteries } from "@ghost/shared/src/lib/firestore/queries"
import { HOMEPAGE_MYSTERY_LIMIT } from "@/lib/constants"
import { FileStack, Search, ShieldAlert } from "lucide-react"
import { isValidLang } from "@/lib/i18n/config"
import type { SupportedLang } from "@/lib/i18n/config"
import { getDictionary } from "@/lib/i18n/dictionaries"
import type { Dictionary } from "@/lib/i18n/dictionaries"

async function MysteryList({ lang, dict }: { lang: SupportedLang; dict: Dictionary }) {
  let mysteries: Awaited<ReturnType<typeof getPublishedMysteries>> = []
  try {
    mysteries = await getPublishedMysteries(HOMEPAGE_MYSTERY_LIMIT)
  } catch (error) {
    console.error("[MysteryList] Failed to fetch mysteries:", error)
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

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {mysteries.map((mystery) => (
        <MysteryCard key={mystery.mystery_id} mystery={mystery} lang={lang} />
      ))}
    </div>
  )
}

function MysteryListSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(6)].map((_, i) => (
        <MysteryCardSkeleton key={i} />
      ))}
    </div>
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
      <Header lang={lang} />

      <main className="flex-1">
        <Hero dict={dict} />

        {/* ヒーロー画像バナー */}
        <section className="relative overflow-hidden -mt-32">
          <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-background to-transparent z-10 pointer-events-none" />

          <picture>
            <source media="(max-width: 640px)" srcSet="/images/hero-bg_sm.webp" type="image/webp" />
            <source media="(max-width: 828px)" srcSet="/images/hero-bg_md.webp" type="image/webp" />
            <source media="(max-width: 1200px)" srcSet="/images/hero-bg_lg.webp" type="image/webp" />
            <source media="(min-width: 1201px)" srcSet="/images/hero-bg_xl.webp" type="image/webp" />
            <img
              src="/images/hero-bg_xl.webp"
              alt="Ghost in the Archive — AI agents at work in the archive"
              className="w-full h-auto"
              fetchPriority="high"
            />
          </picture>

          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent z-10 pointer-events-none" />
        </section>

        {/* Operational Disclosure */}
        <section className="py-16 border-t border-border/50">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto">
              <div className="border border-gold/20 bg-gold/5 rounded-sm p-6 md:p-8">
                <div className="flex items-center gap-3 mb-6 justify-center">
                  <ShieldAlert className="w-5 h-5 text-gold" aria-hidden="true" />
                  <h3 className="font-serif text-xl text-parchment">
                    {dict.disclosure.title}
                  </h3>
                </div>

                <div className="space-y-4 text-sm text-muted-foreground leading-relaxed">
                  <p>
                    <span className="font-mono text-xs text-gold/80">{dict.disclosure.notice}</span>{" "}
                    {dict.disclosure.paragraph1}
                  </p>
                  <p>
                    {dict.disclosure.paragraph2}
                  </p>
                  <p>
                    {dict.disclosure.paragraph3}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-border/30">
                  <div className="flex items-center justify-center gap-4 text-xs font-mono text-muted-foreground">
                    <span>{dict.disclosure.footer.verified}</span>
                    <span className="text-border">•</span>
                    <span>{dict.disclosure.footer.crossReferenced}</span>
                    <span className="text-border">•</span>
                    <span>{dict.disclosure.footer.accuracy}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Latest Discoveries Section */}
        <section className="py-16 md:py-24">
          <div className="container mx-auto px-4">
            {/* Section header */}
            <div className="flex items-center gap-4 mb-12">
              <div className="flex items-center gap-3">
                <FileStack className="w-5 h-5 text-gold" />
                <h2 className="font-serif text-2xl md:text-3xl text-parchment">
                  {dict.home.latestDiscoveries}
                </h2>
              </div>
              <div className="flex-1 h-px bg-gradient-to-r from-border to-transparent" />
            </div>

            <Suspense fallback={<MysteryListSkeleton />}>
              <MysteryList lang={lang} dict={dict} />
            </Suspense>

            {/* View all link */}
            <div className="mt-12 text-center">
              <p className="text-sm text-muted-foreground font-mono">
                <span className="redacted">████████</span> {dict.home.classifiedRedacted} <span className="redacted">████████</span>
              </p>
            </div>
          </div>
        </section>
      </main>

      <Footer labels={dict.footer} />
    </div>
  )
}
