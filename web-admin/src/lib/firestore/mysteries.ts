/**
 * Mysteries Firestore 操作（管理者用）
 * 書き込み操作と管理者固有の読み取りクエリのみ
 * 共通の読み取りクエリは @ghost/shared から動的ラッパー経由で提供
 *
 * NOTE: @ghost/shared/src/lib/firestore/queries は firebase/firestore と
 * firebase/config を静的 import しているため、re-export すると Docker ビルド時
 * （環境変数なし）に Firebase 初期化が失敗してプリレンダリングエラーになる。
 * すべて動的 import で取得すること。
 */

import type {
  FirestoreMystery,
  MysteryStatus,
} from "@ghost/shared/src/types/mystery";

// ============================================
// 共通クエリの動的ラッパー
// （queries.ts の静的 Firebase import を回避するため）
// ============================================

/**
 * 単一ミステリーをIDで取得（@ghost/shared の動的ラッパー）
 */
export async function getMysteryById(
  mysteryId: string
): Promise<FirestoreMystery | null> {
  const { getMysteryById: fn } = await import(
    "@ghost/shared/src/lib/firestore/queries"
  );
  return fn(mysteryId);
}

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
  const { docToMystery } = await import("@ghost/shared/src/lib/firestore/queries");

  const db = getFirestoreDb();
  const mysteriesRef = collection(db, COLLECTIONS.MYSTERIES);

  const q = query(
    mysteriesRef,
    where("status", "==", "pending" as MysteryStatus),
    orderBy("createdAt", "desc"),
    limit(maxCount)
  );

  const snapshot = await getDocs(q);
  return snapshot.docs.map((d) => docToMystery(d.data()));
}

/**
 * 全ミステリー一覧を取得（管理者用）
 */
export async function getAllMysteries(
  maxCount: number = 100
): Promise<FirestoreMystery[]> {
  const { collection, getDocs, query, orderBy, limit } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config");
  const { docToMystery } = await import("@ghost/shared/src/lib/firestore/queries");

  const db = getFirestoreDb();
  const mysteriesRef = collection(db, COLLECTIONS.MYSTERIES);

  const q = query(mysteriesRef, orderBy("createdAt", "desc"), limit(maxCount));

  const snapshot = await getDocs(q);
  return snapshot.docs.map((d) => docToMystery(d.data()));
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
 * 公開済みミステリーを非公開に戻す（published → pending）
 * publishedAt は再公開時の参考情報として保持する
 */
export async function unpublishMystery(mysteryId: string): Promise<void> {
  const { doc, updateDoc, Timestamp } = await import("firebase/firestore");
  const { getFirestoreDb, COLLECTIONS } = await import("@ghost/shared/src/lib/firebase/config");

  const db = getFirestoreDb();
  const docRef = doc(db, COLLECTIONS.MYSTERIES, mysteryId);

  await updateDoc(docRef, {
    status: "pending" as MysteryStatus,
    updatedAt: Timestamp.now(),
  });
}
