import { Footer } from "@ghost/shared/src/components/footer"
import type { Dictionary } from "@/lib/i18n/dictionaries"

interface PublicFooterProps {
  lang: string
  dict: Dictionary
}

export function PublicFooter({ lang, dict }: PublicFooterProps) {
  return (
    <Footer
      labels={dict.footer}
      siteLinks={[
        { label: dict.footer.home, href: `/${lang}` },
        { label: dict.footer.archive, href: `/${lang}/archive` },
        { label: dict.footer.about, href: `/${lang}/about` },
      ]}
    />
  )
}
