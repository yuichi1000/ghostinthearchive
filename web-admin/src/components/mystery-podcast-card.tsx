import Link from "next/link"
import { cn } from "@ghost/shared/src/lib/utils"
import { PodcastStatusBadge } from "@/components/podcast-status-badge"
import type { FirestoreMystery, FirestorePodcast } from "@ghost/shared/src/types/mystery"
import { FileText, Mic, MicOff } from "lucide-react"

interface MysteryPodcastCardProps {
  mystery: FirestoreMystery
  podcast?: FirestorePodcast
}

export function MysteryPodcastCard({ mystery, podcast }: MysteryPodcastCardProps) {
  const href = podcast
    ? `/podcasts/${podcast.podcast_id}`
    : `/podcasts/new/${mystery.mystery_id}`

  return (
    <Link href={href} className="no-underline block group">
      <article className="aged-card letterpress-border rounded-sm p-5 transition-colors group-hover:border-gold/40">
        {/* ヘッダー: Mystery ID + Podcast ステータス */}
        <div className="flex items-start justify-between gap-4 mb-3">
          <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
            <FileText className="w-3.5 h-3.5 text-gold" />
            <span>{mystery.mystery_id}</span>
          </div>
          {podcast ? (
            <PodcastStatusBadge status={podcast.status} />
          ) : (
            <span
              className={cn(
                "inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-sm border font-mono uppercase tracking-wide",
                "bg-muted/20 text-muted-foreground border-border"
              )}
            >
              <MicOff className="w-3.5 h-3.5" />
              未制作
            </span>
          )}
        </div>

        {/* 記事タイトル */}
        <h3 className="font-serif text-lg text-parchment mb-1 leading-tight line-clamp-2 group-hover:text-gold transition-colors">
          {mystery.title}
        </h3>

        {/* サマリー */}
        <p className="text-sm text-foreground/80 leading-relaxed mb-4 line-clamp-2">
          {mystery.summary}
        </p>

        {/* フッター */}
        <div className="flex items-center justify-between pt-3 border-t border-border/50">
          <span className="text-xs text-muted-foreground">
            {mystery.createdAt.toLocaleDateString()}
          </span>
          {podcast ? (
            <span className="inline-flex items-center gap-1.5 text-sm text-gold">
              <Mic className="w-4 h-4" />
              詳細を見る
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 text-sm text-teal-400">
              <Mic className="w-4 h-4" />
              Podcast を制作
            </span>
          )}
        </div>
      </article>
    </Link>
  )
}
