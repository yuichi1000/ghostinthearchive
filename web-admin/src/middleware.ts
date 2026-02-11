import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * 認証ミドルウェア
 * - 本番: Cloud IAP ヘッダーで認証確認（defense-in-depth）
 * - ローカル: 認証なし（開発環境）
 */
export function middleware(request: NextRequest) {
  if (process.env.NODE_ENV === "production") {
    const iapEmail = request.headers.get("X-Goog-Authenticated-User-Email");
    if (!iapEmail) {
      return new NextResponse("Unauthorized", { status: 401 });
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
