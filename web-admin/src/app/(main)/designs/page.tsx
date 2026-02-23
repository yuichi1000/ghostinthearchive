"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import { useSearchParams } from "next/navigation"
import { cn } from "@ghost/shared/src/lib/utils"
import { getDesignsByMysteryIdMap } from "@/lib/firestore/designs"
import { getAllMysteries } from "@/lib/firestore/mysteries"
import { DesignCard } from "@/components/design-card"
import { ActionToast } from "@/components/action-toast"
import { ActivePipelinePanel } from "@/components/active-pipeline-panel"
import { usePipelineRuns } from "@/hooks/use-pipeline-runs"
import { useActionFeedback } from "@/hooks/use-action-feedback"
import type { FirestoreDesign, FirestoreMystery } from "@ghost/shared/src/types/mystery"
import {
  Palette,
  Filter,
  Inbox,
  Loader2,
} from "lucide-react"

type FilterTab = "all" | "no_design" | "has_design"

const FILTER_LABELS: Record<FilterTab, string> = {
  all: "すべて",
  no_design: "未制作",
  has_design: "制作済み",
}

export default function DesignsPage() {
  const searchParams = useSearchParams()
  const newMysteryId = searchParams.get("new")

  const [filter, setFilter] = useState<FilterTab>("all")
  const [designMap, setDesignMap] = useState<Map<string, FirestoreDesign>>(new Map())
  const [mysteries, setMysteries] = useState<FirestoreMystery[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [customInstructions, setCustomInstructions] = useState("")
  const feedback = useActionFeedback()

  // Design タイプのパイプラインのみ表示
  const { runs: runningPipelines, dismiss: dismissRunning } = usePipelineRuns()
  const designRuns = useMemo(
    () => runningPipelines.filter((r) => r.type === "design" || r.type === "design_render"),
    [runningPipelines]
  )

  const fetchData = useCallback(async () => {
    try {
      const [designData, mysteryData] = await Promise.all([
        getDesignsByMysteryIdMap(),
        getAllMysteries(100),
      ])
      setDesignMap(designData)
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

  // 新規デザイン生成ハンドラ
  const handleGenerate = useCallback(async (mysteryId: string) => {
    setGenerating(true)
    try {
      const res = await fetch("/api/design/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mystery_id: mysteryId,
          custom_instructions: customInstructions,
        }),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || `API error (${res.status})`)
      }
      const data = await res.json()
      feedback.showSuccess("デザイン生成を開始しました")
      if (data.design_id) {
        window.location.href = `/designs/${data.design_id}`
      }
    } catch (error) {
      console.error("Failed to generate design:", error)
      const message = error instanceof Error ? error.message : "不明なエラー"
      feedback.showError(`デザイン生成の開始に失敗しました: ${message}`)
    } finally {
      setGenerating(false)
    }
  }, [customInstructions])

  // 公開済み記事のみ
  const publishedMysteries = useMemo(
    () => mysteries.filter((m) => m.status === "published"),
    [mysteries]
  )

  // フィルタ適用
  const filteredMysteries = useMemo(() => {
    switch (filter) {
      case "no_design":
        return publishedMysteries.filter((m) => !designMap.has(m.mystery_id))
      case "has_design":
        return publishedMysteries.filter((m) => designMap.has(m.mystery_id))
      default:
        return publishedMysteries
    }
  }, [filter, publishedMysteries, designMap])

  // カウント
  const counts: Record<FilterTab, number> = useMemo(() => ({
    all: publishedMysteries.length,
    no_design: publishedMysteries.filter((m) => !designMap.has(m.mystery_id)).length,
    has_design: publishedMysteries.filter((m) => designMap.has(m.mystery_id)).length,
  }), [publishedMysteries, designMap])

  // 新規生成フォーム（URL パラメータで記事指定時）
  const newMystery = useMemo(
    () => newMysteryId ? publishedMysteries.find((m) => m.mystery_id === newMysteryId) : null,
    [newMysteryId, publishedMysteries]
  )

  return (
    <div className="py-8 md:py-12">
      <div className="container mx-auto px-4">
        {/* ページヘッダー */}
        <div className="flex items-center gap-4 mb-8">
          <div className="flex items-center gap-3 px-4 py-2 bg-gold/10 border border-gold/30 rounded-sm">
            <Palette className="w-5 h-5 text-[#d4af37]" />
            <span className="font-mono text-sm uppercase tracking-wider text-[#d4af37]">
              Design Studio
            </span>
          </div>
          <div className="h-px flex-1 bg-border" />
        </div>

        <div className="mb-8">
          <h1 className="font-serif text-3xl md:text-4xl text-parchment mb-2">
            Product Designs
          </h1>
          <p className="text-muted-foreground">
            公開済み記事からプロダクトデザイン（T-シャツ・マグカップ）を制作する。記事をクリックして開始。
          </p>
        </div>

        <ActionToast message={feedback.message} isError={feedback.isError} />

        {/* 新規生成フォーム */}
        {newMystery && (
          <div className="aged-card letterpress-border rounded-sm p-5 mb-8">
            <h2 className="font-serif text-lg text-parchment mb-2">
              {newMystery.title}
            </h2>
            <p className="text-sm text-muted-foreground mb-4">
              この記事のプロダクトデザインを生成します。
            </p>
            <div className="mb-4">
              <label className="block text-xs font-mono uppercase tracking-wider text-muted-foreground mb-2">
                カスタム指示（オプション）
              </label>
              <textarea
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                placeholder="例: 日本のモチーフを強調して、ダークカラーで"
                rows={2}
                className="w-full px-3 py-2 text-sm bg-background border border-border rounded-sm resize-none focus:outline-none focus:border-gold/50"
              />
            </div>
            <button
              onClick={() => handleGenerate(newMystery.mystery_id)}
              disabled={generating}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-mono bg-gold/20 border border-gold/30 text-[#d4af37] rounded-sm hover:bg-gold/30 transition-colors disabled:opacity-50"
            >
              {generating ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Palette className="w-4 h-4" />
              )}
              デザイン生成を開始
            </button>
          </div>
        )}

        {/* 実行中のパイプライン */}
        {designRuns.length > 0 && (
          <div className="space-y-3 mb-8">
            {designRuns.map((run) => (
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
          {(["all", "no_design", "has_design"] as FilterTab[]).map(
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

        {/* 記事×Design カードグリッド */}
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
                : filter === "no_design"
                  ? "デザイン未制作の記事はありません。"
                  : "デザイン制作済みの記事はありません。"}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredMysteries.map((mystery) => (
              <DesignCard
                key={mystery.mystery_id}
                mystery={mystery}
                design={designMap.get(mystery.mystery_id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
