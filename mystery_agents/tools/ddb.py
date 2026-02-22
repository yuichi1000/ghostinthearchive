"""Deutsche Digitale Bibliothek (DDB) REST API ソース。

DDB の集約コレクション（ドイツの文化遺産機関）を検索する。
OAuth consumer key 認証を使用。
"""

import os
from typing import Optional

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .search_utils import build_search_query
from .source_registry import register_source

BASE_URL = "https://api.deutsche-digitale-bibliothek.de/search"
ITEM_URL = "https://www.deutsche-digitale-bibliothek.de/item"


class DDBSource(ArchiveSource):
    """Deutsche Digitale Bibliothek ソース。"""

    source_key = "ddb"
    source_name = "Deutsche Digitale Bibliothek"
    source_type = "ddb"
    min_request_delay = 1.0
    supported_languages = {"de"}
    supports_language_filter = False
    is_newspaper_source = False
    expected_domains = ["deutsche-digitale-bibliothek.de"]
    env_var_key = "DDB_API_KEY"

    def _search_impl(
        self,
        keywords: list[str],
        date_start: str | None,
        date_end: str | None,
        max_results: int,
        language: str | None,
    ) -> ArchiveSearchResult:
        api_key = os.environ.get("DDB_API_KEY", "")

        search_text = build_search_query(keywords)
        if not search_text:
            return ArchiveSearchResult(error="No keywords provided")

        # DDB は Lucene クエリ構文をサポート
        query = f"({search_text})"
        # 年代フィルタ: temporal フィールドへの Lucene 範囲クエリ
        if date_start and date_end:
            start_year = date_start[:4] if len(date_start) >= 4 else date_start
            end_year = date_end[:4] if len(date_end) >= 4 else date_end
            query += f" AND temporal:[{start_year} TO {end_year}]"

        params = {
            "query": query,
            "rows": min(max_results, 100),
            "offset": 0,
        }

        headers = {
            "Authorization": f'OAuth oauth_consumer_key="{api_key}"',
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
        results = data.get("results", [])
        if isinstance(results, list):
            items = results
        else:
            items = results.get("docs", []) if isinstance(results, dict) else []

        for item in items:
            title = item.get("title", item.get("label", "Unknown Title"))
            if isinstance(title, list):
                title = title[0] if title else "Unknown Title"

            subtitle = item.get("subtitle", "")
            description = subtitle if subtitle else str(title)

            # DDB アイテム ID から URL 生成
            item_id = item.get("id", "")
            url = f"{ITEM_URL}/{item_id}" if item_id else ""
            if not url:
                continue

            # 日付情報
            date_str = ""
            temporal = item.get("temporal", item.get("date", ""))
            if isinstance(temporal, list) and temporal:
                date_str = str(temporal[0])
            elif isinstance(temporal, str):
                date_str = temporal

            # 場所の取得
            location = "Germany"
            place = item.get("place", item.get("spatial", ""))
            if isinstance(place, list) and place:
                location = str(place[0])
            elif isinstance(place, str) and place:
                location = place

            combined = f"{title} {description}".lower()
            matched = [kw for kw in keywords if kw.lower() in combined]

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=self.parse_year(str(date_str), min_century=13),
                source_url=url,
                summary=str(description)[:500] if description else str(title)[:500],
                language=SourceLanguage.DE,
                location=str(location)[:200],
                source_type=self.source_type,
                raw_text=str(description)[:5000] if description else None,
                keywords_matched=matched,
            )
            documents.append(doc)

        total_hits = data.get("numberOfResults", data.get("numFound", len(documents)))
        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


# レジストリに自動登録
_instance = DDBSource()
register_source(_instance)
