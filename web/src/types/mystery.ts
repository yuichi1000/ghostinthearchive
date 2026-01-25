/**
 * Mystery Report 型定義
 * Python schemas/mystery_report.py と同期
 */

/** 矛盾の種類 */
export type DiscrepancyType =
  | "date_mismatch"     // 日付の不一致
  | "person_missing"    // 人物の欠落
  | "event_outcome"     // 事件結末の相違
  | "location_conflict" // 場所の矛盾
  | "narrative_gap"     // 物語の空白
  | "name_variant";     // 名前の変異

/** 信頼度レベル */
export type ConfidenceLevel = "high" | "medium" | "low";

/** ソースタイプ */
export type SourceType = "newspaper" | "nara_catalog";

/** ソース言語 */
export type SourceLanguage = "en" | "es";

/** ミステリーのステータス */
export type MysteryStatus = "pending" | "published" | "archived";

/**
 * 証拠データ
 * 各ソース文書からの引用情報
 */
export interface Evidence {
  /** ソースタイプ: newspaper または nara_catalog */
  source_type: SourceType;
  /** ソース言語: en または es */
  source_language: SourceLanguage;
  /** ソース文書のタイトル */
  source_title: string;
  /** ソース文書の日付（YYYY-MM-DD形式） */
  source_date?: string;
  /** オリジナルソースへのURL */
  source_url: string;
  /** 関連する抜粋テキスト */
  relevant_excerpt: string;
  /** 地理的コンテキスト（Boston, NYC等） */
  location_context?: string;
}

/**
 * 歴史的コンテキスト
 * ミステリーを理解するための背景情報
 */
export interface HistoricalContext {
  /** 時代区分（例: "Early 19th Century", "1820s"） */
  time_period: string;
  /** 関連する地域（例: ["Boston", "New York"]） */
  geographic_scope: string[];
  /** 当時の関連歴史イベント */
  relevant_events: string[];
  /** 登場する歴史的人物 */
  key_figures: string[];
  /** 政治的・外交的背景（米西関係、貿易摩擦等） */
  political_climate?: string;
}

/**
 * ミステリーレポート
 * Historian Agentの出力結果
 */
export interface MysteryReport {
  /** 一意識別子（例: "MYSTERY-1820-BOSTON-001"） */
  mystery_id: string;
  /** キャッチーなタイトル（例: "The Vanishing of the Santa Maria"） */
  title: string;
  /** 2-3文のサマリー */
  summary: string;

  /** 発見された矛盾の明確な説明 */
  discrepancy_detected: string;
  /** 矛盾の種類 */
  discrepancy_type: DiscrepancyType;

  /** 主要証拠A（通常は英語新聞ソース） */
  evidence_a: Evidence;
  /** 対比証拠B（通常はスペイン語アーカイブソース） */
  evidence_b: Evidence;
  /** 追加の補強証拠 */
  additional_evidence: Evidence[];

  /** 主要仮説 */
  hypothesis: string;
  /** 代替仮説リスト */
  alternative_hypotheses: string[];
  /** 信頼度レベル */
  confidence_level: ConfidenceLevel;

  /** 歴史的コンテキスト */
  historical_context: HistoricalContext;

  /** さらなる調査のための質問 */
  research_questions: string[];
  /** Storyteller Agent向けのナラティブフック */
  story_hooks: string[];

  /** 分析実行日時（ISO形式） */
  analysis_timestamp: string;
}

/**
 * Firestoreに保存されるミステリードキュメント
 * MysteryReportにステータス管理フィールドを追加
 */
export interface FirestoreMystery extends MysteryReport {
  /** ステータス: pending, published, archived */
  status: MysteryStatus;
  /** 作成日時（Firestoreタイムスタンプ） */
  createdAt: Date;
  /** 更新日時 */
  updatedAt: Date;
  /** 公開日時（publishedの場合のみ） */
  publishedAt?: Date;
}

/**
 * ミステリーカード表示用の簡易型
 * 一覧表示で必要な最小限のフィールド
 */
export interface MysteryCardData {
  mystery_id: string;
  title: string;
  summary: string;
  discrepancy_type: DiscrepancyType;
  confidence_level: ConfidenceLevel;
  status: MysteryStatus;
  createdAt: Date;
}

/**
 * 矛盾タイプの日本語ラベルマッピング
 */
export const DISCREPANCY_TYPE_LABELS: Record<DiscrepancyType, string> = {
  date_mismatch: "日付の不一致",
  person_missing: "人物の欠落",
  event_outcome: "結末の相違",
  location_conflict: "場所の矛盾",
  narrative_gap: "物語の空白",
  name_variant: "名前の変異",
};

/**
 * 信頼度レベルの日本語ラベルマッピング
 */
export const CONFIDENCE_LEVEL_LABELS: Record<ConfidenceLevel, string> = {
  high: "高",
  medium: "中",
  low: "低",
};
