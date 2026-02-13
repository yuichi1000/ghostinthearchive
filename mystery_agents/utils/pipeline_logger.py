"""Pipeline Logger - パイプライン実行ログの記録

各エージェントの実行状況（開始・完了・エラー・所要時間・出力サマリー）を
記録し、Firestore 保存用のデータを生成する。
並列実行エージェントの追跡に対応し、複数エージェントの同時実行を管理する。
"""

from datetime import datetime, timezone
from typing import Literal


AgentStatus = Literal["running", "completed", "error"]


class PipelineLogger:
    """パイプライン実行中の各エージェントの状態を追跡する。

    並列実行に対応するため、エージェントごとの開始時刻を dict で管理する。
    """

    def __init__(self) -> None:
        self.logs: list[dict] = []
        # エージェント名 → 開始時刻（並列対応）
        self._start_times: dict[str, datetime] = {}

    def start_agent(self, agent_name: str) -> None:
        """エージェントの実行開始を記録する。"""
        self._start_times[agent_name] = datetime.now(timezone.utc)
        self.logs.append({
            "agent_name": agent_name,
            "status": "running",
            "start_time": self._start_times[agent_name].isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "output_summary": None,
        })

    def complete_agent(self, agent_name: str, output_summary: str) -> None:
        """指定したエージェントを完了としてマークする。"""
        self._finish_agent(agent_name, "completed", output_summary)

    def error_agent(self, agent_name: str, error_message: str) -> None:
        """指定したエージェントをエラーとしてマークする。"""
        self._finish_agent(agent_name, "error", f"ERROR: {error_message}")

    def get_logs(self) -> list[dict]:
        """全ログエントリを返す。"""
        return self.logs

    def remove_last_log(self, agent_name: str) -> None:
        """指定したエージェントの最後のログエントリを削除する。

        スキップされたエージェント（空テキスト + 短時間）のログを除去する際に使用。
        """
        for i in range(len(self.logs) - 1, -1, -1):
            if self.logs[i]["agent_name"] == agent_name:
                self.logs.pop(i)
                break

    def _finish_agent(self, agent_name: str, status: AgentStatus, summary: str) -> None:
        start_time = self._start_times.pop(agent_name, None)
        if start_time is None:
            return

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        for log in reversed(self.logs):
            if log["agent_name"] == agent_name and log["status"] == "running":
                log["status"] = status
                log["end_time"] = end_time.isoformat()
                log["duration_seconds"] = round(duration, 2)
                log["output_summary"] = self._truncate(summary)
                break

    @staticmethod
    def _truncate(text: str, max_length: int = 200) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."
