"""Unit tests for podcast_agents/tools/tts.py - TTS 音声生成."""

from unittest.mock import MagicMock, patch

import pytest

from podcast_agents.tools.tts import (
    _split_text,
    _split_by_sentences,
    synthesize_segment,
    generate_podcast_audio,
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
    """Tests for generate_podcast_audio()."""

    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_combines_segments_and_uploads(self, mock_synth, mock_bucket):
        """セグメントを結合して GCS にアップロードする。"""
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
            {"type": "intro", "label": "Intro", "text": "Welcome"},
            {"type": "body", "label": "Main", "text": "The story begins..."},
            {"type": "outro", "label": "Closing", "text": "Goodbye"},
        ]

        with patch("podcast_agents.tools.tts.AudioSegment") as mock_as:
            mock_as.silent.return_value = MagicMock()

            result = generate_podcast_audio(segments, "test-podcast-id")

        assert result["format"] == "mp3"
        assert result["voice_name"] == "en-US-Studio-O"
        assert result["segment_count"] == 3
        assert "podcasts/test-podcast-id/episode.mp3" in result["gcs_path"]
        mock_blob.upload_from_string.assert_called_once()

    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_skips_empty_segments(self, mock_synth, mock_bucket):
        """テキストが空のセグメントはスキップする。"""
        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=30000)
        mock_audio.export = MagicMock()
        mock_synth.return_value = mock_audio

        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test.appspot.com"
        mock_bucket_obj.blob.return_value = MagicMock()
        mock_bucket.return_value = mock_bucket_obj

        segments = [
            {"type": "intro", "label": "Intro", "text": "Welcome"},
            {"type": "body", "label": "Empty", "text": ""},
            {"type": "body", "label": "Also Empty", "text": "   "},
        ]

        with patch("podcast_agents.tools.tts.AudioSegment"):
            result = generate_podcast_audio(segments, "test-id")

        assert result["segment_count"] == 1
        assert mock_synth.call_count == 1

    def test_raises_when_no_synthesizable_segments(self):
        """全セグメントが空の場合は RuntimeError を送出する。"""
        segments = [
            {"type": "intro", "label": "Empty", "text": ""},
            {"type": "body", "label": "Also Empty", "text": "  "},
        ]

        with pytest.raises(RuntimeError, match="合成可能なセグメントがありません"):
            generate_podcast_audio(segments, "test-id")

    @patch("podcast_agents.tools.tts.get_storage_bucket")
    @patch("podcast_agents.tools.tts.synthesize_segment")
    def test_emulator_url_format(self, mock_synth, mock_bucket):
        """エミュレータ環境では適切な URL 形式を使う。"""
        import os

        mock_audio = MagicMock()
        mock_audio.__len__ = MagicMock(return_value=10000)
        mock_audio.export = MagicMock()
        mock_synth.return_value = mock_audio

        mock_bucket_obj = MagicMock()
        mock_bucket_obj.name = "test.appspot.com"
        mock_bucket_obj.blob.return_value = MagicMock()
        mock_bucket.return_value = mock_bucket_obj

        segments = [{"type": "intro", "label": "Intro", "text": "Hello"}]

        with patch("podcast_agents.tools.tts.AudioSegment"), \
             patch.dict(os.environ, {"STORAGE_EMULATOR_HOST": "http://localhost:9199"}):
            result = generate_podcast_audio(segments, "test-id")

        assert "localhost:9199" in result["public_url"]
