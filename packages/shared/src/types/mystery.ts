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
export type SourceType = "newspaper" | "loc_digital" | "nypl"
  | "pares" | "internet_archive" | "ddb" | "europeana" | "trove"
  | "delpher" | "ndl" | "wellcome" | "digitalnz"
  | "archive" | "book";

/** ソース言語 */
export type SourceLanguage = "en" | "es" | "de" | "fr" | "nl" | "pt";

/** 翻訳対象言語（ソース言語 + 日本語） */
export type TranslationLang = "ja" | "es" | "de";

/**
 * 翻訳済みコンテンツ
 * translations map の各言語エントリ
 */
export interface TranslatedContent {
  title: string;
  summary: string;
  narrative_content: string;
  discrepancy_detected?: string;
  hypothesis?: string;
  alternative_hypotheses?: string[];
  story_hooks?: string[];
  historical_context?: { political_climate?: string };
  evidence_a_excerpt?: string;
  evidence_b_excerpt?: string;
  additional_evidence_excerpts?: string[];
  confidence_rationale?: string;
}

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
 * 学術論文カバレッジ
 * OpenAlex データに基づく学術界の分析
 */
export interface AcademicCoverage {
  /** 関連論文の総数 */
  papers_found: number;
  /** 言語別の論文数 */
  language_distribution: Record<string, number>;
  /** 時代別の論文数 */
  temporal_distribution: Record<string, number>;
  /** 頻出概念タグ */
  key_concepts: string[];
  /** Polymath が特定した学術的盲点 */
  identified_gaps: string[];
  /** 学術的コンセンサスと一次資料の緊張関係 */
  consensus_vs_primary?: string;
}

/**
 * ソースカバレッジ評価
 * Polymath が行う調査範囲の自己評価
 */
export interface SourceCoverage {
  /** 検索した API/アーカイブのリスト */
  apis_searched: string[];
  /** 結果を返した API/アーカイブのリスト */
  apis_with_results: string[];
  /** 結果を返さなかった API/アーカイブのリスト */
  apis_without_results: string[];
  /** この時代・地域に存在するがデジタル化されていない既知のソース */
  known_undigitized_sources?: string[];
  /** デジタル化範囲と調査限界に関する総合評価 */
  coverage_assessment?: string;
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
  /** ソースカバレッジ評価（検索範囲と限界の自己評価） */
  source_coverage?: SourceCoverage;
  /** 学術論文カバレッジ（OpenAlex データに基づく） */
  academic_coverage?: AcademicCoverage;
  /** confidence_level 判定の根拠 */
  confidence_rationale?: string;

  /** 歴史的コンテキスト */
  historical_context: HistoricalContext;

  /** さらなる調査のための質問 */
  research_questions: string[];
  /** Storyteller Agent向けのナラティブフック */
  story_hooks: string[];

