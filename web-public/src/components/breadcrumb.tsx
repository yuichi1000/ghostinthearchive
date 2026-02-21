import Link from "next/link"
import { ChevronRight } from "lucide-react"

interface BreadcrumbProps {
  lang: string
  title: string
  labels: {
    home: string
    archive: string
  }
}

export function Breadcrumb({ lang, title, labels }: BreadcrumbProps) {
  const items = [
    { label: labels.home, href: `/${lang}` },
    { label: labels.archive, href: `/${lang}/archive` },
  ]

  // JSON-LD 構造化データ（SSG 環境でドメイン非依存のパスのみ）
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: item.label,
      item: item.href,
    })),
  }

  return (
    <nav aria-label="Breadcrumb" className="mb-8">
      <ol className="flex items-center gap-2 text-sm font-mono">
        {items.map((item, i) => (
          <li key={item.href} className="flex items-center gap-2">
            {i > 0 && <ChevronRight className="w-3 h-3 text-muted-foreground/50" />}
            <Link
              href={item.href}
              className="text-muted-foreground hover:text-parchment transition-colors no-underline"
            >
              {item.label}
            </Link>
          </li>
        ))}
        <li className="flex items-center gap-2">
          <ChevronRight className="w-3 h-3 text-muted-foreground/50" />
          <span className="text-parchment truncate max-w-[200px] md:max-w-[400px]" aria-current="page">
            {title}
          </span>
        </li>
      </ol>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </nav>
  )
}
