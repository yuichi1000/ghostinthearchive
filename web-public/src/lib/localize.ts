/**
 * 後方互換: shared パッケージから再エクスポート
 * 新コードは @ghost/shared/src/lib/localize から直接 import すること
 */
export { localizeMystery, getTranslatedExcerpt } from "@ghost/shared/src/lib/localize"
export type { LocalizedMystery } from "@ghost/shared/src/lib/localize"
