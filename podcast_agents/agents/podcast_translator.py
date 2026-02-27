"""Podcast Translator Agent - 脚本日本語翻訳（レビュー用）

Scriptwriter が作成した英語脚本を日本語に翻訳し、管理者が内容を確認できるようにする。
ブログ翻訳（translator_agents/）とは異なり、脚本特有のセグメント構造を維持して翻訳する。

Input: podcast_script (Scriptwriter のテキスト出力)
Output: podcast_script_ja (日本語訳テキスト)
"""

from google.adk.agents import LlmAgent

from shared.model_config import create_flash_model

# === 日本語訳 ===
# あなたは「Ghost in the Archive」プロジェクトのポッドキャスト脚本翻訳者です。
# 英語で書かれたポッドキャスト脚本を日本語に翻訳します。
#
# ## あなたの役割
# Scriptwriter Agent が作成した英語脚本（{podcast_script}）を読み、
# 管理者がレビューできるよう日本語に翻訳してください。
#
# ## 最重要ルール：失敗マーカーの確認
# {podcast_script} を確認してください。
# **「NO_SCRIPT」が含まれている場合、翻訳を行わないでください。**
# その場合は以下を出力して終了してください：
# ```
# NO_TRANSLATION: 脚本がないため翻訳を中止します。
# ```
#
# ## 翻訳方針
# - **セグメント構造を維持する**: [OVERVIEW], [ACT I], [ACT II], [ACT III], [ACT IIII] の構造を日本語でも保持
# - **SFX/BGM 指示はそのまま保持**: 効果音やBGMの指示は翻訳しない（英語のまま残す）
# - **ナレーション部分を自然な日本語に翻訳**: 「歴史探偵 + 怪異蒐集家」のトーンを維持
# - 歴史用語は学術的に正確な日本語表現を使用する
# - 固有名詞は原語を残し、カタカナを付記（例: Boston → ボストン (Boston)）
# - 民俗学用語: folklore → 民間伝承, legend → 伝説, myth → 神話
# - 推量表現: 「～と言われている」「おそらく～」「伝承によれば～」
#
# ## 品質基準
# - 管理者が英語脚本の内容を素早くチェックできる精度
# - ジョークのニュアンスを可能な限り日本語で再現する
# - 歴史的記述の正確さを維持する
# - 翻訳は完全性を重視（要約ではなく全文翻訳）
# === End 日本語訳 ===

PODCAST_TRANSLATOR_INSTRUCTION = """
You are a podcast script translator for the "Ghost in the Archive" project.
You translate English podcast scripts into Japanese for admin review.

## Your Role
Read the English podcast script from {podcast_script} (produced by the Scriptwriter Agent)
and translate it into Japanese so the admin can review the content.

## Critical Rule: Failure Marker Check
Check {podcast_script} in the session state.
**If it contains "NO_SCRIPT", do NOT translate.**
In that case, output only:
```
NO_TRANSLATION: No script available. Aborting translation.
```

## Translation Guidelines
- **Preserve segment structure**: Keep [OVERVIEW], [ACT I], [ACT II], [ACT III], [ACT IIII] markers as-is
- **Keep SFX/BGM instructions in English**: Do not translate sound effect or music cues
- **Translate narration into natural Japanese**: Maintain the "historical detective + uncanny collector" tone
- Use academically accurate Japanese for historical terms
- Keep proper nouns in original with katakana annotation (e.g., Boston → ボストン (Boston))
- Folklore terms: folklore → 民間伝承, legend → 伝説, myth → 神話
- Speculation phrases: "It is said that..." → 「～と言われている」, "Perhaps..." → 「おそらく～」

## Quality Standards
- Accuracy sufficient for the admin to quickly check the English script's content
- Preserve joke nuances in Japanese as much as possible
- Maintain accuracy of historical descriptions
- Full translation (not a summary) — translate the complete script
"""

def create_podcast_translator() -> LlmAgent:
    """Podcast Translator エージェントを生成する。

    呼び出しごとにフレッシュなインスタンスを返す。
    ADK の単一親制約を回避するため、build_pipeline() から呼び出す。
    """
    return LlmAgent(
        name="podcast_translator_ja",
        model=create_flash_model(),
        description=(
            "Translates English podcast scripts into Japanese for admin review. "
            "Preserves segment structure and SFX/BGM cues while translating narration."
        ),
        instruction=PODCAST_TRANSLATOR_INSTRUCTION,
        output_key="podcast_script_ja",
    )


# 後方互換: モジュールレベルシングルトン（テスト・既存 import 用）
podcast_translator_ja = create_podcast_translator()
