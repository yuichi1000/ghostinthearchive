"""Unit tests for podcast_agents/tools/tts.py - TTS 音声生成."""

from unittest.mock import MagicMock, patch

import pytest

from podcast_agents.tools.tts import (
    _split_text,
    _split_by_sentences,
    synthesize_segment,
    generate_podcast_audio,
    AI_DISCLOSURE_TEXT,
    WEBSITE_PROMOTION_TEXT,
)


class TestSplitText:
    """Tests for _split_text()."""

    def test_short_text_no_split(self):
        """制限以内のテキストは分割しない。"""
        text = "Hello, welcome to the podcast."
        result = _split_text(text)
        assert result == [text]

    def test_splits_by_paragraph(self):
        """段落で分割する。"""
        # 2つの段落で合計が制限を超えるケース
        para1 = "A" * 3000
        para2 = "B" * 3000
        text = f"{para1}\n\n{para2}"
        result = _split_text(text, max_bytes=4000)
        assert len(result) == 2
        assert result[0] == para1
        assert result[1] == para2

    def test_handles_empty_paragraphs(self):
        """空の段落をスキップする。"""
        text = "Hello\n\n\n\nWorld"
        result = _split_text(text)
        assert len(result) == 1  # 制限内なので1つのまま

    def test_large_single_paragraph_splits_by_sentence(self):
        """段落が制限超過なら文単位で分割する。"""
        # 1文が短く、段落全体が長いケース
        sentences = ["This is sentence number %d." % i for i in range(100)]
        text = " ".join(sentences)
        result = _split_text(text, max_bytes=500)
        assert len(result) > 1
        for chunk in result:
            assert len(chunk.encode("utf-8")) <= 500


class TestSplitBySentences:
    """Tests for _split_by_sentences()."""

    def test_splits_on_period(self):
        """ピリオドで分割する。"""
        sent1 = "A" * 300
        sent2 = "B" * 300
        text = f"{sent1}. {sent2}."
        result = _split_by_sentences(text, max_bytes=400)
        assert len(result) == 2

    def test_single_sentence_exceeding_limit(self):
        """制限超過の単一文はそのまま返す。"""
        long_sentence = "A" * 6000
        result = _split_by_sentences(long_sentence, max_bytes=5000)
        assert len(result) == 1
        assert result[0] == long_sentence


class TestSynthesizeSegment:
    """Tests for synthesize_segment()."""

    @patch("podcast_agents.tools.tts._get_tts_client")
    def test_calls_tts_client(self, mock_get_client):
        """TTS クライアントが呼ばれる。"""
        # AudioSegment.from_mp3 のモックセットアップ
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.audio_content = b"\x00" * 100  # ダミー音声バイト
        mock_client.synthesize_speech.return_value = mock_response
        mock_get_client.return_value = mock_client

        mock_audio = MagicMock()
        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_as.from_mp3.return_value = mock_audio

            result = synthesize_segment("Hello world")

            mock_client.synthesize_speech.assert_called_once()
            assert result == mock_audio

    @patch("podcast_agents.tools.tts._get_tts_client")
    def test_retries_on_rate_limit(self, mock_get_client):
        """レート制限エラーでリトライする。"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.audio_content = b"\x00" * 100

        # 1回目: レート制限エラー、2回目: 成功
        mock_client.synthesize_speech.side_effect = [
            Exception("429 resource exhausted"),
            mock_response,
        ]
        mock_get_client.return_value = mock_client

        mock_audio = MagicMock()
        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as, \
             patch("podcast_agents.tools.tts.time.sleep"):
            mock_as.from_mp3.return_value = mock_audio

            result = synthesize_segment("Hello")

            assert mock_client.synthesize_speech.call_count == 2
            assert result == mock_audio

    @patch("podcast_agents.tools.tts._get_tts_client")
    def test_raises_after_max_retries(self, mock_get_client):
        """全リトライ失敗で RuntimeError を送出する。"""
        mock_client = MagicMock()
        mock_client.synthesize_speech.side_effect = Exception("Permanent error")
        mock_get_client.return_value = mock_client

        with patch("podcast_agents.tools.tts.time.sleep"), \
             pytest.raises(RuntimeError, match="TTS 合成失敗"):
            synthesize_segment("Hello")

    @patch("podcast_agents.tools.tts._get_tts_client")
    def test_splits_long_text(self, mock_get_client):
        """長いテキストは分割して合成する。"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.audio_content = b"\x00" * 100
        mock_client.synthesize_speech.return_value = mock_response
        mock_get_client.return_value = mock_client

        mock_audio = MagicMock()
        mock_audio.__add__ = MagicMock(return_value=mock_audio)
        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_as.from_mp3.return_value = mock_audio

            # 制限を超えるテキスト
            long_text = ("Short sentence. " * 500).strip()
            synthesize_segment(long_text)

            # 複数回 TTS 呼び出し
            assert mock_client.synthesize_speech.call_count > 1


