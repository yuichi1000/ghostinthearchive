"""Deutsche Digitale Bibliothek (DDB) REST API tool.

Searches the DDB aggregated collections from German cultural heritage
institutions. Uses OAuth consumer key authentication.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage, SourceType
from .search_utils import build_search_query

BASE_URL = "https://api.deutsche-digitale-bibliothek.de/search"
ITEM_URL = "https://www.deutsche-digitale-bibliothek.de/item"
MIN_REQUEST_DELAY = 1.0
_last_request_time = 0.0


def _rate_limit() -> None:
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_REQUEST_DELAY:
        time.sleep(MIN_REQUEST_DELAY - elapsed)
    _last_request_time = time.time()


def search_ddb(
    keywords: List[str],
    date_start: str = "1800",
    date_end: str = "1899",
    max_results: int = 20,
) -> Dict[str, Any]:
    """Search Deutsche Digitale Bibliothek for historical materials.

    Args:
        keywords: List of search keywords
        date_start: Start year
        date_end: End year
        max_results: Maximum results to return

    Returns:
        Dict with documents, total_hits, error keys.
    """
    api_key = os.environ.get("DDB_API_KEY", "")
    if not api_key:
        return {"documents": [], "total_hits": 0, "error": "DDB_API_KEY not set"}

    search_text = build_search_query(keywords)
    if not search_text:
        return {"documents": [], "total_hits": 0, "error": "No keywords provided"}

    # DDB は Lucene クエリ構文をサポート
    # 日付フィルタは temporal.begin_time / temporal.end_time ファセットで絞り込み
    query = f"({search_text})"

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

    _rate_limit()

    try:
        response = requests.get(
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

            # DDB は基本的にドイツ語資料
            lang = SourceLanguage.DE

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
                date=_parse_year(str(date_str)),
                source_url=url,
                summary=str(description)[:500] if description else str(title)[:500],
                language=lang,
                location=str(location)[:200],
                source_type=SourceType.DDB,
                raw_text=str(description)[:5000] if description else None,
                keywords_matched=matched,
            )
            documents.append(doc)

        total_hits = data.get("numberOfResults", data.get("numFound", len(documents)))
        return {"documents": documents, "total_hits": total_hits, "error": None}

    except (requests.RequestException, json.JSONDecodeError) as e:
        return {"documents": [], "total_hits": 0, "error": f"DDB API error: {e}"}


def _parse_year(date_str: str) -> Optional[str]:
    if not date_str:
        return None
    import re
    year_match = re.search(r"\b(1[3-9]\d{2}|20\d{2})\b", date_str)
    if year_match:
        return f"{year_match.group(1)}-01-01"
    return date_str[:10] if len(date_str) > 10 else date_str
