"""AggregatorAgent — API Librarian の検索結果を言語別に集約する。

LLM を介さず、セッション状態の raw_search_results* キーを動的スキャンし、
ドキュメントを言語別にグループ化して collected_documents_{lang} に書き込む。

また active_languages（ドキュメント数ランキング）をステートに書き込み、
後段の DynamicScholarBlock が参照する。
"""

import logging
from collections import defaultdict
from collections.abc import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event, EventActions
from google.genai import types

from shared.language_names import get_language_name
from shared.state_keys import (
    ACTIVE_LANGUAGES,
    FULLTEXT_METRICS,
    RAW_SEARCH_RESULTS,
    SELECTED_LANGUAGES,
    collected_documents_key,
)

logger = logging.getLogger(__name__)


class AggregatorAgent(BaseAgent):
    """API Librarian 出力を言語別に集約する LLM 不使用エージェント。

    raw_search_results* キーを動的スキャンし、
    各ドキュメントの language フィールドに基づいて言語別にグループ化する。
    """

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state

        # raw_search_results* キーを動的スキャン
        docs_by_lang: dict[str, list[dict]] = defaultdict(list)

        for key in list(state.keys()):
            if not key.startswith(RAW_SEARCH_RESULTS):
                continue
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

        # 全文メトリクス算出
        fulltext_metrics = _compute_fulltext_metrics(docs_by_lang, active_languages)

        global_fulltext = fulltext_metrics["fulltext_documents"]

        # state_delta を構築
        state_delta: dict[str, object] = {}

        for lang in active_languages:
            docs = docs_by_lang[lang]
            lang_stats = fulltext_metrics["by_language"].get(lang, {})
            text = _format_documents(
                lang,
                docs,
                lang_fulltext=lang_stats.get("fulltext", 0),
                lang_metadata_only=lang_stats.get("metadata_only", 0),
                global_fulltext=global_fulltext,
            )
            state_delta[collected_documents_key(lang)] = text

        state_delta[ACTIVE_LANGUAGES] = active_languages
        state_delta[FULLTEXT_METRICS] = fulltext_metrics

        # selected_languages を active_languages で更新（Scholar/debate layer 互換）
        if active_languages:
            state_delta[SELECTED_LANGUAGES] = active_languages

        total_docs = sum(len(d) for d in docs_by_lang.values())
        ft = fulltext_metrics["fulltext_documents"]
        summary = (
            f"Aggregated {total_docs} documents across "
            f"{len(active_languages)} languages: "
            f"{', '.join(f'{lang}({len(docs_by_lang[lang])})' for lang in active_languages)}"
            f" Full text: {ft}/{total_docs}"
        )
        logger.info(
            "Aggregator: %s",
            summary,
            extra={
                "active_languages": active_languages,
                "total_documents": total_docs,
                "fulltext_documents": ft,
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


def _deduplicate_docs(docs: list[dict]) -> list[dict]:
    """URL ベースでドキュメントを重複除去する。"""
    seen_urls: set[str] = set()
    unique: list[dict] = []
    for doc in docs:
        url = doc.get("source_url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(doc)
        elif not url:
            unique.append(doc)
    return unique


def _compute_fulltext_metrics(
    docs_by_lang: dict[str, list[dict]],
    active_languages: list[str],
) -> dict:
    """全文テキスト取得メトリクスを算出する。

    Returns:
        {
            "total_documents": int,
            "fulltext_documents": int,
            "metadata_only_documents": int,
            "by_language": {
                lang: {"total": int, "fulltext": int, "metadata_only": int},
                ...
            }
        }
    """
    by_language: dict[str, dict[str, int]] = {}
    total = 0
    total_ft = 0

    for lang in active_languages:
        docs = _deduplicate_docs(docs_by_lang[lang])
        ft = sum(1 for d in docs if d.get("raw_text"))
        mo = len(docs) - ft
        by_language[lang] = {"total": len(docs), "fulltext": ft, "metadata_only": mo}
        total += len(docs)
        total_ft += ft

    return {
        "total_documents": total,
        "fulltext_documents": total_ft,
        "metadata_only_documents": total - total_ft,
        "by_language": by_language,
    }


def _format_documents(
    lang: str,
    docs: list[dict],
    *,
    lang_fulltext: int = 0,
    lang_metadata_only: int = 0,
    global_fulltext: int = 0,
) -> str:
    """ドキュメントリストを Scholar が読める形式にフォーマットする。

    重複 URL を除去し、各ドキュメントのメタデータとテキスト抜粋を
    構造化テキストとして整形する。
    """
    unique_docs = _deduplicate_docs(docs)

    lang_name = get_language_name(lang)

    if not unique_docs:
        return f"NO_DOCUMENTS_FOUND: No {lang_name}-language documents collected."

    lines = [
        f"# Collected Documents ({lang_name}) — {len(unique_docs)} documents"
        f" ({lang_fulltext} with full text, {lang_metadata_only} metadata-only)\n"
    ]

    # 全言語合計の全文ドキュメントが 1-2 件の場合、限定的証拠の注記
    if 0 < global_fulltext <= 2:
        lines.append(
            f"> **Note**: Only {global_fulltext} document(s) with full text available "
            f"across all languages. Analysis may be limited.\n"
        )

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
        ref_matched = doc.get("reference_keywords_matched")
        if isinstance(ref_matched, list):
            if ref_matched:
                ref_str = ", ".join(ref_matched)
                lines.append(f"- **Reference keywords matched**: {ref_str}")
            else:
                lines.append("- **Reference keywords matched**: (none — exploratory match only)")
        if doc.get("raw_text"):
            # テキスト抜粋は5000文字に制限（fulltext_extraction.max_output_chars と一致）
            excerpt = str(doc["raw_text"])[:5000]
            if len(str(doc["raw_text"])) > 5000:
                excerpt += "..."
            lines.append(f"- **Excerpt**: {excerpt}")
        else:
            lines.append("- **Excerpt**: [metadata only — full text not available]")
        lines.append("")  # ドキュメント間の空行

    return "\n".join(lines)


def create_aggregator() -> AggregatorAgent:
    """AggregatorAgent を新規生成する。"""
    return AggregatorAgent(
        name="aggregator",
        description=(
            "Aggregates search results from all API Librarians by document language. "
            "Dynamically scans raw_search_results* keys. "
            "Writes collected_documents_{lang} for each language found. "
            "Deterministic execution without LLM."
        ),
    )
