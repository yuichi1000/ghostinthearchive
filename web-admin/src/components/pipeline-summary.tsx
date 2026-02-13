"use client"

import { cn } from "@ghost/shared/src/lib/utils"
import type { AgentLogEntry } from "@ghost/shared/src/types/mystery"
import { PIPELINE_PHASES, groupLogsByPhase } from "@/lib/pipeline-phases"
import { CheckCircle, XCircle, Loader2 } from "lucide-react"

interface PipelineSummaryProps {
  logs: AgentLogEntry[]
  className?: string
}

export function PipelineSummary({ logs, className }: PipelineSummaryProps) {
  if (!logs || logs.length === 0) return null

  const completed = logs.filter((l) => l.status === "completed").length
  const errors = logs.filter((l) => l.status === "error").length
  const running = logs.filter((l) => l.status === "running").length
  const total = logs.length
  const totalDuration = logs.reduce((sum, l) => sum + (l.duration_seconds || 0), 0)

  // フェーズ進捗ドット
  const activePhases = groupLogsByPhase(logs)
  const activePhaseIds = new Set(activePhases.map((g) => g.phase.id))
  const phaseStatusMap = new Map(activePhases.map((g) => [g.phase.id, g.status]))

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {/* 既存のサマリー行 */}
      <div className="flex items-center gap-3 text-xs font-mono">
        <span className="text-muted-foreground">Pipeline:</span>

        {completed > 0 && (
          <span className="flex items-center gap-1 text-[#5fb3a1]">
            <CheckCircle className="w-3 h-3" />
            {completed}/{total}
          </span>
        )}

        {errors > 0 && (
          <span className="flex items-center gap-1 text-[#ff6b6b]">
            <XCircle className="w-3 h-3" />
            {errors} failed
          </span>
        )}

        {running > 0 && (
          <span className="flex items-center gap-1 text-[#d4af37]">
            <Loader2 className="w-3 h-3 animate-spin" />
            running
          </span>
        )}

        {totalDuration > 0 && (
          <span className="text-muted-foreground">{Math.round(totalDuration)}s</span>
        )}
      </div>

      {/* フェーズ進捗ドットインジケーター */}
      <div className="flex items-center gap-1.5">
        {PIPELINE_PHASES.map((phase) => {
          const status = phaseStatusMap.get(phase.id)
          const isActive = activePhaseIds.has(phase.id)

          return (
            <div
              key={phase.id}
              className="flex flex-col items-center gap-0.5"
              title={phase.label}
            >
              <div
                className={cn(
                  "w-2 h-2 rounded-full",
                  !isActive && "bg-muted-foreground/30",
                  status === "completed" && "bg-[#5fb3a1]",
                  status === "running" && "bg-[#d4af37] animate-pulse",
                  status === "error" && "bg-[#ff6b6b]",
                )}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}
