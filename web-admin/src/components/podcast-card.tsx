"use client"

import Link from "next/link"
import type { FirestorePodcast } from "@ghost/shared/src/types/mystery"
import { PodcastStatusBadge } from "@/components/podcast-status-badge"
import { AudioPlayer } from "@/components/audio-player"
import { FileText, Clock, Eye } from "lucide-react"

interface PodcastCardProps {
  podcast: FirestorePodcast
}

export function PodcastCard({ podcast }: PodcastCardProps) {
  return (
    <article className="aged-card letterpress-border rounded-sm p-5">
      {/* ヘッダー: 記事タイトル + ステータス */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <h3 className="font-serif text-lg text-parchment leading-tight line-clamp-2">
          {podcast.mystery_title}
        </h3>
        <PodcastStatusBadge status={podcast.status} />
      </div>

      {/* 脚本情報 */}
      {podcast.script && (
        <div className="mb-3">
          <div className="flex items-center gap-2 text-sm text-foreground/80 mb-1">
            <FileText className="w-3.5 h-3.5 text-gold" />
            <span>{podcast.script.episode_title}</span>
          </div>
          {podcast.script.estimated_duration_minutes > 0 && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Clock className="w-3 h-3" />
              <span>{podcast.script.estimated_duration_minutes} min</span>
            </div>
          )}
        </div>
      )}

      {/* 音声完了時: コンパクト AudioPlayer */}
      {podcast.status === "audio_ready" && podcast.audio?.public_url && (
        <div className="mb-3">
          <AudioPlayer
            src={podcast.audio.public_url}
            downloadUrl={podcast.audio.public_url}
          />
        </div>
      )}

      {/* エラー時: エラーメッセージ */}
      {podcast.status === "error" && podcast.error_message && (
        <div className="bg-blood-red/10 border border-blood-red/20 rounded-sm p-2 mb-3">
          <p className="text-xs text-[#ff6b6b] font-mono line-clamp-2">
            {podcast.error_message}
          </p>
        </div>
      )}

      {/* フッター: 作成日時 + 詳細リンク */}
      <div className="flex items-center justify-between pt-3 border-t border-border/50">
        <span className="text-xs text-muted-foreground">
          {podcast.created_at.toLocaleDateString()}
        </span>
        <Link
          href={`/podcasts/${podcast.podcast_id}`}
          className="inline-flex items-center gap-1.5 text-sm text-gold hover:text-parchment transition-colors no-underline"
        >
          <Eye className="w-4 h-4" />
          詳細
        </Link>
      </div>
    </article>
  )
}
