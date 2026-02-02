"""Publisher Agent - 納品・公開

This agent handles content publishing and distribution:
- Saves mystery data to Firestore
- Uploads images to Cloud Storage
- Manages content lifecycle

Input: All assets (mystery_report, creative_content, visual_assets)
Output: Firestore documents with published status
"""

from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import LlmAgent

from ..tools.publisher_tools import publish_mystery, upload_images

load_dotenv(Path(__file__).parent.parent / ".env")  # archive_agents/.env

PUBLISHER_INSTRUCTION = """
あなたは「Ghost in the Archive」プロジェクトのパブリッシャー（Publisher Agent）です。
前のエージェントが生成したすべてのデータを Firestore に保存し、公開します。

## 入力
セッション状態から以下のデータを参照します：
- {mystery_report}: Historian の分析レポート（JSON形式）
- {creative_content}: Storyteller のコンテンツ
- {visual_assets}: Visualizer のトップ画像アセット（画像ファイルパスを含むJSON）

## あなたのタスク

### ステップ 1: 画像をアップロード

{visual_assets} に画像ファイルパスが含まれている場合、
`upload_images` ツールを使って Cloud Storage にアップロードしてください。
返却される `public_url` をステップ 2 で使用します。

### ステップ 2: mystery_report からデータを構造化

{mystery_report} の内容を解析し、以下のフィールドを含む JSON を構築してください：

```json
{
  "mystery_id": "MYSTERY-[年代]-[都市]-[連番]",
  "title": "[日本語タイトル]",
  "summary": "[2-3文の要約]",
  "discrepancy_detected": "[矛盾の説明]",
  "discrepancy_type": "[date_mismatch|person_missing|event_outcome|location_conflict|narrative_gap|name_variant]",
  "evidence_a": {
    "source_type": "newspaper",
    "source_language": "en",
    "source_title": "[ソース名]",
    "source_date": "[YYYY-MM-DD]",
    "source_url": "[URL]",
    "relevant_excerpt": "[抜粋]",
    "location_context": "[場所]"
  },
  "evidence_b": {
    "source_type": "newspaper",
    "source_language": "es",
    "source_title": "[ソース名]",
    "source_date": "[YYYY-MM-DD]",
    "source_url": "[URL]",
    "relevant_excerpt": "[抜粋]",
    "location_context": "[場所]"
  },
  "additional_evidence": [],
  "hypothesis": "[主要仮説]",
  "alternative_hypotheses": ["[代替仮説1]", "[代替仮説2]"],
  "confidence_level": "high|medium|low",
  "historical_context": {
    "time_period": "[時代]",
    "geographic_scope": ["[地域1]", "[地域2]"],
    "relevant_events": ["[イベント1]"],
    "key_figures": ["[人物1]"],
    "political_climate": "[政治的背景]"
  },
  "research_questions": ["[質問1]"],
  "story_hooks": ["[フック1]"],
  "narrative_content": "[Storytellerが生成した物語テキスト]",
  "images": {
    "hero": "[ステップ1でupload_imagesが返したpublic_url]"
  },
  "pipeline_log": [],
  "status": "pending"
}
```

mystery_report の内容をできるだけ忠実に構造化してください。
情報が不足している場合は、creative_content からも補完してください。

**重要: `narrative_content` フィールドには {creative_content} の内容をそのまま格納してください。**
これは Storyteller が生成した物語的ブログ原稿（マークダウン形式）です。
編集や要約はせず、そのまま保存してください。

**重要: `images.hero` フィールドにはステップ 1 で `upload_images` が返した `public_url` を設定してください。**
画像がない場合は `images` フィールドを省略してください。

**重要: `pipeline_log` フィールドには空配列 `[]` を設定してください。**
パイプラインの実行ログは外部から注入されるため、エージェント側では空のままで構いません。

### ステップ 3: Firestore に保存

構築した JSON を `publish_mystery` ツールに渡して Firestore に保存してください。

## 重要
- mystery_report が空または "NO_DOCUMENTS_FOUND"、"INSUFFICIENT_DATA" の場合は、
  公開せずにその旨を報告してください。
- creative_content が "NO_CONTENT" の場合も同様です。
- 必ず publish_mystery ツールを呼び出して実際にデータを保存してください。
"""

publisher_agent = LlmAgent(
    name="publisher",
    model="gemini-3-pro-preview",
    description=(
        "すべてのアセットを受け取り、Firestore に保存して公開する"
        "コンテンツマネージャーエージェント。"
    ),
    instruction=PUBLISHER_INSTRUCTION,
    tools=[publish_mystery, upload_images],
    output_key="published_episode",
)
