import Link from "next/link"
import { StatusBadge } from "@/components/status-badge"
import { Button } from "@ghost/shared/src/components/ui/button"
import { localizeMystery } from "@ghost/shared/src/lib/localize"
import type { FirestoreMystery } from "@ghost/shared/src/types/mystery"
import type { PreviewLang } from "@/components/language-selector"
import {
  FileText,
  CheckCircle,
  XCircle,
  Eye,
  EyeOff,
  Clock,
  MapPin,
  RefreshCw,
} from "lucide-react"

interface AdminMysteryCardProps {
  mystery: FirestoreMystery
  lang: PreviewLang
  onApprove: () => void
  onArchive: () => void
  onUnpublish: () => void
}

export function AdminMysteryCard({ mystery, lang, onApprove, onArchive, onUnpublish }: AdminMysteryCardProps) {
  const isPending = mystery.status === "pending"
  const location = mystery.historical_context?.geographic_scope?.[0] || ""
  const timePeriod = mystery.historical_context?.time_period || ""
  const { title, summary } = localizeMystery(mystery, lang)

  return (
    <article className="aged-card letterpress-border rounded-sm p-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
          <FileText className="w-3.5 h-3.5 text-gold" />
          <span>{mystery.mystery_id}</span>
        </div>
        <StatusBadge status={mystery.status} />
      </div>

      {/* タイトル（グローバル言語設定に連動） */}
      <h3 className="font-serif text-lg text-parchment mb-1 leading-tight">
        {title}
      </h3>

      {/* サマリー（グローバル言語設定に連動） */}
      <p className="text-sm text-foreground/80 leading-relaxed mb-4 line-clamp-2">
        {summary}
      </p>

      {/* Metadata */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground mb-4 pb-4 border-b border-border/50">
        {location && (
          <span className="flex items-center gap-1">
            <MapPin className="w-3 h-3" />
            {location}
          </span>
        )}
        {timePeriod && (
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {timePeriod}
          </span>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between gap-4">
        {mystery.status === "published" ? (
          <>
            <div className="flex items-center gap-3">
              <a
                href={`${process.env.NEXT_PUBLIC_SITE_URL || ""}/${lang}/mystery/${mystery.mystery_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-gold hover:text-parchment transition-colors no-underline"
              >
                <Eye className="w-4 h-4" />
                View Published
              </a>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={onUnpublish}
              className="border-blood-red/30 text-[#ff6b6b] hover:bg-blood-red/20 hover:text-[#ff6b6b] bg-transparent"
            >
              <EyeOff className="w-4 h-4 mr-1" />
              Unpublish
            </Button>
          </>
        ) : (
          <div className="flex items-center gap-3">
            <Link
              href={`/preview/${mystery.mystery_id}`}
              className="inline-flex items-center gap-2 text-sm text-gold hover:text-parchment transition-colors no-underline"
            >
              <Eye className="w-4 h-4" />
              Preview
            </Link>
            <span className="text-xs text-muted-foreground">
              Created: {mystery.createdAt.toLocaleDateString()}
            </span>
          </div>
        )}

        {isPending && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onArchive}
              className="border-blood-red/30 text-[#ff6b6b] hover:bg-blood-red/20 hover:text-[#ff6b6b] bg-transparent"
            >
              <XCircle className="w-4 h-4 mr-1" />
              Archive
            </Button>
            <Button
              size="sm"
              onClick={onApprove}
              className="bg-teal/20 border border-teal/30 text-[#5fb3a1] hover:bg-teal/30"
            >
              <CheckCircle className="w-4 h-4 mr-1" />
              Approve
            </Button>
          </div>
        )}

        {mystery.status === "archived" && (
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground hover:text-parchment"
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            Reconsider
          </Button>
        )}

      </div>
    </article>
  )
}
