"""TTS 音声生成モジュール

Google Cloud Text-to-Speech を使って構造化脚本の各セグメントを音声合成し、
pydub で結合して GCS にアップロードする。ADK エージェントではなく、
決定論的 Python 関数として実装（LLM 不要）。

podcast設計書.md 準拠:
- フォーマット: MP3 / 128kbps
- 音声: en-US-Chirp3-HD-Enceladus（デフォルト）
- セグメント間: 1.5秒の無音挿入
- TTS 制限: 5000バイト超のテキストは段落単位で分割
"""

import io
import logging
import os
import time

from google.cloud import texttospeech
from pydub import AudioSegment

from shared.firestore import get_storage_bucket

logger = logging.getLogger(__name__)

# TTS 設定
MAX_TTS_BYTES = 5000  # Cloud TTS 入力上限
PAUSE_BETWEEN_SEGMENTS_MS = 1500  # セグメント間の無音（ミリ秒）
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# デフォルト音声設定
DEFAULT_VOICE_NAME = "en-US-Chirp3-HD-Enceladus"
DEFAULT_SPEAKING_RATE = 0.95
DEFAULT_PITCH = 0.0  # Chirp 3 HD は自然な声質を内蔵
DEFAULT_SAMPLE_RATE = 24000


def _get_tts_client() -> texttospeech.TextToSpeechClient:
    """TTS クライアントを取得する。

    GOOGLE_CLOUD_PROJECT が設定されている場合、クォータプロジェクトとして
    明示的に指定する（ADC のデフォルトクォータプロジェクトに依存しない）。
    """
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if project:
        from google.api_core.client_options import ClientOptions
        client_options = ClientOptions(quota_project_id=project)
        return texttospeech.TextToSpeechClient(client_options=client_options)
    return texttospeech.TextToSpeechClient()


def _split_text(text: str, max_bytes: int = MAX_TTS_BYTES) -> list[str]:
    """テキストを TTS のバイト制限以内に段落単位で分割する。

    Args:
        text: 分割対象のテキスト
        max_bytes: 最大バイト数（デフォルト: 5000）

    Returns:
        分割されたテキストチャンクのリスト
    """
    if len(text.encode("utf-8")) <= max_bytes:
        return [text]

    # 段落（ダブル改行）で分割
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 単一段落が制限超過の場合、文単位で分割
        if len(para.encode("utf-8")) > max_bytes:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            chunks.extend(_split_by_sentences(para, max_bytes))
            continue

        candidate = f"{current_chunk}\n\n{para}" if current_chunk else para
        if len(candidate.encode("utf-8")) <= max_bytes:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def _split_by_sentences(text: str, max_bytes: int) -> list[str]:
    """文単位でテキストを分割する（段落分割でも制限を超える場合のフォールバック）。"""
    # ピリオド、疑問符、感嘆符で分割
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks: list[str] = []
    current_chunk = ""

    for sentence in sentences:
        candidate = f"{current_chunk} {sentence}" if current_chunk else sentence
        if len(candidate.encode("utf-8")) <= max_bytes:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # 単一文が制限超過の場合、そのまま追加（TTS 側で切り詰められる）
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def synthesize_segment(
    text: str,
    voice_name: str = DEFAULT_VOICE_NAME,
    speaking_rate: float = DEFAULT_SPEAKING_RATE,
    pitch: float = DEFAULT_PITCH,
) -> AudioSegment:
    """単一セグメントのテキストを TTS で音声合成する。

    テキストが TTS のバイト制限を超える場合は自動分割して結合する。

    Args:
        text: 合成するテキスト
        voice_name: TTS ボイス名
        speaking_rate: 発話速度
        pitch: ピッチ

    Returns:
        合成された AudioSegment

    Raises:
        RuntimeError: TTS 合成に失敗した場合
    """
    chunks = _split_text(text)
    audio_parts: list[AudioSegment] = []

    client = _get_tts_client()

    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue

        last_error = None
        for attempt in range(MAX_RETRIES):
            try:
                synthesis_input = texttospeech.SynthesisInput(text=chunk)
                voice = texttospeech.VoiceSelectionParams(
                    language_code=voice_name[:5],  # "en-US" from "en-US-Studio-O"
                    name=voice_name,
                )
                audio_config = texttospeech.AudioConfig(
                    audio_encoding=texttospeech.AudioEncoding.MP3,
                    sample_rate_hertz=DEFAULT_SAMPLE_RATE,
                    speaking_rate=speaking_rate,
                    pitch=pitch,
                )
                response = client.synthesize_speech(
                    input=synthesis_input,
                    voice=voice,
                    audio_config=audio_config,
                )
                audio_part = AudioSegment.from_mp3(io.BytesIO(response.audio_content))
                audio_parts.append(audio_part)
                break

            except Exception as e:
                last_error = str(e)
                error_lower = last_error.lower()

                if "resource exhausted" in error_lower or "429" in error_lower:
                    wait_time = RETRY_DELAY_SECONDS * (attempt + 1) * 2
                    logger.warning(
                        "TTS レート制限 (chunk %d/%d, attempt %d/%d): %s — %d秒待機",
                        i + 1, len(chunks), attempt + 1, MAX_RETRIES,
                        last_error, wait_time,
                    )
                    time.sleep(wait_time)
                    continue

                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        "TTS エラー (chunk %d/%d, attempt %d/%d): %s",
                        i + 1, len(chunks), attempt + 1, MAX_RETRIES, last_error,
                    )
                    time.sleep(RETRY_DELAY_SECONDS)
                    continue

                raise RuntimeError(
                    f"TTS 合成失敗 (chunk {i + 1}/{len(chunks)}): {last_error}"
                ) from e

    if not audio_parts:
        raise RuntimeError("TTS 合成結果が空です")

    # チャンクを結合
    combined = audio_parts[0]
    for part in audio_parts[1:]:
        combined += part

    return combined


