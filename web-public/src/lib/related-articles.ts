import type { FirestoreMystery } from "@ghost/shared/src/types/mystery"

/**
 * 関連記事をスコアリングで抽出する
 * - 同じ分類コード（mystery_id 先頭3文字）: +3
 * - geographic_scope の重複1件あたり: +2
 * - time_period 完全一致: +1
 */
export function findRelatedArticles(
  current: FirestoreMystery,
  all: FirestoreMystery[],
  maxCount = 3
): FirestoreMystery[] {
  const currentClassification = current.mystery_id.slice(0, 3)
  const currentGeo = new Set(current.historical_context?.geographic_scope ?? [])
  const currentTime = current.historical_context?.time_period ?? ""

  const scored = all
    .filter((m) => m.mystery_id !== current.mystery_id)
    .map((m) => {
      let score = 0

      // 同じ分類コード
      if (m.mystery_id.slice(0, 3) === currentClassification) {
        score += 3
      }

      // geographic_scope の重複
      const geo = m.historical_context?.geographic_scope ?? []
      for (const g of geo) {
        if (currentGeo.has(g)) score += 2
      }

      // time_period 完全一致
      if (currentTime && m.historical_context?.time_period === currentTime) {
        score += 1
      }

      return { mystery: m, score }
    })
    .filter(({ score }) => score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, maxCount)

  return scored.map(({ mystery }) => mystery)
}
