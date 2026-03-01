"""LLM-facing tool functions for the Scholar Agent.

These functions provide structured report storage via session state
for downstream agents, plus evidence grounding against raw search results.
"""

import json
import logging
from typing import Any

from google.adk.tools.tool_context import ToolContext

from shared.state_keys import (
    APPROVED_ARCHIVE_IMAGES,
    ARCHIVE_IMAGES,
    RAW_SEARCH_RESULTS,
    STRUCTURED_REPORT,
    WORD_COUNT_TIER,
)

logger = logging.getLogger(__name__)


def _validate_evidence(evidence: dict, label: str) -> list[str]:
    """evidence オブジェクトの必須フィールドを検証する。

    Args:
        evidence: evidence オブジェクト（source_url, relevant_excerpt 等）
        label: ログ用ラベル（例: "evidence_a", "additional_evidence[0]"）

    Returns:
        警告メッセージのリスト（問題がなければ空リスト）
    """
    warnings: list[str] = []
    if not evidence.get("relevant_excerpt", "").strip():
        warnings.append(f"{label}: relevant_excerpt is empty or missing")
    if not evidence.get("source_url", "").strip():
        warnings.append(f"{label}: source_url is empty or missing")
    return warnings


def _build_url_index(tool_context: ToolContext) -> dict[str, dict[str, Any]]:
    """raw_search_results から URL→文書メタデータのマッピングを構築する。

    raw_search_results と raw_search_results_{lang} の両方から文書を収集し、
    source_url をキーとする辞書を返す。
    """
    url_index: dict[str, dict[str, Any]] = {}
    state = tool_context.state

    # ベースキー
    base = state.get(RAW_SEARCH_RESULTS)
    if base and isinstance(base, list):
        for result in base:
            if isinstance(result, dict):
                for doc in result.get("documents", []):
                    url = doc.get("source_url", "")
                    if url:
                        url_index[url] = doc

    # 言語別キー
    state_dict = state.to_dict() if hasattr(state, "to_dict") else state
    for key in list(state_dict.keys()):
        if key.startswith(RAW_SEARCH_RESULTS + "_") and key != RAW_SEARCH_RESULTS:
            lang_results = state.get(key)
            if lang_results and isinstance(lang_results, list):
                for result in lang_results:
                    if isinstance(result, dict):
                        for doc in result.get("documents", []):
                            url = doc.get("source_url", "")
                            if url:
                                url_index[url] = doc

    return url_index


def _validate_evidence_grounding(
    report_data: dict, tool_context: ToolContext
) -> list[str]:
    """証拠を raw_search_results と照合し、正確性を検証・修正する。

    1. URL 照合: evidence の source_url が raw_search_results に存在するか確認
       → 不在なら warning（ハルシネーションの可能性）
    2. メタデータ修正: URL 一致した場合、raw_search_results の title / date で
       evidence の source_title / source_date を上書き（LLM の転記ミスを修正）
    3. ソース識別: raw_search_results の source_type を evidence に
       archive_source として付与（ログ・デバッグ用）

    Returns: warning メッセージのリスト
    """
    url_index = _build_url_index(tool_context)
    if not url_index:
        return []

    warnings: list[str] = []

    # 検証対象の evidence 項目を収集
    evidence_items: list[tuple[str, dict]] = []
    for key in ("evidence_a", "evidence_b"):
        ev = report_data.get(key)
        if ev and isinstance(ev, dict):
            evidence_items.append((key, ev))

    additional = report_data.get("additional_evidence")
    if additional and isinstance(additional, list):
        for i, ev in enumerate(additional):
            if isinstance(ev, dict):
                evidence_items.append((f"additional_evidence[{i}]", ev))

    for label, ev in evidence_items:
        source_url = ev.get("source_url", "")
        if not source_url:
            continue

        raw_doc = url_index.get(source_url)
        if raw_doc:
            # メタデータを raw データで上書き（LLM 転記ミス修正）
            raw_title = raw_doc.get("title")
            if raw_title:
                ev["source_title"] = raw_title
            raw_date = raw_doc.get("date")
            if raw_date:
                ev["source_date"] = raw_date
            # ソース種別を付与
            raw_source_type = raw_doc.get("source_type")
            if raw_source_type:
                ev["archive_source"] = raw_source_type

            # キーワード妥当性チェック
            kw_matched = raw_doc.get("keywords_matched", [])
            ev["_kw_match_count"] = len(kw_matched)
            if not kw_matched:
                warnings.append(
                    f"{label}: キーワード無一致 — false positive の可能性 "
                    f"(title: {raw_doc.get('title', 'unknown')})"
                )
        else:
            ev["_ungrounded"] = True
            warnings.append(
                f"{label}: source_url not found in collected documents"
            )

    return warnings


