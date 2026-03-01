/**
 * Mysteries Firestore 読み取り操作（管理者用）
 * 書き込み操作は Server Actions（@/actions/mysteries）に移行済み
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
