"use client"

import { cn } from "@/lib/utils"
import type { AgentLogEntry } from "@/types/mystery"
import { AGENT_NAME_LABELS } from "@/types/mystery"
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
} from "lucide-react"

const AGENT_ICONS: Record<string, React.ReactNode> = {
  librarian: <FileSearch className="w-4 h-4" />,
  scholar: <BookOpen className="w-4 h-4" />,
  storyteller: <Pen className="w-4 h-4" />,
  scriptwriter: <FileText className="w-4 h-4" />,
  illustrator: <Palette className="w-4 h-4" />,
  producer: <Mic className="w-4 h-4" />,
  publisher: <Upload className="w-4 h-4" />,
}

const STATUS_CONFIG = {
  completed: {
    icon: <CheckCircle className="w-5 h-5" />,
    className: "bg-teal/20 text-[#5fb3a1] border-teal/30",
  },
  error: {
    icon: <XCircle className="w-5 h-5" />,
    className: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  },
  running: {
    icon: <Loader2 className="w-5 h-5 animate-spin" />,
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
} as const

interface PipelineTimelineProps {
  logs: AgentLogEntry[]
  className?: string
}

export function PipelineTimeline({ logs, className }: PipelineTimelineProps) {
  if (!logs || logs.length === 0) return null

  return (
    <div className={cn("space-y-4", className)}>
      <h3 className="text-sm font-mono uppercase tracking-wider text-muted-foreground mb-4">
        Pipeline Execution Log
      </h3>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-6 top-0 bottom-0 w-px bg-border" />

        <div className="space-y-6">
          {logs.map((log, index) => {
            const config = STATUS_CONFIG[log.status]
            const label = AGENT_NAME_LABELS[log.agent_name] || log.agent_name

            return (
              <div key={`${log.agent_name}-${index}`} className="relative flex gap-4">
                {/* Timeline dot */}
                <div className="relative z-10 flex-shrink-0">
                  <div className={cn("w-12 h-12 rounded-sm border-2 flex items-center justify-center", config.className)}>
                    {config.icon}
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 pt-1">
                  <div className="flex items-center gap-2 mb-1">
                    {AGENT_ICONS[log.agent_name]}
                    <h4 className="font-mono text-sm uppercase tracking-wider text-parchment">
                      {label}
                    </h4>
                    {log.duration_seconds !== null && (
                      <span className="text-xs text-muted-foreground font-mono">
                        ({log.duration_seconds}s)
                      </span>
                    )}
                  </div>

                  {log.output_summary && (
                    <div className="aged-card letterpress-border rounded-sm p-3 mt-2">
                      <p className="text-xs text-foreground/80 leading-relaxed">
                        {log.output_summary}
                      </p>
                    </div>
                  )}

                  {log.start_time && (
                    <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground font-mono">
                      <span>開始: {new Date(log.start_time).toLocaleTimeString()}</span>
                      {log.end_time && (
                        <span>終了: {new Date(log.end_time).toLocaleTimeString()}</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
