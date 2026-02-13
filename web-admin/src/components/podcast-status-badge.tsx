import React from "react"
import { cn } from "@ghost/shared/src/lib/utils"
import type { PodcastStatus } from "@ghost/shared/src/types/mystery"
import { Loader2, FileText, Headphones, AlertTriangle } from "lucide-react"

const podcastStatusConfig: Record<PodcastStatus, { icon: React.ReactNode; label: string; className: string }> = {
  script_generating: {
    icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
    label: "脚本生成中",
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  script_ready: {
    icon: <FileText className="w-3.5 h-3.5" />,
    label: "脚本完了",
    className: "bg-teal/20 text-[#5fb3a1] border-teal/30",
  },
  audio_generating: {
    icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
    label: "音声生成中",
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  audio_ready: {
    icon: <Headphones className="w-3.5 h-3.5" />,
    label: "音声完了",
    className: "bg-teal/20 text-[#5fb3a1] border-teal/30",
  },
  error: {
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
    label: "エラー",
    className: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  },
}

interface PodcastStatusBadgeProps {
  status: PodcastStatus
  className?: string
}

export function PodcastStatusBadge({ status, className }: PodcastStatusBadgeProps) {
  const config = podcastStatusConfig[status]
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-sm border font-mono uppercase tracking-wide",
        config.className,
        className
      )}
    >
      {config.icon}
      {config.label}
    </span>
  )
}
