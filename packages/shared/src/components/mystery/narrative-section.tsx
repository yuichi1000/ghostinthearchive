import Markdown, { type Components } from "react-markdown"
import remarkGfm from "remark-gfm"
import { rehypeUnwrapImages } from "../../lib/rehype-unwrap-images"
import { normalizeImagePlacement } from "../../lib/normalize-image-placement"
import { FileText } from "lucide-react"
import { stripLeadingH1 } from "../../lib/utils"
import { slugify } from "../../lib/markdown-headings"
import type { ReactNode } from "react"
import { ArchiveImage } from "./archive-image"

// 4言語のアーカイブ引用ラベル
const ARCHIVE_LABEL: Record<string, string> = {
  en: "From the Archive",
  ja: "アーカイブ記録",
  es: "Del Archivo",
  de: "Aus dem Archiv",
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

/**
 * React children からプレーンテキストを再帰的に抽出する。
 * h2 要素の children はネストした要素（bold, em 等）を含むため再帰処理が必要。
 */
function getTextContent(children: ReactNode): string {
  if (typeof children === "string") return children
  if (typeof children === "number") return String(children)
  if (Array.isArray(children)) return children.map(getTextContent).join("")
  if (children && typeof children === "object" && "props" in children) {
    return getTextContent((children as { props: { children?: ReactNode } }).props.children)
  }
  return ""
}

interface NarrativeSectionProps {
  narrativeContent?: string
  summary: string
  lang?: string
  // extractHeadings で事前計算した ID 配列。渡された場合はこの ID を使い、
  // TOC と DOM 見出しの ID 一致を保証する（スクロールスパイ修正の核心）
  precomputedHeadingIds?: string[]
}

export function NarrativeSection({ narrativeContent, summary, lang = "en", precomputedHeadingIds }: NarrativeSectionProps) {
  if (narrativeContent) {
    // 重複スラグを追跡するクロージャ（レンダーごとにリセット）
    const slugCounts = new Map<string, number>()
    let headingIndex = 0

    const markdownComponents: Components = {
      blockquote: ({ children }) => (
        <ArchiveBlockquote lang={lang}>{children}</ArchiveBlockquote>
      ),
      img: ({ src, alt }) => (
        <ArchiveImage src={typeof src === "string" ? src : undefined} alt={alt} lang={lang} />
      ),
      h2: ({ children }) => {
        const currentIndex = headingIndex
        headingIndex++
        // precomputedHeadingIds があればそれを使い、TOC と DOM の ID を一致させる
        if (precomputedHeadingIds && currentIndex < precomputedHeadingIds.length) {
          return <h2 id={precomputedHeadingIds[currentIndex]} className="scroll-mt-24">{children}</h2>
        }
        // フォールバック: 従来の getTextContent + slugify
        const text = getTextContent(children)
        const baseSlug = slugify(text) || `heading-${currentIndex}`
        const count = slugCounts.get(baseSlug) || 0
        const id = count > 0 ? `${baseSlug}-${count}` : baseSlug
        slugCounts.set(baseSlug, count + 1)
        return <h2 id={id} className="scroll-mt-24">{children}</h2>
      },
    }

    return (
      <section id="section-narrative" className="scroll-mt-24 prose prose-lg prose-invert max-w-none prose-headings:font-serif prose-headings:text-parchment prose-headings:mt-12 prose-headings:mb-4 prose-p:text-foreground/90 prose-p:leading-loose prose-p:mb-6 prose-a:text-gold prose-strong:text-parchment prose-hr:border-border">
        <Markdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeUnwrapImages]} components={markdownComponents}>
          {normalizeImagePlacement(stripLeadingH1(narrativeContent).replace(/\*\*(.+?)\*\*/g, ' **$1** '))}
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
