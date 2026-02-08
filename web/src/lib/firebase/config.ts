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

/** Firebaseアプリインスタンス（シングルトン） */
let app: FirebaseApp;

/** Firestoreインスタンス（シングルトン） */
let db: Firestore;

/** Storageインスタンス（シングルトン） */
let storageInstance: FirebaseStorage;

/** エミュレータ接続済みフラグ */
let emulatorConnected = false;
let storageEmulatorConnected = false;

/**
 * Firebaseアプリを初期化して返す
 * 既に初期化済みの場合は既存のインスタンスを返す
 */
export function getFirebaseApp(): FirebaseApp {
  if (!app) {
    // 既存のアプリがあれば再利用、なければ新規作成
    const existingApps = getApps();
    if (existingApps.length > 0) {
      app = existingApps[0];
    } else {
      app = initializeApp(firebaseConfig);
    }
  }
  return app;
}

/**
 * Firestoreインスタンスを取得
 * 開発環境ではエミュレータに接続
 */
export function getFirestoreDb(): Firestore {
  if (!db) {
    const firebaseApp = getFirebaseApp();
    db = getFirestore(firebaseApp);

    // 開発環境でエミュレータを使用する場合（クライアント・サーバー両方）
    if (
      process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === "true" &&
      !emulatorConnected
    ) {
      const host = process.env.NEXT_PUBLIC_FIREBASE_EMULATOR_HOST || "localhost";
      const port = parseInt(
        process.env.NEXT_PUBLIC_FIRESTORE_EMULATOR_PORT || "8080",
        10
      );
      connectFirestoreEmulator(db, host, port);
      emulatorConnected = true;
      console.log(`[Firebase] Firestore Emulator に接続: ${host}:${port}`);
    }
  }
  return db;
}

/**
 * Firebase Storageインスタンスを取得
 * 開発環境ではエミュレータに接続
 */
export function getFirebaseStorage(): FirebaseStorage {
  if (!storageInstance) {
    const firebaseApp = getFirebaseApp();
    storageInstance = getStorage(firebaseApp);

    if (
      process.env.NEXT_PUBLIC_USE_FIREBASE_EMULATOR === "true" &&
      !storageEmulatorConnected
    ) {
      const host = process.env.NEXT_PUBLIC_FIREBASE_EMULATOR_HOST || "localhost";
      const port = parseInt(
        process.env.NEXT_PUBLIC_STORAGE_EMULATOR_PORT || "9199",
        10
      );
      connectStorageEmulator(storageInstance, host, port);
      storageEmulatorConnected = true;
      console.log(`[Firebase] Storage Emulator に接続: ${host}:${port}`);
    }
  }
  return storageInstance;
}

/**
 * Firestore コレクション名
 */
export const COLLECTIONS = {
  MYSTERIES: "mysteries",
  PIPELINE_RUNS: "pipeline_runs",
} as const;
