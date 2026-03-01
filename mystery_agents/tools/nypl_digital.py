"""NYPL Digital Collections API ソース。

ニューヨーク公共図書館のデジタル化コレクション（写本、地図、写真、
希少資料）を検索する。

plain_text エンドポイントによる OCR 全文テキスト取得にも対応。
"""

import logging
import os

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .fulltext_extraction import build_extraction_keywords, extract_keyword_passages
from .search_utils import build_search_query
from .source_registry import register_source

logger = logging.getLogger(__name__)

BASE_URL = "https://api.repo.nypl.org/api/v2/items/search"
_PLAIN_TEXT_URL = "https://api.repo.nypl.org/api/v2/items/plain_text/{uuid}"

# 全文取得の上限設定
_MAX_FULLTEXT_FETCHES = 10
_FULLTEXT_TIMEOUT = 15
_MAX_RAW_FETCH = 200_000


def _fetch_plain_text(
    session: requests.Session, uuid: str, token: str = ""
) -> str | None:
    """NYPL plain_text エンドポイントから OCR テキストを取得する。

    Args:
        session: HTTP セッション
        uuid: NYPL アイテムの UUID

    Returns:
        OCR テキスト（安全上限で切り詰め）。取得失敗時は None。
    """
    try:
        headers = {"User-Agent": "GhostInTheArchive/1.0"}
        if token:
            headers["Authorization"] = f'Token token="{token}"'
        resp = session.get(
            _PLAIN_TEXT_URL.format(uuid=uuid),
            timeout=_FULLTEXT_TIMEOUT,
            headers=headers,
        )
        if resp.status_code != 200:
            logger.debug("NYPL plain_text %d for UUID %s", resp.status_code, uuid)
            return None

        data = resp.json()
        # レスポンス構造: nyplAPI.response.text (文字列)
        text = (
            data.get("nyplAPI", {})
            .get("response", {})
            .get("text", "")
        )
        if not text or not isinstance(text, str):
            return None
        return text.strip()[:_MAX_RAW_FETCH]

    except (requests.RequestException, ValueError, KeyError) as e:
        logger.debug("NYPL plain_text 取得失敗 (UUID %s): %s", uuid, e)
        return None


class NYPLSource(ArchiveSource):
    """NYPL Digital Collections ソース。"""

    source_key = "nypl"
    source_name = "NYPL Digital Collections"
    source_type = "nypl"
    min_request_delay = 1.0
    supported_languages = {"en"}
    supports_language_filter = False
    is_newspaper_source = False
    expected_domains = ["digitalcollections.nypl.org", "nypl.org"]
    env_var_key = "NYPL_API_TOKEN"

    def _search_impl(
        self,
        keywords: list[str],
        date_start: str | None,
        date_end: str | None,
        max_results: int,
        language: str | None,
        reference_keywords: list[str] | None = None,
    ) -> ArchiveSearchResult:
        search_text = build_search_query(keywords)
        if not search_text:
            return ArchiveSearchResult(error="No keywords provided")

        # 空文字日付対応: 日付範囲をクエリに含めるのを条件付きに
        if date_start and date_end:
            start_year = date_start[:4] if len(date_start) >= 4 else date_start
            end_year = date_end[:4] if len(date_end) >= 4 else date_end
            search_text_with_date = f"{search_text} {start_year}-{end_year}"
        else:
            search_text_with_date = search_text

        params = {
            "q": search_text_with_date,
            "per_page": min(max_results, 100),
            "page": 1,
            "publicDomainOnly": "true",
        }

        token = os.environ.get("NYPL_API_TOKEN", "")
        response = self._session.get(
            BASE_URL,
            params=params,
            timeout=30,
            headers={
                "User-Agent": "GhostInTheArchive/1.0",
                "Authorization": f'Token token="{token}"',
            },
        )
        response.raise_for_status()
        data = response.json()

        documents = []
        # 全文取得対象の (index, uuid) ペア
        fulltext_targets: list[tuple[int, str]] = []

        nypl_response = data.get("nyplAPI", {}).get("response", {})
        results = nypl_response.get("result", [])
        if not isinstance(results, list):
            results = [results] if results else []

        for item in results:
            title = item.get("title", "Unknown Title")
            if isinstance(title, list):
                title = title[0] if title else "Unknown Title"

            uuid = item.get("uuid", "")
            url = f"https://digitalcollections.nypl.org/items/{uuid}" if uuid else ""
            if not url:
                continue

            date_str = item.get("dateDigitized", "")

            # サムネイル URL 構築（imageID から）
            image_id = item.get("imageID", "")
            thumbnail_url = (
                f"https://images.nypl.org/index.php?id={image_id}&t=w"
                if image_id
                else None
            )

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=self.parse_year(str(date_str)),
                source_url=url,
                summary=str(title)[:500],
                language=SourceLanguage.EN,
                location="New York",
                source_type=self.source_type,
                raw_text=None,
                thumbnail_url=thumbnail_url,
                keywords_matched=[
                    kw for kw in keywords if kw.lower() in str(title).lower()
                ],
            )
            documents.append(doc)

            # UUID が存在する場合は全文取得候補に追加（上位5件まで）
            if uuid and len(fulltext_targets) < _MAX_FULLTEXT_FETCHES:
                fulltext_targets.append((len(documents) - 1, uuid))

        # 全文テキストエンリッチメント（キーワード指向抽出）
        for idx, uuid in fulltext_targets:
            self._rate_limit()
            text = _fetch_plain_text(self._session, uuid, token=token)
            if text:
                extraction_kws = build_extraction_keywords(
                    keywords, title=documents[idx].title
                )
                documents[idx].raw_text = extract_keyword_passages(text, extraction_kws)

        total_hits = int(nypl_response.get("numResults", 0))
        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


# レジストリに自動登録
_instance = NYPLSource()
register_source(_instance)
