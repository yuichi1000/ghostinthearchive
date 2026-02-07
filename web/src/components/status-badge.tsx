import React from "react"
import { cn } from "@/lib/utils"
import type { DiscrepancyType, ConfidenceLevel, MysteryStatus } from "@/types/mystery"
import { DISCREPANCY_TYPE_LABELS } from "@/types/mystery"
import { Clock, Ghost, FileQuestion, AlertTriangle, MapPin, User, CheckCircle, XCircle, Clock3, Languages } from "lucide-react"

// Discrepancy type badge
const discrepancyConfig: Record<DiscrepancyType, { icon: React.ReactNode; className: string }> = {
  date_mismatch: {
    icon: <Clock className="w-3.5 h-3.5" />,
    className: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  },
  person_missing: {
    icon: <User className="w-3.5 h-3.5" />,
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  event_outcome: {
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
    className: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  },
  location_conflict: {
    icon: <MapPin className="w-3.5 h-3.5" />,
    className: "bg-teal/20 text-[#5fb3a1] border-teal/30",
  },
  narrative_gap: {
    icon: <Ghost className="w-3.5 h-3.5" />,
    className: "bg-parchment/20 text-parchment border-parchment/30",
  },
  name_variant: {
    icon: <FileQuestion className="w-3.5 h-3.5" />,
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
}

interface DiscrepancyBadgeProps {
  type: DiscrepancyType
  className?: string
}

export function DiscrepancyBadge({ type, className }: DiscrepancyBadgeProps) {
  const config = discrepancyConfig[type]
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-sm border font-mono uppercase tracking-wide",
        config.className,
        className
      )}
    >
      {config.icon}
      {DISCREPANCY_TYPE_LABELS[type]}
    </span>
  )
}

// Confidence level badge
const confidenceConfig: Record<ConfidenceLevel, { label: string; className: string }> = {
  high: {
    label: "High Confidence",
    className: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  },
  medium: {
    label: "Medium Confidence",
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  low: {
    label: "Low Confidence",
    className: "bg-muted text-muted-foreground border-border",
  },
}

interface ConfidenceBadgeProps {
  level: ConfidenceLevel
  className?: string
}

export function ConfidenceBadge({ level, className }: ConfidenceBadgeProps) {
  const config = confidenceConfig[level]
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-sm border font-mono uppercase tracking-wide",
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  )
}

// Status badge (for admin)
const statusConfig: Record<MysteryStatus, { icon: React.ReactNode; label: string; className: string }> = {
  pending: {
    icon: <Clock3 className="w-3.5 h-3.5" />,
    label: "Pending Review",
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  translating: {
    icon: <Languages className="w-3.5 h-3.5" />,
    label: "Translating",
    className: "bg-gold/20 text-[#d4af37] border-gold/30",
  },
  published: {
    icon: <CheckCircle className="w-3.5 h-3.5" />,
    label: "Published",
    className: "bg-teal/20 text-[#5fb3a1] border-teal/30",
  },
  archived: {
    icon: <XCircle className="w-3.5 h-3.5" />,
    label: "Archived",
    className: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  },
  error: {
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
    label: "Error",
    className: "bg-blood-red/20 text-[#ff6b6b] border-blood-red/30",
  },
}

interface StatusBadgeProps {
  status: MysteryStatus
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status]
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
