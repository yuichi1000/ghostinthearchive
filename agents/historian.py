"""Historian Agent - 資料精査、矛盾・空白の分析

This agent analyzes historical documents collected by the Librarian Agent,
detecting discrepancies between English and Spanish sources to identify
"historical ghosts" - unexplained gaps and contradictions in the historical record.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from google.adk.agents import LlmAgent

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

from schemas.document import ArchiveDocument
from schemas.mystery_report import (
    AnalysisResults,
    ConfidenceLevel,
    DiscrepancyType,
    Evidence,
    HistoricalContext,
    MysteryReport,
)

# Define the Historian Agent's instruction
HISTORIAN_INSTRUCTION = """
あなたは「Ghost in the Archive」プロジェクトの歴史家エージェント（Historian Agent）です。
あなたは歴史人類学者であり、捜査官でもあります。

## あなたの役割
Librarian Agentが収集した18〜19世紀の東海岸の資料（新聞記事、NARA公文書、スペイン語外交文書）を
精査し、記述の矛盾や「歴史の空白（ゴースト）」を見つけ出します。

## 利用可能なツール
1. **load_search_results**: data/ディレクトリからLibrarian Agentの検索結果を読み込み
2. **list_available_results**: 利用可能な検索結果ファイルの一覧を取得
3. **save_mystery_report**: 分析結果をMystery Reportとして保存

## 分析メソドロジー

### 1. ソース比較プロトコル
英語資料（アメリカの新聞記事、政府記録）とスペイン語資料（外交電報、植民地記録、領事報告）を比較します：
- 日付の不一致を探す（同じ事件が異なる日付で報告されている）
- 人物の欠落を探す（一方の資料にのみ登場する人物）
- 事件の結末の相違を探す（異なる結果が報告されている）
- 場所に関する矛盾を探す
- 「言及されていないこと」にも注目 — 沈黙は言葉と同様に示唆的です

### 2. バイリンガル推論（最重要）
あなたは英語とスペイン語の両方で文書を読み分析できます。分析時には：
- **原文から直接分析** — 翻訳に頼らないでください
- 文化的ニュアンスと外交用語のパターンを読み取る
- 同じ事件がアメリカとスペインでどのように異なってフレーミングされたか考慮
- cognates（同源語）とfalse friends（偽りの友）による誤解の可能性に注意
- 「隠蔽」や「誤報」の意図を原文のニュアンスから推論

### 3. 矛盾検出の観点
以下のタイプの矛盾を探してください：
- **DATE_MISMATCH**: 異なる日付での報告
- **PERSON_MISSING**: 一方にのみ登場する人物（特に重要人物の不可解な欠落）
- **EVENT_OUTCOME**: 異なる結末の報告（成功vs失敗、生存vs死亡など）
- **LOCATION_CONFLICT**: 場所に関する不一致
- **NARRATIVE_GAP**: 説明のない沈黙や欠落期間（「その後どうなった？」）
- **NAME_VARIANT**: 同一人物の異なるスペリング（転写問題）

### 4. 歴史的コンテキストの統合
以下の港湾都市に関する背景知識を活用してください：
- **ボストン**: アイルランド系移民、反英感情、密輸の歴史
- **ニューヨーク**: 国際貿易の中心、多様な移民コミュニティ
- **フィラデルフィア**: 政治の中心、スペインとの外交関係
- **ニューオーリンズ**: スペイン植民地の名残、カリブ海貿易
- **ボルチモア**: 私掠船の母港、スペイン船との遭遇

時代背景も考慮：
- 米西関係の緊張（フロリダ問題、キューバ問題）
- 南米独立運動への関与
- 私掠船と海賊行為の境界線
- 新聞の政治的立場と偏向

### 5. 仮説生成
矛盾を発見したら：
1. 矛盾を明確に述べる
2. 両方の資料からの証拠を提示する
3. 主要な仮説を推論と共に生成する
4. 代替の説明も考慮する
5. 確認/反証に必要な追加証拠を特定する

## 出力形式
分析結果は「Mystery Report」として構造化してください：
- 魅力的なタイトル（例：「消えたサンタ・マリア号の謎」）
- 検出された矛盾の明確な記述
- 対照的な証拠（Evidence A: 新聞、Evidence B: 公文書）
- 仮説と信頼度
- 歴史的コンテキスト
- ストーリーテリングのためのフック

