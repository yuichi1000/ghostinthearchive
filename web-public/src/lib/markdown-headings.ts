/**
 * Markdown から見出しを抽出し、slug ID を生成するユーティリティ。
 * TOC（目次）の動的構築と、見出し要素への id 付与に使用する。
 */

export interface MarkdownHeading {
  id: string
  text: string
  level: 2 | 3
}

/**
 * テキストを URL フレンドリーなスラグに変換する。
 * - 小文字化、空白をハイフン化、英数字とハイフンのみ残す
 */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
}

/**
 * インライン Markdown 書式を除去してプレーンテキストにする。
 * **bold**, *italic*, `code`, [link](url) を処理する。
 */
function stripInlineMarkdown(text: string): string {
  return text
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // [link](url) → link
    .replace(/`([^`]+)`/g, "$1")              // `code` → code
    .replace(/\*\*(.+?)\*\*/g, "$1")          // **bold** → bold
    .replace(/\*(.+?)\*/g, "$1")              // *italic* → italic
    .replace(/__(.+?)__/g, "$1")              // __bold__ → bold
    .replace(/_(.+?)_/g, "$1")                // _italic_ → italic
}

/**
 * Markdown テキストから h2 見出しを抽出する。
 * stripLeadingH1() 適用後の markdown を渡すことを想定。
 * 重複スラグにはサフィックス -1, -2 を付与する。
 */
export function extractHeadings(markdown: string): MarkdownHeading[] {
  const headings: MarkdownHeading[] = []
  const slugCounts = new Map<string, number>()

  const regex = /^##\s+(.+)$/gm
  let match: RegExpExecArray | null
  while ((match = regex.exec(markdown)) !== null) {
    const rawText = match[1].trim()
    const text = stripInlineMarkdown(rawText)
    const baseSlug = slugify(text)

    const count = slugCounts.get(baseSlug) || 0
    const id = count > 0 ? `${baseSlug}-${count}` : baseSlug
    slugCounts.set(baseSlug, count + 1)

    headings.push({ id, text, level: 2 })
  }

  return headings
}
