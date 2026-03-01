/**
 * Markdown テキスト内の画像行をプログラム的に各セクション末尾に再配置する。
 *
 * Storyteller が出力した画像（![alt](url)）の位置に依存せず、
 * H2 セクション 1〜4 の末尾に最大1枚ずつ均等配置する（最大4枚）。
 * 同一 URL の画像は重複排除し、ユニークな画像のみ配置する。
 */

/** 行頭が `![` で始まる独立した画像行にマッチ */
const IMAGE_LINE_RE = /^!\[.*?\]\(.*?\)\s*$/

/** 画像行から URL を抽出する */
const IMAGE_URL_RE = /!\[.*?\]\((.*?)\)/

export function normalizeImagePlacement(markdown: string): string {
  const lines = markdown.split("\n")

  // 1. 全画像行を抽出し、元の位置から除去
  const rawImages: string[] = []
  const filteredLines: string[] = []

  for (const line of lines) {
    if (IMAGE_LINE_RE.test(line)) {
      rawImages.push(line.trim())
    } else {
      filteredLines.push(line)
    }
  }

  // 画像がなければそのまま返す
  if (rawImages.length === 0) return markdown

  // URL ベースの重複排除
  const seenUrls = new Set<string>()
  const images: string[] = []
  for (const img of rawImages) {
    const match = IMAGE_URL_RE.exec(img)
    const url = match?.[1] ?? ""
    if (url && seenUrls.has(url)) continue
    if (url) seenUrls.add(url)
    images.push(img)
  }

  // 2. H2 見出しの行インデックスを特定
  const h2Indices: number[] = []
  for (let i = 0; i < filteredLines.length; i++) {
    if (filteredLines[i].startsWith("## ")) {
      h2Indices.push(i)
    }
  }

  // H2 が2つ未満なら配置先がないので画像除去のみ
  if (h2Indices.length < 2) {
    return filteredLines.join("\n").replace(/\n{3,}/g, "\n\n")
  }

  // 3. セクション1〜4の末尾に画像を1枚ずつ挿入（最大4枚）
  // 最終セクション（次の H2 なし）はドキュメント末尾に挿入
  const placementSlots = Math.min(h2Indices.length, 4)
  const imageCount = Math.min(images.length, placementSlots)

  // 後ろから挿入してインデックスのずれを防ぐ
  for (let i = imageCount - 1; i >= 0; i--) {
    const insertBefore = (i + 1 < h2Indices.length)
      ? h2Indices[i + 1]
      : filteredLines.length
    filteredLines.splice(insertBefore, 0, "", images[i], "")
  }

  // 余分な連続空行を整理して返す
  return filteredLines.join("\n").replace(/\n{3,}/g, "\n\n")
}
