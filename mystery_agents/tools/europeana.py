"""Europeana Search API ソース。

Europeana の集約コレクション（6,000+ の欧州文化遺産機関）を検索する。
wskey クエリパラメータ認証を使用。
Fulltext API v3 による全文テキスト取得にも対応。
"""

import logging
import os
from typing import Any

import requests

from ..schemas.document import ArchiveDocument
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .search_utils import build_combined_query, build_search_query
from .source_registry import register_source

logger = logging.getLogger(__name__)

BASE_URL = "https://api.europeana.eu/record/v2/search.json"
_FULLTEXT_URL = "https://api.europeana.eu/fulltext/v3/{dataset_id}/{local_id}"

# 全文取得の上限設定
_MAX_FULLTEXT_FETCHES = 10
_FULLTEXT_TIMEOUT = 15
_MAX_TEXT_LENGTH = 5000


def _extract_record_ids(europeana_id: str) -> tuple[str | None, str | None]:
    """Europeana item ID からデータセット ID とローカル ID を抽出する。

    ID 形式: /{datasetId}/{localId}
    例: /2020601/https___1702_uva_nl_object_dcp_id_...

    Args:
        europeana_id: Europeana アイテム ID

    Returns:
        (dataset_id, local_id) のタプル。パース失敗時は (None, None)。
    """
    if not europeana_id or not europeana_id.startswith("/"):
        return None, None
    parts = europeana_id.lstrip("/").split("/", 1)
    if len(parts) != 2:
        return None, None
    return parts[0], parts[1]


def _parse_annotation_text(data: dict) -> str | None:
    """IIIF Annotation JSON からテキストを抽出する。

    Europeana Fulltext API v3 は IIIF Annotation 形式で返す。
    AnnotationPage 直接のアイテムとネストされた AnnotationPage の
    両方に対応する。

    Args:
        data: IIIF Annotation JSON レスポンス

    Returns:
        抽出テキスト（最大5000文字）。テキストがない場合は None。
    """
    texts: list[str] = []
    for item in data.get("items", []):
        body = item.get("body", {})
        if isinstance(body, dict):
            value = body.get("value", "")
            if value:
                texts.append(value)
        # ネストされた AnnotationPage
        for nested in item.get("items", []):
            body = nested.get("body", {})
            if isinstance(body, dict):
                value = body.get("value", "")
                if value:
                    texts.append(value)
    if not texts:
        return None
    return "\n".join(texts)[:_MAX_TEXT_LENGTH]


def _fetch_fulltext(
    session: requests.Session,
    dataset_id: str,
    local_id: str,
    api_key: str,
) -> str | None:
    """Europeana Fulltext API v3 から全文テキストを取得する。

    Args:
        session: HTTP セッション
        dataset_id: Europeana データセット ID
        local_id: Europeana ローカル ID
        api_key: Europeana API キー

    Returns:
        全文テキスト（最大5000文字）。取得失敗時は None。
    """
    try:
        url = _FULLTEXT_URL.format(dataset_id=dataset_id, local_id=local_id)
        params: dict[str, str] = {}
        if api_key:
            params["wskey"] = api_key
        resp = session.get(
            url,
            timeout=_FULLTEXT_TIMEOUT,
            params=params,
            headers={
                "Accept": "application/ld+json",
                "User-Agent": "GhostInTheArchive/1.0",
            },
        )
        if resp.status_code != 200:
            logger.debug("Europeana fulltext %d for %s/%s", resp.status_code, dataset_id, local_id)
            return None
        return _parse_annotation_text(resp.json())
    except (requests.RequestException, ValueError, KeyError) as e:
        logger.debug("Europeana fulltext 取得失敗 (%s/%s): %s", dataset_id, local_id, e)
        return None

# 言語コード → Europeana COUNTRY フィルタ値マッピング
# LANGUAGE フィルタではなく COUNTRY フィルタを使用する理由:
# 歴史資料（特に 1650-1850 の医学テキスト等）はラテン語で書かれていることが多く、
# LANGUAGE:de では捕捉できない。COUNTRY フィルタは提供機関の所在国で絞り込むため、
# ドイツの機関が保管するラテン語文書もヒットする。
_LANG_TO_COUNTRY: dict[str, str] = {
    "de": "germany",
    "es": "spain",
    "fr": "france",
    "it": "italy",
    "nl": "netherlands",
    "pt": "portugal",
}


