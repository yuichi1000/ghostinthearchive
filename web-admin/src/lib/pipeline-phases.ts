import type { AgentLogEntry, AgentStatus } from "@ghost/shared/src/types/mystery"
import { AGENT_NAME_LABELS } from "@ghost/shared/src/types/mystery"

/**
 * パイプラインフェーズ定義
 * エージェント名のパターンマッチでフェーズを判定する
 */
export interface PipelinePhase {
  id: string
  label: string
  match: (agentName: string) => boolean
}

export const PIPELINE_PHASES: PipelinePhase[] = [
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
  { id: "scriptwriting",      label: "脚本作成",    match: (n) => n === "scriptwriter" },
  { id: "script_translation", label: "脚本翻訳",    match: (n) => n === "podcast_translator_ja" },
]

/**
 * フェーズグループ: フェーズごとにログをまとめた構造
 */
export interface PhaseGroup {
  phase: PipelinePhase
  logs: AgentLogEntry[]
  status: AgentStatus
  totalDuration: number | null
}

/**
 * スキップされたエージェントのログエントリか判定する。
 * Orchestrator 側で除外するのが本筋だが、修正前の既存ログデータへの防御として
 * ダッシュボード側でもフィルタする。
 */
function isSkippedEntry(log: AgentLogEntry): boolean {
  return (
    log.duration_seconds !== null &&
    log.duration_seconds < 1.0 &&
    (!log.output_summary || log.output_summary === "(no text output)")
  )
}

/**
 * ログ配列をフェーズごとにグループ化する
 */
export function groupLogsByPhase(logs: AgentLogEntry[]): PhaseGroup[] {
  const groups: PhaseGroup[] = []

  for (const log of logs) {
    // スキップされたエントリを除外（language_gate による空応答等）
    if (isSkippedEntry(log)) continue

    const phase = PIPELINE_PHASES.find((p) => p.match(log.agent_name))
    if (!phase) continue

    let group = groups.find((g) => g.phase.id === phase.id)
    if (!group) {
      group = { phase, logs: [], status: "completed", totalDuration: null }
      groups.push(group)
    }
    group.logs.push(log)
  }

  // 各フェーズのステータスと合計時間を集約
  for (const group of groups) {
    group.status = aggregateStatus(group.logs)
    const durations = group.logs
      .map((l) => l.duration_seconds)
      .filter((d): d is number => d !== null)
    group.totalDuration = durations.length > 0
      ? Math.round(durations.reduce((a, b) => a + b, 0))
      : null
  }

  return groups
}

/**
 * 子エージェントのステータスからフェーズ全体のステータスを集約する
 * - 1つでも error → error
 * - 1つでも running → running
 * - 全完了 → completed
 */
function aggregateStatus(logs: AgentLogEntry[]): AgentStatus {
  if (logs.some((l) => l.status === "error")) return "error"
  if (logs.some((l) => l.status === "running")) return "running"
  return "completed"
}

/**
 * エージェント名から所属フェーズのラベルを返す
 * フェーズにマッチしない場合は AGENT_NAME_LABELS にフォールバック
 */
export function resolvePhaseLabel(agentName: string): string {
  const phase = PIPELINE_PHASES.find((p) => p.match(agentName))
  if (phase) return phase.label
  return AGENT_NAME_LABELS[agentName] || agentName
}
