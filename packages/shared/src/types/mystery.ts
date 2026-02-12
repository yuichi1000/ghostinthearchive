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
export type SourceType = "newspaper" | "loc_digital" | "dpla" | "nypl"
  | "pares" | "internet_archive" | "ddb";

/** ソース言語 */
export type SourceLanguage = "en" | "es" | "de" | "fr" | "nl" | "pt";

/** ミステリーのステータス */
export type MysteryStatus = "pending" | "translating" | "published" | "archived" | "error";

/** エージェント実行ステータス */
export type AgentStatus = "running" | "completed" | "error";

/**
 * パイプライン実行ログの単一エントリ
 */
export interface AgentLogEntry {
  /** エージェント名 (librarian, scholar, etc.) */
  agent_name: string;
  /** 実行ステータス */
  status: AgentStatus;
  /** 開始タイムスタンプ (ISO format) */
  start_time: string;
  /** 終了タイムスタンプ (ISO format) */
  end_time: string | null;
  /** 所要時間（秒） */
  duration_seconds: number | null;
  /** 出力の要約 */
  output_summary: string | null;
}

/**
 * 証拠データ
 * 各ソース文書からの引用情報
 */
export interface Evidence {
  /** ソースタイプ: newspaper */
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
 * Scholar Agentの出力結果
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

  /** Storyteller が生成した物語的ブログ原稿（マークダウン形式） */
  narrative_content?: string;

  /** 分析実行日時（ISO形式） */
  analysis_timestamp: string;
}

/**
 * Firestoreに保存されるミステリードキュメント
 * MysteryReportにステータス管理フィールドを追加
 */
/** Podcast 生成ステータス */
export type PodcastStatus = "generating" | "completed" | "error";

export interface FirestoreMystery extends MysteryReport {
  /** ステータス: pending, translating, published, archived */
  status: MysteryStatus;
  /** 作成日時（Firestoreタイムスタンプ） */
  createdAt: Date;
  /** 更新日時 */
  updatedAt: Date;
  /** 公開日時（publishedの場合のみ） */
  publishedAt?: Date;
  /** 翻訳完了日時 */
  translatedAt?: Date;
  /** 画像アセット（Cloud Storage URLs） */
  images?: {
    hero?: string;
    thumbnail?: string;
    inserts?: string[];
    /** レスポンシブ画像バリアント（WebP） */
    variants?: {
      sm?: string;
      md?: string;
      lg?: string;
      xl?: string;
    };
  };
  /** 多言語 Scholar 分析結果 (言語コード → 分析テキスト) */
  multilingual_analysis?: Record<string, string>;
  /** 分析に使用された言語コードのリスト */
  languages_analyzed?: string[];
  /** パイプライン実行ログ */
  pipeline_log?: AgentLogEntry[];
  /** ポッドキャスト脚本 */
  podcast_script?: string;
  /** 音声アセット */
  audio_assets?: {
    japanese_audio?: string;
    english_audio?: string;
  };
  /** ポッドキャスト生成ステータス */
  podcast_status?: PodcastStatus;

  // === 日本語翻訳フィールド ===
  /** タイトル（日本語） */
  title_ja?: string;
  /** サマリー（日本語） */
  summary_ja?: string;
  /** 物語的ブログ原稿（日本語、マークダウン形式） */
  narrative_content_ja?: string;
  /** 発見された矛盾の説明（日本語） */
  discrepancy_detected_ja?: string;
  /** 主要仮説（日本語） */
  hypothesis_ja?: string;
  /** 代替仮説リスト（日本語） */
  alternative_hypotheses_ja?: string[];
  /** 歴史的コンテキスト（日本語） */
  historical_context_ja?: {
    political_climate?: string;
  };
  /** ナラティブフック（日本語） */
  story_hooks_ja?: string[];

  // === 英語翻訳フィールド（レガシー、後方互換用） ===
  /** @deprecated Use base fields (title, summary, etc.) which are now in English */
  title_en?: string;
  /** @deprecated */
  summary_en?: string;
  /** @deprecated */
  narrative_content_en?: string;
  /** @deprecated */
  discrepancy_detected_en?: string;
  /** @deprecated */
  hypothesis_en?: string;
  /** @deprecated */
  alternative_hypotheses_en?: string[];
  /** @deprecated */
  historical_context_en?: {
    political_climate?: string;
  };
  /** @deprecated */
  story_hooks_en?: string[];
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

/**
 * パイプライン実行ステータス
 */
export type PipelineRunStatus = "running" | "completed" | "error";

/**
 * パイプライン種別
 */
export type PipelineRunType = "blog" | "translate" | "podcast";

/**
 * パイプライン実行ドキュメント
 * Python 側 shared/pipeline_run.py と同期
 */
export interface PipelineRun {
  id: string;
  type: PipelineRunType;
  status: PipelineRunStatus;
  query: string | null;
  mystery_id: string | null;
  current_agent: string | null;
  pipeline_log: AgentLogEntry[];
  started_at: Date;
  updated_at: Date;
  completed_at: Date | null;
  error_message: string | null;
}

/**
 * エージェント名の日本語ラベルマッピング
 */
export const AGENT_NAME_LABELS: Record<string, string> = {
  theme_analyzer: "テーマ分析",
  librarian: "資料収集",
  librarian_en: "資料収集（英語）",
  librarian_es: "資料収集（スペイン語）",
  librarian_de: "資料収集（ドイツ語）",
  librarian_fr: "資料収集（フランス語）",
  librarian_nl: "資料収集（オランダ語）",
  librarian_pt: "資料収集（ポルトガル語）",
  scholar: "学際分析",
  scholar_en: "学際分析（英語）",
  scholar_es: "学際分析（スペイン語）",
  scholar_de: "学際分析（ドイツ語）",
  scholar_fr: "学際分析（フランス語）",
  scholar_nl: "学際分析（オランダ語）",
  scholar_pt: "学際分析（ポルトガル語）",
  scholar_en_debate: "討論（英語）",
  scholar_es_debate: "討論（スペイン語）",
  scholar_de_debate: "討論（ドイツ語）",
  scholar_fr_debate: "討論（フランス語）",
  scholar_nl_debate: "討論（オランダ語）",
  scholar_pt_debate: "討論（ポルトガル語）",
  armchair_polymath: "統合分析",
  cross_reference_scholar: "統合分析",
  storyteller: "物語生成",
  translator: "翻訳",
  scriptwriter: "脚本作成",
  illustrator: "画像生成",
  producer: "音声生成",
  publisher: "公開処理",
};
