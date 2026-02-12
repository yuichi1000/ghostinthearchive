"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { cn } from "@ghost/shared/src/lib/utils"
import { AGENT_NAME_LABELS } from "@ghost/shared/src/types/mystery"
import type { PipelineRun } from "@ghost/shared/src/types/mystery"
import { PipelineSummary } from "@/components/pipeline-summary"
import { PipelineTimeline } from "@/components/pipeline-timeline"
import {
  Loader2,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  X,
  Eye,
  Clock,
} from "lucide-react"

/**
 * 経過時間を「Xm Ys」形式でフォーマットする
 */
function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}s`
  return `${m}m ${s}s`
}

interface ActivePipelinePanelProps {
  run: PipelineRun
  onDismiss: () => void
}

export function ActivePipelinePanel({ run, onDismiss }: ActivePipelinePanelProps) {
  const [expanded, setExpanded] = useState(false)
  const [elapsed, setElapsed] = useState(0)

  // running 中のみ毎秒経過時間を更新
  useEffect(() => {
    if (run.status !== "running") return

    const updateElapsed = () => {
      const diff = Math.floor((Date.now() - run.started_at.getTime()) / 1000)
      setElapsed(diff)
    }
    updateElapsed()
    const interval = setInterval(updateElapsed, 1000)
    return () => clearInterval(interval)
  }, [run.status, run.started_at])

  const agentLabel = run.current_agent
    ? (AGENT_NAME_LABELS[run.current_agent] || run.current_agent)
    : null

  const typeLabel = run.type === "blog" ? "ブログ調査" : run.type === "podcast" ? "Podcast 生成" : "翻訳"

  return (
    <div className={cn(
      "aged-card letterpress-border rounded-sm p-4 transition-colors",
      run.status === "running" && "border-gold/40",
      run.status === "completed" && "border-teal/40",
      run.status === "error" && "border-blood-red/40",
    )}>
      {/* ヘッダー */}
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-3">
          {run.status === "running" && (
            <Loader2 className="w-5 h-5 text-[#d4af37] animate-spin flex-shrink-0" />
          )}
          {run.status === "completed" && (
            <CheckCircle className="w-5 h-5 text-[#5fb3a1] flex-shrink-0" />
          )}
          {run.status === "error" && (
            <XCircle className="w-5 h-5 text-[#ff6b6b] flex-shrink-0" />
          )}

          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm uppercase tracking-wider text-parchment">
                {typeLabel}
              </span>
              {run.status === "running" && (
                <span className="flex items-center gap-1 text-xs text-muted-foreground font-mono">
                  <Clock className="w-3 h-3" />
                  {formatElapsed(elapsed)}
                </span>
              )}
            </div>
            {run.query && (
              <p className="text-xs text-muted-foreground mt-0.5 line-clamp-1">
                {run.query}
              </p>
            )}
          </div>
        </div>

        {/* 右側: 現在のエージェント + dismiss/close */}
        <div className="flex items-center gap-3">
          {run.status === "running" && agentLabel && (
            <span className="text-xs font-mono text-[#d4af37] bg-gold/10 px-2 py-1 rounded-sm">
              {agentLabel}
            </span>
          )}
          {run.status !== "running" && (
            <button
              onClick={onDismiss}
              className="p-1 text-muted-foreground hover:text-parchment transition-colors"
              title="閉じる"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* 完了時: 記事プレビューリンク */}
      {run.status === "completed" && run.mystery_id && (
        <div className="flex items-center gap-2 mb-2">
          <Link
            href={`/preview/${run.mystery_id}`}
            className="inline-flex items-center gap-1.5 text-sm text-gold hover:text-parchment transition-colors no-underline"
          >
            <Eye className="w-4 h-4" />
            記事プレビュー
          </Link>
        </div>
      )}

      {/* エラー時: エラーメッセージ */}
      {run.status === "error" && run.error_message && (
        <div className="bg-blood-red/10 border border-blood-red/20 rounded-sm p-2 mb-2">
          <p className="text-xs text-[#ff6b6b] font-mono">
            {run.error_message}
          </p>
        </div>
      )}

      {/* Pipeline Summary + Timeline (展開/折りたたみ) */}
      {run.pipeline_log.length > 0 && (
        <div className="pt-2 border-t border-border/50">
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-between hover:bg-muted/50 transition-colors p-1 -mx-1 rounded-sm"
          >
            <PipelineSummary logs={run.pipeline_log} />
            {expanded ? (
              <ChevronUp className="w-4 h-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            )}
          </button>

          {expanded && (
            <div className="mt-3 pt-3 border-t border-border/50">
              <PipelineTimeline logs={run.pipeline_log} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
