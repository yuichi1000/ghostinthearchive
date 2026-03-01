"""Internet Archive (Archive.org) Search API ソース。

Internet Archive の膨大なコレクション（書籍、雑誌、ウェブページ、
その他のデジタル化資料）を検索する。
djvu.txt エンドポイントによる OCR 全文テキスト取得にも対応。
"""

import logging

import requests

from ..schemas.document import ArchiveDocument
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .fulltext_extraction import build_extraction_keywords, extract_keyword_passages
from .search_utils import build_search_query
from .source_registry import register_source

logger = logging.getLogger(__name__)

BASE_URL = "https://archive.org/advancedsearch.php"
_DJVU_TEXT_URL = "https://archive.org/download/{identifier}/{identifier}_djvu.txt"

# 全文取得の上限設定
_MAX_FULLTEXT_FETCHES = 5
_FULLTEXT_TIMEOUT = 15
_MAX_RAW_FETCH = 200_000


def _fetch_djvu_text(
    session: requests.Session, identifier: str
) -> str | None:
    """Internet Archive の djvu.txt から OCR テキストを取得する。

    Args:
        session: HTTP セッション
        identifier: Internet Archive アイテム識別子

    Returns:
        OCR テキスト（安全上限で切り詰め）。取得失敗時は None。
    """
    try:
        url = _DJVU_TEXT_URL.format(identifier=identifier)
        resp = session.get(
            url,
            timeout=_FULLTEXT_TIMEOUT,
            headers={"User-Agent": "GhostInTheArchive/1.0"},
        )
        if resp.status_code != 200:
            logger.debug("IA djvu.txt %d for %s", resp.status_code, identifier)
            return None
        text = resp.text.strip()
        return text[:_MAX_RAW_FETCH] if text else None
    except (requests.RequestException, ValueError) as e:
        logger.debug("IA djvu.txt 取得失敗 (%s): %s", identifier, e)
        return None

_LANG_CODE_MAP = {
    "en": ["eng", "english"],
    "es": ["spa", "spanish", "español"],
    "de": ["ger", "deu", "german", "deutsch"],
    "fr": ["fre", "fra", "french", "français"],
    "nl": ["dut", "nld", "dutch", "nederlands"],
    "pt": ["por", "portuguese", "português"],
    "ja": ["jpn", "japanese"],
}


class InternetArchiveSource(ArchiveSource):
    """Internet Archive ソース。"""

    source_key = "internet_archive"
    source_name = "Internet Archive"
    source_type = "internet_archive"
    min_request_delay = 2.0
    supported_languages = {"en", "es", "de", "fr", "nl", "pt", "ja"}
    supports_language_filter = True
    is_newspaper_source = False
    expected_domains = ["archive.org"]
    env_var_key = None

    def _search_impl(
        self,
        keywords: list[str],
        date_start: str | None,
        date_end: str | None,
        max_results: int,
        language: str | None,
    ) -> ArchiveSearchResult:
        search_text = build_search_query(keywords)
        if not search_text:
            return ArchiveSearchResult(error="No keywords provided")

        # 空文字日付対応: 日付フィルタを条件付きに
        query = f"({search_text})"
        if date_start and date_end:
            start_year = date_start[:4] if len(date_start) >= 4 else date_start
            end_year = date_end[:4] if len(date_end) >= 4 else date_end
            query += f" AND date:[{start_year}-01-01 TO {end_year}-12-31]"

        # 言語フィルタ
        if language and language in _LANG_CODE_MAP:
            lang_codes = _LANG_CODE_MAP[language]
            lang_filter = " OR ".join(f'language:"{code}"' for code in lang_codes)
            query = f"{query} AND ({lang_filter})"

        params = {
            "q": query,
            "fl[]": [
                "identifier",
                "title",
                "description",
                "date",
                "language",
                "subject",
                "creator",
            ],
            "sort[]": "date asc",
            "rows": min(max_results, 100),
            "page": 1,
            "output": "json",
        }

        response = self._session.get(
            BASE_URL,
            params=params,
            timeout=30,
            headers={"User-Agent": "GhostInTheArchive/1.0"},
        )
        response.raise_for_status()
        data = response.json()

        resp = data.get("response", {})
        documents = []
        # 全文取得対象の (index, identifier, subjects) タプル
        fulltext_targets: list[tuple[int, str, list[str]]] = []

        for item in resp.get("docs", []):
            title = item.get("title", "Unknown Title")
            if isinstance(title, list):
                title = title[0] if title else "Unknown Title"

            description = item.get("description", "")
            if isinstance(description, list):
                description = " ".join(str(d) for d in description)

            identifier = item.get("identifier", "")
            url = f"https://archive.org/details/{identifier}" if identifier else ""
            if not url:
                continue

            date_str = item.get("date", "")
            if isinstance(date_str, list) and date_str:
                date_str = str(date_str[0])

            item_language = item.get("language", "")
            if isinstance(item_language, list) and item_language:
                item_language = str(item_language[0])
            lang = _detect_source_language(str(item_language))

            combined = f"{title} {description}".lower()
            matched = [kw for kw in keywords if kw.lower() in combined]

            # サムネイル URL（identifier から構築）
            thumbnail_url = (
                f"https://archive.org/services/img/{identifier}" if identifier else None
            )

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=self.parse_year(str(date_str), min_century=13),
                source_url=url,
                summary=str(description)[:500] if description else str(title)[:500],
                language=lang,
                location="Unknown",
                source_type=self.source_type,
                raw_text=None,
                thumbnail_url=thumbnail_url,
                keywords_matched=matched,
            )
            documents.append(doc)

            # 全文取得候補に追加（上位5件まで）
            if identifier and len(fulltext_targets) < _MAX_FULLTEXT_FETCHES:
                subjects_raw = item.get("subject", [])
                if isinstance(subjects_raw, str):
                    subjects_raw = [subjects_raw]
                fulltext_targets.append((len(documents) - 1, identifier, subjects_raw))

        # 全文テキストエンリッチメント（キーワード指向抽出）
        for idx, ident, subjects in fulltext_targets:
            self._rate_limit()
            text = _fetch_djvu_text(self._session, ident)
            if text:
                extraction_kws = build_extraction_keywords(
                    keywords, title=documents[idx].title, subjects=subjects
                )
                documents[idx].raw_text = extract_keyword_passages(text, extraction_kws)

        # 全文取得成功したドキュメントのみ保持
        documents = [doc for doc in documents if doc.raw_text]

        total_hits = resp.get("numFound", 0)
        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


def _detect_source_language(lang_str: str) -> str:
    """メタデータの言語文字列から ISO 639-1 コードを返す。

    _LANG_CODE_MAP でマッピング可能ならそのコードを返す。
    不明な場合はフォールバックとして "en" を返す。
    """
    lower = lang_str.lower()
    for lang_code, identifiers in _LANG_CODE_MAP.items():
        for ident in identifiers:
            if ident in lower:
                return lang_code
    return "en"


# レジストリに自動登録
_instance = InternetArchiveSource()
register_source(_instance)
