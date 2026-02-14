import { AGENT_NAME_LABELS } from "@ghost/shared/src/types/mystery"

/**
 * パイプラインフェーズ定義
 * エージェント名のパターンマッチでフェーズを判定する
 */
interface PipelinePhase {
  id: string
  label: string
  match: (agentName: string) => boolean
}

const PIPELINE_PHASES: PipelinePhase[] = [
  // ブログパイプライン
  { id: "theme",              label: "テーマ分析",  match: (n) => n === "theme_analyzer" },
  { id: "research",           label: "資料収集",    match: (n) => n.startsWith("librarian") },
  { id: "analysis",           label: "学際分析",    match: (n) => n.startsWith("scholar") && !n.includes("debate") },
  { id: "debate",             label: "討論",        match: (n) => n.includes("debate") },
  { id: "integration",        label: "統合分析",    match: (n) => n === "armchair_polymath" },
  { id: "narrative",          label: "物語生成",    match: (n) => n === "storyteller" },
  { id: "illustration",       label: "画像生成",    match: (n) => n === "illustrator" },
  { id: "translation",        label: "翻訳",        match: (n) => n.startsWith("translator") },
  { id: "publish",            label: "公開処理",    match: (n) => n === "publisher" },
  // Podcast パイプライン
  { id: "script_planning",    label: "アウトライン設計", match: (n) => n === "script_planner" },
  { id: "scriptwriting",      label: "脚本作成",    match: (n) => n === "scriptwriter" },
  { id: "script_translation", label: "脚本翻訳",    match: (n) => n === "podcast_translator_ja" },
]

/**
 * エージェント名から所属フェーズのラベルを返す
 * フェーズにマッチしない場合は AGENT_NAME_LABELS にフォールバック
 */
export function resolvePhaseLabel(agentName: string): string {
  const phase = PIPELINE_PHASES.find((p) => p.match(agentName))
  if (phase) return phase.label
  return AGENT_NAME_LABELS[agentName] || agentName
}
