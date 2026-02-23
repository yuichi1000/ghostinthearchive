"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { SUPPORTED_LANGS, DEFAULT_LANG } from "@/lib/i18n/config"
import type { SupportedLang } from "@/lib/i18n/config"

/**
 * ルートページ: ブラウザ言語を検出して /{lang}/ にリダイレクト
 * SSG のため client-side で navigator.language を使用
 */
export default function RootRedirect() {
  const router = useRouter()

  useEffect(() => {
    // localStorage に保存済みの言語を優先
    const stored = localStorage.getItem("preferred-lang")
    if (stored && (SUPPORTED_LANGS as readonly string[]).includes(stored)) {
      router.replace(`/${stored}/`)
      return
    }

    // navigator.language からマッチ（例: "ja-JP" → "ja", "pt-BR" → "pt"）
    const browserLang = navigator.language.split("-")[0]
    const matched: SupportedLang =
      (SUPPORTED_LANGS as readonly string[]).includes(browserLang)
        ? (browserLang as SupportedLang)
        : DEFAULT_LANG

    localStorage.setItem("preferred-lang", matched)
    router.replace(`/${matched}/`)
  }, [router])

  // リダイレクト中のフォールバック表示
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-gold/30 border-t-gold rounded-full animate-spin mx-auto mb-4" />
        <p className="text-sm text-muted-foreground font-mono">Initializing archive access...</p>
      </div>
    </div>
  )
}