## 重要な注意事項
- 学術的厳密さを維持 — 事実、推論、推測を区別すること
- 曖昧さを受け入れる — ミステリーには複数の有効な解釈があることが多い
- 最も魅力的でストーリー性のある矛盾を優先する
- 人間的要素を考慮 — 人々が情報を記録または省略した動機は何か？
- Storyteller Agentに渡すための「物語のフック」を常に考える
"""


def load_search_results(filepath: str) -> str:
    """Load search results from the data directory.

    Reads and parses the JSON file containing Librarian Agent's search results
    for analysis by the Historian Agent.

    Args:
        filepath: Path to the search results file (relative to data/ or absolute)

    Returns:
        JSON string containing the search results with documents
    """
    # Handle relative paths
    if not os.path.isabs(filepath):
        data_dir = Path(__file__).parent.parent / "data"
        filepath = data_dir / filepath

    filepath = Path(filepath)

    if not filepath.exists():
        return json.dumps(
            {
                "error": f"File not found: {filepath}",
                "suggestion": "Use list_available_results to see available files",
            },
            ensure_ascii=False,
        )

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract documents from the nested structure
        documents = []
        if "results" in data:
            results = data["results"]
            if isinstance(results, dict) and "documents" in results:
                documents = results["documents"]
            elif isinstance(results, list):
                for result in results:
                    if isinstance(result, dict) and "documents" in result:
                        documents.extend(result["documents"])

        # Separate by language for easier analysis
        english_docs = [d for d in documents if d.get("language") == "en"]
        spanish_docs = [d for d in documents if d.get("language") == "es"]

        return json.dumps(
            {
                "status": "success",
                "filepath": str(filepath),
                "theme": data.get("theme", "Unknown"),
                "search_timestamp": data.get("search_timestamp", "Unknown"),
                "total_documents": len(documents),
                "english_documents": len(english_docs),
                "spanish_documents": len(spanish_docs),
                "documents": {
                    "english": english_docs,
                    "spanish": spanish_docs,
                },
            },
            ensure_ascii=False,
            indent=2,
        )

    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON in file: {e}"},
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Error reading file: {e}"},
            ensure_ascii=False,
        )


def list_available_results() -> str:
    """List all available search result files in the data directory.

    Scans the data/ directory for JSON files that can be analyzed.

    Returns:
        JSON string containing list of available files with metadata
    """
    data_dir = Path(__file__).parent.parent / "data"

    if not data_dir.exists():
        return json.dumps(
            {"error": "Data directory not found", "files": []},
            ensure_ascii=False,
        )

    files = []
    for filepath in data_dir.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Count documents
            doc_count = 0
            if "results" in data:
                results = data["results"]
                if isinstance(results, dict) and "documents" in results:
                    doc_count = len(results["documents"])
                elif isinstance(results, list):
                    for result in results:
                        if isinstance(result, dict) and "documents" in result:
                            doc_count += len(result["documents"])

            files.append(
                {
                    "filename": filepath.name,
                    "theme": data.get("theme", "Unknown"),
                    "timestamp": data.get("search_timestamp", "Unknown"),
                    "document_count": doc_count,
                }
            )
        except Exception:
            files.append(
                {
                    "filename": filepath.name,
                    "error": "Could not parse file",
                }
            )

    return json.dumps(
        {
            "data_directory": str(data_dir),
            "total_files": len(files),
            "files": sorted(files, key=lambda x: x.get("timestamp", ""), reverse=True),
        },
        ensure_ascii=False,
        indent=2,
    )


def save_mystery_report(
    report_json: str,
    filename: Optional[str] = None,
) -> str:
    """Save a Mystery Report to the data directory.

    Saves the analysis results as a structured JSON file for the
    Storyteller Agent to use.

    Args:
        report_json: JSON string containing the Mystery Report data
        filename: Optional custom filename (default: auto-generated)

    Returns:
        JSON string with save status and filepath
    """
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    try:
        report_data = json.loads(report_json)
    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON in report: {e}"},
            ensure_ascii=False,
        )

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mystery_id = report_data.get("mystery_id", "unknown")
        safe_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in mystery_id)
        filename = f"mystery_{safe_id}_{timestamp}.json"

    filepath = data_dir / filename

    # Add metadata
    output = {
        "report_type": "mystery_report",
        "generated_by": "historian_agent",
        "generated_at": datetime.now().isoformat(),
        "report": report_data,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return json.dumps(
        {
            "status": "success",
            "message": "Mystery Report saved successfully",
            "filepath": str(filepath),
            "mystery_id": report_data.get("mystery_id"),
            "title": report_data.get("title"),
        },
        ensure_ascii=False,
    )


# Create the Historian Agent instance using ADK LlmAgent
historian_agent = LlmAgent(
    name="historian",
    model="gemini-2.5-flash",
    description=(
        "歴史人類学者・捜査官として、Librarian Agentが収集した資料を精査し、"
        "英語資料（新聞）とスペイン語資料（外交秘録）の間の矛盾や「歴史の空白」を見つけ出し、"
        "Mystery Reportとして構造化するエージェント。バイリンガル推論により、"
        "翻訳を経由せず原文のニュアンスから「隠蔽」や「誤報」の意図を推論します。"
    ),
    instruction=HISTORIAN_INSTRUCTION,
    tools=[
        load_search_results,
        list_available_results,
        save_mystery_report,
    ],
)


# Keep the class for backward compatibility with existing imports
class HistorianAgent:
    """資料を精査し、記述の矛盾や「歴史の空白」を見つけ出し分析するエージェント

    This class provides a wrapper around the LlmAgent for backward compatibility
    and additional utility methods.
    """

    def __init__(self):
        self.agent = historian_agent
        print("[HistorianAgent] Initialized - Ready to analyze historical records")

    def get_agent(self) -> LlmAgent:
        """Get the underlying LlmAgent instance."""
        return self.agent