def generate_podcast_audio(
    segments: list[dict],
    podcast_id: str,
    voice_name: str = DEFAULT_VOICE_NAME,
) -> dict:
    """全セグメントを TTS で合成し、結合して GCS にアップロードする。

    Args:
        segments: 構造化脚本のセグメント配列。
            各セグメント: {"type": "intro"|"body"|"outro", "label": str, "text": str}
        podcast_id: Podcast ドキュメント ID（GCS パスに使用）
        voice_name: TTS ボイス名

    Returns:
        {
            "gcs_path": "gs://bucket/podcasts/{podcast_id}/episode.mp3",
            "public_url": "https://...",
            "duration_seconds": float,
            "voice_name": str,
            "format": "mp3",
            "segment_count": int,
        }

    Raises:
        RuntimeError: 音声生成またはアップロードに失敗した場合
    """
    logger.info(
        "Podcast 音声生成開始: podcast_id=%s, segments=%d, voice=%s",
        podcast_id, len(segments), voice_name,
    )

    pause = AudioSegment.silent(duration=PAUSE_BETWEEN_SEGMENTS_MS)
    episode_audio: AudioSegment | None = None
    synthesized_count = 0

    for i, segment in enumerate(segments):
        text = segment.get("text", "").strip()
        if not text:
            logger.warning("セグメント %d (%s) のテキストが空 — スキップ", i, segment.get("label", "?"))
            continue

        label = segment.get("label", f"Segment {i}")
        seg_type = segment.get("type", "body")
        logger.info("TTS 合成中: [%s] %s (%d文字)", seg_type, label, len(text))

        segment_audio = synthesize_segment(text, voice_name=voice_name)
        synthesized_count += 1

        if episode_audio is None:
            episode_audio = segment_audio
        else:
            episode_audio = episode_audio + pause + segment_audio

    if episode_audio is None:
        raise RuntimeError("合成可能なセグメントがありませんでした")

    # MP3 エクスポート
    mp3_buffer = io.BytesIO()
    episode_audio.export(mp3_buffer, format="mp3", bitrate="128k")
    mp3_buffer.seek(0)
    mp3_bytes = mp3_buffer.read()

    duration_seconds = len(episode_audio) / 1000.0

    logger.info(
        "音声合成完了: %d セグメント, %.1f秒, %.1f MB",
        synthesized_count, duration_seconds, len(mp3_bytes) / (1024 * 1024),
    )

    # GCS アップロード
    bucket = get_storage_bucket()
    blob_name = f"podcasts/{podcast_id}/episode.mp3"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(mp3_bytes, content_type="audio/mpeg")

    # URL 構築（emulator / 本番）
    storage_public_host = (
        os.environ.get("STORAGE_EMULATOR_PUBLIC_HOST", "")
        or os.environ.get("STORAGE_EMULATOR_HOST", "")
    )
    if storage_public_host:
        host = storage_public_host if storage_public_host.startswith("http") else f"http://{storage_public_host}"
        public_url = f"{host}/v0/b/{bucket.name}/o/{blob_name.replace('/', '%2F')}?alt=media"
    else:
        public_url = (
            f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}"
            f"/o/{blob_name.replace('/', '%2F')}?alt=media"
        )

    gcs_path = f"gs://{bucket.name}/{blob_name}"

    logger.info("GCS アップロード完了: %s", gcs_path)

    return {
        "gcs_path": gcs_path,
        "public_url": public_url,
        "duration_seconds": round(duration_seconds, 1),
        "voice_name": voice_name,
        "format": "mp3",
        "segment_count": synthesized_count,
    }
