// TOC 固定セクション ID とセクション型
// サーバー / クライアント両方からインポート可能にするため "use client" を付けない

export const SECTION_IDS = {
  narrative: "section-narrative",
  discrepancy: "section-discrepancy",
  evidence: "section-evidence",
  hypothesis: "section-hypothesis",
  historicalContext: "section-historical-context",
} as const

export interface TocSection {
  id: string
  label: string
}
