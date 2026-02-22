/**
 * Atom フィード (feed.xml) 生成スクリプト
 * next build (output: "export") 後に out/ ディレクトリから記事情報を抽出して生成
 *
 * 使用方法: npx tsx scripts/generate-feed.ts
 */

import fs from "fs"
import path from "path"

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://ghostinthearchive.ai"
const OUT_DIR = path.resolve(__dirname, "../out")
const FEED_LANG = "en" // フィードは英語版の記事を配信

interface FeedEntry {
  id: string
  title: string
  summary: string
  url: string
  published: string
  updated: string
}

/**
 * XML 特殊文字をエスケープ
 */
function escapeXml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;")
}

/**
 * out/en/mystery/ から記事ページを収集し、HTML からメタデータを抽出
 */
function collectArticles(): FeedEntry[] {
  const mysteryDir = path.join(OUT_DIR, FEED_LANG, "mystery")
  if (!fs.existsSync(mysteryDir)) {
    console.warn(`[feed] ${mysteryDir} が見つかりません。記事がない可能性があります。`)
    return []
  }

  const entries: FeedEntry[] = []
  const dirs = fs.readdirSync(mysteryDir, { withFileTypes: true })

  for (const dir of dirs) {
    if (!dir.isDirectory()) continue

    const htmlPath = path.join(mysteryDir, dir.name, "index.html")
    if (!fs.existsSync(htmlPath)) continue

    const html = fs.readFileSync(htmlPath, "utf-8")

    // <title> からタイトルを抽出
    const titleMatch = html.match(/<title>([^<]+)<\/title>/)
    const rawTitle = titleMatch?.[1] || dir.name
    // " | Ghost in the Archive" サフィックスを除去
    const title = rawTitle.replace(/\s*\|\s*Ghost in the Archive$/, "")

    // meta description から summary を抽出
    const descMatch = html.match(/<meta name="description" content="([^"]*)"/)
    const summary = descMatch?.[1] || ""

    // article:published_time から日時を抽出（JSON-LD からフォールバック）
    const jsonLdMatch = html.match(/"datePublished"\s*:\s*"([^"]+)"/)
    const published = jsonLdMatch?.[1] || new Date().toISOString()

    const modifiedMatch = html.match(/"dateModified"\s*:\s*"([^"]+)"/)
    const updated = modifiedMatch?.[1] || published

    const url = `${SITE_URL}/${FEED_LANG}/mystery/${dir.name}/`

    entries.push({
      id: dir.name,
      title,
      summary,
      url,
      published,
      updated,
    })
  }

  // 新しい記事を先頭にソート
  entries.sort((a, b) => new Date(b.published).getTime() - new Date(a.published).getTime())

  return entries
}

/**
 * Atom フィード XML を生成
 */
function generateAtomFeed(entries: FeedEntry[]): string {
  const now = new Date().toISOString()
  const feedEntries = entries
    .map(
      (entry) => `  <entry>
    <title>${escapeXml(entry.title)}</title>
    <link href="${escapeXml(entry.url)}" rel="alternate"/>
    <id>${escapeXml(entry.url)}</id>
    <published>${entry.published}</published>
    <updated>${entry.updated}</updated>
    <summary>${escapeXml(entry.summary)}</summary>
    <author>
      <name>Ghost in the Archive</name>
    </author>
  </entry>`
    )
    .join("\n")

  return `<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Ghost in the Archive</title>
  <subtitle>Unearthing anomalies across languages, archives, and disciplines</subtitle>
  <link href="${SITE_URL}/feed.xml" rel="self" type="application/atom+xml"/>
  <link href="${SITE_URL}/" rel="alternate" type="text/html"/>
  <id>${SITE_URL}/</id>
  <updated>${now}</updated>
  <author>
    <name>Ghost in the Archive</name>
  </author>
${feedEntries}
</feed>
`
}

// メイン処理
const articles = collectArticles()
const feed = generateAtomFeed(articles)
const outputPath = path.join(OUT_DIR, "feed.xml")
fs.writeFileSync(outputPath, feed, "utf-8")
console.log(`[feed] ${outputPath} を生成しました（${articles.length} エントリ）`)
