/**
 * Podcasts Firestore 操作（管理者用）
 * podcasts コレクションの CRUD 操作
 */

import type { FirestorePodcast, PodcastScript } from "@ghost/shared/src/types/mystery"

/**
 * Firestore Timestamp → Date 変換ヘルパー
 */
function toDate(val: unknown): Date {
  if (val && typeof val === "object" && "toDate" in val) {
    return (val as { toDate: () => Date }).toDate()
  }
  if (val instanceof Date) return val
  if (typeof val === "string") return new Date(val)
  return new Date()
}

/**
 * Firestore ドキュメントデータを FirestorePodcast に変換
 */
function docToPodcast(id: string, data: Record<string, unknown>): FirestorePodcast {
  return {
    podcast_id: id,
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
  }
}

/**
 * 全 Podcast 一覧を取得（updated_at desc）
 */
export async function getAllPodcasts(
  maxCount: number = 50
): Promise<FirestorePodcast[]> {
  const { collection, getDocs, query, orderBy, limit } = await import("firebase/firestore")
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config")

  const db = getFirestoreDb()
  const ref = collection(db, COLLECTIONS.PODCASTS)
  const q = query(ref, orderBy("updated_at", "desc"), limit(maxCount))
  const snapshot = await getDocs(q)

  return snapshot.docs.map((doc) => docToPodcast(doc.id, doc.data()))
}

/**
 * 単一 Podcast を取得
 */
export async function getPodcastById(
  podcastId: string
): Promise<FirestorePodcast | null> {
  const { doc, getDoc } = await import("firebase/firestore")
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config")

  const db = getFirestoreDb()
  const docRef = doc(db, COLLECTIONS.PODCASTS, podcastId)
  const snapshot = await getDoc(docRef)

  if (!snapshot.exists()) return null
  return docToPodcast(snapshot.id, snapshot.data())
}

/**
 * 記事に紐付く Podcast 一覧を取得
 */
export async function getPodcastsByMysteryId(
  mysteryId: string
): Promise<FirestorePodcast[]> {
  const { collection, getDocs, query, where, orderBy } = await import("firebase/firestore")
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config")

  const db = getFirestoreDb()
  const ref = collection(db, COLLECTIONS.PODCASTS)
  const q = query(
    ref,
    where("mystery_id", "==", mysteryId),
    orderBy("created_at", "desc")
  )
  const snapshot = await getDocs(q)

  return snapshot.docs.map((doc) => docToPodcast(doc.id, doc.data()))
}

/**
 * 脚本を更新（編集後の保存）
 */
export async function updatePodcastScript(
  podcastId: string,
  script: PodcastScript
): Promise<void> {
  const { doc, updateDoc, Timestamp } = await import("firebase/firestore")
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config")

  const db = getFirestoreDb()
  const docRef = doc(db, COLLECTIONS.PODCASTS, podcastId)

  await updateDoc(docRef, {
    script,
    updated_at: Timestamp.now(),
  })
}

export { docToPodcast }
