import Markdown, { type Components } from "react-markdown"
import remarkGfm from "remark-gfm"
import { FileText } from "lucide-react"
import { stripLeadingH1 } from "@ghost/shared/src/lib/utils"

// 7言語のアーカイブ引用ラベル
const ARCHIVE_LABEL: Record<string, string> = {
  en: "From the Archive",
  ja: "アーカイブ記録",
  es: "Del Archivo",
  de: "Aus dem Archiv",
  fr: "Extrait d'archive",
  nl: "Uit het Archief",
  pt: "Do Arquivo",
}

function ArchiveBlockquote({ children, lang }: { children?: React.ReactNode; lang: string }) {
  return (
    <blockquote className="not-prose relative my-8 border-l-2 border-gold/40 bg-paper-light/50 px-6 py-5 rounded-sm">
      <div className="flex items-center gap-2 mb-3 text-xs font-mono uppercase tracking-wider text-gold/70">
        <FileText className="w-3.5 h-3.5" />
        <span>{ARCHIVE_LABEL[lang] || ARCHIVE_LABEL.en}</span>
      </div>
      <div className="font-serif text-foreground/80 italic leading-relaxed">
        {children}
      </div>
    </blockquote>
  )
}

interface NarrativeSectionProps {
  narrativeContent?: string
  summary: string
  lang?: string
}

export function NarrativeSection({ narrativeContent, summary, lang = "en" }: NarrativeSectionProps) {
  if (narrativeContent) {
    const markdownComponents: Components = {
      blockquote: ({ children }) => (
        <ArchiveBlockquote lang={lang}>{children}</ArchiveBlockquote>
      ),
    }

    return (
      <section id="section-narrative" className="scroll-mt-24 prose prose-lg prose-invert max-w-none prose-headings:font-serif prose-headings:text-parchment prose-headings:mt-12 prose-headings:mb-4 prose-p:text-foreground/90 prose-p:leading-loose prose-p:mb-6 prose-a:text-gold prose-strong:text-parchment prose-hr:border-border">
        <Markdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
          {stripLeadingH1(narrativeContent).replace(/\*\*(.+?)\*\*/g, ' **$1** ')}
        </Markdown>
      </section>
    )
  }

  return (
    <section id="section-narrative" className="scroll-mt-24">
      <p className="text-lg text-foreground/90 leading-relaxed">
        {summary}
      </p>
    </section>
  )
}
