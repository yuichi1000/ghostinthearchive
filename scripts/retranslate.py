"""特定記事の不足翻訳を再生成し Firestore に保存するリペアスクリプト。

使用例:
    # 特定言語を指定して再翻訳
    python scripts/retranslate.py HIS-DE-HAJ-20260228142041 --languages es

    # 不足言語を自動検出して再翻訳
    python scripts/retranslate.py HIS-DE-HAJ-20260228142041

前提:
    - GOOGLE_CLOUD_PROJECT 環境変数が設定済み
    - Vertex AI 認証済み（gcloud auth application-default login）
    - Firestore に対象記事が存在
"""

import argparse
import asyncio
import json
import logging
import sys

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from mystery_agents.agents.translator import create_translator
from shared.constants import TRANSLATION_LANGUAGES
from shared.firestore import get_firestore_client
from shared.language_validator import validate_translation_language

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _detect_missing_languages(doc_data: dict) -> list[str]:
    """Firestore ドキュメントから不足言語を検出する。"""
    translations = doc_data.get("translations", {})
    return [lang for lang in TRANSLATION_LANGUAGES if lang not in translations]


async def _run_translator(lang: str, creative_content: str, mystery_report: str) -> dict | None:
    """ADK Runner で Translator エージェントを実行し翻訳結果を返す。"""
    agent = create_translator(lang)
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name=f"retranslate_{lang}",
        session_service=session_service,
    )

    # セッション作成（Translator は creative_content と mystery_report をセッション状態から参照する）
    await session_service.create_session(
        app_name=f"retranslate_{lang}",
        user_id="retranslate_script",
        session_id=f"retranslate_{lang}",
        state={
            "creative_content": creative_content,
            "mystery_report": mystery_report or "",
        },
    )

    # エージェント実行（Translator は creative_content を入力として翻訳を実行）
    from google.genai import types

    user_content = types.Content(
        role="user",
        parts=[types.Part(text="Translate the article in session state.")],
    )

    result_text = ""
    async for event in runner.run_async(
        user_id="retranslate_script",
        session_id=f"retranslate_{lang}",
        new_message=user_content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            result_text = event.content.parts[0].text

    if not result_text:
        logger.error("Translator %s が結果を返しませんでした", lang)
        return None

    # JSON パース
    try:
        # コードブロックで包まれている場合を考慮
        import re
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", result_text, re.DOTALL)
        json_text = match.group(1) if match else result_text
        parsed = json.loads(json_text, strict=False)
        if not isinstance(parsed, dict):
            logger.error("Translator %s の出力が dict ではありません: %s", lang, type(parsed))
            return None
        return parsed
    except json.JSONDecodeError:
        logger.error("Translator %s の出力を JSON パースできません（先頭200文字: %s）", lang, result_text[:200])
        return None


async def retranslate(mystery_id: str, languages: list[str] | None) -> None:
    """指定記事の翻訳を再生成し Firestore に保存する。"""
    db = get_firestore_client()
    doc_ref = db.collection("mysteries").document(mystery_id)
    doc = doc_ref.get()

    if not doc.exists:
        logger.error("記事 %s が Firestore に存在しません", mystery_id)
        sys.exit(1)

    doc_data = doc.to_dict()
    creative_content = doc_data.get("narrative_content", "")
    mystery_report = doc_data.get("mystery_report", "")

    if not creative_content:
        logger.error("記事 %s に narrative_content がありません", mystery_id)
        sys.exit(1)

    # 翻訳対象言語の決定
    if languages:
        target_langs = languages
    else:
        target_langs = _detect_missing_languages(doc_data)
        if not target_langs:
            logger.info("記事 %s の翻訳は全言語揃っています。再翻訳は不要です。", mystery_id)
            return

    logger.info("記事 %s の翻訳対象言語: %s", mystery_id, target_langs)

    for lang in target_langs:
        if lang not in TRANSLATION_LANGUAGES:
            logger.warning("サポートされていない言語 '%s' をスキップ", lang)
            continue

        logger.info("翻訳開始: %s → %s", mystery_id, lang)
        translated = await _run_translator(lang, creative_content, mystery_report)

        if translated is None:
            logger.error("翻訳失敗: %s", lang)
            continue

        # 言語バリデーション
        vr = validate_translation_language(lang, translated)
        if not vr.is_valid:
            logger.error("翻訳バリデーション失敗 (%s): %s", lang, vr.reason)
            continue

        # Firestore に保存（translations map のマージ更新）
        doc_ref.update({f"translations.{lang}": translated})
        logger.info("翻訳保存完了: %s → translations.%s (%d フィールド)",
                     mystery_id, lang, len(translated))


def main():
    parser = argparse.ArgumentParser(
        description="特定記事の不足翻訳を再生成し Firestore に保存する",
    )
    parser.add_argument("mystery_id", help="対象記事の mystery_id")
    parser.add_argument(
        "--languages", "-l",
        nargs="+",
        choices=TRANSLATION_LANGUAGES,
        default=None,
        help="再翻訳する言語コード（省略時は不足言語を自動検出）",
    )
    args = parser.parse_args()

    asyncio.run(retranslate(args.mystery_id, args.languages))


if __name__ == "__main__":
    main()
