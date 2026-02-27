"""Cloud Storage 画像アップロード機能。

publisher_tools.py から分離した画像アップロードロジック。
_upload_images_internal（内部用）と upload_images（LLM-facing ツール）を提供する。
"""

import json
import logging
import os
from pathlib import Path

from shared.firestore import get_storage_bucket

logger = logging.getLogger(__name__)


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
