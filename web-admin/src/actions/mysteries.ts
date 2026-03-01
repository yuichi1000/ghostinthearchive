"use server"

/**
 * Mystery 書き込み操作の Server Actions
 * クライアント SDK → Admin SDK に移行してセキュリティルールをバイパス
 */

import { getAdminFirestore, ADMIN_COLLECTIONS } from "@/lib/firebase/admin"
import { FieldValue } from "firebase-admin/firestore"

type ActionResult = { success: true } | { success: false; error: string }

/**
 * ミステリーを承認（pending → published）
 */
export async function approveMystery(mysteryId: string): Promise<ActionResult> {
  try {
    const db = getAdminFirestore()
    await db.collection(ADMIN_COLLECTIONS.MYSTERIES).doc(mysteryId).update({
      status: "published",
      publishedAt: FieldValue.serverTimestamp(),
      updatedAt: FieldValue.serverTimestamp(),
    })
    return { success: true }
  } catch (error) {
    console.error("Failed to approve mystery:", error)
    const message = error instanceof Error ? error.message : "不明なエラー"
    return { success: false, error: message }
  }
}

/**
 * ミステリーをアーカイブ（→ archived）
 */
export async function archiveMystery(mysteryId: string): Promise<ActionResult> {
  try {
    const db = getAdminFirestore()
    await db.collection(ADMIN_COLLECTIONS.MYSTERIES).doc(mysteryId).update({
      status: "archived",
      updatedAt: FieldValue.serverTimestamp(),
    })
    return { success: true }
  } catch (error) {
    console.error("Failed to archive mystery:", error)
    const message = error instanceof Error ? error.message : "不明なエラー"
    return { success: false, error: message }
  }
}

/**
 * 公開済みミステリーを非公開に戻す（published → pending）
 */
export async function unpublishMystery(mysteryId: string): Promise<ActionResult> {
  try {
    const db = getAdminFirestore()
    await db.collection(ADMIN_COLLECTIONS.MYSTERIES).doc(mysteryId).update({
      status: "pending",
      updatedAt: FieldValue.serverTimestamp(),
    })
    return { success: true }
  } catch (error) {
    console.error("Failed to unpublish mystery:", error)
    const message = error instanceof Error ? error.message : "不明なエラー"
    return { success: false, error: message }
  }
}