  /** セマンティックタグ（記事分類・関連記事推薦用） */
  tags?: string[];

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
export type PodcastStatus = "script_generating" | "script_ready" | "audio_generating" | "audio_ready" | "error";

/** Podcast 脚本セグメント */
export interface PodcastSegment {
  /** セグメント種別 */
  type: "overview" | "act_i" | "act_ii" | "act_iii" | "act_iiii"
    | "intro" | "body" | "outro";  // 後方互換（レガシー）
  /** セグメントラベル（例: "Historical Background"） */
  label: string;
  /** ナレーションテキスト（TTS に渡す） */
  text: string;
  /** SFX/BGM 指示（TTS には渡さない） */
  notes?: string;
}

/** Podcast 構造化脚本 */
export interface PodcastScript {
  /** エピソードタイトル */
  episode_title: string;
  /** 想定再生時間（分） */
  estimated_duration_minutes: number;
  /** セグメント一覧 */
  segments: PodcastSegment[];
}

/** Podcast 音声メタデータ */
export interface PodcastAudio {
  /** GCS パス（gs://bucket/path） */
  gcs_path: string;
  /** 公開 URL */
  public_url: string;
  /** 再生時間（秒） */
  duration_seconds: number;
  /** TTS ボイス名 */
  voice_name: string;
  /** ファイルフォーマット */
  format: string;
}

/**
 * Podcast ドキュメント（podcasts コレクション）
 * mystery_id でミステリー記事とリンク
 */
export interface FirestorePodcast {
  /** Podcast ドキュメント ID */
  podcast_id: string;
  /** リンク先ミステリー記事 ID */
  mystery_id: string;
  /** 記事タイトル（非正規化、表示用） */
  mystery_title: string;
  /** 生成ステータス */
  status: PodcastStatus;
  /** 管理者のカスタム指示 */
  custom_instructions?: string;
  /** 構造化英語脚本 */
  script?: PodcastScript;
  /** 日本語訳（レビュー用、プレーンテキスト） */
  script_ja?: string;
  /** 音声メタデータ */
  audio?: PodcastAudio;
  /** パイプライン実行 ID */
  pipeline_run_id?: string;
  /** 作成日時 */
  created_at: Date;
  /** 更新日時 */
  updated_at: Date;
  /** エラーメッセージ */
  error_message?: string | null;
}

/** ストーリーテラー LLM メタデータ（使用モデル・トークン数・エラー情報） */
export interface StorytellerLlmMetadata {
  storyteller: string;
  display_name: string;
  model_id: string;
  actual_model?: string | null;
  prompt_tokens?: number | null;
  output_tokens?: number | null;
  finish_reason?: string | null;
  error_code?: string | null;
  error_message?: string | null;
  has_content?: boolean;
}

/** 検索活動ログエントリ（再現性条件の担保） */
export interface SearchLogEntry {
  /** 記録タイムスタンプ（ISO 8601） */
  timestamp: string;
  /** 使用ツール */
  tool: "search_archives" | "search_newspapers";
  /** 系統的キーワード（固有名詞・日付・場所） */
  reference_keywords: string[];
  /** 探索的キーワード（創造的関連語・類義語） */
  exploratory_keywords: string[];
  /** 検索言語（ISO 639-1） */
  language: string | null;
  /** API 別統計 */
  sources_searched: Record<string, { total_hits: number; documents_returned: number }>;
  /** 返却ドキュメント総数 */
  total_documents: number;
  /** 検索日付範囲 */
  date_range?: { start: string | null; end: string | null };
  /** リンク検証結果 */
  link_validation: {
    total_checked: number;
    reachable: number;
    unreachable: number;
    removed_count: number;
  };
  /** フォールバック検索が使用されたか */
  fallback_used: boolean;
}

export interface FirestoreMystery extends MysteryReport {
  /** スキーマバージョン: 1 = legacy (*_ja/*_en), 2 = translations map */
  schema_version?: number;
  /** 記事を執筆したストーリーテラー（LLM）の識別子 */
  storyteller?: string;
  /** ストーリーテラー LLM メタデータ（モデル情報 + トークン使用量） */
  storyteller_llm_metadata?: StorytellerLlmMetadata;
  /** 検索活動ログ（再現性条件の担保） */
  search_log?: SearchLogEntry[];
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
  /** Armchair Polymath の統合分析レポート全文 */
  mystery_report?: string;
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

  /** 多言語翻訳 map (言語コード → 翻訳済みコンテンツ) */
  translations?: Record<string, TranslatedContent>;

