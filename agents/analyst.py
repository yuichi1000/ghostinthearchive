"""Analyst Agent - 深い推論と隠された真実の分析

This agent performs deep reasoning on historical documents analyzed by the
Historian Agent, detecting contradictions between sources and inferring
hidden truths using Gemini Pro for advanced analysis.
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from tools import (
    build_analysis_context,
    list_available_results,
    load_multiple_search_results,
    load_search_results,
    save_mystery_report,
)

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# Analysis prompt for deep reasoning with Gemini Pro
ANALYSIS_PROMPT = """
あなたは歴史分析の専門家です。以下の分析コンテキストに基づいて、2つの情報源間の矛盾と隠された真実を分析してください。

## 分析対象
{context}

## 分析タスク

### タスク1: 矛盾検出
以下の観点から、英語資料（新聞）とスペイン語資料（公文書）の間の矛盾を特定してください：
- 日付の不一致
- 人物の欠落または相違
- 事件の結末の違い
- 場所に関する矛盾
- 説明のない沈黙や空白

### タスク2: 隠された真実の推論
検出した矛盾から、以下を推論してください：
- なぜこの矛盾が生じたのか？
- 誰が情報を隠蔽または操作した可能性があるか？
- 当時の政治的・外交的背景から何が読み取れるか？
- 「言及されていないこと」が示唆するものは何か？

### タスク3: Mystery Report 生成
以下のJSON形式でMystery Reportを生成してください：

```json
{{
  "mystery_id": "MYSTERY-YYYY-LOCATION-NNN",
  "title": "魅力的なタイトル（例：消えた船員の謎）",
  "summary": "2-3文の要約",
  "discrepancy_detected": "検出された矛盾の明確な記述",
  "discrepancy_type": "date_mismatch | person_missing | event_outcome | location_conflict | narrative_gap | name_variant",
  "evidence_a": {{
    "source_type": "newspaper",
    "source_language": "en",
    "source_title": "資料タイトル",
    "source_date": "YYYY-MM-DD",
    "source_url": "URL",
    "relevant_excerpt": "関連する引用",
    "location_context": "場所"
  }},
  "evidence_b": {{
    "source_type": "nara_catalog",
    "source_language": "es",
    "source_title": "資料タイトル",
    "source_date": "YYYY-MM-DD",
    "source_url": "URL",
    "relevant_excerpt": "関連する引用",
    "location_context": "場所"
  }},
  "hypothesis": "主要な仮説",
  "alternative_hypotheses": ["代替仮説1", "代替仮説2"],
  "confidence_level": "high | medium | low",
  "historical_context": {{
    "time_period": "時代",
    "geographic_scope": ["場所1", "場所2"],
    "relevant_events": ["関連する歴史的事件"],
    "key_figures": ["重要人物"],
    "political_climate": "政治的背景"
  }},
  "research_questions": ["追加調査が必要な質問"],
  "story_hooks": ["物語のフック - Storyteller Agentへのヒント"]
}}
```

矛盾が見つからない場合でも、資料から読み取れる興味深いパターンや、さらなる調査が必要な「空白」について報告してください。
"""

# Define the Analyst Agent's instruction
ANALYST_INSTRUCTION = """
あなたは「Ghost in the Archive」プロジェクトのアナリストエージェント（Analyst Agent）です。
歴史資料を深く分析し、矛盾点や隠された真実を見つけ出す専門家です。

## あなたの役割
Historian Agentが精査した資料に対して、Gemini Proの高度な推論能力を使って
深い分析を行い、「歴史のゴースト」の真相に迫ります。

## 利用可能なツール
1. **load_search_results**: 単一の検索結果ファイルを読み込み
2. **load_multiple_search_results**: 複数の検索結果を統合して読み込み
3. **build_analysis_context**: 分析用コンテキストを構築
4. **list_available_results**: 利用可能なファイル一覧を取得
5. **save_mystery_report**: Mystery Reportを保存

## 分析の原則

### 1. 学術的厳密さ
- 事実、推論、推測を明確に区別する
- 証拠に基づいた仮説を立てる
- 不確実性を認め、複数の解釈を提示する

### 2. バイリンガル分析
- 英語とスペイン語の両方の資料を原文で理解する
- 翻訳によるニュアンスの欠落を避ける
- 文化的コンテキストを考慮する

### 3. 歴史的文脈理解
- 18-19世紀の米西関係を考慮
- 海上貿易、私掠船、外交的緊張の背景を理解
- 新聞の政治的バイアスを考慮

### 4. 批判的思考
- 「誰がこの情報を記録したか」を常に問う
- 「なぜこの情報が省略されたか」を考える
- 沈黙や欠落から意味を読み取る

## 矛盾検出の観点
- **DATE_MISMATCH**: 異なる日付での報告
- **PERSON_MISSING**: 一方にのみ登場する人物
- **EVENT_OUTCOME**: 異なる結末の報告
- **LOCATION_CONFLICT**: 場所に関する不一致
- **NARRATIVE_GAP**: 説明のない沈黙や欠落期間
- **NAME_VARIANT**: 同一人物の異なるスペリング

