import { notFound } from "next/navigation"
import { Header } from "@/components/header"
import { PublicFooter } from "@/components/public-footer"
import { Hero } from "@/components/hero"
import { BookOpen, Pen, ShieldAlert } from "lucide-react"
import { REPORTER_DISPLAY_NAMES } from "@ghost/shared/src/types/mystery"
import { isValidLang } from "@/lib/i18n/config"
import { SUPPORTED_LANGS } from "@/lib/i18n/config"
import { getDictionary } from "@/lib/i18n/dictionaries"
import { buildOgpMetadata, buildAlternates } from "@/lib/seo"

// SSG: ビルド時に生成されたページ以外は 404
export const dynamicParams = false

export async function generateStaticParams() {
  return SUPPORTED_LANGS.map((lang) => ({ lang }))
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ lang: string }>
}) {
  const { lang } = await params
  if (!isValidLang(lang)) return {}

  const dict = await getDictionary(lang)

  return {
    title: dict.about.title,
    description: dict.seo.aboutDescription,
    alternates: buildAlternates("about"),
    ...buildOgpMetadata(lang, {
      title: dict.about.heading,
      description: dict.seo.aboutDescription,
      path: "about",
    }),
  }
}

export default async function AboutPage({
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
        <Hero dict={dict} />

        {/* ヒーロー画像バナー */}
        <section className="relative overflow-hidden">
          <picture>
            <source media="(max-width: 640px)" srcSet="/images/hero-bg_sm.webp" type="image/webp" />
            <source media="(max-width: 828px)" srcSet="/images/hero-bg_md.webp" type="image/webp" />
            <source media="(max-width: 1200px)" srcSet="/images/hero-bg_lg.webp" type="image/webp" />
            <source media="(min-width: 1201px)" srcSet="/images/hero-bg_xl.webp" type="image/webp" />
            <img
              src="/images/hero-bg_xl.webp"
              alt="Ghost in the Archive"
              className="w-full h-auto"
              fetchPriority="high"
            />
          </picture>

          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-background to-transparent z-10 pointer-events-none" />
        </section>

        {/* Concept */}
        <section className="py-16 border-t border-border/50">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto">
              <div className="flex items-center gap-3 mb-8 justify-center">
                <BookOpen className="w-5 h-5 text-gold" aria-hidden="true" />
                <h2 className="font-serif text-2xl text-parchment">
                  {dict.about.concept.heading}
                </h2>
              </div>

              <p className="text-base text-muted-foreground leading-relaxed mb-8">
                {dict.about.concept.intro}
              </p>

              <h3 className="text-sm font-mono uppercase tracking-wider text-parchment mb-4">
                {dict.about.concept.principlesHeading}
              </h3>

              <ul className="space-y-4 mb-8">
                {([
                  ["autonomousAgents", "autonomousAgentsDesc"],
                  ["transparency", "transparencyDesc"],
                  ["crossDiscovery", "crossDiscoveryDesc"],
                  ["interdisciplinary", "interdisciplinaryDesc"],
                  ["intellectualAwe", "intellectualAweDesc"],
                ] as const).map(([key, descKey]) => (
                  <li key={key} className="flex gap-3">
                    <span className="text-gold mt-1 shrink-0">&#x2022;</span>
                    <div>
                      <span className="font-semibold text-parchment">{dict.about.concept[key]}</span>
                      <span className="text-muted-foreground"> — {dict.about.concept[descKey]}</span>
                    </div>
                  </li>
                ))}
              </ul>

              <p className="text-base text-muted-foreground leading-relaxed italic border-l-2 border-gold/30 pl-4 mb-6">
                {dict.about.concept.folklore}
              </p>

              <p className="text-sm text-muted-foreground/70 leading-relaxed">
                {dict.about.concept.coda}
              </p>
            </div>
          </div>
        </section>

        {/* Our Reporters */}
        <section className="py-16 border-t border-border/50">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto">
              <div className="flex items-center gap-3 mb-8 justify-center">
                <Pen className="w-5 h-5 text-gold" aria-hidden="true" />
                <h2 className="font-serif text-2xl text-parchment">
                  {dict.about.reporters.heading}
                </h2>
              </div>

              <p className="text-base text-muted-foreground leading-relaxed mb-8 text-center">
                {dict.about.reporters.intro}
              </p>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(REPORTER_DISPLAY_NAMES).map(([key, name]) => (
                  <div
                    key={key}
                    className="border border-border/50 rounded-sm p-4 text-center hover:border-gold/30 transition-colors"
                  >
                    <p className="font-serif text-lg text-parchment">{name}</p>
                    <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground mt-1">
                      {key}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Operational Disclosure */}
        <section className="py-16 border-t border-border/50">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto">
              <div className="border border-gold/20 bg-gold/5 rounded-sm p-6 md:p-8">
                <div className="flex items-center gap-3 mb-6 justify-center">
                  <ShieldAlert className="w-5 h-5 text-gold" aria-hidden="true" />
                  <h2 className="font-serif text-xl text-parchment">
                    {dict.disclosure.title}
                  </h2>
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
                    <span className="text-border">&bull;</span>
                    <span>{dict.disclosure.footer.crossReferenced}</span>
                    <span className="text-border">&bull;</span>
                    <span>{dict.disclosure.footer.accuracy}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <PublicFooter lang={lang} dict={dict} />
    </div>
  )
}
