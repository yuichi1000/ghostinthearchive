"use client"

import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import type { PipelineRun } from "@/types/mystery"
import { AGENT_NAME_LABELS } from "@/types/mystery"
import { PipelineSummary } from "@/components/pipeline-summary"
import { PipelineTimeline } from "@/components/pipeline-timeline"
import {
  Search,
  Languages,
  Mic,
  Loader2,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from "lucide-react"

const TYPE_CONFIG: Record<
  string,
  { icon: React.ReactNode; label: string; colorClass: string }
> = {
  blog: {
    icon: <Search className="w-4 h-4" />,
    label: "調査パイプライン",
    colorClass: "text-[#5fb3a1]",
  },
  translate: {
    icon: <Languages className="w-4 h-4" />,
    label: "翻訳パイプライン",
    colorClass: "text-[#d4af37]",
  },
  podcast: {
    icon: <Mic className="w-4 h-4" />,
    label: "Podcast パイプライン",
    colorClass: "text-[#8b7ec8]",
  },
}

function ElapsedTimer({ startedAt }: { startedAt: Date }) {
  const [elapsed, setElapsed] = useState("")

  useEffect(() => {
    const update = () => {
      const now = Date.now()
      const diff = Math.floor((now - startedAt.getTime()) / 1000)
      const minutes = Math.floor(diff / 60)
      const seconds = diff % 60
      setElapsed(`${minutes}:${seconds.toString().padStart(2, "0")}`)
    }
    update()
    const interval = setInterval(update, 1000)
    return () => clearInterval(interval)
  }, [startedAt])

  return <span className="font-mono text-xs text-muted-foreground">{elapsed}</span>
}

interface RunningPipelineCardProps {
  run: PipelineRun
}

function RunningPipelineCard({ run }: RunningPipelineCardProps) {
  const [expanded, setExpanded] = useState(false)
  const config = TYPE_CONFIG[run.type] || TYPE_CONFIG.blog
  const currentAgentLabel = run.current_agent
    ? AGENT_NAME_LABELS[run.current_agent] || run.current_agent
    : null
  const isStale =
    run.status === "running" &&
    Date.now() - run.updated_at.getTime() > 30 * 60 * 1000
  const hasLogs = run.pipeline_log && run.pipeline_log.length > 0

  return (
    <div className="aged-card letterpress-border rounded-sm p-4">
      <div className="flex items-center justify-between gap-3">
        {/* Left: type icon + label + description */}
        <div className="flex items-center gap-3 min-w-0 flex-1">
          <div className={cn("flex-shrink-0", config.colorClass)}>
            {config.icon}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "text-sm font-mono uppercase tracking-wider",
                  config.colorClass
                )}
              >
                {config.label}
              </span>
              {isStale && (
                <span className="flex items-center gap-1 text-xs text-[#ff6b6b]">
                  <AlertCircle className="w-3 h-3" />
                  応答なし
                </span>
              )}
            </div>
            <p className="text-xs text-muted-foreground truncate mt-0.5">
              {run.query || run.mystery_id || ""}
            </p>
          </div>
        </div>

        {/* Right: current agent + elapsed + expand */}
        <div className="flex items-center gap-3 flex-shrink-0">
          {run.status === "running" && currentAgentLabel && (
            <span className="flex items-center gap-1.5 text-xs text-[#d4af37] font-mono">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              {currentAgentLabel}
            </span>
          )}
          {run.status === "error" && (
            <span className="flex items-center gap-1 text-xs text-[#ff6b6b] font-mono">
              <AlertCircle className="w-3.5 h-3.5" />
              Error
            </span>
          )}
          <ElapsedTimer startedAt={run.started_at} />
          {hasLogs && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1 hover:bg-muted/50 rounded-sm transition-colors"
            >
              {expanded ? (
                <ChevronUp className="w-4 h-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="w-4 h-4 text-muted-foreground" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Expanded: pipeline details */}
      {expanded && hasLogs && (
        <div className="mt-4 pt-4 border-t border-border/50">
          <PipelineSummary logs={run.pipeline_log} className="mb-4" />
          <PipelineTimeline logs={run.pipeline_log} />
        </div>
      )}
    </div>
  )
}

interface RunningPipelinesProps {
  runs: PipelineRun[]
  className?: string
}

export function RunningPipelines({ runs, className }: RunningPipelinesProps) {
  if (runs.length === 0) return null

  return (
    <div className={cn("mb-8", className)}>
      <h2 className="font-serif text-xl text-parchment mb-4">
        実行中のパイプライン
      </h2>
      <div className="space-y-3">
        {runs.map((run) => (
          <RunningPipelineCard key={run.id} run={run} />
        ))}
      </div>
    </div>
  )
}