class EuropeanaSource(ArchiveSource):
    """Europeana ソース。"""

    source_key = "europeana"
    source_name = "Europeana"
    source_type = "europeana"
    min_request_delay = 1.0
    supported_languages = {"en", "de", "es", "fr", "nl", "pt"}
    supports_language_filter = True
    is_newspaper_source = False
    expected_domains = ["europeana.eu"]
    env_var_key = "EUROPEANA_API_KEY"

    def _search_impl(
        self,
        keywords: list[str],
        date_start: str | None,
        date_end: str | None,
        max_results: int,
        language: str | None,
        reference_keywords: list[str] | None = None,
    ) -> ArchiveSearchResult:
        api_key = os.environ.get("EUROPEANA_API_KEY", "")

        search_text = (
            build_combined_query(reference_keywords, keywords)
            if reference_keywords
            else build_search_query(keywords)
        )
        if not search_text:
            return ArchiveSearchResult(error="No keywords provided")

        params: dict[str, Any] = {
            "wskey": api_key,
            "query": search_text,
            "rows": min(max_results, 100),
            "start": 1,
            "profile": "standard",
        }

        # 空文字日付対応: フィルタを条件付きに
        qf_list: list[str] = []
        if date_start and date_end:
            qf_list.append(f"YEAR:[{date_start} TO {date_end}]")
        # COUNTRY フィルタ: 提供機関の所在国で絞り込む
        # LANGUAGE フィルタは歴史資料（ラテン語混在）を見逃すため不使用
        if language and language in _LANG_TO_COUNTRY:
            qf_list.append(f"COUNTRY:{_LANG_TO_COUNTRY[language]}")
        if qf_list:
            params["qf"] = qf_list

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
        # 全文取得対象の (index, europeana_id) ペア
        fulltext_targets: list[tuple[int, str]] = []
        items = data.get("items", [])

        for item in items:
            # タイトル抽出
            title = item.get("title", ["Unknown Title"])
            if isinstance(title, list):
                title = title[0] if title else "Unknown Title"

            # 説明文抽出
            description = ""
            dc_description = item.get("dcDescription", [])
            if isinstance(dc_description, list) and dc_description:
                description = str(dc_description[0])
            elif isinstance(dc_description, str):
                description = dc_description

            # URL 抽出（guid を優先、edmIsShownAt にフォールバック）
            url = item.get("guid", "")
            if not url:
                shown_at = item.get("edmIsShownAt", [])
                if isinstance(shown_at, list) and shown_at:
                    url = str(shown_at[0])
                elif isinstance(shown_at, str):
                    url = shown_at
            if not url:
                continue

            # 日付抽出
            date_str = ""
            year = item.get("year", [])
            if isinstance(year, list) and year:
                date_str = str(year[0])
            elif isinstance(year, str):
                date_str = year

            # 言語検出
            lang = _detect_language(item)

            # 場所抽出
            location = _extract_location(item)

            # キーワードマッチ
            combined = f"{title} {description}".lower()
            matched = [kw for kw in keywords if kw.lower() in combined]

            # サムネイル / フル画像URL抽出
            edm_preview = item.get("edmPreview", [])
            thumbnail = edm_preview[0] if isinstance(edm_preview, list) and edm_preview else None
            edm_shown_by = item.get("edmIsShownBy", [])
            full_image = edm_shown_by[0] if isinstance(edm_shown_by, list) and edm_shown_by else None

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=self.parse_year(str(date_str), min_century=13),
                source_url=url,
                summary=str(description)[:500] if description else str(title)[:500],
                language=lang,
                location=str(location)[:200],
                source_type=self.source_type,
                raw_text=None,
                thumbnail_url=thumbnail,
                image_url=full_image,
                keywords_matched=matched,
            )
            documents.append(doc)

            # 全文取得候補に追加（上位5件まで）
            europeana_id = item.get("id", "")
            if europeana_id and len(fulltext_targets) < _MAX_FULLTEXT_FETCHES:
                fulltext_targets.append((len(documents) - 1, europeana_id))

        # 全文テキストエンリッチメント
        for idx, eid in fulltext_targets:
            self._rate_limit()
            ds_id, loc_id = _extract_record_ids(eid)
            if ds_id and loc_id:
                text = _fetch_fulltext(self._session, ds_id, loc_id, api_key)
                if text:
                    documents[idx].raw_text = text

        total_hits = data.get("totalResults", len(documents))
        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


def _detect_language(item: dict) -> str:
    """アイテムの language フィールドから ISO 639-1 コードを返す。

    API レスポンスの language フィールドをそのまま ISO 639-1 文字列として返す。
    フォールバック: "en"。
    """
    languages = item.get("language", [])
    if isinstance(languages, list):
        for lang in languages:
            if lang and len(lang.strip()) >= 2:
                return lang.strip().lower()[:2]
    elif isinstance(languages, str) and len(languages.strip()) >= 2:
        return languages.strip().lower()[:2]
    return "en"


def _extract_location(item: dict) -> str:
    """アイテムから場所情報を抽出する。"""
    place_labels = item.get("edmPlaceLabelLangAware", {})
    if isinstance(place_labels, dict):
        for key in ("en", "def"):
            if key in place_labels and place_labels[key]:
                labels = place_labels[key]
                if isinstance(labels, list) and labels:
                    return str(labels[0])[:200]

    country = item.get("country", [])
    if isinstance(country, list) and country:
        return str(country[0])[:200]
    elif isinstance(country, str) and country:
        return country[:200]

    return "Europe"


# レジストリに自動登録
_instance = EuropeanaSource()
register_source(_instance)
