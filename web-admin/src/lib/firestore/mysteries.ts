/**
 * Mysteries Firestore 操作（管理者用）
 * 書き込み操作と管理者固有の読み取りクエリのみ
 * 共通の読み取りクエリは @ghost/shared から import
 */

import type {
  FirestoreMystery,
  MysteryStatus,
  PodcastStatus,
} from "@ghost/shared/src/types/mystery";
import { docToMystery } from "@ghost/shared/src/lib/firestore/queries";

// 共通の読み取りクエリを re-export
export { getPublishedMysteries, getMysteryById, getPublishedMysteryIds, toCardData } from "@ghost/shared/src/lib/firestore/queries";

// ============================================
// 管理者固有のクエリ
// ============================================

/**
 * 承認待ちミステリー一覧を取得
 * 管理ダッシュボード用
 */
export async function getPendingMysteries(
  maxCount: number = 50
): Promise<FirestoreMystery[]> {
  const { collection, getDocs, query, where, orderBy, limit } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config");

  const db = getFirestoreDb();
  const mysteriesRef = collection(db, COLLECTIONS.MYSTERIES);

  const q = query(
    mysteriesRef,
    where("status", "==", "pending" as MysteryStatus),
    orderBy("createdAt", "desc"),
    limit(maxCount)
  );

  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => docToMystery(doc.data()));
}

/**
 * 全ミステリー一覧を取得（管理者用）
 */
export async function getAllMysteries(
  maxCount: number = 100
): Promise<FirestoreMystery[]> {
  const { collection, getDocs, query, orderBy, limit } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config");

  const db = getFirestoreDb();
  const mysteriesRef = collection(db, COLLECTIONS.MYSTERIES);

  const q = query(mysteriesRef, orderBy("createdAt", "desc"), limit(maxCount));

  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => docToMystery(doc.data()));
}

// ============================================
// 書き込み操作
// ============================================

/**
 * ミステリーを承認（直接公開）
 * status を pending → published に更新
 * English-first フローでは翻訳は既にパイプライン内で完了しているため、
 * Approve は即座に公開する。
 */
export async function approveMystery(mysteryId: string): Promise<void> {
  const { doc, updateDoc, Timestamp } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);

  await updateDoc(docRef, {
    status: "published" as MysteryStatus,
    publishedAt: Timestamp.now(),
    updatedAt: Timestamp.now(),
  });
}

/**
 * ミステリーをアーカイブ（非公開化）
 */
export async function archiveMystery(mysteryId: string): Promise<void> {
  const { doc, updateDoc, Timestamp } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);

  await updateDoc(docRef, {
    status: "archived" as MysteryStatus,
    updatedAt: Timestamp.now(),
  });
}

/**
 * Podcast 生成をリクエスト
 * podcast_status を "generating" に更新
 */
export async function requestPodcast(mysteryId: string): Promise<void> {
  const { doc, updateDoc, Timestamp } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);

  await updateDoc(docRef, {
    podcast_status: "generating" as PodcastStatus,
    updatedAt: Timestamp.now(),
  });
}
