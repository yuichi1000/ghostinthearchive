"""AggregatorAgent — API Librarian の検索結果を言語別に集約する。

LLM を介さず、セッション状態の raw_search_results から
ドキュメントを言語別にグループ化し、collected_documents_{lang} に
Scholar が読める形式でテキストを書き込む。

また active_languages（ドキュメント数ランキング）をステートに書き込み、
後段の DynamicScholarBlock（PR 3）が参照する。
"""

import logging
from collections import defaultdict
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event, EventActions
from google.genai import types

logger = logging.getLogger(__name__)

# 言語名マッピング（ログ・ヘッダー表示用）
_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "ja": "Japanese",
    "nl": "Dutch",
    "pt": "Portuguese",
}

# 収集対象の raw_search_results キーサフィックス
_KNOWN_LANGUAGES = ["en", "de", "es", "fr", "ja", "nl", "pt"]


class AggregatorAgent(BaseAgent):
    """API Librarian 出力を言語別に集約する LLM 不使用エージェント。

    raw_search_results* からドキュメントを抽出し、
    各ドキュメントの language フィールドに基づいて言語別にグループ化する。
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state

        # 全 raw_search_results を収集（既知キーパターンを安全にチェック）
        docs_by_lang: dict[str, list[dict]] = defaultdict(list)

        keys_to_check = ["raw_search_results"] + [
            f"raw_search_results_{lang}" for lang in _KNOWN_LANGUAGES
        ]

        for key in keys_to_check:
            value = state.get(key)
            if not value or not isinstance(value, list):
                continue
            for result_entry in value:
                if not isinstance(result_entry, dict):
                    continue
                for doc in result_entry.get("documents", []):
                    lang = doc.get("language", "en")
                    docs_by_lang[lang].append(doc)

        # 言語別ドキュメント数でランキング（降順）
        active_languages = sorted(
            docs_by_lang.keys(),
            key=lambda lang: len(docs_by_lang[lang]),
            reverse=True,
        )

        # state_delta を構築
        state_delta: dict[str, object] = {}

        for lang in active_languages:
            docs = docs_by_lang[lang]
            text = _format_documents(lang, docs)
            state_delta[f"collected_documents_{lang}"] = text

        state_delta["active_languages"] = active_languages

        # selected_languages を active_languages で更新（Scholar/debate layer 互換）
        if active_languages:
            state_delta["selected_languages"] = active_languages

        total_docs = sum(len(d) for d in docs_by_lang.values())
        summary = (
            f"Aggregated {total_docs} documents across "
            f"{len(active_languages)} languages: "
            f"{', '.join(f'{lang}({len(docs_by_lang[lang])})' for lang in active_languages)}"
        )
        logger.info(
            "Aggregator: %s",
            summary,
            extra={
                "active_languages": active_languages,
                "total_documents": total_docs,
                "docs_per_language": {
                    lang: len(docs_by_lang[lang]) for lang in active_languages
                },
            },
        )

        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            branch=ctx.branch,
            content=types.Content(
                role="model", parts=[types.Part(text=summary)]
            ),
            actions=EventActions(state_delta=state_delta),
        )


def _format_documents(lang: str, docs: list[dict]) -> str:
    """ドキュメントリストを Scholar が読める形式にフォーマットする。

    重複 URL を除去し、各ドキュメントのメタデータとテキスト抜粋を
    構造化テキストとして整形する。
    """
    # URL 重複除去
    seen_urls: set[str] = set()
    unique_docs: list[dict] = []
    for doc in docs:
        url = doc.get("source_url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_docs.append(doc)
        elif not url:
            unique_docs.append(doc)

    if not unique_docs:
        lang_name = _LANGUAGE_NAMES.get(lang, lang)
        return f"NO_DOCUMENTS_FOUND: No {lang_name}-language documents collected."

    lang_name = _LANGUAGE_NAMES.get(lang, lang)
    lines = [
        f"# Collected Documents ({lang_name}) — {len(unique_docs)} documents\n"
    ]

    for i, doc in enumerate(unique_docs, 1):
        lines.append(f"## [{i}] {doc.get('title', 'Untitled')}")
        if doc.get("date"):
            lines.append(f"- **Date**: {doc['date']}")
        source_type = doc.get("source_type", "unknown")
        lines.append(f"- **Archive**: {source_type}")
        lines.append(f"- **URL**: {doc.get('source_url', 'N/A')}")
        if doc.get("location"):
            lines.append(f"- **Location**: {doc['location']}")
        if doc.get("summary"):
            lines.append(f"- **Summary**: {doc['summary']}")
        matched = doc.get("keywords_matched")
        if matched:
            kw_str = ", ".join(matched) if isinstance(matched, list) else str(matched)
            lines.append(f"- **Keywords matched**: {kw_str}")
        if doc.get("raw_text"):
            # テキスト抜粋は500文字に制限
            excerpt = str(doc["raw_text"])[:500]
            if len(str(doc["raw_text"])) > 500:
                excerpt += "..."
            lines.append(f"- **Excerpt**: {excerpt}")
        lines.append("")  # ドキュメント間の空行

    return "\n".join(lines)


def create_aggregator() -> AggregatorAgent:
    """AggregatorAgent を新規生成する。"""
    return AggregatorAgent(
        name="aggregator",
        description=(
            "Aggregates search results from all API Librarians by document language. "
            "Writes collected_documents_{lang} for each language found. "
            "Deterministic execution without LLM."
        ),
    )
