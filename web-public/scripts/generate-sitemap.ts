/**
 * sitemap.xml 生成スクリプト
 * next build (output: "export") 後に out/ ディレクトリをスキャンして生成
 *
 * 使用方法: npx tsx scripts/generate-sitemap.ts
 */

import fs from "fs"
import path from "path"

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://ghostinthearchive.ai"
const OUT_DIR = path.resolve(__dirname, "../out")
const LANGS = ["en", "ja", "es", "de", "fr", "nl", "pt"]
const DEFAULT_LANG = "en"

interface SitemapEntry {
  path: string // 言語なしのパス（例: "", "archive", "mystery/OCC-MA-001"）
  lastmod?: string
}

/**
 * out/ ディレクトリをスキャンして URL パスを収集
 */
function collectPaths(): SitemapEntry[] {
  const entries: SitemapEntry[] = []
  const enDir = path.join(OUT_DIR, "en")

  if (!fs.existsSync(enDir)) {
    console.error(`[sitemap] ${enDir} が見つかりません。next build を先に実行してください。`)
    process.exit(1)
  }

  // 再帰的に index.html を探索
  function scan(dir: string, prefix: string) {
    const items = fs.readdirSync(dir, { withFileTypes: true })
    for (const item of items) {
      if (item.isDirectory()) {
        scan(path.join(dir, item.name), `${prefix}${item.name}/`)
      } else if (item.name === "index.html") {
        // prefix からパスを抽出（末尾の / を除去）
        const pagePath = prefix.replace(/\/$/, "")
        entries.push({ path: pagePath })
      }
    }
  }

  // ルート（ホームページ）
  if (fs.existsSync(path.join(enDir, "index.html"))) {
    entries.push({ path: "" })
  }

  // サブディレクトリを走査
  const items = fs.readdirSync(enDir, { withFileTypes: true })
  for (const item of items) {
    if (item.isDirectory()) {
      scan(path.join(enDir, item.name), `${item.name}/`)
    }
  }

  return entries
}

/**
 * sitemap.xml を生成
 */
function generateSitemap(entries: SitemapEntry[]): string {
  const urls = entries.map((entry) => {
    const langAlternates = LANGS.map(
      (lang) =>
        `    <xhtml:link rel="alternate" hreflang="${lang}" href="${SITE_URL}/${lang}/${entry.path}${entry.path ? "/" : ""}"/>`
    ).join("\n")

    const xDefault = `    <xhtml:link rel="alternate" hreflang="x-default" href="${SITE_URL}/${DEFAULT_LANG}/${entry.path}${entry.path ? "/" : ""}"/>`

    return `  <url>
    <loc>${SITE_URL}/${DEFAULT_LANG}/${entry.path}${entry.path ? "/" : ""}</loc>
${langAlternates}
${xDefault}
  </url>`
  })

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urls.join("\n")}
</urlset>
`
}

// メイン処理
const entries = collectPaths()
const sitemap = generateSitemap(entries)
const outputPath = path.join(OUT_DIR, "sitemap.xml")
fs.writeFileSync(outputPath, sitemap, "utf-8")
console.log(`[sitemap] ${outputPath} を生成しました（${entries.length} URL）`)
