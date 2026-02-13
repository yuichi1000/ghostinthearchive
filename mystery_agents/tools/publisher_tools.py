"""LLM-facing tool functions for the Publisher Agent.

Writes mystery data to Firestore and uploads images to Cloud Storage.
Supports both Firebase emulator (local dev) and production environments.

When tool_context is available, reads structured data from session state
to reduce dependency on LLM text interpretation for critical fields.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from google.adk.tools.tool_context import ToolContext

from shared.firestore import get_firestore_client, get_storage_bucket

logger = logging.getLogger(__name__)


def _generate_mystery_id(classification: str, state_code: str, area_code: str) -> str:
    """Generate a unique mystery_id with timestamp.

    Args:
        classification: 3-letter classification code (e.g., "OCC", "HIS", "FLK").
        state_code: 2-letter US state code (e.g., "MA", "NY").
        area_code: 3-digit telephone area code (e.g., "617", "212").

    Returns:
        Mystery ID in format: {CLS}-{ST}-{AREA}-{YYYYMMDDHHMMSS}
        Example: OCC-MA-617-20260207143025
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d%H%M%S")
    return f"{classification.upper()}-{state_code.upper()}-{area_code}-{timestamp}"


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
        for label in ("_sm", "_md", "_lg", "_xl"):
            if p.stem.endswith(label):
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
        storage_public_host = os.environ.get("STORAGE_EMULATOR_PUBLIC_HOST", "") or os.environ.get("STORAGE_EMULATOR_HOST", "")
        if storage_public_host:
            public_url = f"{storage_public_host}/v0/b/{bucket.name}/o/{blob_name.replace('/', '%2F')}?alt=media"
        else:
            public_url = f"https://storage.googleapis.com/{bucket.name}/{blob_name}"

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
    Automatically generates mystery_id from classification, state_code, and area_code.
    When visual_assets_json is provided, uploads images to Cloud Storage using the
    generated mystery_id, ensuring ID consistency between images and Firestore.

    When tool_context is available, reads structured data from session state:
    - structured_report: Accurate evidence, hypothesis, classification data from Scholar
    - image_metadata: Accurate file paths and variant info from Illustrator
    - translation_ja: Japanese translation fields from Translator

    Args:
        mystery_json: JSON string containing the full mystery data.
            Required fields for ID generation:
            - classification: 3-letter code (HIS, FLK, ANT, OCC, URB, CRM, REL, LOC)
            - state_code: 2-letter US state code (MA, NY, CA, etc.)
            - area_code: 3-digit telephone area code (617, 212, etc.)

            Other required fields: title, summary, discrepancy_detected,
            discrepancy_type, evidence_a, evidence_b, hypothesis,
            alternative_hypotheses, confidence_level, historical_context,
            research_questions, story_hooks.

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
                    "classification", "state_code", "area_code",
                    "evidence_a", "evidence_b", "additional_evidence",
                    "hypothesis", "alternative_hypotheses",
                    "confidence_level", "discrepancy_detected", "discrepancy_type",
                    "historical_context", "research_questions", "story_hooks",
                    "title", "summary",
                ):
                    if key in structured_report:
                        data[key] = structured_report[key]

            # 各言語の Scholar 分析を multilingual_analysis として保存
            multilingual = {}
            for lang in ["en", "de", "es", "fr", "nl", "pt"]:
                analysis = tool_context.state.get(f"scholar_analysis_{lang}")
                if analysis and "INSUFFICIENT_DATA" not in str(analysis):
                    multilingual[lang] = str(analysis)
            if multilingual:
                data["multilingual_analysis"] = multilingual
                data["languages_analyzed"] = list(multilingual.keys())

            # 全言語の翻訳結果を translations map に収集
            translations: dict[str, dict] = {}
            for lang in ["ja", "es", "de", "fr", "nl", "pt"]:
                translation_result = tool_context.state.get(f"translation_result_{lang}")
                if not translation_result:
                    continue
                # output_key の値は LLM テキスト出力（JSON 文字列の場合がある）
                if isinstance(translation_result, str):
                    if "NO_TRANSLATION" in translation_result:
                        continue
                    try:
                        parsed = json.loads(translation_result, strict=False)
                        if isinstance(parsed, dict):
                            translations[lang] = parsed
                    except (json.JSONDecodeError, ValueError):
                        logger.warning("Failed to parse translation_result_%s as JSON", lang)
                elif isinstance(translation_result, dict):
                    translations[lang] = translation_result
            if translations:
                data["translations"] = translations

        # Auto-generate mystery_id from classification, state_code, and area_code
        classification = data.get("classification")
        state_code = data.get("state_code")
        area_code = data.get("area_code")

        if classification and state_code and area_code:
            # Generate mystery_id automatically
            mystery_id = _generate_mystery_id(classification, state_code, str(area_code))
            data["mystery_id"] = mystery_id
        else:
            return json.dumps({
                "status": "error",
                "error": "classification, state_code, and area_code are required for mystery_id generation",
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

                    if image_paths:
                        images = _upload_images_internal(mystery_id, image_paths)
                        if images:
                            data["images"] = images
            except (json.JSONDecodeError, KeyError):
                logger.warning("Failed to parse visual_assets_json, skipping image upload")
            except Exception as e:
                logger.error("Image upload failed, continuing without images: %s", e)

        now = datetime.now(timezone.utc)

        # Set timestamps and status
        data["status"] = data.get("status", "pending")
        data["createdAt"] = now
        data["updatedAt"] = now
        if data["status"] == "published":
            data["publishedAt"] = now
        data["analysis_timestamp"] = data.get("analysis_timestamp", now.isoformat())

        # Ensure required list fields exist
        data.setdefault("additional_evidence", [])
        data["additional_evidence"] = data["additional_evidence"][:5]

        # additional_evidence の source_url 欠落チェック
        for i, ev in enumerate(data.get("additional_evidence", [])):
            if not ev.get("source_url"):
                logger.warning("additional_evidence[%d] missing source_url, title=%s", i, ev.get("source_title", "unknown"))
        data.setdefault("alternative_hypotheses", [])
        data.setdefault("research_questions", [])
        data.setdefault("story_hooks", [])
        data.setdefault("pipeline_log", [])

        mystery_id = data["mystery_id"]
        db.collection("mysteries").document(mystery_id).set(data)

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
            for label in ("_sm", "_md", "_lg", "_xl"):
                if p.stem.endswith(label):
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
            storage_public_host = os.environ.get("STORAGE_EMULATOR_PUBLIC_HOST", "") or os.environ.get("STORAGE_EMULATOR_HOST", "")
            if storage_public_host:
                public_url = f"{storage_public_host}/v0/b/{bucket.name}/o/{blob_name.replace('/', '%2F')}?alt=media"
            else:
                public_url = f"https://storage.googleapis.com/{bucket.name}/{blob_name}"

            uploaded.append({
                "path": local_path,
                "label": variant_suffix.lstrip("_") if variant_suffix else "original",
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
            if lbl == "original":
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
