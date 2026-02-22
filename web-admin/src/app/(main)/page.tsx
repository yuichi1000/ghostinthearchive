"use client"

import { useEffect, useState, useCallback, useRef, useMemo } from "react"
import { cn } from "@ghost/shared/src/lib/utils"
import { getAllMysteries } from "@/lib/firestore/mysteries"
import type { FirestoreMystery, PipelineRun } from "@ghost/shared/src/types/mystery"
import { AdminMysteryCard } from "@/components/admin-mystery-card"
import { ActionToast } from "@/components/action-toast"
import { InvestigationForm } from "@/components/investigation-form"
import { ActivePipelinePanel } from "@/components/active-pipeline-panel"
import { usePipelineRuns } from "@/hooks/use-pipeline-runs"
import { usePipelineRun } from "@/hooks/use-pipeline-run"
import { useMysteryActions } from "@/hooks/use-mystery-actions"
import { useInvestigation } from "@/hooks/use-investigation"
import { useLanguage } from "@/contexts/language-context"
import {
  Shield,
  Filter,
  Inbox,
} from "lucide-react"

type FilterStatus = "all" | "pending" | "published" | "archived"

export default function AdminPage() {
  const { lang } = useLanguage()
  const [filter, setFilter] = useState<FilterStatus>("all")
  const [mysteries, setMysteries] = useState<FirestoreMystery[]>([])
  const [loading, setLoading] = useState(true)
  const [currentRunId, setCurrentRunId] = useState<string | null>(null)
  const [dismissedRunIds, setDismissedRunIds] = useState<Set<string>>(new Set())

  // パイプライン進捗監視フック
  const { runs: runningPipelines, dismiss: dismissRunning } = usePipelineRuns()
  const currentRun = usePipelineRun(currentRunId)

  // running → completed/error を検知して記事一覧を自動更新
  const prevStatusRef = useRef<string | null>(null)

  const fetchMysteries = useCallback(async () => {
    try {
      const data = await getAllMysteries(100)
      setMysteries(data)
    } catch (error) {
      console.error("Failed to fetch mysteries:", error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchMysteries()
  }, [fetchMysteries])

  // パイプライン完了時に記事一覧を自動更新
  useEffect(() => {
    const status = currentRun?.status ?? null
    if (prevStatusRef.current === "running" && (status === "completed" || status === "error")) {
      fetchMysteries()
    }
    prevStatusRef.current = status
  }, [currentRun?.status, fetchMysteries])

  // running パイプライン + currentRun をマージ（ID 重複排除、currentRun 優先）
  const mergedRuns = useMemo(() => {
    const runsMap = new Map<string, PipelineRun>()
    for (const r of runningPipelines) {
      if (!dismissedRunIds.has(r.id)) {
        runsMap.set(r.id, r)
      }
    }
    // currentRun は完了/エラー後も表示するため優先
    if (currentRun && !dismissedRunIds.has(currentRun.id)) {
      runsMap.set(currentRun.id, currentRun)
    }
    return Array.from(runsMap.values())
  }, [runningPipelines, currentRun, dismissedRunIds])

  const handleDismissRun = useCallback((runId: string) => {
    dismissRunning(runId)
    setDismissedRunIds((prev) => new Set(prev).add(runId))
    if (runId === currentRunId) {
      setCurrentRunId(null)
    }
  }, [dismissRunning, currentRunId])

  // 記事アクション（Approve / Archive / Unpublish）
  const { actions, feedback: actionFeedback } = useMysteryActions({ onSuccess: fetchMysteries })

  // 新規調査（パイプライン開始 / テーマ提案）
  const investigation = useInvestigation({ onPipelineStarted: setCurrentRunId })

  // 直近のアクティブなフィードバックを表示
  const activeFeedback = investigation.feedback.message ? investigation.feedback : actionFeedback

  const filteredMysteries = filter === "all"
    ? mysteries
    : mysteries.filter((m) => m.status === filter)

  const counts = {
    all: mysteries.length,
    pending: mysteries.filter((m) => m.status === "pending").length,
    published: mysteries.filter((m) => m.status === "published").length,
    archived: mysteries.filter((m) => m.status === "archived").length,
  }

  return (
    <div className="py-8 md:py-12">
      <div className="container mx-auto px-4">
        {/* Page header */}
        <div className="flex items-center gap-4 mb-8">
          <div className="flex items-center gap-3 px-4 py-2 bg-blood-red/10 border border-blood-red/30 rounded-sm">
            <Shield className="w-5 h-5 text-[#ff6b6b]" />
            <span className="font-mono text-sm uppercase tracking-wider text-[#ff6b6b]">
              Admin Access
            </span>
          </div>
          <div className="h-px flex-1 bg-border" />
        </div>

        <div className="mb-8">
          <h1 className="font-serif text-3xl md:text-4xl text-parchment mb-2">
            Research Review Dashboard
          </h1>
          <p className="text-muted-foreground">
            Review, approve, or archive pending mystery discoveries before publication.
          </p>
        </div>

        {/* New Investigation section */}
        <InvestigationForm
          themeInput={investigation.themeInput}
          onThemeInputChange={investigation.setThemeInput}
          suggestions={investigation.suggestions}
          onSelectSuggestion={(theme) => {
            investigation.setThemeInput(theme)
            investigation.clearSuggestions()
          }}
          suggestLoading={investigation.suggestLoading}
          pipelineLoading={investigation.pipelineLoading}
          onStartPipeline={investigation.handleStartPipeline}
          onSuggestThemes={investigation.handleSuggestThemes}
        />

        <ActionToast message={activeFeedback.message} isError={activeFeedback.isError} />

        {/* 実行中のパイプライン */}
        {mergedRuns.length > 0 && (
          <div className="space-y-3 mb-8">
            {mergedRuns.map((run) => (
              <ActivePipelinePanel
                key={run.id}
                run={run}
                onDismiss={() => handleDismissRun(run.id)}
              />
            ))}
          </div>
        )}

        {/* TODO: 記事一覧 UI 改善（段階的対応）
         * 記事数が増えた場合の対応計画:
         *
         * Phase 1（30件〜）: 検索バー + 人気タグ
         * - タイトル・サマリーのインクリメンタル検索
         * - 人気のテーマをチップ表示（失踪事件, 禁忌, 都市伝説 等）
         * - 検索キーワードが思いつかないユーザー向けの Discovery UI
         *
         * Phase 2（50件〜）: Era/地域ファセットフィルタ
         * - historical_context.time_period でのフィルタ
         * - historical_context.geographic_scope でのフィルタ
         * - フィルタチップで適用中のフィルタを可視化
         *
         * Phase 3（100件〜）: ページネーション
         * - Firestore のカーソルベースページング
         * - 現在の limit(100) を解除
         * - 無限スクロールまたはページ番号方式
         *
         * 参考: Ghost CMS, Algolia の検索 UX
         * 参考: https://www.pencilandpaper.io/articles/ux-pattern-analysis-enterprise-filtering
         */}

        {/* Filter tabs */}
        <div className="flex flex-wrap items-center gap-2 mb-8 pb-4 border-b border-border">
          <Filter className="w-4 h-4 text-muted-foreground mr-2" />
          {(["all", "pending", "published", "archived"] as FilterStatus[]).map((status) => (
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
              {status === "all" ? "All Cases" : status}
              <span className="ml-2 text-muted-foreground">({counts[status]})</span>
            </button>
          ))}
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="aged-card letterpress-border rounded-sm p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1">Total Cases</p>
            <p className="text-2xl font-serif text-parchment">{counts.all}</p>
          </div>
          <div className="aged-card letterpress-border rounded-sm p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-[#d4af37] mb-1">Pending Review</p>
            <p className="text-2xl font-serif text-[#d4af37]">{counts.pending}</p>
          </div>
          <div className="aged-card letterpress-border rounded-sm p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-[#5fb3a1] mb-1">Published</p>
            <p className="text-2xl font-serif text-[#5fb3a1]">{counts.published}</p>
          </div>
          <div className="aged-card letterpress-border rounded-sm p-4">
            <p className="text-xs font-mono uppercase tracking-wider text-[#ff6b6b] mb-1">Archived</p>
            <p className="text-2xl font-serif text-[#ff6b6b]">{counts.archived}</p>
          </div>
        </div>

        {/* Loading */}
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
            <p className="text-muted-foreground">No cases match the selected filter.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {filteredMysteries.map((mystery) => (
              <AdminMysteryCard
                key={mystery.mystery_id}
                mystery={mystery}
                lang={lang}
                onApprove={() => actions.handleApprove(mystery.mystery_id)}
                onArchive={() => actions.handleArchive(mystery.mystery_id)}
                onUnpublish={() => actions.handleUnpublish(mystery.mystery_id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
