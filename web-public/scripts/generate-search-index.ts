/**
 * 検索インデックス (search-index.json) 生成スクリプト
 * next build (output: "export") 後に out/ ディレクトリから記事情報を抽出して生成
 *
 * 分類フィルタリング等のクライアントサイド機能で使用
 *
 * 使用方法: npx tsx scripts/generate-search-index.ts
 */

import fs from "fs"
import path from "path"

const OUT_DIR = path.resolve(__dirname, "../out")
const SUPPORTED_LANGS = ["en", "ja", "es", "de", "fr", "nl", "pt"]

interface MysteryI18n {
  title: string
  summary: string
}

interface MysteryEntry {
  id: string
  classification: string
  thumbnail: string | null
  publishedAt: string
  i18n: Record<string, MysteryI18n>
}

interface SearchIndex {
  mysteries: MysteryEntry[]
}

/**
 * out/en/mystery/ から mystery_id 一覧を取得
 */
function collectMysteryIds(): string[] {
  const mysteryDir = path.join(OUT_DIR, "en", "mystery")
  if (!fs.existsSync(mysteryDir)) {
    console.warn(`[search-index] ${mysteryDir} が見つかりません。記事がない可能性があります。`)
    return []
  }

  return fs
    .readdirSync(mysteryDir, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
}

/**
 * HTML ファイルからメタデータを抽出
 */
function extractMetadata(htmlPath: string): {
  title: string
  summary: string
  publishedAt: string
  thumbnail: string | null
} {
  const html = fs.readFileSync(htmlPath, "utf-8")

  // <title> からタイトルを抽出（" | Ghost in the Archive" サフィックス除去）
  const titleMatch = html.match(/<title>([^<]+)<\/title>/)
  const rawTitle = titleMatch?.[1] || ""
  const title = rawTitle.replace(/\s*\|\s*Ghost in the Archive$/, "")

  // meta description から summary を抽出
  const descMatch = html.match(/<meta name="description" content="([^"]*)"/)
  const summary = descMatch?.[1] || ""

  // JSON-LD から datePublished を抽出
  const publishedMatch = html.match(/"datePublished"\s*:\s*"([^"]+)"/)
  const publishedAt = publishedMatch?.[1] || ""

  // og:image からサムネイル URL を抽出
  const ogImageMatch = html.match(/<meta property="og:image" content="([^"]*)"/)
  const ogImage = ogImageMatch?.[1] || null

  return { title, summary, publishedAt, thumbnail: ogImage }
}

/**
 * 全言語の記事データを収集し、検索インデックスを生成
 */
function generateIndex(): SearchIndex {
  const mysteryIds = collectMysteryIds()
  const mysteries: MysteryEntry[] = []

  for (const id of mysteryIds) {
    const classification = id.slice(0, 3).toUpperCase()
    let publishedAt = ""
    let thumbnail: string | null = null
    const i18n: Record<string, MysteryI18n> = {}

    for (const lang of SUPPORTED_LANGS) {
      const htmlPath = path.join(OUT_DIR, lang, "mystery", id, "index.html")
      if (!fs.existsSync(htmlPath)) continue

      const meta = extractMetadata(htmlPath)

      // 英語版から publishedAt と thumbnail を取得
      if (lang === "en") {
        publishedAt = meta.publishedAt
        thumbnail = meta.thumbnail
      }

      i18n[lang] = {
        title: meta.title,
        summary: meta.summary,
      }
    }

    // 少なくとも英語版が存在する場合のみ追加
    if (i18n["en"]) {
      mysteries.push({ id, classification, thumbnail, publishedAt, i18n })
    }
  }

  // 新しい記事を先頭にソート
  mysteries.sort(
    (a, b) => new Date(b.publishedAt).getTime() - new Date(a.publishedAt).getTime()
  )

  return { mysteries }
}

// メイン処理
const index = generateIndex()

// out/api/ ディレクトリを作成
const apiDir = path.join(OUT_DIR, "api")
if (!fs.existsSync(apiDir)) {
  fs.mkdirSync(apiDir, { recursive: true })
}

const outputPath = path.join(apiDir, "search-index.json")
fs.writeFileSync(outputPath, JSON.stringify(index), "utf-8")
console.log(
  `[search-index] ${outputPath} を生成しました（${index.mysteries.length} エントリ）`
)
