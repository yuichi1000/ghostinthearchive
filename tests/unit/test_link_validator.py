"""Unit tests for link validator."""

import time
from unittest.mock import patch

import responses
from requests.exceptions import ConnectionError, InvalidURL, Timeout, TooManyRedirects

from mystery_agents.tools.link_validator import (
    LinkCheckResult,
    validate_documents,
    verify_link,
)
from tests.fakes import make_archive_doc as _make_doc


class TestVerifyLink:
    """verify_link() のテスト。"""

    @responses.activate
    def test_reachable_url(self):
        """200 OK → is_reachable=True。"""
        url = "https://digitalcollections.nypl.org/item/test123/"
        responses.add(responses.HEAD, url, status=200, content_type="text/html")

        result = verify_link(url, "nypl")

        assert result.is_reachable is True
        assert result.status_code == 200
        assert result.error is None
        assert result.check_duration_ms >= 0

    @responses.activate
    def test_404_not_found(self):
        """404 → is_reachable=False。"""
        url = "https://digitalcollections.nypl.org/item/missing/"
        responses.add(responses.HEAD, url, status=404)

        result = verify_link(url, "nypl")

        assert result.is_reachable is False
        assert result.status_code == 404

    @responses.activate
    def test_403_forbidden(self):
        """403 → is_reachable=False。"""
        url = "https://digitalcollections.nypl.org/item/forbidden/"
        responses.add(responses.HEAD, url, status=403)

        result = verify_link(url, "nypl")

        assert result.is_reachable is False
        assert result.status_code == 403

    @responses.activate
    def test_head_405_fallback_to_get(self):
        """HEAD→405、GET→200 にフォールバック。"""
        url = "https://digitalcollections.nypl.org/item/no-head/"
        responses.add(responses.HEAD, url, status=405)
        responses.add(responses.GET, url, status=200, body=b"OK")

        result = verify_link(url, "nypl")

        assert result.is_reachable is True
        assert result.status_code == 200

    @responses.activate
    def test_timeout_handling(self):
        """Timeout 例外 → is_reachable=False + error 記録。"""
        url = "https://digitalcollections.nypl.org/item/slow/"
        responses.add(responses.HEAD, url, body=Timeout("Connection timed out"))

        result = verify_link(url, "nypl")

        assert result.is_reachable is False
        assert result.status_code is None
        assert result.error is not None
        assert "timed out" in result.error.lower() or "timeout" in result.error.lower()

    @responses.activate
    def test_connection_error(self):
        """ConnectionError 例外 → is_reachable=False + error 記録。"""
        url = "https://digitalcollections.nypl.org/item/down/"
        responses.add(responses.HEAD, url, body=ConnectionError("DNS resolution failed"))

        result = verify_link(url, "nypl")

        assert result.is_reachable is False
        assert result.status_code is None
        assert result.error is not None

    @responses.activate
    def test_redirect_domain_consistent(self):
        """同一ドメインへの 301 → is_domain_consistent=True。"""
        url = "https://digitalcollections.nypl.org/item/old/"
        final_url = "https://digitalcollections.nypl.org/item/new/"
        responses.add(
            responses.HEAD,
            url,
            status=301,
            headers={"Location": final_url},
        )
        responses.add(responses.HEAD, final_url, status=200)

        result = verify_link(url, "nypl")

        assert result.is_reachable is True
        assert result.is_domain_consistent is True
        assert result.final_url == final_url

    @responses.activate
    def test_redirect_domain_mismatch(self):
        """別ドメインへの 301 → is_domain_consistent=False。"""
        url = "https://digitalcollections.nypl.org/item/moved/"
        final_url = "https://error.example.com/not-found"
        responses.add(
            responses.HEAD,
            url,
            status=301,
            headers={"Location": final_url},
        )
        responses.add(responses.HEAD, final_url, status=200)

        result = verify_link(url, "nypl")

        assert result.is_reachable is True
        assert result.is_domain_consistent is False
        assert result.final_url == final_url

    @responses.activate
    def test_dpla_skips_domain_check(self):
        """DPLA は任意ドメインでも is_domain_consistent=True。"""
        url = "https://partner-museum.org/item/123"
        responses.add(responses.HEAD, url, status=200)

        result = verify_link(url, "dpla")

        assert result.is_reachable is True
        assert result.is_domain_consistent is True

    @responses.activate
    def test_too_many_redirects_handling(self):
        """TooManyRedirects 例外 → is_reachable=False + error 記録。"""
        url = "https://digitalcollections.nypl.org/item/loop/"
        responses.add(responses.HEAD, url, body=TooManyRedirects("Exceeded redirects"))

        result = verify_link(url, "nypl")

        assert result.is_reachable is False
        assert result.status_code is None
        assert result.error is not None

    @responses.activate
    def test_invalid_url_handling(self):
        """InvalidURL 例外 → is_reachable=False + error 記録。"""
        url = "https://digitalcollections.nypl.org/item/bad\x00url/"
        responses.add(responses.HEAD, url, body=InvalidURL("Invalid URL"))

        result = verify_link(url, "nypl")

        assert result.is_reachable is False
        assert result.status_code is None
        assert result.error is not None


