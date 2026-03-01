"""KB/Delpher API ソース（Koninklijke Bibliotheek / オランダ国立図書館）。

SRU v1.2 プロトコルでオランダ語の歴史的新聞・書籍（1618年〜）を検索する。
認証不要（API キー不要）。レスポンスは Dublin Core XML。
resolver URL + :ocr サフィックスによる OCR 全文テキスト取得にも対応。
"""

import logging
import xml.etree.ElementTree as ET

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .fulltext_extraction import build_extraction_keywords, extract_keyword_passages
from .search_utils import build_search_query
from .source_registry import register_source

logger = logging.getLogger(__name__)

BASE_URL = "https://jsru.kb.nl/sru/sru"
COLLECTION = "DDD_artikel"

# 全文取得の上限設定
_MAX_FULLTEXT_FETCHES = 5
_FULLTEXT_TIMEOUT = 15
_MAX_RAW_FETCH = 200_000


def _fetch_ocr_text(
    session: requests.Session, resolver_url: str
) -> str | None:
    """Delpher resolver URL から OCR テキストを取得する。

    resolver URL に :ocr サフィックスを付けてリクエストする。

    Args:
        session: HTTP セッション
        resolver_url: Delpher resolver URL（例: http://resolver.kb.nl/resolve?urn=...）

    Returns:
        OCR テキスト（安全上限で切り詰め）。取得失敗時は None。
    """
    try:
        ocr_url = f"{resolver_url.rstrip('/')}:ocr"
        resp = session.get(
            ocr_url,
            timeout=_FULLTEXT_TIMEOUT,
            headers={"User-Agent": "GhostInTheArchive/1.0"},
        )
        if resp.status_code != 200:
            logger.debug("Delpher OCR %d for %s", resp.status_code, resolver_url)
            return None
        text = resp.text.strip()
        return text[:_MAX_RAW_FETCH] if text else None
    except (requests.RequestException, ValueError) as e:
        logger.debug("Delpher OCR 取得失敗 (%s): %s", resolver_url, e)
        return None

# SRU / Dublin Core 名前空間
NS = {
    "srw": "http://www.loc.gov/zing/srw/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "diag": "http://www.loc.gov/zing/srw/diagnostic/",
}


def _get_dc_text(record_data: ET.Element, tag: str) -> str:
    """Dublin Core 要素のテキストを取得するヘルパー。

    Args:
        record_data: recordData 要素
        tag: DC 要素名（例: "title", "date"）

    Returns:
        要素のテキスト。見つからない場合は空文字列。
    """
    elem = record_data.find(f"dc:{tag}", NS)
    if elem is not None and elem.text:
        return elem.text.strip()
    return ""


def _parse_sru_response(
    xml_text: str, keywords: list[str]
) -> ArchiveSearchResult:
    """SRU XML レスポンスをパースして ArchiveSearchResult を返す。

    Args:
        xml_text: SRU レスポンスの XML 文字列
        keywords: マッチ検出用のキーワードリスト

    Returns:
        パース済みの ArchiveSearchResult
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning("Delpher SRU XML パースエラー: %s", e)
        return ArchiveSearchResult(error=f"XML parse error: {e}")

    # 総ヒット数
    num_records_elem = root.find(".//srw:numberOfRecords", NS)
    total_hits = int(num_records_elem.text) if num_records_elem is not None and num_records_elem.text else 0

    documents = []
    for record in root.findall(".//srw:record", NS):
        data = record.find("srw:recordData", NS)
        if data is None:
            continue

        # identifier（URL）がないレコードはスキップ
        identifier = _get_dc_text(data, "identifier")
        if not identifier:
            continue

        title = _get_dc_text(data, "title") or "Unknown Title"
        date_str = _get_dc_text(data, "date")
        description = _get_dc_text(data, "description")
        publisher = _get_dc_text(data, "publisher")
        source = _get_dc_text(data, "source")

        # 場所のヒント: publisher or source
        location = publisher or source or "Netherlands"

        # サマリー: description があればそれを使う、なければ title
        summary_text = description or title

        # キーワードマッチ
        combined = f"{title} {description}".lower()
        matched = [kw for kw in keywords if kw.lower() in combined]

        # 日付パース（"YYYY/MM/DD HH:MM:SS" 形式 → "YYYY-01-01"）
        parsed_date = None
        if date_str:
            # "YYYY/MM/DD ..." → YYYY 部分を抽出
            year_part = date_str.split("/")[0] if "/" in date_str else date_str
            parsed_date = ArchiveSource.parse_year(year_part, min_century=16)

        doc = ArchiveDocument(
            title=str(title)[:500],
            date=parsed_date,
            source_url=identifier,
            summary=str(summary_text)[:500],
            language=SourceLanguage.NL,
            location=str(location)[:200],
            source_type="delpher",
            raw_text=None,
            keywords_matched=matched,
        )
        documents.append(doc)

    return ArchiveSearchResult(documents=documents, total_hits=total_hits)


class DelpherSource(ArchiveSource):
    """KB/Delpher（オランダ国立図書館）ソース。"""

    source_key = "delpher"
    source_name = "KB/Delpher (Koninklijke Bibliotheek)"
    source_type = "delpher"
    min_request_delay = 2.0  # 公開 API への配慮
    supported_languages = {"nl"}
    supports_language_filter = False
    is_newspaper_source = False
    expected_domains = ["kb.nl", "delpher.nl", "resolver.kb.nl"]
    env_var_key = None  # 認証不要

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

        # CQL クエリ構築（年代フィルタ: dc.date への範囲比較）
        if date_start and date_end:
            start_year = date_start[:4] if len(date_start) >= 4 else date_start
            end_year = date_end[:4] if len(date_end) >= 4 else date_end
            query = f'({search_text}) AND dc.date >= "{start_year}" AND dc.date <= "{end_year}"'
        else:
            query = search_text

        params = {
            "operation": "searchRetrieve",
            "version": "1.2",
            "x-collection": COLLECTION,
            "query": query,
            "maximumRecords": min(max_results, 100),
            "recordSchema": "dc",
        }

        headers = {
            "Accept": "application/xml",
            "User-Agent": "GhostInTheArchive/1.0",
        }

        response = self._session.get(
            BASE_URL,
            params=params,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()

        result = _parse_sru_response(response.text, keywords)
        if result.error or not result.documents:
            return result

        # 全文テキストエンリッチメント（resolver URL + :ocr）
        fulltext_targets: list[tuple[int, str]] = []
        for idx, doc in enumerate(result.documents):
            if doc.source_url and len(fulltext_targets) < _MAX_FULLTEXT_FETCHES:
                fulltext_targets.append((idx, doc.source_url))

        for idx, url in fulltext_targets:
            self._rate_limit()
            text = _fetch_ocr_text(self._session, url)
            if text:
                extraction_kws = build_extraction_keywords(
                    keywords, title=result.documents[idx].title
                )
                result.documents[idx].raw_text = extract_keyword_passages(
                    text, extraction_kws
                )

        # 全文取得成功したドキュメントのみ保持
        filtered = [doc for doc in result.documents if doc.raw_text]
        return ArchiveSearchResult(documents=filtered, total_hits=result.total_hits)


# レジストリに自動登録
_instance = DelpherSource()
register_source(_instance)
