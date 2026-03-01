"""Trove API ソース（National Library of Australia）。

オーストラリア国立図書館の Trove API v3 を使用して
1803年以降の新聞 OCR 全文検索を行う。
"""

import os
from typing import Any

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .fulltext_extraction import build_extraction_keywords, extract_keyword_passages
from .search_utils import build_combined_query, build_search_query
from .source_registry import register_source

BASE_URL = "https://api.trove.nla.gov.au/v3/result"


class TroveSource(ArchiveSource):
    """Trove（オーストラリア国立図書館）ソース。"""

    source_key = "trove"
    source_name = "Trove (National Library of Australia)"
    source_type = "trove"
    min_request_delay = 0.5  # 200req/min → 余裕を持って 0.5s
    supported_languages = {"en"}
    supports_language_filter = False
    is_newspaper_source = True
    expected_domains = ["trove.nla.gov.au", "nla.gov.au"]
    env_var_key = "TROVE_API_KEY"

    def _search_impl(
        self,
        keywords: list[str],
        date_start: str | None,
        date_end: str | None,
        max_results: int,
        language: str | None,
        reference_keywords: list[str] | None = None,
    ) -> ArchiveSearchResult:
        api_key = os.environ.get("TROVE_API_KEY", "")

        search_text = (
            build_combined_query(reference_keywords, keywords)
            if reference_keywords
            else build_search_query(keywords)
        )
        if not search_text:
            return ArchiveSearchResult(error="No keywords provided")

        params: dict[str, Any] = {
            "key": api_key,
            "category": "newspaper",
            "q": search_text,
            "encoding": "json",
            "n": min(max_results, 100),
            "s": "*",
            "sortby": "relevance",
            "include": "articletext",
        }

        # decade フィルタ（年代絞り込み）
        # Trove API v3 は l-decade パラメータで単一 decade のみフィルタ可能。
        # 複数 decade にまたがる範囲は API がサポートしないためフィルタなし。
        # 結果が0件の場合は _search_single_source() の日付拡大フォールバックが発動する。
        if date_start and date_end:
            start_decade = int(date_start[:4]) // 10
            end_decade = int(date_end[:4]) // 10
            if start_decade == end_decade:
                params["l-decade"] = start_decade * 10

        headers = {
            "Accept": "application/json",
            "User-Agent": "GhostInTheArchive/1.0",
        }

        response = self._session.get(
            BASE_URL,
            params=params,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        documents = []
        # Trove v3 レスポンス構造: category[0].records.article
        categories = data.get("category", [])
        articles = []
        if categories:
            records = categories[0].get("records", {})
            articles = records.get("article", [])

        for article in articles:
            title = article.get("heading", "Unknown Title")
            date_str = article.get("date", "")
            trove_url = article.get("troveUrl", "")
            if not trove_url:
                continue

            # OCR 全文 or スニペット
            article_text = article.get("articleText", "")
            snippet = article.get("snippet", "")
            summary_text = snippet or (article_text[:500] if article_text else title)

            # 新聞タイトルから場所のヒント
            newspaper_title = article.get("title", {})
            if isinstance(newspaper_title, dict):
                location = newspaper_title.get("value", "Australia")
            elif isinstance(newspaper_title, str):
                location = newspaper_title
            else:
                location = "Australia"

            # キーワードマッチ
            combined = f"{title} {summary_text}".lower()
            matched = [kw for kw in keywords if kw.lower() in combined]

            # キーワード指向抽出（Trove はインラインで全文を取得）
            raw_text = None
            if article_text:
                extraction_kws = build_extraction_keywords(
                    keywords, title=str(title)
                )
                raw_text = extract_keyword_passages(article_text, extraction_kws)

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=self.parse_year(str(date_str), min_century=18),
                source_url=trove_url,
                summary=str(summary_text)[:500],
                language=SourceLanguage.EN,
                location=str(location)[:200],
                source_type=self.source_type,
                raw_text=raw_text,
                keywords_matched=matched,
            )
            documents.append(doc)

        total_hits = 0
        if categories:
            records = categories[0].get("records", {})
            total_hits = records.get("total", len(documents))

        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


# レジストリに自動登録
_instance = TroveSource()
register_source(_instance)
