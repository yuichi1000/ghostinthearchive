"""LLM-facing tool functions for the Publisher Agent.

Writes mystery data to Firestore and uploads images to Cloud Storage.
Supports both Firebase emulator (local dev) and production environments.

When tool_context is available, reads structured data from session state
to reduce dependency on LLM text interpretation for critical fields.
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

from google.adk.tools.tool_context import ToolContext

from shared.constants import (
    SCHEMA_VERSION,
    STATUS_PENDING,
    STATUS_PUBLISHED,
    TRANSLATION_LANGUAGES,
)
from shared.firestore import get_firestore_client
from shared.language_validator import validate_translation_language
from shared.state_keys import (
    ACTIVE_LANGUAGES,
    CREATIVE_CONTENT,
    IMAGE_METADATA,
    MYSTERY_REPORT,
    PUBLISHED_MYSTERY_ID,
    SEARCH_LOG,
    STORYTELLER_LLM_METADATA,
    STRUCTURED_REPORT,
    collected_documents_key,
    scholar_analysis_key,
    translation_result_key,
)

from mystery_agents.tools.scholar_tools import _build_url_index
from mystery_agents.tools.search_metadata import get_search_metadata as _get_search_metadata

from .image_upload import _upload_images_internal
from .publisher_utils import _extract_json_from_text, _generate_mystery_id

logger = logging.getLogger(__name__)


def _audit_evidence_relevance(data: dict, tool_context: ToolContext) -> None:
    """証拠の妥当性を監査ログに記録する（ブロッキングなし）。"""
    url_index = _build_url_index(tool_context)
    if not url_index:
        return
    for key in ("evidence_a", "evidence_b"):
        ev = data.get(key, {})
        url = ev.get("source_url", "")
        raw = url_index.get(url)
        if raw and not raw.get("keywords_matched"):
            logger.warning(
                "証拠妥当性監査: %s はキーワード無一致 (title: %s)",
                key, raw.get("title", "unknown"),
            )


def publish_mystery(
    mystery_json: str,
    visual_assets_json: str = "",
    tool_context: Optional[ToolContext] = None,
) -> str:
    """Save a mystery document to Firestore with integrated image upload.

    Writes the complete mystery data to the 'mysteries' collection in Firestore.
    Automatically generates mystery_id from classification, country_code, and region_code.
    When visual_assets_json is provided, uploads images to Cloud Storage using the
    generated mystery_id, ensuring ID consistency between images and Firestore.

    When tool_context is available, reads structured data from session state:
    - structured_report: Accurate evidence, hypothesis, classification data from Scholar
    - creative_content: Blog narrative (narrative_content) — LLM にコピーさせず state から直接取得
    - collected_documents_en: Raw search metadata (raw_data) — LLM にコピーさせず state から直接取得
    - image_metadata: Accurate file paths and variant info from Illustrator
    - translation_result_{lang}: 6-language translations

    Args:
        mystery_json: JSON string containing the mystery data.
            Required fields for ID generation:
            - classification: 3-letter code (HIS, FLK, ANT, OCC, URB, CRM, REL, LOC)
            - country_code: 2-letter ISO 3166-1 alpha-2 country code (US, GB, JP, etc.)
            - region_code: 3-5 letter IATA region code (BOS, LHR, NRT, etc.)

            narrative_content と raw_data は mystery_json に含める必要なし
            （tool_context から自動取得される）。

        visual_assets_json: Optional JSON string from generate_image tool output.
            When provided, images are uploaded to Cloud Storage and the resulting
            URLs are set in data["images"]. Expected format:
            {"filepath": "...", "variants": [{"filepath": "...", "label": "sm"}, ...]}

        tool_context: ADK tool context for session state access.

    Returns:
        JSON string with status and document ID.
    """
    try:
        data = json.loads(mystery_json, strict=False)

        db = get_firestore_client()

        # Overlay structured report from session state (more accurate than LLM text)
        if tool_context is not None:
            structured_report = tool_context.state.get(STRUCTURED_REPORT)
            if structured_report and isinstance(structured_report, dict):
                # Use structured data for critical fields, preferring state over LLM text
                for key in (
                    "classification", "country_code", "region_code",
                    "evidence_a", "evidence_b", "additional_evidence",
                    "hypothesis", "alternative_hypotheses",
                    "confidence_level", "discrepancy_detected", "discrepancy_type",
                    "historical_context", "research_questions", "story_hooks",
                    "title", "summary",
                    "source_coverage", "academic_coverage", "confidence_rationale",
                ):
                    if key in structured_report:
                        data[key] = structured_report[key]

            # narrative_content: creative_content セッション状態から直接読み取り
            creative_content = tool_context.state.get(CREATIVE_CONTENT)
            if creative_content and isinstance(creative_content, str):
                if not any(marker in creative_content for marker in ("NO_CONTENT", "NO_DOCUMENTS_FOUND")):
                    data["narrative_content"] = creative_content

            # narrative_content からアーカイブ画像URLを抽出して images.inserts に保存
            if data.get("narrative_content"):
                md_images = re.findall(r'!\[.*?\]\((https?://[^)]+)\)', data["narrative_content"])
                if md_images:
                    images_dict = data.get("images", {})
                    images_dict["inserts"] = md_images
                    data["images"] = images_dict

            # raw_data: collected_documents_en セッション状態から直接読み取り
            collected_docs = tool_context.state.get(collected_documents_key("en"))
            if collected_docs:
                data["raw_data"] = collected_docs if isinstance(collected_docs, str) else str(collected_docs)

            # 各言語の Scholar 分析を multilingual_analysis として保存
            # active_languages を参照し、動的に検出された全言語をカバーする
            multilingual = {}
            active_langs = tool_context.state.get(ACTIVE_LANGUAGES, [])
            for lang in active_langs:
                analysis = tool_context.state.get(scholar_analysis_key(lang))
                if analysis and "INSUFFICIENT_DATA" not in str(analysis):
                    multilingual[lang] = str(analysis)
            # Multilingual Scholar の分析も保存
            ml_analysis = tool_context.state.get(scholar_analysis_key("multilingual"))
            if ml_analysis and "INSUFFICIENT_DATA" not in str(ml_analysis):
                multilingual["multilingual"] = str(ml_analysis)
            if multilingual:
                data["multilingual_analysis"] = multilingual
                data["languages_analyzed"] = list(multilingual.keys())

            # mystery_report: Armchair Polymath の統合分析レポート全文を保存
            mystery_report = tool_context.state.get(MYSTERY_REPORT)
            if mystery_report and isinstance(mystery_report, str):
                if "INSUFFICIENT_DATA" not in mystery_report:
                    data["mystery_report"] = mystery_report

            # source_coverage の API フィールドを raw_search_results から programmatic に上書き
            # （LLM の手動転記ではなくセッション状態から直接生成）
            search_meta_json = _get_search_metadata(tool_context)
            search_meta = json.loads(search_meta_json)
            if search_meta.get("status") == "ok":
                sc = data.get("source_coverage")
                if sc and isinstance(sc, dict):
                    sc["apis_searched"] = search_meta["apis_searched"]
                    sc["apis_with_results"] = search_meta["apis_with_results"]
                    sc["apis_without_results"] = search_meta["apis_without_results"]
                else:
                    sc = {
                        "apis_searched": search_meta["apis_searched"],
                        "apis_with_results": search_meta["apis_with_results"],
                        "apis_without_results": search_meta["apis_without_results"],
                    }
                    data["source_coverage"] = sc
                # API エラー情報を記録（エラーがある場合のみ）
                if search_meta.get("errors"):
                    sc["api_errors"] = search_meta["errors"]

            # 全言語の翻訳結果を translations map に収集
            translations: dict[str, dict] = {}
            rejected_languages: list[str] = []
            for lang in TRANSLATION_LANGUAGES:
                translation_result = tool_context.state.get(translation_result_key(lang))
                if not translation_result:
                    continue
                # output_key の値は LLM テキスト出力（JSON 文字列の場合がある）
                if isinstance(translation_result, str):
                    if "NO_TRANSLATION" in translation_result:
                        continue
                    parsed = _extract_json_from_text(translation_result)
                    if parsed:
                        # 言語バリデーション: 翻訳が正しい言語で書かれているか検証
                        vr = validate_translation_language(lang, parsed)
                        if not vr.is_valid:
                            text_preview = (parsed.get("narrative_content") or parsed.get("summary") or "")[:100]
                            logger.warning(
                                "Translation rejected for '%s': %s (preview: %s)",
                                lang, vr.reason, text_preview,
                            )
                            rejected_languages.append(lang)
                            continue
                        translations[lang] = parsed
                    else:
                        logger.warning(
                            "Failed to parse translation_result_%s as JSON (first 200 chars: %s)",
                            lang, translation_result[:200],
                        )
                elif isinstance(translation_result, dict):
                    # 言語バリデーション: 翻訳が正しい言語で書かれているか検証
                    vr = validate_translation_language(lang, translation_result)
                    if not vr.is_valid:
                        text_preview = (translation_result.get("narrative_content") or translation_result.get("summary") or "")[:100]
                        logger.warning(
                            "Translation rejected for '%s': %s (preview: %s)",
                            lang, vr.reason, text_preview,
                        )
                        rejected_languages.append(lang)
                        continue
                    translations[lang] = translation_result

            # 翻訳収集のサマリログ
            skipped = [lang for lang in TRANSLATION_LANGUAGES if lang not in translations and lang not in rejected_languages]
            logger.info(
                "Translations collected: %s, skipped: %s, rejected (wrong language): %s",
                list(translations.keys()), skipped, rejected_languages,
            )
            if rejected_languages:
                from shared.pipeline_failure import log_pipeline_failure
                log_pipeline_failure(
                    theme=data.get("title", "unknown"),
                    stage="publisher",
                    reason=f"Translation language validation failed for: {rejected_languages}",
                )
            if translations:
                data["translations"] = translations

        # Auto-generate mystery_id from classification, country_code, and region_code
        classification = data.get("classification")
        country_code = data.get("country_code")
        region_code = data.get("region_code")

        if classification and country_code and region_code:
            # Generate mystery_id automatically
            mystery_id = _generate_mystery_id(classification, country_code, str(region_code))
            data["mystery_id"] = mystery_id
        else:
            return json.dumps({
                "status": "error",
                "error": "classification, country_code, and region_code are required for mystery_id generation",
            }, ensure_ascii=False)

        # Upload images: prefer image_metadata from session state, fall back to LLM text
        image_source = None
        if tool_context is not None:
            image_source = tool_context.state.get(IMAGE_METADATA)

        if image_source and isinstance(image_source, dict):
            # Use accurate image metadata from session state
            if image_source.get("status") in ("success", "fallback"):
                image_paths = []
                if image_source.get("filepath"):
                    image_paths.append(image_source["filepath"])
                for variant in image_source.get("variants", []):
                    if variant.get("filepath"):
                        image_paths.append(variant["filepath"])
                # サムネイルも含める
                thumb = image_source.get("thumbnail")
                if thumb and isinstance(thumb, dict) and thumb.get("filepath"):
                    image_paths.append(thumb["filepath"])
                if image_paths:
                    images = _upload_images_internal(mystery_id, image_paths)
                    if images:
                        data["images"] = images
        elif visual_assets_json and visual_assets_json.strip():
            # Fallback: parse LLM-provided visual_assets_json
            try:
                visual_assets = json.loads(visual_assets_json, strict=False)
                if visual_assets.get("status") in ("success", "fallback"):
                    image_paths = []
                    if visual_assets.get("filepath"):
                        image_paths.append(visual_assets["filepath"])
                    for variant in visual_assets.get("variants", []):
                        if variant.get("filepath"):
                            image_paths.append(variant["filepath"])
                    # サムネイルも含める
                    thumb = visual_assets.get("thumbnail")
                    if thumb and isinstance(thumb, dict) and thumb.get("filepath"):
                        image_paths.append(thumb["filepath"])

                    if image_paths:
                        images = _upload_images_internal(mystery_id, image_paths)
                        if images:
                            data["images"] = images
            except (json.JSONDecodeError, KeyError):
                logger.warning("Failed to parse visual_assets_json, skipping image upload")
            except Exception as e:
                logger.error("Image upload failed, continuing without images: %s", e)

        # 画像処理結果の診断ログ
        if "images" in data:
            logger.info("Images prepared: hero=%s, variants=%s",
                        data["images"].get("hero", "MISSING"),
                        list(data["images"].get("variants", {}).keys()))
        else:
            logger.warning("No images attached. image_metadata=%s, visual_assets_json=%s",
                           type(image_source).__name__ if image_source else "None",
                           "provided" if visual_assets_json and visual_assets_json.strip() else "empty")

        now = datetime.now(timezone.utc)

        # ストーリーテラー（記事を執筆した LLM）をセッション状態から取得
        if tool_context is not None:
            data["storyteller"] = tool_context.state.get("storyteller", "claude")
        else:
            data.setdefault("storyteller", "claude")

        # ストーリーテラー LLM メタデータ（モデル情報 + トークン使用量）
        if tool_context is not None:
            storyteller_meta = tool_context.state.get(STORYTELLER_LLM_METADATA)
            if storyteller_meta and isinstance(storyteller_meta, dict):
                data["storyteller_llm_metadata"] = storyteller_meta

        # 検索活動ログ（再現性条件の担保: 第三者が同じ検索を追跡可能）
        if tool_context is not None:
            search_log = tool_context.state.get(SEARCH_LOG)
            if search_log and isinstance(search_log, list):
                data["search_log"] = search_log

        # スキーマバージョン（ドキュメント構造の世代管理）
        data["schema_version"] = SCHEMA_VERSION

        # Set timestamps and status
        data["status"] = data.get("status", STATUS_PENDING)
        data["createdAt"] = now
        data["updatedAt"] = now
        if data["status"] == STATUS_PUBLISHED:
            data["publishedAt"] = now
        data["analysis_timestamp"] = data.get("analysis_timestamp", now.isoformat())

        # Ensure required list fields exist
        data.setdefault("additional_evidence", [])
        data["additional_evidence"] = data["additional_evidence"][:5]

        # evidence_a / evidence_b: 空 excerpt にはフォールバック文を挿入
        for key in ("evidence_a", "evidence_b"):
            ev = data.get(key)
            if ev and isinstance(ev, dict):
                if not ev.get("relevant_excerpt", "").strip():
                    source_title = ev.get("source_title", "unknown source")
                    ev["relevant_excerpt"] = f"[See original source: {source_title}]"
                    logger.warning("%s: empty relevant_excerpt replaced with fallback, title=%s", key, source_title)

        # additional_evidence の source_url 欠落チェック + 空 excerpt フィルタリング
        filtered_additional = []
        for i, ev in enumerate(data.get("additional_evidence", [])):
            if not ev.get("source_url"):
                logger.warning("additional_evidence[%d] missing source_url, title=%s", i, ev.get("source_title", "unknown"))
            if not ev.get("relevant_excerpt", "").strip():
                logger.warning("additional_evidence[%d] removed (empty relevant_excerpt), title=%s", i, ev.get("source_title", "unknown"))
                continue
            filtered_additional.append(ev)
        data["additional_evidence"] = filtered_additional
        data.setdefault("alternative_hypotheses", [])
        data.setdefault("research_questions", [])
        data.setdefault("story_hooks", [])
        data.setdefault("pipeline_log", [])

        # 証拠妥当性の監査ログ（ブロッキングなし、ログ記録のみ）
        if tool_context is not None:
            _audit_evidence_relevance(data, tool_context)

        mystery_id = data["mystery_id"]
        db.collection("mysteries").document(mystery_id).set(data)

        # mystery_id をセッション状態に直接保存（LLM テキスト解析に依存しない確実な受け渡し）
        if tool_context is not None:
            tool_context.state[PUBLISHED_MYSTERY_ID] = mystery_id

        return json.dumps({
            "status": "success",
            "mystery_id": mystery_id,
            "firestore_path": f"mysteries/{mystery_id}",
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
        }, ensure_ascii=False)
