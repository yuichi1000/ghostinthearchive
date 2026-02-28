"""セッション状態キーのランタイム定数。

state.get("mystery_report") 等のマジックストリングを定数化し、
typo によるサイレントバグを防止する。

注意:
- output_key="mystery_report" 等の ADK パラメータはここの定数に置換しない
  （ADK 内部で文字列として扱われるため）
- instruction 内の {mystery_report} プレースホルダーも置換しない
  （LLM が読むテンプレート変数であり、Python 定数参照ではない）
- ドキュメント/依存関係図は shared/state_registry.py を参照
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 固定キー
# ---------------------------------------------------------------------------
MYSTERY_REPORT = "mystery_report"
CREATIVE_CONTENT = "creative_content"
STRUCTURED_REPORT = "structured_report"
DEBATE_WHITEBOARD = "debate_whiteboard"
VISUAL_ASSETS = "visual_assets"
IMAGE_METADATA = "image_metadata"
PUBLISHED_EPISODE = "published_episode"
ARCHIVE_IMAGES = "archive_images"
SELECTED_LANGUAGES = "selected_languages"
ACTIVE_LANGUAGES = "active_languages"
RAW_SEARCH_RESULTS = "raw_search_results"
PUBLISHED_MYSTERY_ID = "published_mystery_id"
INVESTIGATION_QUERY = "investigation_query"
PIPELINE_RUN_ID = "pipeline_run_id"
STORYTELLER_LLM_METADATA = "storyteller_llm_metadata"
WORD_COUNT_TIER = "_word_count_tier"
SEARCH_LOG = "search_log"
AGENT_TOKEN_LOG = "_agent_token_log"


# ---------------------------------------------------------------------------
# 動的キー（言語/API サフィックス付き）
# ---------------------------------------------------------------------------
def collected_documents_key(lang: str) -> str:
    """Aggregator が集約した資料キー（言語別）。"""
    return f"collected_documents_{lang}"


def scholar_analysis_key(lang: str) -> str:
    """Scholar 分析レポートキー（言語別）。"""
    return f"scholar_analysis_{lang}"


def translation_result_key(lang: str) -> str:
    """Translator 翻訳結果キー（言語別）。"""
    return f"translation_result_{lang}"


def raw_search_results_key(identifier: str) -> str:
    """Librarian 検索結果キー（API/言語別）。"""
    return f"raw_search_results_{identifier}"
