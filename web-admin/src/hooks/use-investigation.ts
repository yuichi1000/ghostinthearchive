"use client"

import { useState, useCallback } from "react"
import { useActionFeedback, type ActionFeedback } from "@/hooks/use-action-feedback"

interface ThemeSuggestion {
  theme: string
  description: string
  theme_ja?: string
  description_ja?: string
  coverage_score?: "HIGH" | "MEDIUM" | "LOW"
  primary_apis?: string[]
  probe_hits?: Record<string, number>
}

interface UseInvestigationOptions {
  onPipelineStarted: (runId: string) => void
}

export function useInvestigation({ onPipelineStarted }: UseInvestigationOptions) {
  const [themeInput, setThemeInput] = useState("")
  const [suggestions, setSuggestions] = useState<ThemeSuggestion[]>([])
  const [suggestLoading, setSuggestLoading] = useState(false)
  const [storyteller, setStoryteller] = useState("claude")
  const [pipelineLoading, setPipelineLoading] = useState(false)
  const feedback = useActionFeedback()

  const clearSuggestions = useCallback(() => {
    setSuggestions([])
  }, [])

  const handleStartPipeline = useCallback(async () => {
    if (!themeInput.trim()) return
    setPipelineLoading(true)
    try {
      const res = await fetch("/api/mysteries/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: themeInput.trim(), storyteller }),
      })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || errorData.error || `API error (${res.status})`)
      }
      const data = await res.json()
      if (data.run_id) {
        onPipelineStarted(data.run_id)
      }
      feedback.showSuccess("調査パイプラインを開始しました")
      setThemeInput("")
      setSuggestions([])
    } catch (error) {
      console.error("Failed to start pipeline:", error)
      const message = error instanceof Error ? error.message : "不明なエラー"
      feedback.showError(`パイプラインの開始に失敗しました: ${message}`)
    } finally {
      setPipelineLoading(false)
    }
  }, [themeInput, storyteller, feedback, onPipelineStarted])

  const handleSuggestThemes = useCallback(async () => {
    setSuggestLoading(true)
    setSuggestions([])
    try {
      const res = await fetch("/api/themes/suggest", { method: "POST" })
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        if (errorData.error_type === "auth_error") {
          throw new Error("Google Cloud の認証が切れています。サーバーで再認証を実行してください。")
        }
        throw new Error(errorData.detail || errorData.error || `API error (${res.status})`)
      }
      const data = await res.json()
      setSuggestions(Array.isArray(data.suggestions) ? data.suggestions : [])
    } catch (error) {
      console.error("Failed to get suggestions:", error)
      const message = error instanceof Error ? error.message : "不明なエラー"
      feedback.showError(`テーマ提案の取得に失敗しました: ${message}`)
    } finally {
      setSuggestLoading(false)
    }
  }, [feedback])

  return {
    themeInput,
    setThemeInput,
    storyteller,
    setStoryteller,
    suggestions,
    clearSuggestions,
    suggestLoading,
    pipelineLoading,
    handleStartPipeline,
    handleSuggestThemes,
    feedback,
  }
}
