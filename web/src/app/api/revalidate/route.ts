import { NextRequest, NextResponse } from "next/server";
import { revalidatePath } from "next/cache";

/**
 * ISR再検証APIエンドポイント
 * ミステリーが承認された際に呼び出され、静的ページを再生成する
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { mysteryId, secret } = body;

    // シークレットトークンの検証
    const expectedSecret = process.env.REVALIDATE_SECRET;
    if (expectedSecret && secret !== expectedSecret) {
      return NextResponse.json(
        { error: "Invalid revalidation secret" },
        { status: 401 }
      );
    }

    // 再検証を実行
    // トップページ（ミステリー一覧）を再検証
    revalidatePath("/");

    // 特定のミステリー詳細ページを再検証
    if (mysteryId) {
      revalidatePath(`/mystery/${mysteryId}`);
    }

    console.log(`[Revalidate] 再検証完了: / および /mystery/${mysteryId || "all"}`);

    return NextResponse.json({
      success: true,
      revalidated: true,
      timestamp: new Date().toISOString(),
      paths: ["/", mysteryId ? `/mystery/${mysteryId}` : null].filter(Boolean),
    });
  } catch (error) {
    console.error("[Revalidate] エラー:", error);
    return NextResponse.json(
      {
        error: "Revalidation failed",
        message: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}

/**
 * GETリクエスト（ヘルスチェック用）
 */
export async function GET() {
  return NextResponse.json({
    status: "ok",
    endpoint: "revalidate",
    method: "POST required",
  });
}