## 出力要件
- Mystery Reportは必ず有効なJSON形式で出力する
- 推論には必ず根拠となる証拠を示す
- Storyteller Agentに渡すための「物語のフック」を含める
"""

# Create the Analyst Agent instance using ADK LlmAgent with Gemini Pro
analyst_agent = LlmAgent(
    name="analyst",
    model="gemini-2.5-pro",
    description=(
        "深い推論を行い、歴史資料間の矛盾を分析し、隠された真実を推論するエージェント。"
        "Gemini Proを使用した高度な推論能力を持ち、Historian Agentが検出した矛盾を"
        "さらに深く分析してMystery Reportを生成します。"
    ),
    instruction=ANALYST_INSTRUCTION,
    tools=[
        load_search_results,
        load_multiple_search_results,
        build_analysis_context,
        list_available_results,
        save_mystery_report,
    ],
)


class AnalystAgent:
    """深い推論と隠された真実の分析を行うエージェント

    Historian Agentが精査した資料に対してGemini Proを使って深い分析を行い、
    矛盾の原因や隠された真実を推論してMystery Reportを生成します。
    """

    def __init__(self):
        self.agent = analyst_agent
        self._session_service = InMemorySessionService()
        self._runner = None
        print("[AnalystAgent] Initialized - Ready for deep analysis with Gemini Pro")

    def get_agent(self) -> LlmAgent:
        """Get the underlying LlmAgent instance."""
        return self.agent

    def build_analysis_context(
        self, filepaths: list[str] | None = None
    ) -> dict[str, Any]:
        """Build a structured analysis context from Librarian results.

        Extracts dates, keywords, locations, and summaries from English
        and Spanish sources for analysis.

        Args:
            filepaths: List of file paths to analyze. If None, uses all available.

        Returns:
            Dictionary containing the structured analysis context
        """
        context_json = build_analysis_context(filepaths)
        return json.loads(context_json)

    async def analyze_for_contradictions(
        self,
        filepaths: list[str] | None = None,
        user_id: str = "analyst_user",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Analyze documents for contradictions using Gemini Pro.

        This method:
        1. Loads and combines search results from specified files
        2. Builds an analysis context with temporal/geographic/keyword analysis
        3. Uses Gemini Pro to detect contradictions and infer hidden truths
        4. Returns a structured Mystery Report

        Args:
            filepaths: List of file paths to analyze. If None, uses all available.
            user_id: User ID for the session
            session_id: Session ID (auto-generated if None)

        Returns:
            Dictionary containing the Mystery Report or analysis results
        """
        # Build analysis context
        context = self.build_analysis_context(filepaths)

        if context.get("status") == "error":
            return {
                "status": "error",
                "error": context.get("error"),
                "suggestion": context.get("suggestion"),
            }

        # Create runner if not exists
        if self._runner is None:
            self._runner = Runner(
                agent=self.agent,
                app_name="ghost_in_the_archive_analyst",
                session_service=self._session_service,
            )

        # Create session
        if session_id is None:
            session_id = f"analysis_{uuid.uuid4().hex[:8]}"

        await self._session_service.create_session(
            app_name="ghost_in_the_archive_analyst",
            user_id=user_id,
            session_id=session_id,
        )

        # Format the analysis prompt with context
        prompt = ANALYSIS_PROMPT.format(
            context=json.dumps(context, ensure_ascii=False, indent=2)
        )

        # Run analysis
        responses = []
        async for event in self._runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            ),
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        responses.append(part.text)

        # Parse response to extract Mystery Report JSON
        full_response = "\n".join(responses)
        mystery_report = self._extract_mystery_report(full_response)

        return {
            "status": "success",
            "session_id": session_id,
            "analysis_context": {
                "files_analyzed": context.get("files_analyzed", []),
                "document_counts": context.get("document_counts", {}),
                "themes": context.get("themes", []),
            },
            "mystery_report": mystery_report,
            "raw_response": full_response,
        }

    def _extract_mystery_report(self, response: str) -> dict[str, Any] | None:
        """Extract Mystery Report JSON from LLM response.

        Args:
            response: Raw response text from the LLM

        Returns:
            Parsed Mystery Report dictionary or None if not found
        """
        import re

        # Try to find JSON block in response
        json_patterns = [
            r"```json\s*([\s\S]*?)\s*```",
            r"```\s*([\s\S]*?)\s*```",
            r"\{[\s\S]*\"mystery_id\"[\s\S]*\}",
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                try:
                    # Clean up the match
                    json_str = match.strip()
                    if not json_str.startswith("{"):
                        continue
                    report = json.loads(json_str)
                    if "mystery_id" in report or "title" in report:
                        return report
                except json.JSONDecodeError:
                    continue

        return None

    def analyze_sync(self, filepaths: list[str] | None = None) -> dict[str, Any]:
        """Synchronous wrapper for analyze_for_contradictions.

        Args:
            filepaths: List of file paths to analyze

        Returns:
            Dictionary containing the Mystery Report or analysis results
        """
        return asyncio.run(self.analyze_for_contradictions(filepaths))
