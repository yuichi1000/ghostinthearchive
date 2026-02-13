"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import type { PreviewLang } from "@/components/language-selector"

const STORAGE_KEY = "ghost-admin-lang"
const SUPPORTED_LANGS: PreviewLang[] = ["en", "ja", "es", "de", "fr", "nl", "pt"]
const DEFAULT_LANG: PreviewLang = "en"

interface LanguageContextValue {
  lang: PreviewLang
  setLang: (lang: PreviewLang) => void
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

/**
 * ブラウザ言語からサポート言語を検出する
 * navigator.language の先頭2文字を抽出し、サポート言語に含まれるか判定
 */
function detectBrowserLang(): PreviewLang {
  if (typeof navigator === "undefined") return DEFAULT_LANG
  const browserLang = navigator.language.slice(0, 2).toLowerCase()
  const matched = SUPPORTED_LANGS.find((l) => l === browserLang)
  return matched ?? DEFAULT_LANG
}

/**
 * グローバル言語設定 Provider
 * - localStorage から復元、なければブラウザ言語を検出
 * - 言語変更時に localStorage に永続化
 */
export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<PreviewLang>(DEFAULT_LANG)
  const [initialized, setInitialized] = useState(false)

  // クライアントサイドで初期化（SSR 安全）
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored && SUPPORTED_LANGS.includes(stored as PreviewLang)) {
      setLangState(stored as PreviewLang)
    } else {
      const detected = detectBrowserLang()
      setLangState(detected)
      localStorage.setItem(STORAGE_KEY, detected)
    }
    setInitialized(true)
  }, [])

  const setLang = (newLang: PreviewLang) => {
    setLangState(newLang)
    localStorage.setItem(STORAGE_KEY, newLang)
  }

  // 初期化前はデフォルト言語で表示（ちらつき防止のため children は常にレンダリング）
  return (
    <LanguageContext.Provider value={{ lang: initialized ? lang : DEFAULT_LANG, setLang }}>
      {children}
    </LanguageContext.Provider>
  )
}

/**
 * グローバル言語を取得・設定するフック
 */
export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider")
  }
  return context
}
