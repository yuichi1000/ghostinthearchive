/**
 * 認証ヘルパー（Cloud IAP / NextAuth.js 両対応）
 */

/**
 * Cloud IAP ヘッダーから認証済みユーザーのメールアドレスを取得
 * 本番環境（Cloud Run + Cloud IAP）で使用
 */
export function getIAPUser(headers: Headers): string | null {
  // Cloud IAP は "accounts.google.com:email@example.com" 形式でヘッダーを付与
  const iapEmail = headers.get("X-Goog-Authenticated-User-Email");
  if (iapEmail) {
    return iapEmail.replace("accounts.google.com:", "");
  }
  return null;
}

/**
 * Cloud IAP のユーザーIDを取得
 */
export function getIAPUserId(headers: Headers): string | null {
  const iapId = headers.get("X-Goog-Authenticated-User-Id");
  if (iapId) {
    return iapId.replace("accounts.google.com:", "");
  }
  return null;
}

/**
 * Cloud IAP 経由のリクエストかどうかを判定
 */
export function isIAPRequest(headers: Headers): boolean {
  return headers.has("X-Goog-Authenticated-User-Email");
}