class TestGeneratePodcastAudio:
    """Tests for generate_podcast_audio().

    音楽アセットは無効化してナレーションのみの動作を検証する。
    """

    @patch("podcast_agents.tools.tts.ACT_AUDIO_PATHS", {})
    @patch("podcast_agents.tools.tts.OUTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.INTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_combines_segments_and_uploads(self, mock_synth, mock_bucket, mock_intro_path, mock_outro_path):
        """セグメントを結合して GCS にアップロードする。"""
        mock_intro_path.exists.return_value = False
        mock_outro_path.exists.return_value = False

        # synthesize_segment が返す AudioSegment モック
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=60000)  # 60秒
        mock_audio.__add__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()
        mock_synth.return_value = mock_audio

        # GCS モック
        mock_blob = MagicMock()
        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test-bucket.appspot.com"
        mock_bucket_obj.blob.return_value = mock_blob
        mock_bucket.return_value = mock_bucket_obj

        segments = [
            {"type": "overview", "label": "Overview", "text": "Welcome"},
            {"type": "act_i", "label": "Act I", "text": "The story begins..."},
            {"type": "act_iiii", "label": "Act IIII", "text": "In conclusion..."},
        ]

        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_as.silent.return_value = MagicMock()
            mock_as.empty.return_value = mock_audio

            result = generate_podcast_audio(segments, "test-podcast-id")

        assert result["format"] == "mp3"
        assert result["voice_name"] == "en-US-Chirp3-HD-Enceladus"
        assert result["segment_count"] == 3
        assert "podcasts/test-podcast-id/episode.mp3" in result["gcs_path"]
        mock_blob.upload_from_string.assert_called_once()

    @patch("podcast_agents.tools.tts.ACT_AUDIO_PATHS", {})
    @patch("podcast_agents.tools.tts.OUTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.INTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_skips_empty_segments(self, mock_synth, mock_bucket, mock_intro_path, mock_outro_path):
        """テキストが空のセグメントはスキップする。"""
        mock_intro_path.exists.return_value = False
        mock_outro_path.exists.return_value = False

        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=30000)
        mock_audio.__add__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()
        mock_synth.return_value = mock_audio

        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test.appspot.com"
        mock_bucket_obj.blob.return_value = MagicMock()
        mock_bucket.return_value = mock_bucket_obj

        segments = [
            {"type": "overview", "label": "Overview", "text": "Welcome"},
            {"type": "act_i", "label": "Empty", "text": ""},
            {"type": "act_ii", "label": "Also Empty", "text": "   "},
        ]

        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_as.silent.return_value = MagicMock()
            mock_as.empty.return_value = mock_audio

            result = generate_podcast_audio(segments, "test-id")

        assert result["segment_count"] == 1
        # 1 ナレーションセグメント + 1 Web 誘導 + 1 AI 開示 = 3
        assert mock_synth.call_count == 3

    def test_raises_when_no_synthesizable_segments(self):
        """全セグメントが空の場合は RuntimeError を送出する。"""
        segments = [
            {"type": "overview", "label": "Empty", "text": ""},
            {"type": "act_i", "label": "Also Empty", "text": "  "},
        ]

        with pytest.raises(RuntimeError, match="合成可能なセグメントがありません"):
            generate_podcast_audio(segments, "test-id")

    @patch("podcast_agents.tools.tts.ACT_AUDIO_PATHS", {})
    @patch("podcast_agents.tools.tts.OUTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.INTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_emulator_url_format(self, mock_synth, mock_bucket, mock_intro_path, mock_outro_path):
        """エミュレータ環境では適切な URL 形式を使う。"""
        import os

        mock_intro_path.exists.return_value = False
        mock_outro_path.exists.return_value = False

        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=10000)
        mock_audio.__add__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()
        mock_synth.return_value = mock_audio

        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test.appspot.com"
        mock_bucket_obj.blob.return_value = MagicMock()
        mock_bucket.return_value = mock_bucket_obj

        segments = [{"type": "overview", "label": "Overview", "text": "Hello"}]

        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as, \
             patch.dict(os.environ, {"STORAGE_EMULATOR_HOST": "http://localhost:9199"}):
            mock_as.silent.return_value = MagicMock()
            mock_as.empty.return_value = mock_audio

            result = generate_podcast_audio(segments, "test-id")

        assert "localhost:9199" in result["public_url"]