  // === 日本語翻訳フィールド（レガシー、translations map に移行済み） ===
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

/** プロダクトデザイン生成ステータス */
export type DesignStatus = "designing" | "design_ready" | "rendering" | "render_ready" | "error";

/** プロダクトタイプ */
export type ProductType = "tshirt" | "mug";

/** デザインスタイルリファレンス */
export type DesignStyleReference = "fact" | "folklore";

/** Imagen プロンプト */
export interface ImagenPrompts {
  /** メインビジュアルプロンプト */
  background: string;
  /** 装飾要素プロンプト（オプション） */
  decorative?: string;
}

/** 単一製品のデザイン提案 */
export interface ProductDesignProposal {
  /** 製品タイプ */
  product_type: ProductType;
  /** アスペクト比 */
  aspect_ratio: "1:1" | "16:9";
  /** キャッチフレーズ（英語） */
  catchphrase_en: string;
  /** キャッチフレーズ（日本語） */
  catchphrase_ja: string;
  /** カラーパレット（hex コード配列） */
  color_palette: string[];
  /** フォント提案 */
  font_suggestion: string;
  /** 構図の説明 */
  composition: string;
  /** Imagen プロンプト */
  imagen_prompts: ImagenPrompts;
  /** スタイルリファレンス */
  style_reference: DesignStyleReference;
  /** ネガティブプロンプト */
  negative_prompt?: string;
}

/** 生成されたデザインアセット */
export interface DesignAsset {
  /** 製品タイプ */
  product_type: ProductType;
  /** レイヤー（background / decorative） */
  layer: string;
  /** GCS パス */
  gcs_path: string;
  /** 公開 URL */
  public_url: string;
  /** アスペクト比 */
  aspect_ratio: string;
}

/**
 * デザインドキュメント（product_designs コレクション）
 * mystery_id でミステリー記事とリンク
 */
export interface FirestoreDesign {
  /** Design ドキュメント ID */
  design_id: string;
  /** リンク先ミステリー記事 ID */
  mystery_id: string;
  /** 記事タイトル（非正規化、表示用） */
  mystery_title: string;
  /** リージョン（国コード） */
  region: string;
  /** 生成ステータス */
  status: DesignStatus;
  /** 管理者のカスタム指示 */
  custom_instructions?: string;
  /** デザイン提案 */
  proposal?: { products: ProductDesignProposal[] };
  /** 生成されたアセット */
  assets?: DesignAsset[];
  /** パイプライン実行 ID */
  pipeline_run_id?: string;
  /** 作成日時 */
  created_at: Date;
  /** 更新日時 */
  updated_at: Date;
  /** エラーメッセージ */
  error_message?: string | null;
}

/**
 * パイプライン実行ステータス
 */
export type PipelineRunStatus = "running" | "completed" | "error";

/**
 * パイプライン種別
 */
export type PipelineRunType = "blog" | "translate" | "podcast" | "design" | "design_render";

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
  librarian: "資料収集",
  librarian_en: "資料収集（英語）",
  librarian_es: "資料収集（スペイン語）",
  librarian_de: "資料収集（ドイツ語）",
  scholar: "学際分析",
  scholar_en: "学際分析（英語）",
  scholar_es: "学際分析（スペイン語）",
  scholar_de: "学際分析（ドイツ語）",
  scholar_en_debate: "討論（英語）",
  scholar_es_debate: "討論（スペイン語）",
  scholar_de_debate: "討論（ドイツ語）",
  armchair_polymath: "統合分析",
  cross_reference_scholar: "統合分析",
  storyteller: "物語生成",
  translator: "翻訳",
  translator_ja: "翻訳（日本語）",
  translator_es: "翻訳（スペイン語）",
  translator_de: "翻訳（ドイツ語）",
  debate_loop: "討論",
  parallel_translators: "翻訳",
  scriptwriter: "脚本作成",
  podcast_translator_ja: "脚本翻訳（日本語）",
  illustrator: "画像生成",
  producer: "音声生成",
  publisher: "公開処理",
  alchemist: "デザイン企画",
  alchemist_renderer: "デザインレンダリング",
};

/**
 * ストーリーテラー（LLM）の表示名マッピング
 */
export const STORYTELLER_DISPLAY_NAMES: Record<string, string> = {
  claude: "Claude Sonnet 4.6",
  gemini: "Gemini 3 Pro",
  gpt: "GPT-4.1",
  llama: "Llama 4 Maverick",
  deepseek: "DeepSeek V3.2",
  mistral: "Mistral Large",
};
