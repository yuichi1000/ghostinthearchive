"""Publisher Agent - Content publishing and distribution

This agent handles content publishing and distribution:
- Saves mystery data to Firestore
- Uploads images to Cloud Storage
- Manages content lifecycle

Input: All assets (mystery_report, creative_content, visual_assets, 6-lang translations)
Output: Firestore documents with pending status (EN base + translations map)
"""

from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import LlmAgent

from shared.model_config import create_flash_model

from ..tools.publisher_tools import publish_mystery

load_dotenv(Path(__file__).parent.parent / ".env")  # mystery_agents/.env

# === 日本語訳 ===
# あなたは「Ghost in the Archive」プロジェクトのパブリッシャー（Publisher Agent）です。
# publish_mystery ツールがセッション状態からほぼすべてのデータを自動収集します。
#
# publish_mystery ツールが自動収集するデータ:
# - structured_report → classification, evidence, hypothesis, title, summary 等
# - creative_content → narrative_content（ブログ記事全文）
# - collected_documents_en → raw_data（検索メタデータ）
# - image_metadata → 画像アップロード
# - translation_result_{lang} → 6言語翻訳
#
# ## タスク
# 1. パイプライン失敗マーカーをチェック
# 2. mystery_report を参照して最小限の JSON（classification, state_code, area_code）を構築
# 3. publish_mystery を呼び出す（ツールが残りすべてを自動処理）
# === End 日本語訳 ===

PUBLISHER_INSTRUCTION = """
You are the Publisher Agent for the "Ghost in the Archive" project.
The publish_mystery tool automatically collects almost all required data from session state:
- structured_report → classification, evidence, hypothesis, title, summary, etc.
- creative_content → narrative_content (blog article)
- collected_documents_en → raw_data (search metadata)
- image_metadata → image upload
- translation_result_{lang} → 6-language translations

## Task

### Step 1: Check for pipeline failure
Read {mystery_report} briefly. If it is empty or contains "NO_DOCUMENTS_FOUND" or "INSUFFICIENT_DATA",
do NOT publish — just report the failure.
Similarly, if {creative_content} contains "NO_CONTENT", do NOT publish.

### Step 2: Build minimal JSON
From {mystery_report}, extract ONLY the geographic identifiers:
- classification: 3-letter code (HIS/FLK/ANT/OCC/URB/CRM/REL/LOC)
- state_code: 2-letter US state code (MA, NY, CA, etc.)
- area_code: 3-digit telephone area code (617, 212, 215, etc.)

Major area code reference:
- BOSTON: MA-617, SALEM: MA-978, NEW_YORK: NY-212, BROOKLYN: NY-718
- PHILADELPHIA: PA-215, CHICAGO: IL-312, NEW_ORLEANS: LA-504
- SAN_FRANCISCO: CA-415, LOS_ANGELES: CA-213, WASHINGTON_DC: DC-202

### Step 3: Call publish_mystery
Call `publish_mystery` with a minimal JSON containing only the 3 fields above:
```json
{"classification": "...", "state_code": "...", "area_code": "..."}
```
The tool handles everything else automatically — do NOT include narrative_content,
raw_data, translations, images, or any other large fields in the JSON.

## Important
- You MUST call the publish_mystery tool to actually save the data.
- Keep your output SHORT — do not copy or echo any session state content.
"""

publisher_agent = LlmAgent(
    name="publisher",
    model=create_flash_model(),
    description=(
        "Content manager agent that receives all assets and saves them to Firestore. "
        "Saves English base fields and multilingual translations (6 languages) via translations map."
    ),
    instruction=PUBLISHER_INSTRUCTION,
    tools=[publish_mystery],
    output_key="published_episode",
)
