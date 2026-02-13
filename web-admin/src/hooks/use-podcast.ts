"use client"

import { useEffect, useState } from "react"
import { doc, onSnapshot, Timestamp } from "firebase/firestore"
import { getFirestoreDb, COLLECTIONS } from "@ghost/shared/src/lib/firebase/config"
import type { FirestorePodcast, PodcastScript } from "@ghost/shared/src/types/mystery"

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
 * 単一 Podcast を onSnapshot でリアルタイム監視するフック
 * ステータス遷移を自動検知（script_generating → script_ready → audio_ready）
 */
export function usePodcast(podcastId: string | null): FirestorePodcast | null {
  const [podcast, setPodcast] = useState<FirestorePodcast | null>(null)

  useEffect(() => {
    if (!podcastId) {
      setPodcast(null)
      return
    }

    const db = getFirestoreDb()
    const docRef = doc(db, COLLECTIONS.PODCASTS, podcastId)

    const unsubscribe = onSnapshot(docRef, (snapshot) => {
      if (!snapshot.exists()) {
        setPodcast(null)
        return
      }
      const data = snapshot.data()
      setPodcast({
        podcast_id: snapshot.id,
        mystery_id: (data.mystery_id as string) || "",
        mystery_title: (data.mystery_title as string) || "",
        status: (data.status as FirestorePodcast["status"]) || "script_generating",
        custom_instructions: (data.custom_instructions as string) || undefined,
        script: (data.script as PodcastScript) || undefined,
        script_ja: (data.script_ja as string) || undefined,
        audio: (data.audio as FirestorePodcast["audio"]) || undefined,
        pipeline_run_id: (data.pipeline_run_id as string) || undefined,
        created_at: toDate(data.created_at),
        updated_at: toDate(data.updated_at),
        error_message: (data.error_message as string) || undefined,
      })
    }, (error) => {
      console.error("[usePodcast] onSnapshot error:", error)
    })

    return () => unsubscribe()
  }, [podcastId])

  return podcast
}
