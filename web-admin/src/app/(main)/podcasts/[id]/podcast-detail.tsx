"use client"

import { useState, useCallback, useRef, useEffect } from "react"
import Link from "next/link"
import { Button } from "@ghost/shared/src/components/ui/button"
import { usePodcast } from "@/hooks/use-podcast"
import { usePipelineRun } from "@/hooks/use-pipeline-run"
import { useActionFeedback } from "@/hooks/use-action-feedback"
import { updatePodcastScript } from "@/actions/podcasts"
import { PodcastStatusBadge } from "@/components/podcast-status-badge"
import { AudioPlayer } from "@/components/audio-player"
import { ScriptEditor } from "@/components/script-editor"
import { ActionToast } from "@/components/action-toast"
import { ActivePipelinePanel } from "@/components/active-pipeline-panel"
import type { PodcastScript } from "@ghost/shared/src/types/mystery"
import {
  ArrowLeft,
  Save,
  Headphones,
  Loader2,
  RefreshCw,
  AlertTriangle,
} from "lucide-react"

interface PodcastDetailProps {
  podcastId: string
}

export function PodcastDetail({ podcastId }: PodcastDetailProps) {
  const podcast = usePodcast(podcastId)
  const pipelineRun = usePipelineRun(podcast?.pipeline_run_id ?? null)

  const [editedScript, setEditedScript] = useState<PodcastScript | null>(null)
  const [saving, setSaving] = useState(false)
  const [audioGenerating, setAudioGenerating] = useState(false)
  const feedback = useActionFeedback()
  const hasUnsavedChanges = useRef(false)

  // podcast のステータスが audio_generating に変わったらローカルの generating フラグもリセット
  useEffect(() => {
    if (podcast?.status === "audio_generating") {
      setAudioGenerating(false)
    }
  }, [podcast?.status])

  const handleScriptChange = useCallback((script: PodcastScript) => {
    setEditedScript(script)
    hasUnsavedChanges.current = true
  }, [])

  const handleSaveScript = useCallback(async () => {
    if (!editedScript || !podcast) return
    setSaving(true)
    try {
      const result = await updatePodcastScript(podcastId, editedScript)
      if (result.success) {
        hasUnsavedChanges.current = false
        feedback.showSuccess("脚本を保存しました")
      } else {
        feedback.showError(`脚本の保存に失敗しました: ${result.error}`)
      }
    } finally {
      setSaving(false)
    }
  }, [editedScript, podcast, podcastId])

  const handleGenerateAudio = useCallback(async () => {
    if (!podcast) return
    setAudioGenerating(true)
    try {
      // 未保存の編集がある場合はスクリプトも送る
      const scriptToSend = hasUnsavedChanges.current ? editedScript : null

      const res = await fetch("/api/podcast/generate-audio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          podcast_id: podcastId,
          script: scriptToSend,
        }),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || `API error (${res.status})`)
      }
      feedback.showSuccess("音声生成を開始しました")
    } catch (error) {
      console.error("Failed to generate audio:", error)
      setAudioGenerating(false)
      const message = error instanceof Error ? error.message : "不明なエラー"
      feedback.showError(`音声生成の開始に失敗しました: ${message}`)
    }
  }, [podcast, podcastId, editedScript])

  const handleRetry = useCallback(async () => {
    if (!podcast) return
    // エラー時は脚本再生成（同じ記事で再試行）
    try {
      const res = await fetch("/api/podcast/generate-script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mystery_id: podcast.mystery_id }),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || `API error (${res.status})`)
      }
      const data = await res.json()
      if (data.podcast_id) {
        window.location.href = `/podcasts/${data.podcast_id}`
      }
    } catch (error) {
      console.error("Failed to retry:", error)
      const message = error instanceof Error ? error.message : "不明なエラー"
      feedback.showError(`再試行に失敗しました: ${message}`)
    }
  }, [podcast])

  // ローディング中
  if (!podcast) {
    return (
      <div className="py-8 md:py-12">
        <div className="container mx-auto px-4">
          <div className="flex items-center gap-4 mb-8">
            <Link
              href="/podcasts"
              className="inline-flex items-center gap-1.5 text-sm text-gold hover:text-parchment transition-colors no-underline"
            >
              <ArrowLeft className="w-4 h-4" />
              Podcast 一覧
            </Link>
          </div>
          <div className="aged-card letterpress-border rounded-sm p-8 animate-pulse">
            <div className="h-6 bg-muted rounded w-1/3 mb-4" />
            <div className="h-4 bg-muted rounded w-2/3 mb-2" />
            <div className="h-4 bg-muted rounded w-1/2" />
          </div>
        </div>
      </div>
    )
  }

  const isEditable = podcast.status === "script_ready"
  const isProcessing = podcast.status === "script_generating" || podcast.status === "audio_generating"

  return (
    <div className="py-8 md:py-12">
      <div className="container mx-auto px-4">
        <ActionToast message={feedback.message} isError={feedback.isError} />

        {/* パンくずリスト */}
        <div className="flex items-center gap-4 mb-8">
          <Link
            href="/podcasts"
            className="inline-flex items-center gap-1.5 text-sm text-gold hover:text-parchment transition-colors no-underline"
          >
            <ArrowLeft className="w-4 h-4" />
            Podcast 一覧
          </Link>
        </div>

        {/* ヘッダー */}
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h1 className="font-serif text-2xl md:text-3xl text-parchment mb-2">
              {podcast.script?.episode_title || podcast.mystery_title}
            </h1>
            <p className="text-sm text-muted-foreground">
              {podcast.mystery_title} | 作成: {podcast.created_at.toLocaleDateString()}
            </p>
          </div>
          <PodcastStatusBadge status={podcast.status} />
        </div>

        {/* パイプライン進捗表示 */}
        {isProcessing && pipelineRun && (
          <div className="mb-6">
            <ActivePipelinePanel
              run={pipelineRun}
              onDismiss={() => {}}
            />
          </div>
        )}

        {/* スケルトン: 脚本生成中 */}
        {podcast.status === "script_generating" && !pipelineRun && (
          <div className="aged-card letterpress-border rounded-sm p-8 mb-6">
            <div className="flex items-center gap-3 mb-4">
              <Loader2 className="w-5 h-5 text-[#d4af37] animate-spin" />
              <span className="font-mono text-sm text-[#d4af37]">
                脚本を生成中...
              </span>
            </div>
            <div className="space-y-3 animate-pulse">
              <div className="h-4 bg-muted rounded w-2/3" />
              <div className="h-4 bg-muted rounded w-full" />
              <div className="h-4 bg-muted rounded w-3/4" />
            </div>
          </div>
        )}

        {/* エラー表示 */}
        {podcast.status === "error" && (
          <div className="aged-card letterpress-border rounded-sm p-6 mb-6 border-blood-red/30">
            <div className="flex items-center gap-3 mb-3">
              <AlertTriangle className="w-5 h-5 text-[#ff6b6b]" />
              <span className="font-mono text-sm text-[#ff6b6b]">
                エラーが発生しました
              </span>
            </div>
            {podcast.error_message && (
              <div className="bg-blood-red/10 border border-blood-red/20 rounded-sm p-3 mb-4">
                <p className="text-xs text-[#ff6b6b] font-mono">
                  {podcast.error_message}
                </p>
              </div>
            )}
            <Button
              size="sm"
              onClick={handleRetry}
              className="bg-gold/20 border border-gold/30 text-[#d4af37] hover:bg-gold/30"
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              再試行
            </Button>
          </div>
        )}

        {/* 音声プレイヤー（audio_ready） */}
        {podcast.status === "audio_ready" && podcast.audio?.public_url && (
          <div className="mb-6">
            <h2 className="font-mono text-sm uppercase tracking-wider text-parchment mb-3">
              Audio
            </h2>
            <AudioPlayer
              src={podcast.audio.public_url}
              downloadUrl={podcast.audio.public_url}
            />
            {podcast.audio.duration_seconds && (
              <p className="text-xs text-muted-foreground mt-2">
                Duration: {Math.floor(podcast.audio.duration_seconds / 60)}m {Math.floor(podcast.audio.duration_seconds % 60)}s
                | Voice: {podcast.audio.voice_name}
                | Format: {podcast.audio.format}
              </p>
            )}
          </div>
        )}

        {/* 脚本エディタ */}
        {podcast.script && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-mono text-sm uppercase tracking-wider text-parchment">
                Script
              </h2>

              {/* アクションボタン */}
              {isEditable && (
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleSaveScript}
                    disabled={saving || !hasUnsavedChanges.current}
                    className="border-gold/30 text-gold hover:bg-gold/20 bg-transparent"
                  >
                    {saving ? (
                      <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4 mr-1" />
                    )}
                    脚本を保存
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleGenerateAudio}
                    disabled={audioGenerating}
                    className="bg-teal/20 border border-teal/30 text-[#5fb3a1] hover:bg-teal/30"
                  >
                    {audioGenerating ? (
                      <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                    ) : (
                      <Headphones className="w-4 h-4 mr-1" />
                    )}
                    音声生成
                  </Button>
                </div>
              )}
            </div>

            <ScriptEditor
              script={podcast.script}
              scriptJa={podcast.script_ja}
              readOnly={!isEditable}
              onChange={handleScriptChange}
            />
          </div>
        )}
      </div>
    </div>
  )
}
