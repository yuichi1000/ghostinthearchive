/**
 * Firebase クライアント設定
 * ブラウザ側で使用するFirebase SDKの初期化
 */

import { initializeApp, getApps, FirebaseApp } from "firebase/app";
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
};

/**
 * Firebaseアプリを初期化して返す
 * 既に初期化済みの場合は既存のインスタンスを返す
 */
export function getFirebaseApp(): FirebaseApp {
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
  if (!globalForFirebase._firestoreDb) {
    const firebaseApp = getFirebaseApp();
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
  if (!globalForFirebase._firebaseStorage) {
    const firebaseApp = getFirebaseApp();
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
} as const;
