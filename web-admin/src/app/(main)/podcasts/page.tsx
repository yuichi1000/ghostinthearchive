"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import { cn } from "@ghost/shared/src/lib/utils"
import { getPodcastsByMysteryIdMap } from "@/lib/firestore/podcasts"
import { getAllMysteries } from "@/lib/firestore/mysteries"
import { MysteryPodcastCard } from "@/components/mystery-podcast-card"
import { ActionToast } from "@/components/action-toast"
import { ActivePipelinePanel } from "@/components/active-pipeline-panel"
import { usePipelineRuns } from "@/hooks/use-pipeline-runs"
import { useActionFeedback } from "@/hooks/use-action-feedback"
import type { FirestorePodcast, FirestoreMystery } from "@ghost/shared/src/types/mystery"
import {
  Mic,
  Filter,
  Inbox,
} from "lucide-react"

type FilterTab = "all" | "no_podcast" | "has_podcast"

const FILTER_LABELS: Record<FilterTab, string> = {
  all: "すべて",
  no_podcast: "未制作",
  has_podcast: "制作済み",
}

export default function PodcastsPage() {
  const [filter, setFilter] = useState<FilterTab>("all")
  const [podcastMap, setPodcastMap] = useState<Map<string, FirestorePodcast>>(new Map())
  const [mysteries, setMysteries] = useState<FirestoreMystery[]>([])
  const [loading, setLoading] = useState(true)
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
        getPodcastsByMysteryIdMap(),
        getAllMysteries(100),
      ])
      setPodcastMap(podcastData)
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

  // 公開済み記事のみ
  const publishedMysteries = useMemo(
    () => mysteries.filter((m) => m.status === "published"),
    [mysteries]
  )

  // フィルタ適用
  const filteredMysteries = useMemo(() => {
    switch (filter) {
      case "no_podcast":
        return publishedMysteries.filter((m) => !podcastMap.has(m.mystery_id))
      case "has_podcast":
        return publishedMysteries.filter((m) => podcastMap.has(m.mystery_id))
      default:
        return publishedMysteries
    }
  }, [filter, publishedMysteries, podcastMap])

  // カウント
  const counts: Record<FilterTab, number> = useMemo(() => ({
    all: publishedMysteries.length,
    no_podcast: publishedMysteries.filter((m) => !podcastMap.has(m.mystery_id)).length,
    has_podcast: publishedMysteries.filter((m) => podcastMap.has(m.mystery_id)).length,
  }), [publishedMysteries, podcastMap])

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
            公開済み記事からポッドキャストエピソードを制作する。記事をクリックして開始。
          </p>
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
          {(["all", "no_podcast", "has_podcast"] as FilterTab[]).map(
            (tab) => (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                className={cn(
                  "px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded-sm border transition-colors",
                  filter === tab
                    ? "bg-gold/20 text-gold border-gold/30"
                    : "bg-transparent text-muted-foreground border-border hover:border-parchment/30 hover:text-parchment"
                )}
              >
                {FILTER_LABELS[tab]}
                <span className="ml-2 text-muted-foreground">
                  ({counts[tab]})
                </span>
              </button>
            )
          )}
        </div>

        {/* 記事×Podcast カードグリッド */}
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
        ) : filteredMysteries.length === 0 ? (
          <div className="text-center py-16">
            <Inbox className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">
              {filter === "all"
                ? "公開済みの記事がありません。"
                : filter === "no_podcast"
                  ? "Podcast 未制作の記事はありません。"
                  : "Podcast 制作済みの記事はありません。"}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredMysteries.map((mystery) => (
              <MysteryPodcastCard
                key={mystery.mystery_id}
                mystery={mystery}
                podcast={podcastMap.get(mystery.mystery_id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