class TestGeneratePodcastAudioWithMusic:
    """Tests for intro/outro/act music in generate_podcast_audio()."""

    @patch("podcast_agents.tools.tts.ACT_AUDIO_PATHS", {})
    @patch("podcast_agents.tools.tts.OUTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.INTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_includes_intro_when_asset_exists(self, mock_synth, mock_bucket, mock_intro_path, mock_outro_path):
        """イントロ音楽アセットが存在する場合、先頭に追加されること。"""
        mock_intro_path.exists.return_value = True
        mock_intro_path.__str__ = MagicMock(return_value="/fake/intro.mp3")
        mock_outro_path.exists.return_value = False

        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=60000)
        mock_audio.__add__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()
        mock_synth.return_value = mock_audio

        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test.appspot.com"
        mock_bucket_obj.blob.return_value = MagicMock()
        mock_bucket.return_value = mock_bucket_obj

        segments = [{"type": "overview", "label": "Overview", "text": "Welcome"}]

        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_intro_music = MagicMock()
            mock_intro_music.__len__ = MagicMock(return_value=7000)
            mock_as.from_mp3.return_value = mock_intro_music
            mock_as.silent.return_value = MagicMock()
            mock_as.empty.return_value = mock_audio
            # イントロ音楽 + pause → episode
            mock_intro_music.__add__ = MagicMock(return_value=mock_audio)

            generate_podcast_audio(segments, "test-id")

        # from_mp3 がイントロアセットで呼ばれた
        mock_as.from_mp3.assert_called_once_with("/fake/intro.mp3")

    @patch("podcast_agents.tools.tts.ACT_AUDIO_PATHS", {})
    @patch("podcast_agents.tools.tts.OUTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.INTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_outro_crossfade_when_asset_exists(self, mock_synth, mock_bucket, mock_intro_path, mock_outro_path):
        """OUTRO 音楽が末尾5秒前からクロスフェードで重ねられること。"""
        mock_intro_path.exists.return_value = False
        mock_outro_path.exists.return_value = True
        mock_outro_path.__str__ = MagicMock(return_value="/fake/outro.mp3")

        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=60000)  # 60秒
        mock_audio.__add__ = MagicMock(return_value=mock_audio)
        mock_audio.__iadd__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()
        mock_audio.overlay = MagicMock(return_value=mock_audio)
        mock_synth.return_value = mock_audio

        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test.appspot.com"
        mock_bucket_obj.blob.return_value = MagicMock()
        mock_bucket.return_value = mock_bucket_obj

        segments = [{"type": "overview", "label": "Overview", "text": "Welcome"}]

        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_outro_music = MagicMock()
            mock_outro_music.__len__ = MagicMock(return_value=15000)
            mock_as.from_mp3.return_value = mock_outro_music
            mock_as.silent.return_value = MagicMock()
            mock_as.empty.return_value = mock_audio

            generate_podcast_audio(segments, "test-id")

        # synthesize_segment: セグメント + Web 誘導 + AI 開示 = 3回
        assert mock_synth.call_count == 3
        # overlay が OUTRO クロスフェードで呼ばれた
        mock_audio.overlay.assert_called_once()
        # overlay の position 引数が末尾5秒前（60000 - 5000 = 55000）
        call_args = mock_audio.overlay.call_args
        assert call_args[1].get("position") == 55000 or call_args[0][1] == 55000 \
            if len(call_args[0]) > 1 else call_args[1].get("position") == 55000

    @patch("podcast_agents.tools.tts.ACT_AUDIO_PATHS", {})
    @patch("podcast_agents.tools.tts.OUTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.INTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_works_without_music_assets(self, mock_synth, mock_bucket, mock_intro_path, mock_outro_path):
        """音楽アセットがない場合でも TTS + AI 開示で動作すること。"""
        mock_intro_path.exists.return_value = False
        mock_outro_path.exists.return_value = False

        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=30000)
        mock_audio.__add__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()
        mock_synth.return_value = mock_audio

        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test.appspot.com"
        mock_bucket_obj.blob.return_value = MagicMock()
        mock_bucket.return_value = mock_bucket_obj

        segments = [{"type": "overview", "label": "Overview", "text": "Hello"}]

        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_as.silent.return_value = MagicMock()
            mock_as.empty.return_value = mock_audio

            result = generate_podcast_audio(segments, "test-id")

        # 1 ナレーションセグメント + 1 Web 誘導 + 1 AI 開示 = 3
        assert mock_synth.call_count == 3
        assert result["segment_count"] == 1


