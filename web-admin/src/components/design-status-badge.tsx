import React from "react"
import { cn } from "@ghost/shared/src/lib/utils"
import type { DesignStatus } from "@ghost/shared/src/types/mystery"
import { Loader2, Palette, Image, CheckCircle, AlertTriangle } from "lucide-react"

const designStatusConfig: Record<DesignStatus, { icon: React.ReactNode; label: string; className: string }> = {
  designing: {
    icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
    label: "デザイン生成中",
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  design_ready: {
    icon: <Palette className="w-3.5 h-3.5" />,
    label: "デザイン完了",
    className: "bg-teal/20 text-[#5fb3a1] border-teal/30",
  },
  rendering: {
    icon: <Loader2 className="w-3.5 h-3.5 animate-spin" />,
    label: "レンダリング中",
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  render_ready: {
    icon: <CheckCircle className="w-3.5 h-3.5" />,
    label: "アセット完了",
    className: "bg-teal/20 text-[#5fb3a1] border-teal/30",
  },
  error: {
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
    label: "エラー",
    className: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  },
}

interface DesignStatusBadgeProps {
  status: DesignStatus
  className?: string
}

export function DesignStatusBadge({ status, className }: DesignStatusBadgeProps) {
  const config = designStatusConfig[status]
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
