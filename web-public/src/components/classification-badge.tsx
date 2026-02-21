import { cn } from "@ghost/shared/src/lib/utils"
import type { Dictionary } from "@/lib/i18n/dictionaries"

type ClassificationCode = "HIS" | "FLK" | "ANT" | "OCC" | "URB" | "CRM" | "REL" | "LOC"

interface ClassificationBadgeProps {
  mysteryId: string
  labels: Dictionary["classification"]
  className?: string
}

const colorMap: Record<ClassificationCode, string> = {
  HIS: "bg-amber-900/30 text-amber-400",
  FLK: "bg-teal-900/30 text-teal-400",
  ANT: "bg-orange-900/30 text-orange-400",
  OCC: "bg-purple-900/30 text-purple-400",
  URB: "bg-slate-700/30 text-slate-400",
  CRM: "bg-red-900/30 text-red-400",
  REL: "bg-indigo-900/30 text-indigo-400",
  LOC: "bg-emerald-900/30 text-emerald-400",
}

function extractClassification(mysteryId: string): ClassificationCode | null {
  const code = mysteryId.slice(0, 3).toUpperCase()
  if (code in colorMap) return code as ClassificationCode
  return null
}

export function ClassificationBadge({ mysteryId, labels, className }: ClassificationBadgeProps) {
  const code = extractClassification(mysteryId)
  if (!code) return null

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider",
        colorMap[code],
        className
      )}
    >
      {labels[code]}
    </span>
  )
}
