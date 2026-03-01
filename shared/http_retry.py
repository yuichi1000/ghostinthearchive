"""リトライ付き requests.Session ファクトリ。

外部アーカイブ API（LOC, DPLA, Internet Archive 等）への HTTP リクエストに
指数バックオフ付きリトライを適用する。新規依存なし（urllib3 は requests に同梱）。

既存の _rate_limit() とは補完関係:
- _rate_limit(): リクエスト間の最小間隔を保証（サーバー負荷軽減）
- create_retry_session(): 一時的なエラー（429, 5xx）に対する自動リトライ
"""

import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


def create_retry_session(
    retries: int = 3,
    backoff_factor: float = 1.0,
    status_forcelist: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> requests.Session:
    """指数バックオフ付きリトライ Session を生成する。

    リトライ間隔: backoff_factor * (2 ** (retry_count - 1))
    例: backoff_factor=1.0 → 1s, 2s, 4s

    Args:
        retries: 最大リトライ回数（デフォルト 3）
        backoff_factor: バックオフ係数（デフォルト 1.0）
        status_forcelist: リトライ対象の HTTP ステータスコード

    Returns:
        リトライ設定済みの requests.Session
    """
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    logger.debug(
        "リトライセッション作成: retries=%d, backoff=%.1f, status=%s",
        retries, backoff_factor, status_forcelist,
    )

    return session
