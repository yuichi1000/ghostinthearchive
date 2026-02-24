/**
 * Markdown テキスト内の画像行をプログラム的に各セクション末尾に再配置する。
 *
 * Storyteller が出力した画像（![alt](url)）の位置に依存せず、
 * H2 セクション 1〜3 の末尾に最大1枚ずつ均等配置する。
 * セクション4（結び）には画像を配置しない。
 */

/** 行頭が `![` で始まる独立した画像行にマッチ */
const IMAGE_LINE_RE = /^!\[.*?\]\(.*?\)\s*$/

export function normalizeImagePlacement(markdown: string): string {
  const lines = markdown.split("\n")

  // 1. 全画像行を抽出し、元の位置から除去
  const images: string[] = []
  const filteredLines: string[] = []

  for (const line of lines) {
    if (IMAGE_LINE_RE.test(line)) {
      images.push(line.trim())
    } else {
      filteredLines.push(line)
    }
  }

  // 画像がなければそのまま返す
  if (images.length === 0) return markdown

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

  // 3. セクション1〜3の末尾（= 次の H2 の直前）に画像を1枚ずつ挿入
  // 最後のセクション（結び）には入れない
  const placementSlots = Math.min(h2Indices.length - 1, 3)
  const imageCount = Math.min(images.length, placementSlots)

  // 後ろから挿入してインデックスのずれを防ぐ
  for (let i = imageCount - 1; i >= 0; i--) {
    const insertBefore = h2Indices[i + 1]
    filteredLines.splice(insertBefore, 0, "", images[i], "")
  }

  // 余分な連続空行を整理して返す
  return filteredLines.join("\n").replace(/\n{3,}/g, "\n\n")
}
