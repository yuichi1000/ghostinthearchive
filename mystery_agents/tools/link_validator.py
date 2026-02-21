"""リンク品質検証モジュール。

Librarian が収集したドキュメントの source_url を HTTP HEAD で疎通確認し、
リンク切れ（404/410）やドメイン不一致のドキュメントを除外する。
"""

import logging
import os
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

import requests

from shared.http_retry import create_retry_session

from ..schemas.document import ArchiveDocument

logger = logging.getLogger(__name__)

# 確定リンク切れとみなすステータスコード
_DEAD_LINK_STATUSES = {404, 410}

# リンク検証は URL 数が多いためリトライ回数を抑制
_session = create_retry_session(retries=2)


@dataclass
class LinkCheckResult:
    """個別リンクの検証結果。"""

    url: str
    status_code: int | None  # None = 接続失敗
    is_reachable: bool  # 2xx/3xx なら True
    is_domain_consistent: bool  # 最終 URL ドメインが期待と一致
    final_url: str | None  # リダイレクト後の URL
    content_type: str | None
    error: str | None
    check_duration_ms: int


@dataclass
class ValidationSummary:
    """検証結果のサマリー。"""

    total_checked: int
    reachable: int
    unreachable: int
    domain_mismatch: int
    removed_urls: list[str]
    duration_ms: int
    verified_documents: list[ArchiveDocument] = field(default_factory=list)


def _get_expected_domains(source_type: str) -> list[str]:
    """source_type に対応する期待ドメインを Source Registry から取得する。

    Registry にソースが見つからない場合は空リスト（ドメイン検証スキップ）。
    """
    from .source_registry import get_all_sources

    for source in get_all_sources().values():
        if source.source_type == source_type:
            return source.expected_domains
    return []


def _check_domain_consistency(
    final_url: str, source_type: str
) -> bool:
    """最終 URL のドメインが期待ドメインと一致するか確認する。"""
    expected = _get_expected_domains(source_type)
    if not expected:
        # 期待ドメインが未定義または空 → ドメイン検証スキップ
        return True
    hostname = urlparse(final_url).hostname or ""
    return any(hostname.endswith(domain) for domain in expected)


def verify_link(
    url: str,
    source_type: str,
    timeout: float = 10.0,
) -> LinkCheckResult:
    """単一 URL の疎通を確認する。

    1. HEAD リクエストを送信
    2. 405（HEAD 非対応）の場合は GET にフォールバック
    3. ステータスコード < 400 なら is_reachable=True
    4. 最終 URL のドメインが期待と一致するか確認

    Args:
        url: 検証対象の URL
        source_type: ソースタイプ文字列（期待ドメイン判定用）
        timeout: リクエストタイムアウト（秒）

    Returns:
        LinkCheckResult
    """
    start = time.monotonic()
    try:
        resp = _session.head(url, timeout=timeout, allow_redirects=True)

        # HEAD 非対応の場合は GET にフォールバック
        if resp.status_code == 405:
            resp = _session.get(url, timeout=timeout, stream=True)
            resp.close()

        elapsed_ms = int((time.monotonic() - start) * 1000)
        final_url = resp.url if resp.url != url else None
        is_reachable = resp.status_code < 400
        check_url = final_url or url
        is_domain_consistent = _check_domain_consistency(check_url, source_type)

        logger.debug("Link OK: %s (%d, %dms)", url, resp.status_code, elapsed_ms)

        return LinkCheckResult(
            url=url,
            status_code=resp.status_code,
            is_reachable=is_reachable,
            is_domain_consistent=is_domain_consistent,
            final_url=final_url,
            content_type=resp.headers.get("Content-Type"),
            error=None,
            check_duration_ms=elapsed_ms,
        )

    except requests.exceptions.RequestException as exc:
        elapsed_ms = int((time.monotonic() - start) * 1000)
        logger.warning("Link check failed: %s (%s)", url, exc)
        return LinkCheckResult(
            url=url,
            status_code=None,
            is_reachable=False,
            is_domain_consistent=True,  # 接続失敗時はドメイン検証不能 → True
            final_url=None,
            content_type=None,
            error=str(exc),
            check_duration_ms=elapsed_ms,
        )


def validate_documents(
    documents: list[ArchiveDocument],
    timeout_per_link: float = 10.0,
    domain_delay: float = 1.0,
) -> ValidationSummary:
    """ドキュメントリストのリンクを一括検証する。

    除外条件（ドキュメント削除）:
      - ステータスコード 404 または 410（確定リンク切れ）
      - is_domain_consistent == False（別ドメインへのリダイレクト）

    保持条件（WARNING ログのみ）:
      - 403, 429, 5xx — サーバー側の一時的問題の可能性
      - タイムアウト / 接続エラー — リンク切れとは断定できない

    Args:
        documents: 検証対象の ArchiveDocument リスト
        timeout_per_link: 個別リンクのタイムアウト（秒）
        domain_delay: 同一ドメインへのリクエスト間隔（秒）

    Returns:
        ValidationSummary
    """
    # 環境変数で無効化可能
    enabled = os.environ.get("ENABLE_LINK_VALIDATION", "true").lower() == "true"
    if not enabled:
        return ValidationSummary(
            total_checked=0,
            reachable=0,
            unreachable=0,
            domain_mismatch=0,
            removed_urls=[],
            duration_ms=0,
            verified_documents=list(documents),
        )

    start = time.monotonic()
    verified = []
    removed_urls = []
    reachable_count = 0
    unreachable_count = 0
    domain_mismatch_count = 0

    # ドメインごとの最終リクエスト時刻（レートリミット用）
    last_request_by_domain: dict[str, float] = {}

    for doc in documents:
        # 同一ドメインへのレートリミット
        hostname = urlparse(doc.source_url).hostname or ""
        last_req = last_request_by_domain.get(hostname)
        if last_req is not None and domain_delay > 0:
            elapsed = time.monotonic() - last_req
            if elapsed < domain_delay:
                time.sleep(domain_delay - elapsed)

        result = verify_link(doc.source_url, doc.source_type, timeout=timeout_per_link)
        last_request_by_domain[hostname] = time.monotonic()

        if result.is_reachable:
            reachable_count += 1
        else:
            unreachable_count += 1

        if not result.is_domain_consistent:
            domain_mismatch_count += 1

        # 除外判定
        should_remove = False

        if result.status_code in _DEAD_LINK_STATUSES:
            logger.warning("Broken link removed: %s (status=%s)", doc.source_url, result.status_code)
            should_remove = True
        elif not result.is_domain_consistent:
            logger.warning(
                "Domain mismatch removed: %s -> %s", doc.source_url, result.final_url
            )
            should_remove = True
        elif not result.is_reachable and result.status_code is not None:
            # 403, 429, 5xx など — 保持するが警告
            logger.warning(
                "Link check inconclusive (keeping): %s (status=%s)",
                doc.source_url,
                result.status_code,
            )

        if should_remove:
            removed_urls.append(doc.source_url)
        else:
            verified.append(doc)

    total_ms = int((time.monotonic() - start) * 1000)
    logger.info(
        "Link validation: %d/%d reachable, %d removed (%dms)",
        reachable_count,
        len(documents),
        len(removed_urls),
        total_ms,
    )

    return ValidationSummary(
        total_checked=len(documents),
        reachable=reachable_count,
        unreachable=unreachable_count,
        domain_mismatch=domain_mismatch_count,
        removed_urls=removed_urls,
        duration_ms=total_ms,
        verified_documents=verified,
    )
