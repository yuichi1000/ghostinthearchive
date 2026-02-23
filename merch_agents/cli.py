"""Merch Design Pipeline - CLI Entry Point

デザイン企画とレンダリングの2つのモードを提供する。

Usage:
    python -m merch_agents design <mystery_id> [--instructions "..."]
    python -m merch_agents render <design_id>

デザイン企画: Alchemist がブログ記事からデザイン提案を生成
レンダリング: AlchemistRenderer が Imagen 3 でアセット画像を生成
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from .agent import alchemist_commander, SKIP_AUTHORS
from .tools.firestore_tools import (
    load_mystery,
    create_design,
    get_design,
    save_design_result,
    save_render_result,
    set_design_status,
    upload_design_assets,
)
from shared.orchestrator import run_pipeline
from shared.pipeline_run import create_pipeline_run


PIPELINE_TIMEOUT_SECONDS = 600  # 10分


async def generate_design(
    mystery_id: str,
    custom_instructions: str = "",
    *,
    run_id: str | None = None,
    design_id: str | None = None,
) -> tuple[str, str]:
    """デザイン提案を生成する。

    1. mystery から narrative_content + メタデータ取得
    2. product_designs ドキュメント作成
    3. run_pipeline(alchemist_commander)
    4. session state から structured_design_proposal 取得
    5. product_designs 更新 (status=design_ready)

    Args:
        mystery_id: Firestore の mystery ドキュメント ID
        custom_instructions: 管理者からのカスタム指示
        run_id: 事前作成済みのパイプライン実行 ID
        design_id: 事前作成済みの design ドキュメント ID

    Returns:
        (design_id, run_id) のタプル
    """
    print("=" * 70)
    print("Ghost in the Archive - Product Design Generation")
    print("=" * 70)
    print()
    print(f"Mystery ID: {mystery_id}")
    if custom_instructions:
        print(f"Custom Instructions: {custom_instructions}")
    print()

    # Firestore から記事読み込み
    mystery = load_mystery(mystery_id)
    if not mystery:
        raise ValueError(f"Mystery '{mystery_id}' not found in Firestore.")

    narrative_content = mystery.get("narrative_content", "")
    if not narrative_content:
        raise ValueError(f"Mystery '{mystery_id}' has no narrative_content.")

    title = mystery.get("title", mystery_id)
    print(f"Article: {title}")
    print("-" * 70)
    print()

    # メタデータを構成
    mystery_metadata = {
        "mystery_id": mystery_id,
        "title": title,
        "summary": mystery.get("summary", ""),
        "discrepancy_type": mystery.get("discrepancy_type", ""),
        "confidence_level": mystery.get("confidence_level", ""),
        "region": "",
        "images": mystery.get("images", {}),
    }
    # mystery_id から国コード抽出
    parts = mystery_id.split("-")
    if len(parts) >= 2:
        mystery_metadata["region"] = parts[1]

    # design ドキュメント作成
    if design_id is None:
        design_id = create_design(mystery_id, custom_instructions)
    print(f"Design ID: {design_id}")

    # pipeline_run ドキュメント作成
    if run_id is None:
        run_id = create_pipeline_run("design", mystery_id=mystery_id)

    # pipeline_run_id を design に紐付け
    from shared.firestore import get_firestore_client
    db = get_firestore_client()
    doc = db.collection("product_designs").document(design_id).get()
    if doc.exists and not doc.to_dict().get("pipeline_run_id"):
        db.collection("product_designs").document(design_id).update({
            "pipeline_run_id": run_id,
        })

    try:
        # Orchestrator 呼び出し
        result = await run_pipeline(
            agent=alchemist_commander,
            app_name="ghost_in_the_archive_merch",
            user_message=f"以下のブログ記事からプロダクトデザインを作成してください: {title}",
            initial_state={
                "creative_content": narrative_content,
                "mystery_metadata": str(mystery_metadata),
                "custom_instructions": custom_instructions,
                "design_proposals": "",
            },
            run_id=run_id,
            run_type="design",
            timeout_seconds=PIPELINE_TIMEOUT_SECONDS,
            max_llm_calls=15,
            skip_authors=SKIP_AUTHORS,
            sequential_agents={"alchemist"},
            on_text=lambda text: print(text),
        )

        # セッション状態から結果取得
        proposal = result.session_state.get("structured_design_proposal", {})

        # Firestore に保存
        save_design_result(design_id, proposal)

        print()
        print("=" * 70)
        print("Design proposal generation complete!")
        print(f"  Design ID: {design_id}")
        if proposal:
            products = proposal.get("products", [])
            print(f"  Products: {len(products)}")
            for p in products:
                print(f"    - {p.get('product_type', '?')}: {p.get('catchphrase_en', 'N/A')}")
        print("=" * 70)

        return design_id, result.run_id

    except TimeoutError:
        print(f"Error: Pipeline timed out after {PIPELINE_TIMEOUT_SECONDS}s")
        set_design_status(design_id, "error", "Pipeline timed out")
        raise
    except Exception as e:
        print(f"Error during design generation: {e}")
        set_design_status(design_id, "error", str(e))
        raise


async def render_assets(
    design_id: str,
    *,
    run_id: str | None = None,
) -> dict:
    """デザイン提案に基づいてアセット画像を生成する。

    1. design ドキュメント取得
    2. structured_design_proposal から Imagen プロンプト読み取り
    3. run_pipeline(alchemist_render_commander) で画像生成
    4. upload_design_assets() で GCS アップロード
    5. save_render_result() で結果保存

    Args:
        design_id: Design ドキュメント ID
        run_id: 事前作成済みのパイプライン実行 ID

    Returns:
        アセットメタデータ dict
    """
    print("=" * 70)
    print("Ghost in the Archive - Design Asset Rendering")
    print("=" * 70)
    print()
    print(f"Design ID: {design_id}")
    print()

    # design ドキュメント取得
    design = get_design(design_id)
    if not design:
        raise ValueError(f"Design '{design_id}' not found.")

    proposal = design.get("proposal")
    if not proposal:
        raise ValueError(f"Design '{design_id}' has no proposal. Run design generation first.")

    mystery_id = design.get("mystery_id", "")
    products = proposal.get("products", [])
    if not products:
        raise ValueError("Design proposal has no products.")

    print(f"Mystery: {design.get('mystery_title', mystery_id)}")
    print(f"Products: {len(products)}")
    print("-" * 70)
    print()

    # ステータス更新
    set_design_status(design_id, "rendering")

    try:
        # Phase 2: AlchemistRenderer パイプライン実行
        from .agent import alchemist_render_commander

        if run_id is None:
            run_id = create_pipeline_run("design_render", mystery_id=mystery_id)

        result = await run_pipeline(
            agent=alchemist_render_commander,
            app_name="ghost_in_the_archive_merch_render",
            user_message=f"以下のデザイン提案のアセット画像を生成してください: {design_id}",
            initial_state={
                "structured_design_proposal": proposal,
                "mystery_metadata": str({"mystery_id": mystery_id, "region": design.get("region", "")}),
                "render_summary": "",
            },
            run_id=run_id,
            run_type="design",
            timeout_seconds=PIPELINE_TIMEOUT_SECONDS,
            max_llm_calls=20,
            skip_authors=SKIP_AUTHORS,
            sequential_agents={"alchemist_renderer"},
            on_text=lambda text: print(text),
        )

        # セッション状態からアセット情報取得
        design_assets = result.session_state.get("design_assets", [])

        # GCS にアップロード
        if design_assets:
            uploaded = upload_design_assets(mystery_id, design_id, design_assets)
            save_render_result(design_id, uploaded)
        else:
            save_render_result(design_id, [])

        print()
        print("=" * 70)
        print("Asset rendering complete!")
        print(f"  Design ID: {design_id}")
        print(f"  Assets: {len(design_assets)}")
        print("=" * 70)

        return {"design_id": design_id, "assets": design_assets}

    except Exception as e:
        print(f"Error during rendering: {e}")
        set_design_status(design_id, "error", str(e))
        raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python -m merch_agents design <mystery_id> [--instructions "..."]')
        print('  python -m merch_agents render <design_id>')
        sys.exit(1)

    command = sys.argv[1]

    if command == "design":
        if len(sys.argv) < 3:
            print("Usage: python -m merch_agents design <mystery_id> [--instructions '...']")
            sys.exit(1)

        mystery_id = sys.argv[2]
        instructions = ""

        # --instructions パース
        for i, arg in enumerate(sys.argv[3:], start=3):
            if arg == "--instructions" and i + 1 < len(sys.argv):
                instructions = sys.argv[i + 1]
                break

        asyncio.run(generate_design(mystery_id, instructions))

    elif command == "render":
        if len(sys.argv) < 3:
            print("Usage: python -m merch_agents render <design_id>")
            sys.exit(1)

        design_id = sys.argv[2]
        asyncio.run(render_assets(design_id))

    else:
        print(f"Unknown command: {command}")
        print("Available commands: design, render")
        sys.exit(1)


if __name__ == "__main__":
    main()
