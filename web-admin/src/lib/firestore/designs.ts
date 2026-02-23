/**
 * Product Designs Firestore 操作（管理者用）
 * product_designs コレクションの読み取り操作
 */

import type { FirestoreDesign } from "@ghost/shared/src/types/mystery"

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
 * Firestore ドキュメントデータを FirestoreDesign に変換
 */
function docToDesign(id: string, data: Record<string, unknown>): FirestoreDesign {
  return {
    design_id: id,
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
  }
}

/**
 * 全 Design 一覧を取得（updated_at desc）
 */
export async function getAllDesigns(
  maxCount: number = 50
): Promise<FirestoreDesign[]> {
  const { collection, getDocs, query, orderBy, limit } = await import("firebase/firestore")
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config")

  const db = getFirestoreDb()
  const ref = collection(db, COLLECTIONS.PRODUCT_DESIGNS)
  const q = query(ref, orderBy("updated_at", "desc"), limit(maxCount))
  const snapshot = await getDocs(q)

  return snapshot.docs.map((doc) => docToDesign(doc.id, doc.data()))
}

/**
 * 単一 Design を取得
 */
export async function getDesignById(
  designId: string
): Promise<FirestoreDesign | null> {
  const { doc, getDoc } = await import("firebase/firestore")
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config")

  const db = getFirestoreDb()
  const docRef = doc(db, COLLECTIONS.PRODUCT_DESIGNS, designId)
  const snapshot = await getDoc(docRef)

  if (!snapshot.exists()) return null
  return docToDesign(snapshot.id, snapshot.data())
}

/**
 * 記事に紐付く Design 一覧を取得
 */
export async function getDesignsByMysteryId(
  mysteryId: string
): Promise<FirestoreDesign[]> {
  const { collection, getDocs, query, where, orderBy } = await import("firebase/firestore")
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config")

  const db = getFirestoreDb()
  const ref = collection(db, COLLECTIONS.PRODUCT_DESIGNS)
  const q = query(
    ref,
    where("mystery_id", "==", mysteryId),
    orderBy("created_at", "desc")
  )
  const snapshot = await getDocs(q)

  return snapshot.docs.map((doc) => docToDesign(doc.id, doc.data()))
}

/**
 * mystery_id → 最新 Design の Map を構築
 */
export async function getDesignsByMysteryIdMap(): Promise<Map<string, FirestoreDesign>> {
  const designs = await getAllDesigns(200)
  const map = new Map<string, FirestoreDesign>()
  for (const d of designs) {
    if (!map.has(d.mystery_id)) map.set(d.mystery_id, d)
  }
  return map
}
