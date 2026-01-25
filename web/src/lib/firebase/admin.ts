/**
 * Firebase Admin SDK 設定
 * サーバーサイド（API Routes, Server Components）で使用
 */

import { initializeApp, getApps, cert, App } from "firebase-admin/app";
import { getFirestore, Firestore } from "firebase-admin/firestore";

/** Admin SDKアプリインスタンス（シングルトン） */
let adminApp: App;

/** Admin Firestoreインスタンス（シングルトン） */
let adminDb: Firestore;

/**
 * Firebase Admin SDKを初期化して返す
 * 既に初期化済みの場合は既存のインスタンスを返す
 */
export function getAdminApp(): App {
  if (!adminApp) {
    const existingApps = getApps();

    if (existingApps.length > 0) {
      adminApp = existingApps[0];
    } else {
      // 環境変数からサービスアカウントキーを読み込む
      // GOOGLE_APPLICATION_CREDENTIALS が設定されている場合は自動で読み込まれる
      // 設定されていない場合はプロジェクトIDのみで初期化（GCP環境向け）
      const projectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;

      if (process.env.FIREBASE_SERVICE_ACCOUNT_KEY) {
        // 環境変数にJSON文字列として設定されている場合
        const serviceAccount = JSON.parse(
          process.env.FIREBASE_SERVICE_ACCOUNT_KEY
        );
        adminApp = initializeApp({
          credential: cert(serviceAccount),
          projectId,
        });
      } else {
        // デフォルト認証情報を使用（GCP環境 or GOOGLE_APPLICATION_CREDENTIALS）
        adminApp = initializeApp({
          projectId,
        });
      }
    }
  }
  return adminApp;
}

/**
 * Admin Firestoreインスタンスを取得
 */
export function getAdminFirestore(): Firestore {
  if (!adminDb) {
    getAdminApp(); // アプリが初期化されていることを確認
    adminDb = getFirestore();

    // エミュレータ設定（開発環境用）
    if (process.env.USE_FIREBASE_EMULATOR === "true") {
      const host = process.env.FIREBASE_EMULATOR_HOST || "localhost";
      const port = process.env.FIRESTORE_EMULATOR_PORT || "8080";
      process.env.FIRESTORE_EMULATOR_HOST = `${host}:${port}`;
      console.log(`[Firebase Admin] Firestore Emulator に接続: ${host}:${port}`);
    }
  }
  return adminDb;
}

/** Admin用 Firestore コレクション名 */
export const ADMIN_COLLECTIONS = {
  MYSTERIES: "mysteries",
} as const;
