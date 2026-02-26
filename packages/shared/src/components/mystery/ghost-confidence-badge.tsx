import { Ghost } from "lucide-react"
import { cn } from "../../lib/utils"
import type { ConfidenceLevel } from "../../types/mystery"

interface ConfidenceLabels {
  confirmedGhost: string
  suspectedGhost: string
  archivalEcho: string
}

interface GhostConfidenceBadgeProps {
  level: ConfidenceLevel
  labels: ConfidenceLabels
  className?: string
}

const colorMap: Record<ConfidenceLevel, string> = {
  high: "bg-emerald-900/30 text-emerald-400",
  medium: "bg-amber-900/30 text-amber-400",
  low: "bg-zinc-700/30 text-zinc-400",
}

const labelMap: Record<ConfidenceLevel, keyof ConfidenceLabels> = {
  high: "confirmedGhost",
  medium: "suspectedGhost",
  low: "archivalEcho",
}

export function GhostConfidenceBadge({ level, labels, className }: GhostConfidenceBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider",
        colorMap[level],
        className
      )}
    >
      <Ghost className="w-3 h-3" />
      {labels[labelMap[level]]}
    </span>
  )
}