class TestWebsitePromotion:
    """Tests for website promotion TTS insertion."""

    @patch("podcast_agents.tools.tts.ACT_AUDIO_PATHS", {})
    @patch("podcast_agents.tools.tts.OUTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.INTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_website_promotion_inserted_before_disclosure(self, mock_synth, mock_bucket, mock_intro_path, mock_outro_path):
        """WEBSITE_PROMOTION_TEXT が AI_DISCLOSURE_TEXT の直前に呼ばれること。"""
        mock_intro_path.exists.return_value = False
        mock_outro_path.exists.return_value = False

        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=30000)
        mock_audio.__add__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()
        mock_synth.return_value = mock_audio

        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test.appspot.com"
        mock_bucket_obj.blob.return_value = MagicMock()
        mock_bucket.return_value = mock_bucket_obj

        segments = [{"type": "overview", "label": "Overview", "text": "Hello"}]

        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_as.silent.return_value = MagicMock()
            mock_as.empty.return_value = mock_audio

            generate_podcast_audio(segments, "test-id")

        # synthesize_segment の呼び出し順序を検証
        call_texts = [call.args[0] for call in mock_synth.call_args_list]
        # 最後の2つが Web 誘導 → AI 開示の順であること
        assert call_texts[-2] == WEBSITE_PROMOTION_TEXT
        assert call_texts[-1] == AI_DISCLOSURE_TEXT


