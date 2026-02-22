"""DigitalNZ API ソース（ニュージーランド文化遺産）。

DigitalNZ Records API v3 を使用して
ニュージーランドの新聞・書籍・画像等の文化遺産コレクションを検索する。
認証不要（2021年に API キー要件撤廃）。JSON レスポンス。
"""

from typing import Any

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .search_utils import build_search_query
from .source_registry import register_source

BASE_URL = "https://api.digitalnz.org/v3/records.json"

# 取得フィールド（帯域節約のため明示指定）
_FIELDS = (
    "title,description,date,landing_url,"
    "content_partner,subject,placename,collection_title"
)


def _first_or_default(value: Any, default: str = "") -> str:
    """配列または文字列から先頭要素を取得する。

    DigitalNZ の多くのフィールドは配列で返される。
    配列なら先頭要素、文字列ならそのまま、それ以外はデフォルト値を返す。
    """
    if isinstance(value, list):
        return str(value[0]) if value else default
    if isinstance(value, str):
        return value
    return default


def _parse_date(date_value: Any) -> str:
    """date フィールドから YYYY-MM-DD を抽出する。

    DigitalNZ は date を ISO 8601 配列 ["1886-12-07T00:00:00.000Z"] で返す。
    先頭10文字（YYYY-MM-DD）を抽出する。
    """
    raw = _first_or_default(date_value)
    if not raw:
        return ""
    return raw[:10]


class DigitalNZSource(ArchiveSource):
    """DigitalNZ（ニュージーランド文化遺産）ソース。"""

    source_key = "digitalnz"
    source_name = "DigitalNZ (Digital New Zealand)"
    source_type = "digitalnz"
    min_request_delay = 1.0
    supported_languages = {"en"}
    supports_language_filter = False
    is_newspaper_source = False  # 新聞以外も含む総合コレクション
    expected_domains = [
        "digitalnz.org",
        "paperspast.natlib.govt.nz",
        "natlib.govt.nz",
    ]
    env_var_key = None  # API キー不要

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

        params: dict[str, Any] = {
            "text": search_text,
            "per_page": min(max_results, 100),
            "fields": _FIELDS,
        }

        # 年代フィルタ
        if date_start and date_end:
            start_year = date_start[:4]
            end_year = date_end[:4]
            params["and[year]"] = f"[{start_year} TO {end_year}]"

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

        search_data = data.get("search", {})
        total_hits = search_data.get("result_count", 0)
        results = search_data.get("results", [])

        documents = []
        for record in results:
            # landing_url 必須（ない場合はスキップ）
            landing_url = record.get("landing_url", "")
            if not landing_url:
                continue

            title = record.get("title", "Unknown Title") or "Unknown Title"

            # description が null の場合は title にフォールバック
            description = record.get("description")
            summary = description if description else title

            # 日付パース
            date_str = _parse_date(record.get("date"))

            # 場所: placename を優先、なければ content_partner
            placename = _first_or_default(record.get("placename"))
            content_partner = _first_or_default(record.get("content_partner"))
            location = placename or content_partner or "New Zealand"

            # collection_title → record_group
            collection_title = _first_or_default(record.get("collection_title"))

            # キーワードマッチ（title + summary + subject）
            subjects = record.get("subject", [])
            subject_text = " ".join(subjects) if isinstance(subjects, list) else ""
            combined = f"{title} {summary} {subject_text}".lower()
            matched = [kw for kw in keywords if kw.lower() in combined]

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=self.parse_year(str(date_str), min_century=13) if date_str else None,
                source_url=landing_url,
                summary=str(summary)[:500],
                language=SourceLanguage.EN,
                location=str(location)[:200],
                source_type=self.source_type,
                raw_text=None,  # DigitalNZ は全文テキスト提供なし
                record_group=collection_title if collection_title else None,
                keywords_matched=matched,
            )
            documents.append(doc)

        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


# レジストリに自動登録
_instance = DigitalNZSource()
register_source(_instance)
