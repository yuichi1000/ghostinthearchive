"""NDL Search API ソース（国立国会図書館サーチ）。

国立国会図書館サーチの OpenSearch API を使用して
日本語の書籍・雑誌・写本等を検索する。
認証不要、RSS 2.0 XML レスポンス。

NDL Lab API（https://lab.ndl.go.jp/）による OCR 全文テキスト取得にも対応。
"""

import logging
import re
import xml.etree.ElementTree as ET

import requests

from ..schemas.document import ArchiveDocument, SourceLanguage
from .archive_source_base import ArchiveSearchResult, ArchiveSource
from .fulltext_extraction import build_extraction_keywords, extract_keyword_passages
from .source_registry import register_source

logger = logging.getLogger(__name__)

# archive_source_base.py に統一された strip_html を使用
_strip_html = ArchiveSource.strip_html

BASE_URL = "https://ndlsearch.ndl.go.jp/api/opensearch"
_NDL_LAB_URL = "https://lab.ndl.go.jp/dl/api/book/layouttext/{pid}"

# 全文取得の上限設定
_MAX_FULLTEXT_FETCHES = 10
_FULLTEXT_TIMEOUT = 15
_MAX_RAW_FETCH = 200_000

# RSS 2.0 + Dublin Core 等の XML 名前空間
_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcndl": "http://ndl.go.jp/dcndl/terms/",
    "openSearch": "http://a9.com/-/spec/opensearchrss/1.0/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
}


def _extract_pid(url: str) -> str | None:
    """NDL デジタルコレクション URL から PID を抽出する。

    Args:
        url: dl.ndl.go.jp/pid/12345 形式の URL

    Returns:
        PID 文字列。抽出できない場合は None。
    """
    match = re.search(r"dl\.ndl\.go\.jp/pid/(\d+)", url)
    return match.group(1) if match else None


def _fetch_fulltext(session: requests.Session, pid: str) -> str | None:
    """NDL Lab API で OCR 全文テキストを取得する。

    NDL Lab の layouttext API は pages/blocks/lines 構造の JSON を返す。
    各ページの各ブロックの各行からテキストを抽出して結合する。

    Args:
        session: HTTP セッション
        pid: NDL デジタルコレクションの PID

    Returns:
        OCR テキスト（安全上限で切り詰め）。取得失敗時は None。
    """
    try:
        resp = session.get(
            _NDL_LAB_URL.format(pid=pid),
            timeout=_FULLTEXT_TIMEOUT,
            headers={"User-Agent": "GhostInTheArchive/1.0"},
        )
        if resp.status_code != 200:
            logger.debug("NDL Lab API %d for PID %s", resp.status_code, pid)
            return None

        data = resp.json()
        lines: list[str] = []
        for page in data if isinstance(data, list) else [data]:
            for block in page.get("blocks", []):
                for line in block.get("lines", []):
                    text = line.get("text", "")
                    if text:
                        lines.append(text)

        if not lines:
            return None
        return "\n".join(lines)[:_MAX_RAW_FETCH]

    except (requests.RequestException, ValueError, KeyError) as e:
        logger.debug("NDL Lab 全文取得失敗 (PID %s): %s", pid, e)
        return None


class NDLSearchSource(ArchiveSource):
    """NDL Search（国立国会図書館サーチ）ソース。"""

    source_key = "ndl"
    source_name = "NDL Search (National Diet Library)"
    source_type = "ndl"
    min_request_delay = 1.0
    supported_languages = {"ja"}
    supports_language_filter = False
    is_newspaper_source = False
    expected_domains = ["ndlsearch.ndl.go.jp", "dl.ndl.go.jp"]
    env_var_key = None  # API キー不要

    def _search_impl(
        self,
        keywords: list[str],
        date_start: str | None,
        date_end: str | None,
        max_results: int,
        language: str | None,
    ) -> ArchiveSearchResult:
        # キーワードをスペース区切りで結合（NDL 側でトークナイズされるため OR/quote ロジック不要）
        search_text = " ".join(kw.strip() for kw in keywords if kw.strip())
        if not search_text:
            return ArchiveSearchResult(error="No keywords provided")

        params: dict[str, str | int] = {
            "any": search_text,
            "cnt": min(max_results, 100),
        }

        # 年代フィルタ
        if date_start:
            params["from"] = date_start[:4]
        if date_end:
            params["until"] = date_end[:4]

        response = self._session.get(
            BASE_URL,
            params=params,
            timeout=30,
            headers={"User-Agent": "GhostInTheArchive/1.0"},
        )
        response.raise_for_status()

        # RSS 2.0 XML パース
        root = ET.fromstring(response.content)
        channel = root.find("channel")
        if channel is None:
            return ArchiveSearchResult()

        # 総ヒット数
        total_el = channel.find("openSearch:totalResults", _NS)
        total_hits = int(total_el.text) if total_el is not None and total_el.text else 0

        documents = []
        # 全文取得対象の (index, pid) ペア
        fulltext_targets: list[tuple[int, str]] = []

        for item in channel.findall("item"):
            title_el = item.find("title")
            title = title_el.text if title_el is not None and title_el.text else "Unknown Title"

            # URL: rdfs:seeAlso（デジタルコンテンツ直リンク）を優先、なければ link（カタログページ）
            source_url = ""
            see_also = item.find("rdfs:seeAlso", _NS)
            if see_also is not None:
                source_url = see_also.get(f"{{{_NS['rdf']}}}resource", "")
            if not source_url:
                link_el = item.find("link")
                source_url = link_el.text if link_el is not None and link_el.text else ""
            if not source_url:
                continue

            # 日付
            date_el = item.find("dc:date", _NS)
            date_str = date_el.text if date_el is not None and date_el.text else ""

            # 説明（HTML タグ除去）
            desc_el = item.find("dc:description", _NS)
            summary = ""
            if desc_el is not None and desc_el.text:
                summary = _strip_html(desc_el.text)

            # 出版地
            place_el = item.find("dcndl:publicationPlace", _NS)
            location = place_el.text if place_el is not None and place_el.text else "Japan"

            # キーワードマッチ
            combined = f"{title} {summary}".lower()
            matched = [kw for kw in keywords if kw.lower() in combined]

            doc = ArchiveDocument(
                title=str(title)[:500],
                date=self.parse_year(str(date_str), min_century=13),
                source_url=source_url,
                summary=str(summary)[:500] if summary else str(title)[:500],
                language=SourceLanguage.JA,
                location=str(location)[:200],
                source_type=self.source_type,
                raw_text=None,
                keywords_matched=matched,
            )
            documents.append(doc)

            # PID が抽出できる場合は全文取得候補に追加（上位5件まで）
            pid = _extract_pid(source_url)
            if pid and len(fulltext_targets) < _MAX_FULLTEXT_FETCHES:
                fulltext_targets.append((len(documents) - 1, pid))

        # 全文テキストエンリッチメント（キーワード指向抽出）
        for idx, pid in fulltext_targets:
            self._rate_limit()
            text = _fetch_fulltext(self._session, pid)
            if text:
                extraction_kws = build_extraction_keywords(
                    keywords, title=documents[idx].title
                )
                documents[idx].raw_text = extract_keyword_passages(text, extraction_kws)

        return ArchiveSearchResult(documents=documents, total_hits=total_hits)


# レジストリに自動登録
_instance = NDLSearchSource()
register_source(_instance)
