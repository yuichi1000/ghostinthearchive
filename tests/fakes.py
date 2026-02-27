"""テスト用フェイクオブジェクト。

同じモック設定が 3 箇所以上で重複する場合にフェイクを提供し、
テストの可読性と保守性を向上させる。
"""

from dataclasses import dataclass, field
from unittest.mock import MagicMock

from mystery_agents.schemas.document import ArchiveDocument, SourceLanguage


@dataclass
class FakeSession:
    """ADK InMemorySessionService のセッションを模倣するフェイク。"""

    state: dict = field(default_factory=dict)


class FakeInMemorySessionService:
    """ADK InMemorySessionService のフェイク実装。

    create_session / get_session の最小限の API サーフェスのみ実装する。
    post_run_state を指定すると、get_session 時にセッション状態を差し替えて
    Runner 実行後の状態をシミュレートできる。
    """

    def __init__(self, post_run_state=None):
        self._session = None
        self._post_run_state = post_run_state

    async def create_session(self, *, app_name, user_id, session_id, state):
        self._session = FakeSession(state=dict(state))

    async def get_session(self, *, app_name, user_id, session_id):
        if self._post_run_state is not None:
            self._session.state = self._post_run_state
        return self._session


def make_tool_context(state: dict | None = None, **kwargs) -> MagicMock:
    """ADK ToolContext のモックを作成する。

    6 箇所以上で重複していた _make_tool_context() を統合。
    """
    ctx = MagicMock()
    ctx.state = dict(state) if state else {}
    for k, v in kwargs.items():
        setattr(ctx, k, v)
    return ctx


def make_archive_doc(
    url: str = "https://www.loc.gov/item/test/",
    title: str = "Test Doc",
    source_type: str = "loc_digital",
    keywords_matched: list[str] | None = None,
) -> ArchiveDocument:
    """テスト用 ArchiveDocument を作成する。

    librarian_tools / link_validator の _make_doc() を統合。
    """
    return ArchiveDocument(
        title=title,
        source_url=url,
        summary="A test document",
        language=SourceLanguage.EN,
        location="Test",
        source_type=source_type,
        keywords_matched=keywords_matched if keywords_matched is not None else ["test"],
    )
