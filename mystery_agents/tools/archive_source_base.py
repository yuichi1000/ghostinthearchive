"""アーカイブソース基底クラス。

全 API ツールに共通するパターン（レートリミット、リトライセッション、
エラーハンドリング、構造化ログ、日付パース）を集約する。
新規 API 追加時はこのクラスを継承し、_search_impl() を実装するだけでよい。
"""

import logging
import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from shared.http_retry import create_retry_session

# pipeline_server.py 経由の実行でも .env が確実に読み込まれるようにする
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from ..schemas.document import ArchiveDocument

logger = logging.getLogger(__name__)


@dataclass
class ArchiveSearchResult:
    """アーカイブ検索の統一結果型。"""

    documents: list[ArchiveDocument] = field(default_factory=list)
    total_hits: int = 0
    error: str | None = None


class ArchiveSource(ABC):
    """アーカイブソースの基底クラス。

    サブクラスはクラス変数でメタデータを宣言し、
    _search_impl() で API 固有の検索ロジックを実装する。
    """

    # --- サブクラスが宣言するクラス変数 ---
    source_key: str = ""
    source_name: str = ""
    source_type: str = ""
    min_request_delay: float = 1.0
    supported_languages: set[str] = set()
    supports_language_filter: bool = False
    is_newspaper_source: bool = False
    expected_domains: list[str] = []
    env_var_key: str | None = None

    def __init__(self) -> None:
        self._session = create_retry_session()
        self._last_request_time = 0.0

    def _rate_limit(self) -> None:
        """最小リクエスト間隔を確保するレートリミッター。"""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.min_request_delay:
            time.sleep(self.min_request_delay - elapsed)
        self._last_request_time = time.time()

    def _check_api_key(self) -> str | None:
        """API キーの存在確認。不要なソースは None を返す。"""
        if self.env_var_key is None:
            return None
        key = os.environ.get(self.env_var_key, "")
        if not key:
            return f"{self.env_var_key} not set"
        return None

    def search(
        self,
        keywords: list[str],
        date_start: str | None = None,
        date_end: str | None = None,
        max_results: int = 20,
        language: str | None = None,
    ) -> ArchiveSearchResult:
        """共通ラッパー: API キーチェック → レートリミット → 検索 → ログ。"""
        # API キーチェック
        key_error = self._check_api_key()
        if key_error:
            return ArchiveSearchResult(error=key_error)

        if not keywords:
            return ArchiveSearchResult(error="No keywords provided")

        self._rate_limit()
        start = time.monotonic()

        try:
            result = self._search_impl(
                keywords=keywords,
                date_start=date_start,
                date_end=date_end,
                max_results=max_results,
                language=language,
            )
            latency_ms = round((time.monotonic() - start) * 1000)
            logger.info(
                "%s 検索完了: %d 件 (%dms)",
                self.source_name,
                len(result.documents),
                latency_ms,
                extra={
                    "api_name": self.source_key,
                    "result_count": len(result.documents),
                    "total_hits": result.total_hits,
                    "latency_ms": latency_ms,
                },
            )
            return result

        except Exception as e:
            latency_ms = round((time.monotonic() - start) * 1000)
            logger.warning(
                "%s API エラー: %s (%dms)",
                self.source_name,
                e,
                latency_ms,
                extra={
                    "api_name": self.source_key,
                    "latency_ms": latency_ms,
                    "error": str(e),
                },
            )
            return ArchiveSearchResult(error=f"{self.source_name} API error: {e}")

    @abstractmethod
    def _search_impl(
        self,
        keywords: list[str],
        date_start: str | None,
        date_end: str | None,
        max_results: int,
        language: str | None,
    ) -> ArchiveSearchResult:
        """サブクラスが実装する API 固有の検索ロジック。"""
        ...

    @staticmethod
    def parse_year(date_str: str, min_century: int = 13) -> str | None:
        """日付文字列から年を抽出し ISO 形式に変換する。

        6 ファイルに重複していた _parse_year を統一。

        Args:
            date_str: 日付文字列
            min_century: 認識する最小の世紀（デフォルト: 13世紀 = 1300年代）

        Returns:
            "YYYY-01-01" 形式の文字列、またはパース失敗時は入力の先頭10文字。
            空文字の場合は None。
        """
        if not date_str:
            return None
        pattern = rf"\b({min_century}[0-9]\d{{2}}|1[{min_century + 1}-9]\d{{2}}|20\d{{2}})\b"
        year_match = re.search(pattern, date_str)
        if year_match:
            return f"{year_match.group(1)}-01-01"
        return date_str[:10] if len(date_str) > 10 else date_str
