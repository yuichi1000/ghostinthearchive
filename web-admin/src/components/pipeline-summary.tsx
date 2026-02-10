"use client"

import { cn } from "@ghost/shared/src/lib/utils"
import type { AgentLogEntry } from "@ghost/shared/src/types/mystery"
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

  return (
    <div className={cn("flex items-center gap-3 text-xs font-mono", className)}>
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
  )
}