class TestValidateDocuments:
    """validate_documents() のテスト。"""

    @responses.activate
    def test_removes_404_documents(self):
        """404 ドキュメントは除外される。"""
        good_url = "https://digitalcollections.nypl.org/item/good/"
        bad_url = "https://digitalcollections.nypl.org/item/missing/"
        responses.add(responses.HEAD, good_url, status=200)
        responses.add(responses.HEAD, bad_url, status=404)

        docs = [_make_doc(url=good_url), _make_doc(url=bad_url, title="Missing")]
        summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 1
        assert summary.verified_documents[0].title == "Test Doc"
        assert bad_url in summary.removed_urls

    @responses.activate
    def test_removes_410_documents(self):
        """410 Gone ドキュメントは除外される。"""
        url = "https://digitalcollections.nypl.org/item/gone/"
        responses.add(responses.HEAD, url, status=410)

        docs = [_make_doc(url=url)]
        summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 0
        assert url in summary.removed_urls

    @responses.activate
    def test_removes_domain_mismatch(self):
        """ドメイン不一致ドキュメントは除外される。"""
        url = "https://digitalcollections.nypl.org/item/redirected/"
        final_url = "https://error.example.com/oops"
        responses.add(
            responses.HEAD,
            url,
            status=301,
            headers={"Location": final_url},
        )
        responses.add(responses.HEAD, final_url, status=200)

        docs = [_make_doc(url=url)]
        summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 0
        assert url in summary.removed_urls

    @responses.activate
    def test_keeps_403_documents(self):
        """403 は保持（サーバー側の問題の可能性）。"""
        url = "https://digitalcollections.nypl.org/item/forbidden/"
        responses.add(responses.HEAD, url, status=403)

        docs = [_make_doc(url=url)]
        summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 1

    @responses.activate
    def test_keeps_500_documents(self):
        """500 は保持（サーバー側の一時的問題）。"""
        url = "https://digitalcollections.nypl.org/item/error/"
        responses.add(responses.HEAD, url, status=500)

        docs = [_make_doc(url=url)]
        summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 1

    @responses.activate
    def test_keeps_timeout_documents(self):
        """タイムアウトは保持（インフラ問題、リンク切れとは断定できない）。"""
        url = "https://digitalcollections.nypl.org/item/slow/"
        responses.add(responses.HEAD, url, body=Timeout("timed out"))

        docs = [_make_doc(url=url)]
        summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 1

    def test_empty_documents_list(self):
        """空リスト→ゼロカウント。"""
        summary = validate_documents([], domain_delay=0)

        assert summary.total_checked == 0
        assert summary.reachable == 0
        assert summary.unreachable == 0
        assert summary.domain_mismatch == 0
        assert len(summary.verified_documents) == 0
        assert len(summary.removed_urls) == 0

    @responses.activate
    def test_validation_disabled(self):
        """ENABLE_LINK_VALIDATION=false で全通過。"""
        url = "https://digitalcollections.nypl.org/item/unchecked/"

        docs = [_make_doc(url=url)]
        with patch.dict("os.environ", {"ENABLE_LINK_VALIDATION": "false"}):
            summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 1
        assert summary.total_checked == 0

    @responses.activate
    def test_summary_counts_correct(self):
        """カウント値の正確性。"""
        ok_url = "https://digitalcollections.nypl.org/item/ok/"
        gone_url = "https://digitalcollections.nypl.org/item/gone/"
        err_url = "https://digitalcollections.nypl.org/item/err/"
        responses.add(responses.HEAD, ok_url, status=200)
        responses.add(responses.HEAD, gone_url, status=404)
        responses.add(responses.HEAD, err_url, status=500)

        docs = [
            _make_doc(url=ok_url, title="OK"),
            _make_doc(url=gone_url, title="Gone"),
            _make_doc(url=err_url, title="Error"),
        ]
        summary = validate_documents(docs, domain_delay=0)

        assert summary.total_checked == 3
        assert summary.reachable == 1  # 200 のみ（500 は >= 400 なので unreachable）
        assert summary.unreachable == 2  # 404 + 500
        assert summary.domain_mismatch == 0
        assert len(summary.removed_urls) == 1
        assert len(summary.verified_documents) == 2

    def test_parallel_different_domains(self):
        """Should process different domains in parallel, not sequentially."""
        # 5つの異なるドメインに各1件ずつ。各検証に 0.3 秒かかる。
        # 逐次なら 0.3 * 5 = 1.5 秒以上、並列なら 0.3 秒程度で完了するはず。
        delay_per_link = 0.3
        domains = [
            "https://alpha.example.com/item/1",
            "https://bravo.example.com/item/2",
            "https://charlie.example.com/item/3",
            "https://delta.example.com/item/4",
            "https://echo.example.com/item/5",
        ]

        def _slow_verify(url, source_type, timeout=10.0):
            time.sleep(delay_per_link)
            return LinkCheckResult(
                url=url,
                status_code=200,
                is_reachable=True,
                is_domain_consistent=True,
                final_url=None,
                content_type="text/html",
                error=None,
                check_duration_ms=int(delay_per_link * 1000),
            )

        docs = [_make_doc(url=u, source_type="dpla") for u in domains]

        with patch(
            "mystery_agents.tools.link_validator.verify_link", side_effect=_slow_verify
        ):
            start = time.monotonic()
            summary = validate_documents(docs, domain_delay=0)
            elapsed = time.monotonic() - start

        assert summary.total_checked == 5
        assert len(summary.verified_documents) == 5
        # 並列実行なら逐次合計（1.5秒）の半分未満で完了するはず
        assert elapsed < delay_per_link * len(domains) * 0.5

    def test_same_domain_sequential(self):
        """Should process same-domain documents sequentially to respect rate limits."""
        # 同一ドメインに3件。domain_delay=0.3 秒。
        # 逐次なら domain_delay * (n-1) = 0.6 秒以上かかるはず。
        domain_delay = 0.3
        urls = [
            "https://same.example.com/item/1",
            "https://same.example.com/item/2",
            "https://same.example.com/item/3",
        ]

        call_times: list[float] = []

        def _tracking_verify(url, source_type, timeout=10.0):
            call_times.append(time.monotonic())
            return LinkCheckResult(
                url=url,
                status_code=200,
                is_reachable=True,
                is_domain_consistent=True,
                final_url=None,
                content_type="text/html",
                error=None,
                check_duration_ms=0,
            )

        docs = [_make_doc(url=u, source_type="dpla") for u in urls]

        with patch(
            "mystery_agents.tools.link_validator.verify_link",
            side_effect=_tracking_verify,
        ):
            start = time.monotonic()
            summary = validate_documents(docs, domain_delay=domain_delay)
            elapsed = time.monotonic() - start

        assert summary.total_checked == 3
        assert len(summary.verified_documents) == 3
        # 同一ドメイン3件は逐次処理されるため、domain_delay * (n-1) 以上かかる
        assert elapsed >= domain_delay * (len(urls) - 1) * 0.8  # マージン 20%