class TestActTransitionAudio:
    """Tests for Act transition audio insertion."""

    @patch("podcast_agents.tools.tts.OUTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.INTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_inserts_act_audio_when_files_exist(self, mock_synth, mock_bucket, mock_intro_path, mock_outro_path):
        """Act 音声ファイルが存在する場合、各 Act セグメント前に挿入されること。"""
        mock_intro_path.exists.return_value = False
        mock_outro_path.exists.return_value = False

        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=60000)
        mock_audio.__add__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()
        mock_synth.return_value = mock_audio

        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test.appspot.com"
        mock_bucket_obj.blob.return_value = MagicMock()
        mock_bucket.return_value = mock_bucket_obj

        segments = [
            {"type": "overview", "label": "Overview", "text": "Welcome"},
            {"type": "act_i", "label": "Act I", "text": "Background..."},
            {"type": "act_ii", "label": "Act II", "text": "Evidence..."},
        ]

        # Act 音声ファイルのモック
        mock_act_i_path = MagicMock()
        mock_act_i_path.exists.return_value = True
        mock_act_i_path.__str__ = MagicMock(return_value="/fake/Act I.wav")
        mock_act_ii_path = MagicMock()
        mock_act_ii_path.exists.return_value = True
        mock_act_ii_path.__str__ = MagicMock(return_value="/fake/Act II.wav")

        act_paths = {"act_i": mock_act_i_path, "act_ii": mock_act_ii_path}

        mock_act_audio = MagicMock()
        mock_act_audio.__len__ = MagicMock(return_value=3000)

        with patch("podcast_agents.tools.tts.ACT_AUDIO_PATHS", act_paths), \
             patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_as.silent.return_value = MagicMock()
            mock_as.empty.return_value = mock_audio
            mock_as.from_file.return_value = mock_act_audio

            generate_podcast_audio(segments, "test-id")

        # from_file が各 Act 音声ファイルで呼ばれた
        assert mock_as.from_file.call_count == 2

    @patch("podcast_agents.tools.tts.OUTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.INTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_skips_act_audio_when_files_missing(self, mock_synth, mock_bucket, mock_intro_path, mock_outro_path):
        """Act 音声ファイルが存在しない場合、スキップしてナレーションのみ。"""
        mock_intro_path.exists.return_value = False
        mock_outro_path.exists.return_value = False

        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=60000)
        mock_audio.__add__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()
        mock_synth.return_value = mock_audio

        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test.appspot.com"
        mock_bucket_obj.blob.return_value = MagicMock()
        mock_bucket.return_value = mock_bucket_obj

        segments = [
            {"type": "act_i", "label": "Act I", "text": "Background..."},
        ]

        # Act 音声ファイルが存在しない
        mock_act_i_path = MagicMock()
        mock_act_i_path.exists.return_value = False

        act_paths = {"act_i": mock_act_i_path}

        with patch("podcast_agents.tools.tts.ACT_AUDIO_PATHS", act_paths), \
             patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_as.silent.return_value = MagicMock()
            mock_as.empty.return_value = mock_audio

            result = generate_podcast_audio(segments, "test-id")

        # from_file は呼ばれない（ファイルが存在しないため）
        mock_as.from_file.assert_not_called()
        assert result["segment_count"] == 1

    @patch("podcast_agents.tools.tts.ACT_AUDIO_PATHS", {})
    @patch("podcast_agents.tools.tts.OUTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.INTRO_MUSIC_PATH")
    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_overview_has_no_act_audio(self, mock_synth, mock_bucket, mock_intro_path, mock_outro_path):
        """overview セグメントには Act トランジション音声を挿入しない。"""
        mock_intro_path.exists.return_value = False
        mock_outro_path.exists.return_value = False

        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=30000)
        mock_audio.__add__ = MagicMock(return_value=mock_audio)
        mock_audio.export = MagicMock()
        mock_synth.return_value = mock_audio

        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test.appspot.com"
        mock_bucket_obj.blob.return_value = MagicMock()
        mock_bucket.return_value = mock_bucket_obj

        segments = [{"type": "overview", "label": "Overview", "text": "Welcome"}]

        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_as.silent.return_value = MagicMock()
            mock_as.empty.return_value = mock_audio

            generate_podcast_audio(segments, "test-id")

        # from_file は呼ばれない（overview は ACT_AUDIO_PATHS に含まれない）
        mock_as.from_file.assert_not_called()
