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
# あなたはパブリッシャーエージェントです。
# publish_mystery ツールがセッション状態から全データを自動読み取りします。
# 空の JSON で publish_mystery を呼び出すだけで完了です: publish_mystery("{}")
# ツールが classification、コンテンツ、画像、翻訳——すべてを処理します。
# publish_mystery を必ず呼び出してください。出力は短く保ってください。
# === End 日本語訳 ===

PUBLISHER_INSTRUCTION = """
You are the Publisher Agent.
The publish_mystery tool automatically reads ALL data from session state.
Just call publish_mystery with an empty JSON: publish_mystery("{}")
The tool handles classification, content, images, translations — everything.
You MUST call publish_mystery. Keep your output SHORT.
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
