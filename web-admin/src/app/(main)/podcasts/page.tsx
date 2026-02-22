"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import { useRouter } from "next/navigation"
import { cn } from "@ghost/shared/src/lib/utils"
import { Button } from "@ghost/shared/src/components/ui/button"
import { getAllPodcasts } from "@/lib/firestore/podcasts"
import { getAllMysteries } from "@/lib/firestore/mysteries"
import { PodcastCard } from "@/components/podcast-card"
import { ActionToast } from "@/components/action-toast"
import { ActivePipelinePanel } from "@/components/active-pipeline-panel"
import { usePipelineRuns } from "@/hooks/use-pipeline-runs"
import { useActionFeedback } from "@/hooks/use-action-feedback"
import type { FirestorePodcast, PodcastStatus, FirestoreMystery } from "@ghost/shared/src/types/mystery"
import {
  Mic,
  Filter,
  Inbox,
  Loader2,
  FileText,
} from "lucide-react"

type FilterStatus = "all" | PodcastStatus

export default function PodcastsPage() {
  const router = useRouter()
  const [filter, setFilter] = useState<FilterStatus>("all")
  const [podcasts, setPodcasts] = useState<FirestorePodcast[]>([])
  const [mysteries, setMysteries] = useState<FirestoreMystery[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedMysteryId, setSelectedMysteryId] = useState("")
  const [customInstructions, setCustomInstructions] = useState("")
  const [generating, setGenerating] = useState(false)
  const feedback = useActionFeedback()

  // Podcast タイプのパイプラインのみ表示
  const { runs: runningPipelines, dismiss: dismissRunning } = usePipelineRuns()
  const podcastRuns = useMemo(
    () => runningPipelines.filter((r) => r.type === "podcast"),
    [runningPipelines]
  )

  const fetchData = useCallback(async () => {
    try {
      const [podcastData, mysteryData] = await Promise.all([
        getAllPodcasts(50),
        getAllMysteries(100),
      ])
      setPodcasts(podcastData)
      setMysteries(mysteryData)
    } catch (error) {
      console.error("Failed to fetch data:", error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  // 公開済み記事のみフィルタ
  const publishedMysteries = useMemo(
    () => mysteries.filter((m) => m.status === "published"),
    [mysteries]
  )

  const filteredPodcasts = filter === "all"
    ? podcasts
    : podcasts.filter((p) => p.status === filter)

  const counts = {
    all: podcasts.length,
    script_generating: podcasts.filter((p) => p.status === "script_generating").length,
    script_ready: podcasts.filter((p) => p.status === "script_ready").length,
    audio_generating: podcasts.filter((p) => p.status === "audio_generating").length,
    audio_ready: podcasts.filter((p) => p.status === "audio_ready").length,
    error: podcasts.filter((p) => p.status === "error").length,
  }

  const handleGenerateScript = async () => {
    if (!selectedMysteryId) return
    setGenerating(true)
    try {
      const res = await fetch("/api/podcast/generate-script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mystery_id: selectedMysteryId,
          custom_instructions: customInstructions.trim(),
        }),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || `API error (${res.status})`)
      }
      const data = await res.json()

      if (data.podcast_id) {
        router.push(`/podcasts/${data.podcast_id}`)
      } else {
        feedback.showSuccess("脚本生成を開始しました")
        fetchData()
      }
    } catch (error) {
      console.error("Failed to generate script:", error)
      const message = error instanceof Error ? error.message : "不明なエラー"
      feedback.showError(`脚本生成の開始に失敗しました: ${message}`)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="py-8 md:py-12">
      <div className="container mx-auto px-4">
        {/* ページヘッダー */}
        <div className="flex items-center gap-4 mb-8">
          <div className="flex items-center gap-3 px-4 py-2 bg-gold/10 border border-gold/30 rounded-sm">
            <Mic className="w-5 h-5 text-[#d4af37]" />
            <span className="font-mono text-sm uppercase tracking-wider text-[#d4af37]">
              Podcast Studio
            </span>
          </div>
          <div className="h-px flex-1 bg-border" />
        </div>

        <div className="mb-8">
          <h1 className="font-serif text-3xl md:text-4xl text-parchment mb-2">
            Podcast Production
          </h1>
          <p className="text-muted-foreground">
            公開済み記事からポッドキャストエピソードを制作する。
          </p>
        </div>

        {/* 新規 Podcast 作成セクション */}
        <div className="aged-card letterpress-border rounded-sm p-5 mb-8">
          <h2 className="font-serif text-xl text-parchment mb-4">
            新規エピソード作成
          </h2>

          <div className="space-y-3">
            {/* 記事セレクタ */}
            <div>
              <label className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1 block">
                対象記事
              </label>
              <select
                value={selectedMysteryId}
                onChange={(e) => setSelectedMysteryId(e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-sm text-sm text-parchment focus:outline-none focus:border-gold/50"
              >
                <option value="">記事を選択...</option>
                {publishedMysteries.map((m) => (
                  <option key={m.mystery_id} value={m.mystery_id}>
                    {m.title}
                  </option>
                ))}
              </select>
            </div>

            {/* カスタム指示 */}
            <div>
              <label className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1 block">
                カスタム指示（任意）
              </label>
              <textarea
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                placeholder="例: 冒頭で地元の伝説を詳しく紹介してほしい"
                rows={2}
                className="w-full px-3 py-2 bg-background border border-border rounded-sm text-sm text-parchment placeholder:text-muted-foreground resize-none focus:outline-none focus:border-gold/50"
              />
            </div>

            <Button
              size="sm"
              onClick={handleGenerateScript}
              disabled={!selectedMysteryId || generating}
              className="bg-teal/20 border border-teal/30 text-[#5fb3a1] hover:bg-teal/30"
            >
              {generating ? (
                <Loader2 className="w-4 h-4 mr-1 animate-spin" />
              ) : (
                <FileText className="w-4 h-4 mr-1" />
              )}
              脚本生成
            </Button>
          </div>
        </div>

        <ActionToast message={feedback.message} isError={feedback.isError} />

        {/* 実行中のパイプライン */}
        {podcastRuns.length > 0 && (
          <div className="space-y-3 mb-8">
            {podcastRuns.map((run) => (
              <ActivePipelinePanel
                key={run.id}
                run={run}
                onDismiss={() => dismissRunning(run.id)}
              />
            ))}
          </div>
        )}

        {/* フィルタタブ */}
        <div className="flex flex-wrap items-center gap-2 mb-8 pb-4 border-b border-border">
          <Filter className="w-4 h-4 text-muted-foreground mr-2" />
          {(["all", "script_generating", "script_ready", "audio_generating", "audio_ready", "error"] as FilterStatus[]).map(
            (status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={cn(
                  "px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded-sm border transition-colors",
                  filter === status
                    ? "bg-gold/20 text-gold border-gold/30"
                    : "bg-transparent text-muted-foreground border-border hover:border-parchment/30 hover:text-parchment"
                )}
              >
                {status === "all" ? "All" : status.replace("_", " ")}
                <span className="ml-2 text-muted-foreground">
                  ({counts[status]})
                </span>
              </button>
            )
          )}
        </div>

        {/* Podcast カードグリッド */}
        {loading ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="aged-card letterpress-border rounded-sm p-5 h-48 animate-pulse">
                <div className="h-4 bg-muted rounded w-1/4 mb-4" />
                <div className="h-5 bg-muted rounded w-3/4 mb-2" />
                <div className="h-4 bg-muted rounded w-full mb-4" />
                <div className="h-6 bg-muted rounded w-1/3" />
              </div>
            ))}
          </div>
        ) : filteredPodcasts.length === 0 ? (
          <div className="text-center py-16">
            <Inbox className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              {filter === "all"
                ? "まだ Podcast がありません。上のフォームから作成してください。"
                : "該当する Podcast がありません。"}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredPodcasts.map((podcast) => (
              <PodcastCard key={podcast.podcast_id} podcast={podcast} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
