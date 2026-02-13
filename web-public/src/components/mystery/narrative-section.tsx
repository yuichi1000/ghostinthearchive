import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { stripLeadingH1 } from "@ghost/shared/src/lib/utils"

interface NarrativeSectionProps {
  narrativeContent?: string
  summary: string
}

export function NarrativeSection({ narrativeContent, summary }: NarrativeSectionProps) {
  if (narrativeContent) {
    return (
      <section className="prose prose-lg prose-invert max-w-none prose-headings:font-serif prose-headings:text-parchment prose-headings:mt-12 prose-headings:mb-4 prose-p:text-foreground/90 prose-p:leading-loose prose-p:mb-6 prose-a:text-gold prose-blockquote:border-gold/30 prose-blockquote:bg-card prose-blockquote:px-6 prose-blockquote:py-4 prose-blockquote:rounded-sm prose-blockquote:text-foreground/70 prose-blockquote:italic prose-blockquote:font-serif prose-strong:text-parchment prose-hr:border-border">
        <Markdown remarkPlugins={[remarkGfm]}>
          {stripLeadingH1(narrativeContent).replace(/\*\*(.+?)\*\*/g, ' **$1** ')}
        </Markdown>
      </section>
    )
  }

  return (
    <section>
      <p className="text-lg text-foreground/90 leading-relaxed">
        {summary}
      </p>
    </section>
  )
}
