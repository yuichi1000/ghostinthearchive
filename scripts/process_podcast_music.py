"""Podcast 用音楽アセットの前処理スクリプト。

ダウンロードした WAV ファイルからイントロ・アウトロ用 MP3 を生成する。
生成されたファイルはフェード・音量調整済みの完成品で、パイプラインでは
そのまま読み込むだけで使用できる。

使用方法:
    python scripts/process_podcast_music.py
"""

from pathlib import Path

from pydub import AudioSegment

# ソースファイル
DOWNLOADS = Path.home() / "Downloads"
INTRO_SRC = DOWNLOADS / "Music_fx_haunting_gothic_atmosphere_scholarl.wav"
OUTRO_SRC = DOWNLOADS / "Music_fx_haunting_pipe_organ_1920s_gramophon.wav"

# 出力先
ASSETS_DIR = Path(__file__).parent.parent / "podcast_agents" / "assets"

# イントロ設定: 5秒フル再生 + 2秒フェードアウト = 7秒
INTRO_FULL_MS = 5000
INTRO_FADE_MS = 2000

# アウトロ設定: 15秒、7秒フェードイン、最後3秒フェードアウト、-8dB
OUTRO_TOTAL_MS = 15_000
OUTRO_FADE_IN_MS = 7000
OUTRO_FADE_OUT_MS = 3000
OUTRO_VOLUME_DB = -8


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # --- イントロ ---
    print(f"イントロ処理: {INTRO_SRC}")
    intro = AudioSegment.from_wav(str(INTRO_SRC))
    intro = intro[: INTRO_FULL_MS + INTRO_FADE_MS]  # 7秒にトリム
    intro = intro.fade_out(INTRO_FADE_MS)
    intro_path = ASSETS_DIR / "intro.mp3"
    intro.export(str(intro_path), format="mp3", bitrate="128k")
    print(f"  → {intro_path} ({len(intro) / 1000:.1f}秒)")

    # --- アウトロ ---
    print(f"アウトロ処理: {OUTRO_SRC}")
    outro = AudioSegment.from_wav(str(OUTRO_SRC))
    if len(outro) > OUTRO_TOTAL_MS:
        outro = outro[:OUTRO_TOTAL_MS]
    outro = outro.fade_in(OUTRO_FADE_IN_MS)
    outro = outro.fade_out(OUTRO_FADE_OUT_MS)
    outro = outro + OUTRO_VOLUME_DB
    outro_path = ASSETS_DIR / "outro.mp3"
    outro.export(str(outro_path), format="mp3", bitrate="128k")
    print(f"  → {outro_path} ({len(outro) / 1000:.1f}秒)")

    print("完了!")


if __name__ == "__main__":
    main()
