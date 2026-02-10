/**
 * Firestore 読み取りクエリ（共有）
 * 公開記事の取得・変換ヘルパー
 */

import type {
  FirestoreMystery,
  MysteryStatus,
  MysteryCardData,
} from "../../types/mystery";
import { Timestamp, DocumentData } from "firebase/firestore";

/**
 * 公開済みミステリー一覧を取得
 * 公開サイトのトップページ用
 */
export async function getPublishedMysteries(
  maxCount: number = 50
): Promise<FirestoreMystery[]> {
  const { collection, getDocs, query, where, orderBy, limit } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("../firebase/config");

  const db = getFirestoreDb();
  const mysteriesRef = collection(db, COLLECTIONS.MYSTERIES);

  const q = query(
    mysteriesRef,
    where("status", "==", "published" as MysteryStatus),
    orderBy("publishedAt", "desc"),
    limit(maxCount)
  );

  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => docToMystery(doc.data()));
}

/**
 * 単一ミステリーをIDで取得
 */
export async function getMysteryById(
  mysteryId: string
): Promise<FirestoreMystery | null> {
  const { doc, getDoc } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("../firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);
  const docSnap = await getDoc(docRef);

  if (!docSnap.exists()) {
    return null;
  }

  return docToMystery(docSnap.data());
}

/**
 * 公開済みミステリーのIDリストを取得
 * generateStaticParams用
 */
export async function getPublishedMysteryIds(): Promise<string[]> {
  const { collection, getDocs, query, where } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("../firebase/config");

  const db = getFirestoreDb();
  const mysteriesRef = collection(db, COLLECTIONS.MYSTERIES);

  const q = query(
    mysteriesRef,
    where("status", "==", "published" as MysteryStatus)
  );

  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => doc.id);
}

/**
 * FirestoreMysteryをMysteryCardDataに変換
 * 一覧表示用の軽量オブジェクト
 */
export function toCardData(mystery: FirestoreMystery): MysteryCardData {
  return {
    mystery_id: mystery.mystery_id,
    title: mystery.title,
    summary: mystery.summary,
    discrepancy_type: mystery.discrepancy_type,
    confidence_level: mystery.confidence_level,
    status: mystery.status,
    createdAt: mystery.createdAt,
  };
}

// ============================================
// ヘルパー関数
// ============================================

/**
 * FirestoreのタイムスタンプをDateに変換
 */
export function convertTimestamp(timestamp: Timestamp | Date | undefined): Date {
  if (!timestamp) return new Date();
  if (timestamp instanceof Timestamp) {
    return timestamp.toDate();
  }
  return timestamp;
}

/**
 * FirestoreドキュメントをFirestoreMysteryに変換
 */
export function docToMystery(docData: DocumentData): FirestoreMystery {
  return {
    ...docData,
    createdAt: convertTimestamp(docData.createdAt),
    updatedAt: convertTimestamp(docData.updatedAt),
    publishedAt: docData.publishedAt
      ? convertTimestamp(docData.publishedAt)
      : undefined,
  } as FirestoreMystery;
}
