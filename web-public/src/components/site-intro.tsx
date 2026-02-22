import type { Dictionary } from "@/lib/i18n/dictionaries"

interface SiteIntroProps {
  dict: Dictionary
}

export function SiteIntro({ dict }: SiteIntroProps) {
  return (
    <section className="py-12 md:py-16">
      <div className="container mx-auto px-4 text-center">
        <h1 className="font-serif text-3xl md:text-4xl lg:text-5xl text-parchment mb-4">
          Ghost in the Archive
        </h1>
        <p className="text-gold font-mono uppercase tracking-wider text-sm mb-6">
          {dict.siteIntro.tagline}
        </p>
        <p className="text-muted-foreground leading-relaxed max-w-3xl mx-auto">
          {dict.siteIntro.description}
        </p>
        <div className="mt-8 h-px bg-gradient-to-r from-transparent via-border to-transparent" />
      </div>
    </section>
  )
}
