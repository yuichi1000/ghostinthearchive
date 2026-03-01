"use client"

import { useCallback } from "react"
import { approveMystery, archiveMystery, unpublishMystery } from "@/actions/mysteries"
import { useActionFeedback, type ActionFeedback } from "@/hooks/use-action-feedback"

interface UseMysteryActionsOptions {
  onSuccess: () => void
}

export function useMysteryActions({ onSuccess }: UseMysteryActionsOptions) {
  const feedback = useActionFeedback()

  // リビルド失敗は approve/archive の成否に影響しない（fire-and-forget）
  const triggerRebuild = async () => {
    try {
      await fetch("/api/deployments/rebuild", { method: "POST" })
    } catch (error) {
      console.error("Failed to trigger rebuild:", error)
    }
  }

  const handleApprove = useCallback(async (id: string) => {
    const result = await approveMystery(id)
    if (result.success) {
      feedback.showSuccess(`Case ${id} approved and published`)
      onSuccess()
      triggerRebuild()
    } else {
      feedback.showError(`承認に失敗しました: ${result.error}`)
    }
  }, [feedback, onSuccess])

  const handleArchive = useCallback(async (id: string) => {
    const result = await archiveMystery(id)
    if (result.success) {
      feedback.showSuccess(`Case ${id} archived`)
      onSuccess()
      triggerRebuild()
    } else {
      feedback.showError(`アーカイブに失敗しました: ${result.error}`)
    }
  }, [feedback, onSuccess])

  const handleUnpublish = useCallback(async (id: string) => {
    if (!window.confirm("この記事を非公開に戻しますか？公開サイトから削除されます。")) return
    const result = await unpublishMystery(id)
    if (result.success) {
      feedback.showSuccess(`Case ${id} unpublished`)
      onSuccess()
      triggerRebuild()
    } else {
      feedback.showError(`非公開への変更に失敗しました: ${result.error}`)
    }
  }, [feedback, onSuccess])

  return {
    actions: { handleApprove, handleArchive, handleUnpublish },
    feedback,
  }
}
