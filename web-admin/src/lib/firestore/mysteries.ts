/**
 * Mysteries Firestore 操作
 * ミステリーデータのCRUD操作を提供
 */

import type {
  FirestoreMystery,
  MysteryStatus,
  MysteryCardData,
  PodcastStatus,
} from "@/types/mystery";

// Firestore から直接読み取り（エミュレータまたは本番）

// ============================================
// Firestore関数（モック対応版）
// ============================================

/**
 * 公開済みミステリー一覧を取得
 * 公開サイトのトップページ用
 */
export async function getPublishedMysteries(
  maxCount: number = 50
): Promise<FirestoreMystery[]> {
  const { collection, getDocs, query, where, orderBy, limit } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

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
 * 承認待ちミステリー一覧を取得
 * 管理ダッシュボード用
 */
export async function getPendingMysteries(
  maxCount: number = 50
): Promise<FirestoreMystery[]> {
  const { collection, getDocs, query, where, orderBy, limit } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

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
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const mysteriesRef = collection(db, COLLECTIONS.MYSTERIES);

  const q = query(mysteriesRef, orderBy("createdAt", "desc"), limit(maxCount));

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
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);
  const docSnap = await getDoc(docRef);

  if (!docSnap.exists()) {
    return null;
  }

  return docToMystery(docSnap.data());
}

/**
 * ミステリーを承認（翻訳開始）
 * status を pending → translating に更新
 * 翻訳完了後に status は published になる
 */
export async function approveMystery(mysteryId: string): Promise<void> {
  const { doc, updateDoc, Timestamp } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);

  await updateDoc(docRef, {
    status: "translating" as MysteryStatus,
    updatedAt: Timestamp.now(),
  });
}

/**
 * ミステリーをアーカイブ（非公開化）
 */
export async function archiveMystery(mysteryId: string): Promise<void> {
  const { doc, updateDoc, Timestamp } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);

  await updateDoc(docRef, {
    status: "archived" as MysteryStatus,
    updatedAt: Timestamp.now(),
  });
}

/**
 * 公開済みミステリーのIDリストを取得
 * generateStaticParams用
 */
export async function getPublishedMysteryIds(): Promise<string[]> {
  const { collection, getDocs, query, where } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

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

/**
 * Podcast 生成をリクエスト
 * podcast_status を "generating" に更新
 */
export async function requestPodcast(mysteryId: string): Promise<void> {
  const { doc, updateDoc, Timestamp } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@/lib/firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);

  await updateDoc(docRef, {
    podcast_status: "generating" as PodcastStatus,
    updatedAt: Timestamp.now(),
  });
}

// ============================================
// ヘルパー関数
// ============================================

import { Timestamp, DocumentData } from "firebase/firestore";

/**
 * FirestoreのタイムスタンプをDateに変換
 */
function convertTimestamp(timestamp: Timestamp | Date | undefined): Date {
  if (!timestamp) return new Date();
  if (timestamp instanceof Timestamp) {
    return timestamp.toDate();
  }
  return timestamp;
}

/**
 * FirestoreドキュメントをFirestoreMysteryに変換
 */
function docToMystery(docData: DocumentData): FirestoreMystery {
  return {
    ...docData,
    createdAt: convertTimestamp(docData.createdAt),
    updatedAt: convertTimestamp(docData.updatedAt),
    publishedAt: docData.publishedAt
      ? convertTimestamp(docData.publishedAt)
      : undefined,
  } as FirestoreMystery;
}
