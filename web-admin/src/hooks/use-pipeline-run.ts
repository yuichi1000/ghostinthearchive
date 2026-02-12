"use client"

import { useEffect, useState } from "react"
import { doc, onSnapshot, Timestamp } from "firebase/firestore"
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
 * 単一パイプライン実行を onSnapshot でリアルタイム監視するフック
 * 完了/エラー後も最終状態を保持し、dismiss まで表示する。
 */
export function usePipelineRun(runId: string | null) {
  const [run, setRun] = useState<PipelineRun | null>(null)

  useEffect(() => {
    if (!runId) {
      setRun(null)
      return
    }

    const db = getFirestoreDb()
    const docRef = doc(db, COLLECTIONS.PIPELINE_RUNS, runId)

    const unsubscribe = onSnapshot(docRef, (snapshot) => {
      if (!snapshot.exists()) {
        setRun(null)
        return
      }
      const data = snapshot.data()
      setRun({
        id: snapshot.id,
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
      })
    }, (error) => {
      console.error("[usePipelineRun] onSnapshot error:", error)
    })

    return () => unsubscribe()
  }, [runId])

  return run
}
