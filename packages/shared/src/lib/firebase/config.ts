/**
 * Firebase クライアント設定
 * ブラウザ側で使用するFirebase SDKの初期化
 */

import { initializeApp, getApps, deleteApp, FirebaseApp } from "firebase/app";
import { getFirestore, Firestore, connectFirestoreEmulator } from "firebase/firestore";
import { getStorage, FirebaseStorage, connectStorageEmulator } from "firebase/storage";

/** Firebase設定オブジェクト */
const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
};

/**
 * globalThis にインスタンスを保持することで、
 * Next.js dev + Turbopack のモジュール再評価でもシングルトンを維持する
 */
const globalForFirebase = globalThis as unknown as {
  _firebaseApp?: FirebaseApp;
  _firestoreDb?: Firestore;
  _firebaseStorage?: FirebaseStorage;
  _firestoreEmulatorConnected?: boolean;
  _storageEmulatorConnected?: boolean;
  _moduleEvalId?: symbol;
};

/**
 * HMR 検出用: モジュールが再評価されるたびに新しい Symbol が生成される。
 * globalThis に保存した前回の Symbol と異なれば HMR が発生したと判定する。
 */
const MODULE_EVAL_ID = Symbol("firebase-config");

/**
 * HMR（Hot Module Replacement）検出 — モジュール再評価時に全キャッシュをクリアする。
 *
 * Turbopack の HMR でモジュールが再評価されると firebase/firestore の
 * collection() 等が新しいクラス定義を持つ。globalThis にキャッシュされた
 * 古い Firestore インスタンスは instanceof チェックに失敗するため、
 * 古い Firebase App ごと破棄して再初期化する必要がある。
 */
function invalidateOnHmr(): void {
  if (globalForFirebase._moduleEvalId === MODULE_EVAL_ID) return;

  // 古い Firebase App を破棄（内部の Firestore/Storage サービスも解放される）
  if (globalForFirebase._firebaseApp) {
    try {
      deleteApp(globalForFirebase._firebaseApp).catch(() => {});
    } catch {
      // 既に削除済みの場合は無視
    }
  }

  globalForFirebase._firebaseApp = undefined;
  globalForFirebase._firestoreDb = undefined;
  globalForFirebase._firebaseStorage = undefined;
  globalForFirebase._firestoreEmulatorConnected = undefined;
  globalForFirebase._storageEmulatorConnected = undefined;
  globalForFirebase._moduleEvalId = MODULE_EVAL_ID;
}

/**
 * Firebaseアプリを初期化して返す
 * 既に初期化済みの場合は既存のインスタンスを返す
 */
export function getFirebaseApp(): FirebaseApp {
  invalidateOnHmr();

  if (!globalForFirebase._firebaseApp) {
    // projectId が未設定なら環境変数の設定漏れ
    if (!firebaseConfig.projectId) {
      throw new Error(
        "[Firebase] NEXT_PUBLIC_FIREBASE_PROJECT_ID が未設定です。" +
        ".env.local（開発）または .env.production（ビルド）を確認してください。"
      );
    }

    // 既存のアプリがあれば再利用、なければ新規作成
    const existingApps = getApps();
    if (existingApps.length > 0) {
      globalForFirebase._firebaseApp = existingApps[0];
    } else {
      globalForFirebase._firebaseApp = initializeApp(firebaseConfig);
    }
  }
  return globalForFirebase._firebaseApp;
}

/**
 * Firestoreインスタンスを取得
 * 開発環境ではエミュレータに接続
 */
export function getFirestoreDb(): Firestore {
  // 必ず getFirebaseApp() を先に呼び、HMR チェックをトリガーする
  const firebaseApp = getFirebaseApp();

  if (!globalForFirebase._firestoreDb) {
    globalForFirebase._firestoreDb = getFirestore(firebaseApp);

    // 開発環境でエミュレータを使用する場合（クライアント・サーバー両方）
    if (
      process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === "true" &&
      !globalForFirebase._firestoreEmulatorConnected
    ) {
      const host = process.env.NEXT_PUBLIC_FIREBASE_EMULATOR_HOST || "localhost";
      const port = parseInt(
        process.env.NEXT_PUBLIC_FIRESTORE_EMULATOR_PORT || "8080",
        10
      );
      connectFirestoreEmulator(globalForFirebase._firestoreDb, host, port);
      globalForFirebase._firestoreEmulatorConnected = true;
      console.log(`[Firebase] Firestore Emulator に接続: ${host}:${port}`);
    }
  }
  return globalForFirebase._firestoreDb;
}

/**
 * Firebase Storageインスタンスを取得
 * 開発環境ではエミュレータに接続
 */
export function getFirebaseStorage(): FirebaseStorage {
  // 必ず getFirebaseApp() を先に呼び、HMR チェックをトリガーする
  const firebaseApp = getFirebaseApp();

  if (!globalForFirebase._firebaseStorage) {
    globalForFirebase._firebaseStorage = getStorage(firebaseApp);

    if (
      process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === "true" &&
      !globalForFirebase._storageEmulatorConnected
    ) {
      const host = process.env.NEXT_PUBLIC_FIREBASE_EMULATOR_HOST || "localhost";
      const port = parseInt(
        process.env.NEXT_PUBLIC_STORAGE_EMULATOR_PORT || "9199",
        10
      );
      connectStorageEmulator(globalForFirebase._firebaseStorage, host, port);
      globalForFirebase._storageEmulatorConnected = true;
      console.log(`[Firebase] Storage Emulator に接続: ${host}:${port}`);
    }
  }
  return globalForFirebase._firebaseStorage;
}

/**
 * Firestore コレクション名
 */
export const COLLECTIONS = {
  MYSTERIES: "mysteries",
  PIPELINE_RUNS: "pipeline_runs",
  PODCASTS: "podcasts",
  PRODUCT_DESIGNS: "product_designs",
} as const;
