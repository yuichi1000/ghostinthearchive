"""Unit tests for link validator."""

from unittest.mock import patch

import responses
from requests.exceptions import ConnectionError, InvalidURL, Timeout, TooManyRedirects

from mystery_agents.schemas.document import (
    ArchiveDocument,
    SourceLanguage,
)
from mystery_agents.tools.link_validator import (
    validate_documents,
    verify_link,
)


def _make_doc(
    url: str = "https://www.loc.gov/item/test123/",
    source_type: str = "loc_digital",
    title: str = "Test Document",
) -> ArchiveDocument:
    """テスト用 ArchiveDocument を生成するヘルパー。"""
    return ArchiveDocument(
        title=title,
        source_url=url,
        summary="A test document",
        language=SourceLanguage.EN,
        location="Test Location",
        source_type=source_type,
    )


class TestVerifyLink:
    """verify_link() のテスト。"""

    @responses.activate
    def test_reachable_url(self):
        """200 OK → is_reachable=True。"""
        url = "https://www.loc.gov/item/test123/"
        responses.add(responses.HEAD, url, status=200, content_type="text/html")

        result = verify_link(url, "loc_digital")

        assert result.is_reachable is True
        assert result.status_code == 200
        assert result.error is None
        assert result.check_duration_ms >= 0

    @responses.activate
    def test_404_not_found(self):
        """404 → is_reachable=False。"""
        url = "https://www.loc.gov/item/missing/"
        responses.add(responses.HEAD, url, status=404)

        result = verify_link(url, "loc_digital")

        assert result.is_reachable is False
        assert result.status_code == 404

    @responses.activate
    def test_403_forbidden(self):
        """403 → is_reachable=False。"""
        url = "https://www.loc.gov/item/forbidden/"
        responses.add(responses.HEAD, url, status=403)

        result = verify_link(url, "loc_digital")

        assert result.is_reachable is False
        assert result.status_code == 403

    @responses.activate
    def test_head_405_fallback_to_get(self):
        """HEAD→405、GET→200 にフォールバック。"""
        url = "https://www.loc.gov/item/no-head/"
        responses.add(responses.HEAD, url, status=405)
        responses.add(responses.GET, url, status=200, body=b"OK")

        result = verify_link(url, "loc_digital")

        assert result.is_reachable is True
        assert result.status_code == 200

    @responses.activate
    def test_timeout_handling(self):
        """Timeout 例外 → is_reachable=False + error 記録。"""
        url = "https://www.loc.gov/item/slow/"
        responses.add(responses.HEAD, url, body=Timeout("Connection timed out"))

        result = verify_link(url, "loc_digital")

        assert result.is_reachable is False
        assert result.status_code is None
        assert result.error is not None
        assert "timed out" in result.error.lower() or "timeout" in result.error.lower()

    @responses.activate
    def test_connection_error(self):
        """ConnectionError 例外 → is_reachable=False + error 記録。"""
        url = "https://www.loc.gov/item/down/"
        responses.add(responses.HEAD, url, body=ConnectionError("DNS resolution failed"))

        result = verify_link(url, "loc_digital")

        assert result.is_reachable is False
        assert result.status_code is None
        assert result.error is not None

    @responses.activate
    def test_redirect_domain_consistent(self):
        """同一ドメインへの 301 → is_domain_consistent=True。"""
        url = "https://www.loc.gov/item/old/"
        final_url = "https://www.loc.gov/item/new/"
        responses.add(
            responses.HEAD,
            url,
            status=301,
            headers={"Location": final_url},
        )
        responses.add(responses.HEAD, final_url, status=200)

        result = verify_link(url, "loc_digital")

        assert result.is_reachable is True
        assert result.is_domain_consistent is True
        assert result.final_url == final_url

    @responses.activate
    def test_redirect_domain_mismatch(self):
        """別ドメインへの 301 → is_domain_consistent=False。"""
        url = "https://www.loc.gov/item/moved/"
        final_url = "https://error.example.com/not-found"
        responses.add(
            responses.HEAD,
            url,
            status=301,
            headers={"Location": final_url},
        )
        responses.add(responses.HEAD, final_url, status=200)

        result = verify_link(url, "loc_digital")

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
        url = "https://www.loc.gov/item/loop/"
        responses.add(responses.HEAD, url, body=TooManyRedirects("Exceeded redirects"))

        result = verify_link(url, "loc_digital")

        assert result.is_reachable is False
        assert result.status_code is None
        assert result.error is not None

    @responses.activate
    def test_invalid_url_handling(self):
        """InvalidURL 例外 → is_reachable=False + error 記録。"""
        url = "https://www.loc.gov/item/bad\x00url/"
        responses.add(responses.HEAD, url, body=InvalidURL("Invalid URL"))

        result = verify_link(url, "loc_digital")

        assert result.is_reachable is False
        assert result.status_code is None
        assert result.error is not None


class TestValidateDocuments:
    """validate_documents() のテスト。"""

    @responses.activate
    def test_removes_404_documents(self):
        """404 ドキュメントは除外される。"""
        good_url = "https://www.loc.gov/item/good/"
        bad_url = "https://www.loc.gov/item/missing/"
        responses.add(responses.HEAD, good_url, status=200)
        responses.add(responses.HEAD, bad_url, status=404)

        docs = [_make_doc(url=good_url), _make_doc(url=bad_url, title="Missing")]
        summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 1
        assert summary.verified_documents[0].title == "Test Document"
        assert bad_url in summary.removed_urls

    @responses.activate
    def test_removes_410_documents(self):
        """410 Gone ドキュメントは除外される。"""
        url = "https://www.loc.gov/item/gone/"
        responses.add(responses.HEAD, url, status=410)

        docs = [_make_doc(url=url)]
        summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 0
        assert url in summary.removed_urls

    @responses.activate
    def test_removes_domain_mismatch(self):
        """ドメイン不一致ドキュメントは除外される。"""
        url = "https://www.loc.gov/item/redirected/"
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
        url = "https://www.loc.gov/item/forbidden/"
        responses.add(responses.HEAD, url, status=403)

        docs = [_make_doc(url=url)]
        summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 1

    @responses.activate
    def test_keeps_500_documents(self):
        """500 は保持（サーバー側の一時的問題）。"""
        url = "https://www.loc.gov/item/error/"
        responses.add(responses.HEAD, url, status=500)

        docs = [_make_doc(url=url)]
        summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 1

    @responses.activate
    def test_keeps_timeout_documents(self):
        """タイムアウトは保持（インフラ問題、リンク切れとは断定できない）。"""
        url = "https://www.loc.gov/item/slow/"
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
        url = "https://www.loc.gov/item/unchecked/"

        docs = [_make_doc(url=url)]
        with patch.dict("os.environ", {"ENABLE_LINK_VALIDATION": "false"}):
            summary = validate_documents(docs, domain_delay=0)

        assert len(summary.verified_documents) == 1
        assert summary.total_checked == 0

    @responses.activate
    def test_summary_counts_correct(self):
        """カウント値の正確性。"""
        ok_url = "https://www.loc.gov/item/ok/"
        gone_url = "https://www.loc.gov/item/gone/"
        err_url = "https://www.loc.gov/item/err/"
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
