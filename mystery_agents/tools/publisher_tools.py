"""LLM-facing tool functions for the Publisher Agent.

Writes mystery data to Firestore and uploads images to Cloud Storage.
Supports both Firebase emulator (local dev) and production environments.

When tool_context is available, reads structured data from session state
to reduce dependency on LLM text interpretation for critical fields.
"""

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from google.adk.tools.tool_context import ToolContext

from shared.constants import (
    ALLOWED_LANGUAGES,
    SCHEMA_VERSION,
    STATUS_PENDING,
    STATUS_PUBLISHED,
    TRANSLATION_LANGUAGES,
)
from shared.firestore import get_firestore_client, get_storage_bucket
from shared.language_validator import validate_translation_language

from mystery_agents.tools.search_metadata import get_search_metadata as _get_search_metadata

logger = logging.getLogger(__name__)


@dataclass
class _PublishContext:
    """publish_mystery の tool_context.state インターフェースをエミュレートするプロキシ。

    Custom Agent から publish_mystery を LLM 非経由で呼び出す際に使用する。
    """

    state: dict


def _extract_json_from_text(text: str) -> Optional[dict]:
    """LLM テキスト出力から JSON dict を抽出する。

    Gemini は JSON を markdown コードブロック（```json ... ```）で包むことがある。
    直接パースを試み、失敗時にコードブロックを剥がしてリトライする。

    Args:
        text: LLM の出力テキスト

    Returns:
        パース済みの dict、または抽出できなかった場合は None
    """
    # 1. 直接パースを試行
    try:
        parsed = json.loads(text, strict=False)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. markdown コードブロックを剥がしてリトライ
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1), strict=False)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def _generate_mystery_id(classification: str, country_code: str, region_code: str) -> str:
    """Generate a unique mystery_id with timestamp.

    Args:
        classification: 3-letter classification code (e.g., "OCC", "HIS", "FLK").
        country_code: 2-letter ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "JP").
        region_code: 3-5 letter IATA region code (e.g., "BOS", "LHR", "NRT").

    Returns:
        Mystery ID in format: {CLS}-{CC}-{REGION}-{YYYYMMDDHHMMSS}
        Example: OCC-US-BOS-20260207143025
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d%H%M%S")
    return f"{classification.upper()}-{country_code.upper()}-{region_code.upper()}-{timestamp}"


def _cleanup_temp_images(file_paths: list[Path]) -> None:
    """Remove uploaded image files and their parent temp directory.

    Deletes each file in *file_paths*, then attempts to remove the
    common parent directory if it lives under the system temp dir and
    is now empty. Failures are logged as warnings but never raised.
    """
    temp_dirs: set[Path] = set()

    for p in file_paths:
        try:
            if p.exists():
                temp_dirs.add(p.parent)
                p.unlink()
        except Exception as e:
            logger.warning("Failed to delete temp image %s: %s", p, e)

    for d in temp_dirs:
        try:
            if d.exists() and not any(d.iterdir()):
                d.rmdir()
                logger.info("Removed empty temp directory: %s", d)
        except Exception as e:
            logger.warning("Failed to remove temp directory %s: %s", d, e)


def _upload_images_internal(mystery_id: str, image_paths: list[str]) -> dict:
    """Upload images to Cloud Storage and return structured images object.

    Internal helper that uploads image files and builds a structured dict
    with 'hero' and 'variants' URLs. Uses the same mystery_id that will be
    used for the Firestore document, ensuring ID consistency.

    Args:
        mystery_id: The mystery ID to use as the storage prefix.
        image_paths: List of local file paths to upload.

    Returns:
        Dict with 'hero' and 'variants' keys, or empty dict if no uploads.
    """
    bucket = get_storage_bucket()
    images = {}
    variants = {}
    total_files = 0
    successful_uploads = 0
    uploaded_files: list[Path] = []

    for local_path in image_paths:
        p = Path(local_path)
        if not p.is_absolute():
            p = Path(__file__).parent.parent / p
        if not p.exists():
            logger.warning("File not found, skipping: %s", p)
            continue

        total_files += 1

        # Rename file to mystery_id-based name
        variant_suffix = ""
        is_thumbnail = False
        for label in ("_thumb", "_sm", "_md", "_lg", "_xl"):
            if p.stem.endswith(label):
                if label == "_thumb":
                    is_thumbnail = True
                variant_suffix = label
                break
        new_filename = f"{mystery_id}{variant_suffix}{p.suffix}"
        blob_name = f"images/{mystery_id}/{new_filename}"

        # Rename local file to mystery_id-based name
        new_local_path = p.parent / new_filename
        if new_local_path != p:
            p.rename(new_local_path)
            p = new_local_path

        try:
            blob = bucket.blob(blob_name)
            content_type_map = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
            content_type = content_type_map.get(p.suffix.lower(), "image/png")
            blob.upload_from_filename(str(p), content_type=content_type)

            # Verify upload succeeded (best-effort: emulator may not support blob.exists())
            try:
                if not blob.exists():
                    logger.warning("Upload verification failed for %s — continuing anyway", blob_name)
            except Exception:
                logger.debug("blob.exists() not supported (emulator?), skipping verification for %s", blob_name)

            logger.info("Uploaded successfully: %s", blob_name)
            successful_uploads += 1
            uploaded_files.append(p)
        except Exception as e:
            logger.error("Failed to upload %s: %s", blob_name, e)
            continue

        # Build public URL (use STORAGE_EMULATOR_PUBLIC_HOST for browser-accessible URL)
        # 本番: Firebase Storage REST API 形式（セキュリティルール allow read: if true が適用される）
        storage_public_host = os.environ.get("STORAGE_EMULATOR_PUBLIC_HOST", "") or os.environ.get("STORAGE_EMULATOR_HOST", "")
        if storage_public_host:
            host = storage_public_host if storage_public_host.startswith("http") else f"http://{storage_public_host}"
            public_url = f"{host}/v0/b/{bucket.name}/o/{blob_name.replace('/', '%2F')}?alt=media"
        else:
            public_url = (
                f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}"
                f"/o/{blob_name.replace('/', '%2F')}?alt=media"
            )

        # サムネイルは images["thumbnail"] に、それ以外は hero/variants に格納
        if is_thumbnail:
            images["thumbnail"] = public_url
        else:
            lbl = variant_suffix.lstrip("_") if variant_suffix else "original"
            if lbl == "original":
                images["hero"] = public_url
            else:
                variants[lbl] = public_url

    if variants:
        if "lg" in variants:
            images["hero"] = variants["lg"]
        images["variants"] = variants

    logger.info("Image upload complete: %d/%d files uploaded successfully", successful_uploads, total_files)

    # Clean up uploaded temp files
    if uploaded_files:
        _cleanup_temp_images(uploaded_files)

    return images


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
            structured_report = tool_context.state.get("structured_report")
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
            creative_content = tool_context.state.get("creative_content")
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
            collected_docs = tool_context.state.get("collected_documents_en")
            if collected_docs:
                data["raw_data"] = collected_docs if isinstance(collected_docs, str) else str(collected_docs)

            # 各言語の Scholar 分析を multilingual_analysis として保存
            # active_languages を参照し、動的に検出された全言語をカバーする
            multilingual = {}
            active_langs = tool_context.state.get("active_languages", [])
            for lang in active_langs:
                analysis = tool_context.state.get(f"scholar_analysis_{lang}")
                if analysis and "INSUFFICIENT_DATA" not in str(analysis):
                    multilingual[lang] = str(analysis)
            # Multilingual Scholar の分析も保存
            ml_analysis = tool_context.state.get("scholar_analysis_multilingual")
            if ml_analysis and "INSUFFICIENT_DATA" not in str(ml_analysis):
                multilingual["multilingual"] = str(ml_analysis)
            if multilingual:
                data["multilingual_analysis"] = multilingual
                data["languages_analyzed"] = list(multilingual.keys())

            # mystery_report: Armchair Polymath の統合分析レポート全文を保存
            mystery_report = tool_context.state.get("mystery_report")
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
                translation_result = tool_context.state.get(f"translation_result_{lang}")
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
            image_source = tool_context.state.get("image_metadata")

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

        mystery_id = data["mystery_id"]
        db.collection("mysteries").document(mystery_id).set(data)

        # mystery_id をセッション状態に直接保存（LLM テキスト解析に依存しない確実な受け渡し）
        if tool_context is not None:
            tool_context.state["published_mystery_id"] = mystery_id

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


def upload_images(mystery_id: str, image_paths: str) -> str:
    """Upload generated images to Cloud Storage.

    Copies image files from local storage to the Cloud Storage bucket
    (or Storage emulator for local development).

    Args:
        mystery_id: The mystery ID to use as the storage prefix.
        image_paths: JSON string containing a list of local file paths to upload.
            Example: '["data/images/boston_harbor_20260201.png"]'

    Returns:
        JSON string with upload results including public URLs.
    """
    try:
        paths = json.loads(image_paths)
        if isinstance(paths, str):
            paths = [paths]

        bucket = get_storage_bucket()
        uploaded = []
        uploaded_files: list[Path] = []

        for local_path in paths:
            p = Path(local_path)
            if not p.is_absolute():
                p = Path(__file__).parent.parent / p
            if not p.exists():
                uploaded.append({
                    "path": local_path,
                    "status": "error",
                    "error": f"File not found: {p}",
                })
                continue

            # Rename file to mystery_id-based name
            variant_suffix = ""
            is_thumbnail = False
            for label in ("_thumb", "_sm", "_md", "_lg", "_xl"):
                if p.stem.endswith(label):
                    if label == "_thumb":
                        is_thumbnail = True
                    variant_suffix = label
                    break
            new_filename = f"{mystery_id}{variant_suffix}{p.suffix}"
            blob_name = f"images/{mystery_id}/{new_filename}"

            # Rename local file to mystery_id-based name
            new_local_path = p.parent / new_filename
            if new_local_path != p:
                p.rename(new_local_path)
                p = new_local_path

            blob = bucket.blob(blob_name)
            content_type_map = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
            content_type = content_type_map.get(p.suffix.lower(), "image/png")
            blob.upload_from_filename(str(p), content_type=content_type)
            uploaded_files.append(p)

            # エミュレータではmake_public()が使えないため、URLを直接構築
            # STORAGE_EMULATOR_PUBLIC_HOST: ブラウザからアクセス可能なURL用ホスト
            # 本番: Firebase Storage REST API 形式（セキュリティルール allow read: if true が適用される）
            storage_public_host = os.environ.get("STORAGE_EMULATOR_PUBLIC_HOST", "") or os.environ.get("STORAGE_EMULATOR_HOST", "")
            if storage_public_host:
                host = storage_public_host if storage_public_host.startswith("http") else f"http://{storage_public_host}"
                public_url = f"{host}/v0/b/{bucket.name}/o/{blob_name.replace('/', '%2F')}?alt=media"
            else:
                public_url = (
                    f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}"
                    f"/o/{blob_name.replace('/', '%2F')}?alt=media"
                )

            uploaded.append({
                "path": local_path,
                "label": "thumb" if is_thumbnail else (variant_suffix.lstrip("_") if variant_suffix else "original"),
                "status": "success",
                "storage_path": f"gs://{bucket.name}/{blob_name}",
                "public_url": public_url,
            })

        # Build structured images object for direct use in Firestore
        images = {}
        variants = {}
        for entry in uploaded:
            if entry["status"] != "success":
                continue
            lbl = entry["label"]
            if lbl == "thumb":
                images["thumbnail"] = entry["public_url"]
            elif lbl == "original":
                images["hero"] = entry["public_url"]
            else:
                variants[lbl] = entry["public_url"]
        if variants:
            # Use lg variant as hero if available (higher quality)
            if "lg" in variants:
                images["hero"] = variants["lg"]
            images["variants"] = variants

        # Clean up uploaded temp files
        if uploaded_files:
            _cleanup_temp_images(uploaded_files)

        return json.dumps({
            "status": "success",
            "mystery_id": mystery_id,
            "uploaded": uploaded,
            "images": images,
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e),
        }, ensure_ascii=False)
