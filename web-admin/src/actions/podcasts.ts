"use server"

/**
 * Podcast 書き込み操作の Server Actions
 * クライアント SDK → Admin SDK に移行してセキュリティルールをバイパス
 */

import { getAdminFirestore, ADMIN_COLLECTIONS } from "@/lib/firebase/admin"
import { FieldValue } from "firebase-admin/firestore"
import type { PodcastScript } from "@ghost/shared/src/types/mystery"

type ActionResult = { success: true } | { success: false; error: string }

/**
 * Podcast 脚本を更新
 */
export async function updatePodcastScript(
  podcastId: string,
  script: PodcastScript
): Promise<ActionResult> {
  try {
    const db = getAdminFirestore()
    await db.collection(ADMIN_COLLECTIONS.PODCASTS).doc(podcastId).update({
      script,
      updated_at: FieldValue.serverTimestamp(),
    })
    return { success: true }
  } catch (error) {
    console.error("Failed to update podcast script:", error)
    const message = error instanceof Error ? error.message : "不明なエラー"
    return { success: false, error: message }
  }
}
