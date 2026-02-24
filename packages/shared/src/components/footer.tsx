import { Archive, ExternalLink } from "lucide-react"

/**
 * 技術スタック一覧（固有名詞のため翻訳不要）
 */
const TECH_STACK = [
  { label: "Google Agent Development Kit (ADK)", href: "https://google.github.io/adk-docs/" },
  { label: "Vertex AI", href: "https://cloud.google.com/vertex-ai" },
  { label: "Next.js", href: "https://nextjs.org/" },
  { label: "Cloud Firestore", href: "https://firebase.google.com/docs/firestore" },
  { label: "Cloud Run", href: "https://cloud.google.com/run" },
] as const

/**
 * 一次資料提供元一覧（固有名詞のため翻訳不要）
 * pending: true の項目は API 利用申請中
 */
const PRIMARY_SOURCES = [
  // 米国
  { label: "Library of Congress", href: "https://www.loc.gov/" },
  { label: "Digital Public Library of America", href: "https://dp.la/" },
  { label: "NYPL Digital Collections", href: "https://digitalcollections.nypl.org/" },
  // 欧州
  { label: "Europeana", href: "https://www.europeana.eu/" },
  { label: "Deutsche Digitale Bibliothek", href: "https://www.deutsche-digitale-bibliothek.de/" },
  { label: "Delpher (KB)", href: "https://www.delpher.nl/" },
  { label: "Wellcome Collection", href: "https://wellcomecollection.org/" },
  // アジア太平洋
  { label: "NDL Search（国立国会図書館）", href: "https://ndlsearch.ndl.go.jp/" },
  { label: "Trove", href: "https://trove.nla.gov.au/", pending: true },
  // グローバル
  { label: "Internet Archive", href: "https://archive.org/" },
] as const

/**
 * Footer ラベル（web-public から辞書を渡す用）
 * 未指定時は英語デフォルト
 */
interface FooterLabels {
  description?: string
  primarySources?: string
  technical?: string
  classification?: string
  pendingApplication?: string
}

interface FooterProps {
  labels?: FooterLabels
  siteLinks?: Array<{ label: string; href: string }>
}

export function Footer({ labels, siteLinks }: FooterProps) {
  const description = labels?.description ?? "Multi-lingual cross-analysis of the world's public digital archives — unearthing the Ghosts hiding in the gaps between records, languages, and disciplines."
  const primarySources = labels?.primarySources ?? "Primary Sources"
  const technical = labels?.technical ?? "Technical"
  const classification = labels?.classification ?? "Document Classification: PUBLIC RELEASE"
  const pendingApplication = labels?.pendingApplication ?? "Application Pending"

  return (
    <footer className="border-t border-border/50 bg-card/50 mt-auto">
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <Archive className="w-5 h-5 text-gold" />
              <span className="font-serif text-parchment">Ghost in the Archive</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {description}
            </p>
            {siteLinks && siteLinks.length > 0 && (
              <nav className="flex gap-4">
                {siteLinks.map(({ label, href }) => (
                  <a
                    key={href}
                    href={href}
                    className="text-sm text-muted-foreground hover:text-gold transition-colors no-underline"
                  >
                    {label}
                  </a>
                ))}
              </nav>
            )}
          </div>

          {/* Sources */}
          <div className="space-y-4">
            <h3 className="text-sm font-mono uppercase tracking-wider text-parchment">{primarySources}</h3>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-2">
              {PRIMARY_SOURCES.map(({ label, href, ...rest }) => (
                <li key={href}>
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-muted-foreground hover:text-gold transition-colors inline-flex items-center gap-1.5 no-underline"
                  >
                    {label}
                    <ExternalLink className="w-3 h-3 shrink-0" />
                  </a>
                  {"pending" in rest && rest.pending && (
                    <span className="ml-1 text-xs text-muted-foreground/60">({pendingApplication})</span>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Technical */}
          <div className="space-y-4">
            <h3 className="text-sm font-mono uppercase tracking-wider text-parchment">{technical}</h3>
            <ul className="space-y-2">
              {TECH_STACK.map(({ label, href }) => (
                <li key={href}>
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-muted-foreground hover:text-gold transition-colors inline-flex items-center gap-1.5 no-underline"
                  >
                    {label}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 pt-6 border-t border-border/30 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-muted-foreground font-mono">
            {classification}
          </p>
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} Ghost in the Archive Research Initiative
          </p>
        </div>
      </div>
    </footer>
  )
}
