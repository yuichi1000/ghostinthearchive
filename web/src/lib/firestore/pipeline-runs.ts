/**
 * Pipeline Runs Firestore 操作
 * pipeline_runs コレクションの読み取り操作を提供
 */

import type { PipelineRun } from "@/types/mystery";
import { Timestamp, DocumentData } from "firebase/firestore";

/**
 * 実行中のパイプライン一覧を取得
 */
export async function getRunningPipelineRuns(): Promise<PipelineRun[]> {
  const { collection, getDocs, query, where, orderBy } = await import(
    "firebase/firestore"
  );
  const { getFirestoreDb, COLLECTIONS } = await import(
    "@/lib/firebase/config"
  );

  const db = getFirestoreDb();
  const runsRef = collection(db, COLLECTIONS.PIPELINE_RUNS);

  const q = query(
    runsRef,
    where("status", "==", "running"),
    orderBy("started_at", "desc")
  );

  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => docToPipelineRun(doc.id, doc.data()));
}

/**
 * 最近完了・エラーのパイプラインも含めて取得
 * 完了後にUIで一瞬表示するために使用
 */
export async function getRecentPipelineRuns(
  maxCount: number = 10
): Promise<PipelineRun[]> {
  const { collection, getDocs, query, orderBy, limit } = await import(
    "firebase/firestore"
  );
  const { getFirestoreDb, COLLECTIONS } = await import(
    "@/lib/firebase/config"
  );

  const db = getFirestoreDb();
  const runsRef = collection(db, COLLECTIONS.PIPELINE_RUNS);

  const q = query(runsRef, orderBy("started_at", "desc"), limit(maxCount));

  const snapshot = await getDocs(q);
  return snapshot.docs.map((doc) => docToPipelineRun(doc.id, doc.data()));
}

/**
 * Firestore タイムスタンプを Date に変換
 */
function convertTimestamp(
  timestamp: Timestamp | Date | undefined | null
): Date {
  if (!timestamp) return new Date();
  if (timestamp instanceof Timestamp) {
    return timestamp.toDate();
  }
  return timestamp;
}

/**
 * Firestore ドキュメントを PipelineRun に変換
 */
function docToPipelineRun(id: string, data: DocumentData): PipelineRun {
  return {
    id,
    type: data.type,
    status: data.status,
    query: data.query || null,
    mystery_id: data.mystery_id || null,
    current_agent: data.current_agent || null,
    pipeline_log: data.pipeline_log || [],
    started_at: convertTimestamp(data.started_at),
    updated_at: convertTimestamp(data.updated_at),
    completed_at: data.completed_at
      ? convertTimestamp(data.completed_at)
      : null,
    error_message: data.error_message || null,
  };
}
