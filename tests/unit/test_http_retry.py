"""Tests for shared/http_retry.py のリトライ動作検証。"""

import responses

from shared.http_retry import create_retry_session


class TestCreateRetrySession:
    """create_retry_session のテスト。"""

    def test_returns_session_with_adapters(self):
        """HTTPS/HTTP アダプタがマウントされている。"""
        session = create_retry_session()
        assert "https://" in session.adapters
        assert "http://" in session.adapters

    def test_custom_retries(self):
        """retries パラメータが適用される。"""
        session = create_retry_session(retries=5)
        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.total == 5

    def test_custom_backoff_factor(self):
        """backoff_factor パラメータが適用される。"""
        session = create_retry_session(backoff_factor=2.0)
        adapter = session.get_adapter("https://example.com")
        assert adapter.max_retries.backoff_factor == 2.0

    def test_custom_status_forcelist(self):
        """status_forcelist パラメータが適用される。"""
        session = create_retry_session(status_forcelist=(503,))
        adapter = session.get_adapter("https://example.com")
        assert 503 in adapter.max_retries.status_forcelist

    def test_default_status_forcelist(self):
        """デフォルトの status_forcelist に 429 と 5xx が含まれる。"""
        session = create_retry_session()
        adapter = session.get_adapter("https://example.com")
        forcelist = adapter.max_retries.status_forcelist
        assert 429 in forcelist
        assert 500 in forcelist
        assert 502 in forcelist
        assert 503 in forcelist
        assert 504 in forcelist


class TestRetryBehavior:
    """responses ライブラリでリトライ動作をシミュレート。"""

    @responses.activate
    def test_success_on_first_try(self):
        """初回成功時はリトライなしで結果を返す。"""
        responses.add(
            responses.GET,
            "https://api.example.com/search",
            json={"results": []},
            status=200,
        )
        session = create_retry_session()
        resp = session.get("https://api.example.com/search", timeout=5)

        assert resp.status_code == 200
        assert len(responses.calls) == 1

    @responses.activate
    def test_retry_on_server_error(self):
        """500 エラー後にリトライして成功する。"""
        responses.add(
            responses.GET,
            "https://api.example.com/search",
            status=500,
        )
        responses.add(
            responses.GET,
            "https://api.example.com/search",
            json={"results": []},
            status=200,
        )
        session = create_retry_session(retries=3, backoff_factor=0)
        resp = session.get("https://api.example.com/search", timeout=5)

        assert resp.status_code == 200
        assert len(responses.calls) == 2

    @responses.activate
    def test_retry_on_429(self):
        """429 Too Many Requests でリトライする。"""
        responses.add(
            responses.GET,
            "https://api.example.com/search",
            status=429,
        )
        responses.add(
            responses.GET,
            "https://api.example.com/search",
            json={"results": []},
            status=200,
        )
        session = create_retry_session(retries=3, backoff_factor=0)
        resp = session.get("https://api.example.com/search", timeout=5)

        assert resp.status_code == 200
        assert len(responses.calls) == 2

    @responses.activate
    def test_no_retry_on_404(self):
        """404 はリトライ対象外。"""
        responses.add(
            responses.GET,
            "https://api.example.com/search",
            status=404,
        )
        session = create_retry_session(retries=3, backoff_factor=0)
        resp = session.get("https://api.example.com/search", timeout=5)

        assert resp.status_code == 404
        assert len(responses.calls) == 1

    @responses.activate
    def test_exhausted_retries_returns_last_response(self):
        """リトライ上限到達時は最後のレスポンスを返す（raise_on_status=False）。"""
        for _ in range(4):
            responses.add(
                responses.GET,
                "https://api.example.com/search",
                status=503,
            )
        session = create_retry_session(retries=3, backoff_factor=0)
        resp = session.get("https://api.example.com/search", timeout=5)

        assert resp.status_code == 503
        # 初回 + 3回リトライ = 4回
        assert len(responses.calls) == 4

    @responses.activate
    def test_head_request_also_retries(self):
        """HEAD リクエストもリトライ対象。"""
        responses.add(
            responses.HEAD,
            "https://example.com/doc",
            status=502,
        )
        responses.add(
            responses.HEAD,
            "https://example.com/doc",
            status=200,
        )
        session = create_retry_session(retries=3, backoff_factor=0)
        resp = session.head("https://example.com/doc", timeout=5)

        assert resp.status_code == 200
        assert len(responses.calls) == 2
