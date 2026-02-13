"use client"

import { useState } from "react"
import { cn } from "@ghost/shared/src/lib/utils"
import type { AgentLogEntry } from "@ghost/shared/src/types/mystery"
import { AGENT_NAME_LABELS } from "@ghost/shared/src/types/mystery"
import { groupLogsByPhase, type PhaseGroup } from "@/lib/pipeline-phases"
import {
  CheckCircle,
  XCircle,
  Loader2,
  FileSearch,
  BookOpen,
  Pen,
  FileText,
  Palette,
  Mic,
  Upload,
  Compass,
  Brain,
  Languages,
  MessageSquare,
  ChevronDown,
  ChevronRight,
} from "lucide-react"

const PHASE_ICONS: Record<string, React.ReactNode> = {
  theme: <Compass className="w-4 h-4" />,
  research: <FileSearch className="w-4 h-4" />,
  analysis: <BookOpen className="w-4 h-4" />,
  debate: <MessageSquare className="w-4 h-4" />,
  integration: <Brain className="w-4 h-4" />,
  narrative: <Pen className="w-4 h-4" />,
  illustration: <Palette className="w-4 h-4" />,
  translation: <Languages className="w-4 h-4" />,
  publish: <Upload className="w-4 h-4" />,
}

const AGENT_ICONS: Record<string, React.ReactNode> = {
  theme_analyzer: <Compass className="w-3.5 h-3.5" />,
  librarian: <FileSearch className="w-3.5 h-3.5" />,
  scholar: <BookOpen className="w-3.5 h-3.5" />,
  armchair_polymath: <Brain className="w-3.5 h-3.5" />,
  storyteller: <Pen className="w-3.5 h-3.5" />,
  translator: <Languages className="w-3.5 h-3.5" />,
  scriptwriter: <FileText className="w-3.5 h-3.5" />,
  illustrator: <Palette className="w-3.5 h-3.5" />,
  producer: <Mic className="w-3.5 h-3.5" />,
  publisher: <Upload className="w-3.5 h-3.5" />,
}

/**
 * エージェント名からベース名を解決してアイコンを返す
 * 例: "librarian_en" → "librarian", "scholar_de_debate" → "scholar"
 */
function getAgentIcon(agentName: string): React.ReactNode {
  if (AGENT_ICONS[agentName]) return AGENT_ICONS[agentName]
  const withoutDebate = agentName.replace(/_debate$/, "")
  if (AGENT_ICONS[withoutDebate]) return AGENT_ICONS[withoutDebate]
  const baseName = withoutDebate.replace(/_[a-z]{2}$/, "")
  return AGENT_ICONS[baseName] || null
}

const STATUS_CONFIG = {
  completed: {
    icon: <CheckCircle className="w-5 h-5" />,
    dotIcon: <CheckCircle className="w-3.5 h-3.5" />,
    className: "bg-teal/20 text-[#5fb3a1] border-teal/30",
  },
  error: {
    icon: <XCircle className="w-5 h-5" />,
    dotIcon: <XCircle className="w-3.5 h-3.5" />,
    className: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  },
  running: {
    icon: <Loader2 className="w-5 h-5 animate-spin" />,
    dotIcon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
} as const

interface PipelineTimelineProps {
  logs: AgentLogEntry[]
  className?: string
}

export function PipelineTimeline({ logs, className }: PipelineTimelineProps) {
  if (!logs || logs.length === 0) return null

  const phases = groupLogsByPhase(logs)

  return (
    <div className={cn("space-y-4", className)}>
      <h3 className="text-sm font-mono uppercase tracking-wider text-muted-foreground mb-4">
        Pipeline Execution Log
      </h3>

      <div className="relative">
        {/* タイムライン縦線 */}
        <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />

        <div className="space-y-4">
          {phases.map((group) => (
            <PhaseEntry key={group.phase.id} group={group} />
          ))}
        </div>
      </div>
    </div>
  )
}

/**
 * フェーズエントリ: 単一エージェントならフラット表示、複数なら折りたたみ
 */
function PhaseEntry({ group }: { group: PhaseGroup }) {
  const [expanded, setExpanded] = useState(false)
  const config = STATUS_CONFIG[group.status]
  const hasChildren = group.logs.length > 1
  const icon = PHASE_ICONS[group.phase.id]

  return (
    <div>
      {/* フェーズヘッダー */}
      <div
        className={cn(
          "relative flex gap-4",
          hasChildren && "cursor-pointer"
        )}
        onClick={hasChildren ? () => setExpanded(!expanded) : undefined}
      >
        {/* タイムラインドット */}
        <div className="relative z-10 flex-shrink-0">
          <div className={cn("w-12 h-12 rounded-sm border-2 flex items-center justify-center", config.className)}>
            {config.icon}
          </div>
        </div>

        {/* コンテンツ */}
        <div className="flex-1 pt-1">
          <div className="flex items-center gap-2 mb-1">
            {icon}
            <h4 className="font-mono text-sm uppercase tracking-wider text-parchment">
              {group.phase.label}
            </h4>
            {group.totalDuration !== null && (
              <span className="text-xs text-muted-foreground font-mono">
                ({group.totalDuration}s)
              </span>
            )}
            {hasChildren && (
              <span className="text-xs text-muted-foreground font-mono">
                {group.logs.length}件
              </span>
            )}
            {hasChildren && (
              expanded
                ? <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
                : <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />
            )}
          </div>

          {/* 単一エージェントの場合はサマリーを直接表示 */}
          {!hasChildren && group.logs[0]?.output_summary && (
            <div className="aged-card letterpress-border rounded-sm p-3 mt-2">
              <p className="text-xs text-foreground/80 leading-relaxed">
                {group.logs[0].output_summary}
              </p>
            </div>
          )}

          {/* 単一エージェントの場合は時刻を表示 */}
          {!hasChildren && group.logs[0]?.start_time && (
            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground font-mono">
              <span>開始: {new Date(group.logs[0].start_time).toLocaleTimeString()}</span>
              {group.logs[0].end_time && (
                <span>終了: {new Date(group.logs[0].end_time).toLocaleTimeString()}</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 子エージェント（複数の場合のみ、展開時） */}
      {hasChildren && expanded && (
        <div className="ml-16 mt-2 space-y-2 border-l border-border/50 pl-4">
          {group.logs.map((log, index) => {
            const childConfig = STATUS_CONFIG[log.status]
            const label = AGENT_NAME_LABELS[log.agent_name] || log.agent_name

            return (
              <div key={`${log.agent_name}-${index}`} className="flex items-start gap-3 py-1.5">
                <div className={cn("flex-shrink-0 mt-0.5", childConfig.className.split(" ").filter(c => c.startsWith("text-")).join(" "))}>
                  {childConfig.dotIcon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    {getAgentIcon(log.agent_name)}
                    <span className="font-mono text-xs text-parchment/80">
                      {label}
                    </span>
                    {log.duration_seconds !== null && (
                      <span className="text-xs text-muted-foreground font-mono">
                        {log.duration_seconds}s
                      </span>
                    )}
                  </div>
                  {log.output_summary && (
                    <p className="text-xs text-foreground/60 mt-1 line-clamp-2">
                      {log.output_summary}
                    </p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
