"""テスト用フェイクオブジェクト。

同じモック設定が 3 箇所以上で重複する場合にフェイクを提供し、
テストの可読性と保守性を向上させる。
"""

from dataclasses import dataclass, field


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
