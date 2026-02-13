"use client"

import { Globe, Check } from "lucide-react"
import { useState, useRef, useEffect } from "react"
import type { TranslationLang } from "@ghost/shared/src/types/mystery"

/**
 * 利用可能な翻訳言語の定義
 */
const ALL_LANGS = [
  { code: "en" as const, label: "English" },
  { code: "ja" as const, label: "日本語" },
  { code: "es" as const, label: "Español" },
  { code: "de" as const, label: "Deutsch" },
  { code: "fr" as const, label: "Français" },
  { code: "nl" as const, label: "Nederlands" },
  { code: "pt" as const, label: "Português" },
] as const

export type PreviewLang = "en" | TranslationLang

interface LanguageSelectorProps {
  currentLang: PreviewLang
  onLangChange: (lang: PreviewLang) => void
  /** translations map に存在する言語 */
  availableLangs: string[]
  /** *_ja レガシーフィールドが存在するか */
  hasLegacyJa?: boolean
}

export function LanguageSelector({
  currentLang,
  onLangChange,
  availableLangs,
  hasLegacyJa = false,
}: LanguageSelectorProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const hasTranslation = (code: string) => {
    if (code === "en") return true
    if (code === "ja" && hasLegacyJa) return true
    return availableLangs.includes(code)
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-card border border-border rounded-sm hover:border-gold/50 transition-colors"
      >
        <Globe className="w-4 h-4 text-gold" />
        <span className="font-mono text-xs uppercase">{currentLang}</span>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-56 bg-card border border-border rounded-sm shadow-lg z-50">
          {ALL_LANGS.map(({ code, label }) => {
            const available = hasTranslation(code)
            return (
              <button
                key={code}
                onClick={() => {
                  onLangChange(code)
                  setOpen(false)
                }}
                className={`w-full flex items-center gap-3 px-4 py-2 text-sm text-left transition-colors ${
                  code === currentLang
                    ? "text-gold bg-gold/10"
                    : available
                    ? "text-foreground hover:bg-card/80"
                    : "text-muted-foreground/50"
                }`}
              >
                <span className="font-mono text-xs uppercase w-6">{code}</span>
                <span className="flex-1">{label}</span>
                {code === currentLang && <Check className="w-3 h-3 text-gold" />}
                {available ? (
                  <span className="w-2 h-2 rounded-full bg-green-500" title="翻訳あり" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-gray-600" title="翻訳なし" />
                )}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}
