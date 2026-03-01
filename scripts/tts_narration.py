"""ナレーション音声生成ツール

Cloud Text-to-Speech でテキストから MP3 を生成し、プロジェクトルートに配置する。

使い方:
    # テキストを直接指定
    python scripts/tts_narration.py "こんにちは、世界" -o hello.mp3

    # ファイルからテキストを読み込む
    python scripts/tts_narration.py --from-file 脚本.txt -o narration.mp3

    # 音声を変更（デフォルト: ja-JP-Neural2-D = 日本語男性）
    python scripts/tts_narration.py "テスト" --voice ja-JP-Wavenet-B -o test.mp3

    # 発話速度を変更（デフォルト: 1.0）
    python scripts/tts_narration.py "テスト" --rate 0.9 -o test.mp3
"""

import argparse
import io
import re
import sys
import time
from pathlib import Path

from google.cloud import texttospeech
from pydub import AudioSegment

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent

# TTS 設定
MAX_TTS_BYTES = 5000
DEFAULT_VOICE = "ja-JP-Neural2-D"  # 日本語男性（Neural2: 高品質）
DEFAULT_RATE = 1.0
DEFAULT_PITCH = 0.0
SAMPLE_RATE = 24000
MAX_RETRIES = 3
RETRY_DELAY = 2


def _get_client() -> texttospeech.TextToSpeechClient:
    """TTS クライアントを取得する。

    GOOGLE_CLOUD_PROJECT が未設定の場合、gcloud config から自動取得する。
    """
    import os
    import subprocess
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        try:
            result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                capture_output=True, text=True, timeout=5,
            )
            project = result.stdout.strip()
        except Exception:
            pass
    if project:
        from google.api_core.client_options import ClientOptions
        return texttospeech.TextToSpeechClient(
            client_options=ClientOptions(quota_project_id=project),
        )
    return texttospeech.TextToSpeechClient()


def _split_text(text: str) -> list[str]:
    """テキストを TTS のバイト制限以内に分割する。"""
    if len(text.encode("utf-8")) <= MAX_TTS_BYTES:
        return [text]

    # 段落（ダブル改行）で分割
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 単一段落が制限超過なら文単位で分割
        if len(para.encode("utf-8")) > MAX_TTS_BYTES:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_by_sentences(para))
            continue

        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate.encode("utf-8")) <= MAX_TTS_BYTES:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = para

    if current:
        chunks.append(current.strip())

    return chunks


def _split_by_sentences(text: str) -> list[str]:
    """文単位でテキストを分割する。"""
    sentences = re.split(r"(?<=[。．.!?！？])", text)
    chunks: list[str] = []
    current = ""

    for s in sentences:
        s = s.strip()
        if not s:
            continue
        candidate = current + s
        if len(candidate.encode("utf-8")) <= MAX_TTS_BYTES:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = s

    if current:
        chunks.append(current)

    return chunks


def synthesize(
    text: str,
    voice_name: str = DEFAULT_VOICE,
    speaking_rate: float = DEFAULT_RATE,
    pitch: float = DEFAULT_PITCH,
) -> AudioSegment:
    """テキストを音声合成して AudioSegment を返す。"""
    client = _get_client()
    chunks = _split_text(text)
    segments: list[AudioSegment] = []

    for i, chunk in enumerate(chunks):
        print(f"  チャンク {i + 1}/{len(chunks)} を合成中... ({len(chunk.encode('utf-8'))} bytes)")

        for attempt in range(MAX_RETRIES):
            try:
                response = client.synthesize_speech(
                    input=texttospeech.SynthesisInput(text=chunk),
                    voice=texttospeech.VoiceSelectionParams(
                        language_code=voice_name[:5],
                        name=voice_name,
                    ),
                    audio_config=texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.MP3,
                        sample_rate_hertz=SAMPLE_RATE,
                        speaking_rate=speaking_rate,
                        pitch=pitch,
                    ),
                )
                segment = AudioSegment.from_mp3(io.BytesIO(response.audio_content))
                segments.append(segment)
                break
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAY * (attempt + 1)
                    print(f"  リトライ {attempt + 1}/{MAX_RETRIES}（{wait}秒待機）: {e}")
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"TTS 合成に失敗しました: {e}") from e

    # 全チャンクを結合
    result = segments[0]
    for s in segments[1:]:
        result += s

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Cloud Text-to-Speech でナレーション音声を生成する",
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="音声化するテキスト（--from-file と排他）",
    )
    parser.add_argument(
        "--from-file", "-f",
        help="テキストを読み込むファイルパス",
    )
    parser.add_argument(
        "--output", "-o",
        default="narration.mp3",
        help="出力ファイル名（デフォルト: narration.mp3）",
    )
    parser.add_argument(
        "--voice", "-v",
        default=DEFAULT_VOICE,
        help=f"音声名（デフォルト: {DEFAULT_VOICE}）",
    )
    parser.add_argument(
        "--rate", "-r",
        type=float,
        default=DEFAULT_RATE,
        help=f"発話速度（デフォルト: {DEFAULT_RATE}）",
    )
    parser.add_argument(
        "--pitch", "-p",
        type=float,
        default=DEFAULT_PITCH,
        help=f"ピッチ（デフォルト: {DEFAULT_PITCH}）",
    )

    args = parser.parse_args()

    # テキスト取得
    if args.from_file:
        file_path = Path(args.from_file)
        if not file_path.is_absolute():
            file_path = PROJECT_ROOT / file_path
        text = file_path.read_text(encoding="utf-8").strip()
    elif args.text:
        text = args.text
    else:
        parser.error("テキストを引数で指定するか、--from-file でファイルを指定してください")
        return

    if not text:
        print("エラー: テキストが空です", file=sys.stderr)
        sys.exit(1)

    # 出力パス（プロジェクトルートに配置）
    output_path = PROJECT_ROOT / args.output

    print(f"音声: {args.voice}")
    print(f"速度: {args.rate}")
    print(f"テキスト: {len(text)} 文字 ({len(text.encode('utf-8'))} bytes)")
    print(f"出力先: {output_path}")
    print()

    # 合成
    audio = synthesize(text, args.voice, args.rate, args.pitch)

    # MP3 エクスポート
    audio.export(str(output_path), format="mp3", bitrate="128k")

    duration = len(audio) / 1000
    print()
    print(f"完了: {output_path.name} ({duration:.1f}秒)")


if __name__ == "__main__":
    main()
