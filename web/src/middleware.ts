import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * 認証ミドルウェア
 * /admin/* ルートを保護
 * - 本番: Cloud IAP ヘッダーで認証確認
 * - ローカル: NextAuth.js セッションで認証確認
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // /admin/login は認証不要
  if (pathname.startsWith("/admin/login")) {
    return NextResponse.next();
  }

  // /admin/* ルートを保護
  if (pathname.startsWith("/admin")) {
    // 本番: Cloud IAP ヘッダー確認
    const iapEmail = request.headers.get("X-Goog-Authenticated-User-Email");
    if (iapEmail) {
      // IAP 通過済み = 認証済み
      return NextResponse.next();
    }

    // ローカル: NextAuth.js セッション確認
    const sessionToken =
      request.cookies.get("next-auth.session-token") ||
      request.cookies.get("__Secure-next-auth.session-token");

    if (!sessionToken) {
      // 未認証 → ログインページへリダイレクト
      const loginUrl = new URL("/admin/login", request.url);
      loginUrl.searchParams.set("callbackUrl", pathname);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*"],
};
