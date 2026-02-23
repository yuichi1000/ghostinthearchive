"use client"

import { useEffect, useState } from "react"
import { doc, onSnapshot, Timestamp } from "firebase/firestore"
import { getFirestoreDb, COLLECTIONS } from "@ghost/shared/src/lib/firebase/config"
import type { FirestoreDesign } from "@ghost/shared/src/types/mystery"

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
 * 単一 Design を onSnapshot でリアルタイム監視するフック
 * ステータス遷移を自動検知（designing → design_ready → rendering → render_ready）
 */
export function useDesign(designId: string | null): FirestoreDesign | null {
  const [design, setDesign] = useState<FirestoreDesign | null>(null)

  useEffect(() => {
    if (!designId) {
      setDesign(null)
      return
    }

    const db = getFirestoreDb()
    const docRef = doc(db, COLLECTIONS.PRODUCT_DESIGNS, designId)

    const unsubscribe = onSnapshot(docRef, (snapshot) => {
      if (!snapshot.exists()) {
        setDesign(null)
        return
      }
      const data = snapshot.data()
      setDesign({
        design_id: snapshot.id,
        mystery_id: (data.mystery_id as string) || "",
        mystery_title: (data.mystery_title as string) || "",
        region: (data.region as string) || "",
        status: (data.status as FirestoreDesign["status"]) || "designing",
        custom_instructions: (data.custom_instructions as string) || undefined,
        proposal: (data.proposal as FirestoreDesign["proposal"]) || undefined,
        assets: (data.assets as FirestoreDesign["assets"]) || undefined,
        pipeline_run_id: (data.pipeline_run_id as string) || undefined,
        created_at: toDate(data.created_at),
        updated_at: toDate(data.updated_at),
        error_message: (data.error_message as string) || undefined,
      })
    }, (error) => {
      console.error("[useDesign] onSnapshot error:", error)
    })

    return () => unsubscribe()
  }, [designId])

  return design
}
