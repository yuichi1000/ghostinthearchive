"""Pipeline Logger - パイプライン実行ログの記録

各エージェントの実行状況（開始・完了・エラー・所要時間・出力サマリー）を
記録し、Firestore 保存用のデータを生成する。
"""

from datetime import datetime, timezone
from typing import Literal


AgentStatus = Literal["running", "completed", "error"]


class PipelineLogger:
    """パイプライン実行中の各エージェントの状態を追跡する。"""

    def __init__(self) -> None:
        self.logs: list[dict] = []
        self._current_agent: str | None = None
        self._start_time: datetime | None = None

    def start_agent(self, agent_name: str) -> None:
        """エージェントの実行開始を記録する。"""
        self._current_agent = agent_name
        self._start_time = datetime.now(timezone.utc)
        self.logs.append({
            "agent_name": agent_name,
            "status": "running",
            "start_time": self._start_time.isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "output_summary": None,
        })

    def complete_agent(self, output_summary: str) -> None:
        """現在のエージェントを完了としてマークする。"""
        self._finish_current("completed", output_summary)

    def error_agent(self, error_message: str) -> None:
        """現在のエージェントをエラーとしてマークする。"""
        self._finish_current("error", f"ERROR: {error_message}")

    def get_logs(self) -> list[dict]:
        """全ログエントリを返す。"""
        return self.logs

    def _finish_current(self, status: AgentStatus, summary: str) -> None:
        if not self._current_agent or not self._start_time:
            return

        end_time = datetime.now(timezone.utc)
        duration = (end_time - self._start_time).total_seconds()

        for log in reversed(self.logs):
            if log["agent_name"] == self._current_agent and log["status"] == "running":
                log["status"] = status
                log["end_time"] = end_time.isoformat()
                log["duration_seconds"] = round(duration, 2)
                log["output_summary"] = self._truncate(summary)
                break

        self._current_agent = None
        self._start_time = None

    @staticmethod
    def _truncate(text: str, max_length: int = 200) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
