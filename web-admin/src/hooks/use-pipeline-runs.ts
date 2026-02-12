"use client"

import { useEffect, useState, useCallback } from "react"
import {
  collection,
  query,
  where,
  orderBy,
  onSnapshot,
  Timestamp,
} from "firebase/firestore"
import { getFirestoreDb } from "@ghost/shared/src/lib/firebase/config"
import { COLLECTIONS } from "@ghost/shared/src/lib/firebase/config"
import type { PipelineRun } from "@ghost/shared/src/types/mystery"

/**
 * Firestore Timestamp を Date に変換するヘルパー
 */
function toDate(val: unknown): Date {
  if (val instanceof Timestamp) return val.toDate()
  if (val instanceof Date) return val
  if (typeof val === "string") return new Date(val)
  return new Date()
}

/**
 * Firestore ドキュメントを PipelineRun に変換する
 */
function docToPipelineRun(id: string, data: Record<string, unknown>): PipelineRun {
  return {
    id,
    type: (data.type as PipelineRun["type"]) || "blog",
    status: (data.status as PipelineRun["status"]) || "running",
    query: (data.query as string) || null,
    mystery_id: (data.mystery_id as string) || null,
    current_agent: (data.current_agent as string) || null,
    pipeline_log: Array.isArray(data.pipeline_log) ? data.pipeline_log : [],
    started_at: toDate(data.started_at),
    updated_at: toDate(data.updated_at),
    completed_at: data.completed_at ? toDate(data.completed_at) : null,
    error_message: (data.error_message as string) || null,
  }
}

/**
 * 全 running パイプラインをリアルタイム監視するフック
 * status=="running" のドキュメントを onSnapshot で購読する。
 * 完了すると Firestore クエリ結果から消えるため、dismiss ロジックを内蔵。
 */
export function usePipelineRuns() {
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set())

  useEffect(() => {
    const db = getFirestoreDb()
    const q = query(
      collection(db, COLLECTIONS.PIPELINE_RUNS),
      where("status", "==", "running"),
      orderBy("started_at", "desc"),
    )

    const unsubscribe = onSnapshot(q, (snapshot) => {
      const pipelineRuns: PipelineRun[] = []
      snapshot.forEach((doc) => {
        pipelineRuns.push(docToPipelineRun(doc.id, doc.data()))
      })
      setRuns(pipelineRuns)
    }, (error) => {
      console.error("[usePipelineRuns] onSnapshot error:", error)
    })

    return () => unsubscribe()
  }, [])

  const dismiss = useCallback((runId: string) => {
    setDismissedIds((prev) => new Set(prev).add(runId))
  }, [])

  const visibleRuns = runs.filter((r) => !dismissedIds.has(r.id))

  return { runs: visibleRuns, dismiss }
}
