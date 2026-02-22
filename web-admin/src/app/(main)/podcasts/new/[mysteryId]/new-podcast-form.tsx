"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@ghost/shared/src/components/ui/button"
import { getMysteryById } from "@/lib/firestore/mysteries"
import { getPodcastsByMysteryId } from "@/lib/firestore/podcasts"
import { ActionToast } from "@/components/action-toast"
import { useActionFeedback } from "@/hooks/use-action-feedback"
import type { FirestoreMystery, FirestorePodcast } from "@ghost/shared/src/types/mystery"
import {
  ArrowLeft,
  FileText,
  Loader2,
  Info,
  Mic,
} from "lucide-react"

interface NewPodcastFormProps {
  mysteryId: string
}

export function NewPodcastForm({ mysteryId }: NewPodcastFormProps) {
  const router = useRouter()
  const feedback = useActionFeedback()
  const [mystery, setMystery] = useState<FirestoreMystery | null>(null)
  const [existingPodcast, setExistingPodcast] = useState<FirestorePodcast | null>(null)
  const [loading, setLoading] = useState(true)
  const [customInstructions, setCustomInstructions] = useState("")
  const [generating, setGenerating] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      const [mysteryData, podcastData] = await Promise.all([
        getMysteryById(mysteryId),
        getPodcastsByMysteryId(mysteryId),
      ])
      setMystery(mysteryData)
      if (podcastData.length > 0) {
        setExistingPodcast(podcastData[0])
      }
    } catch (error) {
      console.error("Failed to fetch data:", error)
    } finally {
      setLoading(false)
    }
  }, [mysteryId])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const handleGenerateScript = async () => {
    setGenerating(true)
    try {
      const res = await fetch("/api/podcast/generate-script", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mystery_id: mysteryId,
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
        router.push("/podcasts")
      }
    } catch (error) {
      console.error("Failed to generate script:", error)
      const message = error instanceof Error ? error.message : "不明なエラー"
      feedback.showError(`脚本生成の開始に失敗しました: ${message}`)
    } finally {
      setGenerating(false)
    }
  }

  if (loading) {
    return (
      <div className="py-8 md:py-12">
        <div className="container mx-auto px-4">
          <div className="aged-card letterpress-border rounded-sm p-8 animate-pulse">
            <div className="h-4 bg-muted rounded w-1/4 mb-6" />
            <div className="h-6 bg-muted rounded w-3/4 mb-4" />
            <div className="h-4 bg-muted rounded w-full mb-8" />
            <div className="h-20 bg-muted rounded w-full mb-4" />
            <div className="h-10 bg-muted rounded w-32" />
          </div>
        </div>
      </div>
    )
  }

  if (!mystery) {
    return (
      <div className="py-8 md:py-12">
        <div className="container mx-auto px-4 text-center">
          <p className="text-muted-foreground">記事が見つかりません。</p>
          <Link href="/podcasts" className="text-gold hover:text-parchment mt-4 inline-block">
            ← Podcast 一覧に戻る
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="py-8 md:py-12">
      <div className="container mx-auto px-4 max-w-2xl">
        {/* パンくず */}
        <Link
          href="/podcasts"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-parchment transition-colors no-underline mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Podcast 一覧
        </Link>

        {/* ページヘッダー */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex items-center gap-3 px-4 py-2 bg-gold/10 border border-gold/30 rounded-sm">
            <Mic className="w-5 h-5 text-[#d4af37]" />
            <span className="font-mono text-sm uppercase tracking-wider text-[#d4af37]">
              New Episode
            </span>
          </div>
          <div className="h-px flex-1 bg-border" />
        </div>

        {/* 記事情報 */}
        <div className="aged-card letterpress-border rounded-sm p-5 mb-6">
          <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono mb-2">
            <FileText className="w-3.5 h-3.5 text-gold" />
            <span>{mystery.mystery_id}</span>
          </div>
          <h1 className="font-serif text-2xl text-parchment mb-2">
            {mystery.title}
          </h1>
          <p className="text-sm text-foreground/80 leading-relaxed line-clamp-3">
            {mystery.summary}
          </p>
        </div>

        {/* 既存 Podcast 警告 */}
        {existingPodcast && (
          <div className="bg-gold/10 border border-gold/30 rounded-sm p-4 mb-6">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-[#d4af37] mt-0.5 flex-shrink-0" />
              <div>
                <p className="text-sm text-parchment mb-2">
                  この記事には既に Podcast が存在します。新たに作成すると追加の Podcast が生成されます。
                </p>
                <Link
                  href={`/podcasts/${existingPodcast.podcast_id}`}
                  className="text-sm text-gold hover:text-parchment transition-colors"
                >
                  既存の Podcast を確認する →
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* カスタム指示 */}
        <div className="aged-card letterpress-border rounded-sm p-5">
          <div className="space-y-4">
            <div>
              <label className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1 block">
                カスタム指示（任意）
              </label>
              <textarea
                value={customInstructions}
                onChange={(e) => setCustomInstructions(e.target.value)}
                placeholder="例: 冒頭で地元の伝説を詳しく紹介してほしい"
                rows={3}
                className="w-full px-3 py-2 bg-background border border-border rounded-sm text-sm text-parchment placeholder:text-muted-foreground resize-none focus:outline-none focus:border-gold/50"
              />
            </div>

            <Button
              size="sm"
              onClick={handleGenerateScript}
              disabled={generating}
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
      </div>
    </div>
  )
}