def save_structured_report(
    report_json: str,
    tool_context: ToolContext,
) -> str:
    """Save a structured analysis report to session state.

    Called by the Scholar Agent after completing analysis to store
    structured data (evidence, hypothesis, etc.) directly in session
    state, bypassing LLM text interpretation for downstream agents.

    前提条件:
    - get_document_inventory が事前に呼ばれていること（_inventory_consulted フラグ）

    evidence バリデーション:
    - evidence_a / evidence_b: 空 excerpt にはフォールバック文を挿入（構造上必須のため除外しない）
    - additional_evidence: 空 excerpt の項目はフィルタリング（除外）

    証拠グラウンディング:
    - raw_search_results と照合し、メタデータを自動修正
    - URL 不一致の場合は警告

    Args:
        report_json: JSON string containing the structured report with fields:
            - evidence_a: Primary evidence object (source_url, source_date, etc.)
            - evidence_b: Contrasting evidence object
            - additional_evidence: List of additional evidence objects
            - hypothesis: Primary hypothesis string
            - alternative_hypotheses: List of alternative hypothesis strings
            - classification: 3-letter classification code
            - country_code: 2-letter ISO 3166-1 alpha-2 country code
            - region_code: 3-5 letter IATA region code
            - title: Mystery title
            - summary: Brief summary
            - discrepancy_detected: Description of the discrepancy
            - discrepancy_type: Type of discrepancy
            - confidence_level: high/medium/low
            - historical_context: Historical context object
            - research_questions: List of research questions
            - story_hooks: List of story hooks
        tool_context: ADK tool context for session state access.

    Returns:
        JSON string with save status and warnings.
    """
    # inventory 参照チェック
    if not tool_context.state.get("_inventory_consulted"):
        return json.dumps(
            {
                "status": "error",
                "error": "get_document_inventory must be called before saving the report. "
                "Review ALL available documents across ALL archives before selecting evidence.",
            },
            ensure_ascii=False,
        )

    # 語数検証チェック
    if not tool_context.state.get("_word_count_verified"):
        tier = tool_context.state.get(
            WORD_COUNT_TIER, {"min_words": 5000, "max_words": 10000}
        )
        return json.dumps(
            {
                "status": "error",
                "error": f"count_words must be called with min_words={tier['min_words']}, "
                f"max_words={tier['max_words']} "
                "and the report must be within range before saving. "
                "Call count_words first, then revise if needed.",
            },
            ensure_ascii=False,
        )

    try:
        report_data = json.loads(report_json)
    except json.JSONDecodeError as e:
        return json.dumps(
            {"status": "error", "error": f"Invalid JSON: {e}"},
            ensure_ascii=False,
        )

    # evidence バリデーション
    warnings: list[str] = []

    # evidence_a / evidence_b: 空 excerpt にはフォールバック文を挿入
    for key in ("evidence_a", "evidence_b"):
        ev = report_data.get(key)
        if ev and isinstance(ev, dict):
            if not ev.get("relevant_excerpt", "").strip():
                source_title = ev.get("source_title", "unknown source")
                ev["relevant_excerpt"] = f"[See original source: {source_title}]"
                warnings.append(f"{key}: empty relevant_excerpt replaced with fallback")
            warnings.extend(_validate_evidence(ev, key))

    # additional_evidence: 空 excerpt の項目をフィルタリング
    additional = report_data.get("additional_evidence")
    if additional and isinstance(additional, list):
        filtered = []
        for i, ev in enumerate(additional):
            if not isinstance(ev, dict):
                continue
            excerpt = ev.get("relevant_excerpt", "").strip()
            if excerpt:
                filtered.append(ev)
            else:
                warnings.append(
                    f"additional_evidence[{i}]: removed (empty relevant_excerpt)"
                )
        report_data["additional_evidence"] = filtered

    # 証拠グラウンディング検証（URL 照合 + メタデータ修正）
    grounding_warnings = _validate_evidence_grounding(report_data, tool_context)
    warnings.extend(grounding_warnings)

    # additional_evidence: キーワード無一致の項目を除外（フィールドが存在する場合のみ）
    additional = report_data.get("additional_evidence")
    if additional is not None:
        before_kw_filter = len(additional)
        additional = [ev for ev in additional if ev.pop("_kw_match_count", 1) > 0]
        kw_removed = before_kw_filter - len(additional)
        if kw_removed:
            warnings.append(f"additional_evidence: {kw_removed} 件除外 (キーワード無一致)")
        report_data["additional_evidence"] = additional

    # additional_evidence: _ungrounded 項目を除外
    additional = report_data.get("additional_evidence")
    if additional is not None:
        before_ungrounded = len(additional)
        additional = [ev for ev in additional if not ev.get("_ungrounded")]
        ungrounded_removed = before_ungrounded - len(additional)
        if ungrounded_removed:
            warnings.append(
                f"additional_evidence: {ungrounded_removed} 件除外 (URL 不一致)"
            )
        report_data["additional_evidence"] = additional

    # evidence_a / evidence_b: _ungrounded の場合フォールバック挿入
    for key in ("evidence_a", "evidence_b"):
        ev = report_data.get(key)
        if ev and isinstance(ev, dict) and ev.get("_ungrounded"):
            source_title = ev.get("source_title", "unknown source")
            ev["relevant_excerpt"] = f"[See original source: {source_title}]"
            warnings.append(
                f"{key}: URL 不一致 — excerpt をフォールバックに置換"
            )

    # evidence_a / evidence_b の一時フィールドをクリーンアップ
    for key in ("evidence_a", "evidence_b"):
        ev = report_data.get(key)
        if ev and isinstance(ev, dict):
            ev.pop("_kw_match_count", None)
            ev.pop("_ungrounded", None)

    # additional_evidence の一時フィールドをクリーンアップ
    additional = report_data.get("additional_evidence")
    if additional is not None:
        for ev in additional:
            ev.pop("_ungrounded", None)

    # タグバリデーション
    tags = report_data.get("tags")
    if tags is not None:
        if not isinstance(tags, list):
            warnings.append("tags: not a list, removed")
            del report_data["tags"]
        else:
            # 小文字正規化、空文字フィルタ、重複排除（順序保持）
            normalized: list[str] = []
            seen: set[str] = set()
            for tag in tags:
                if not isinstance(tag, str):
                    continue
                t = tag.strip().lower()
                if t and t not in seen:
                    normalized.append(t)
                    seen.add(t)
            # 最大10個に制限
            report_data["tags"] = normalized[:10]

    # approved_image_urls → archive_images と照合してフィルタリング
    approved_urls = report_data.pop("approved_image_urls", None)
    if approved_urls is not None:
        archive_images = tool_context.state.get(ARCHIVE_IMAGES, [])
        approved_set = set(approved_urls)
        approved_images = [
            img for img in archive_images
            if img.get("source_url") in approved_set
        ]
        tool_context.state[APPROVED_ARCHIVE_IMAGES] = approved_images
    else:
        # 後方互換: フィールド未指定時は全画像を承認
        tool_context.state[APPROVED_ARCHIVE_IMAGES] = tool_context.state.get(
            ARCHIVE_IMAGES, []
        )
        warnings.append(
            "approved_image_urls not provided — all archive_images approved by default"
        )

    # Store structured report in session state
    tool_context.state[STRUCTURED_REPORT] = report_data

    return json.dumps(
        {
            "status": "success",
            "message": "Structured report saved to session state",
            "fields_saved": list(report_data.keys()),
            "warnings": warnings,
        },
        ensure_ascii=False,
    )
