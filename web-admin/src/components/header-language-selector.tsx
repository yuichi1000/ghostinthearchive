"use client"

import { Globe, Check } from "lucide-react"
import { useState, useRef, useEffect } from "react"
import { useLanguage } from "@/contexts/language-context"
import { ALL_LANGS } from "@/components/language-selector"

/**
 * ヘッダー用グローバル言語セレクタ
 * 翻訳可否ドットは表示しない（記事固有情報のためヘッダーでは不要）
 */
export function HeaderLanguageSelector() {
  const { lang, setLang } = useLanguage()
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

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-card border border-border rounded-sm hover:border-gold/50 transition-colors"
      >
        <Globe className="w-4 h-4 text-gold" />
        <span className="font-mono text-xs uppercase">{lang}</span>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-48 bg-card border border-border rounded-sm shadow-lg z-50">
          {ALL_LANGS.map(({ code, label }) => (
            <button
              key={code}
              onMouseDown={(e) => {
                e.preventDefault()
                e.stopPropagation()
                setLang(code)
                setOpen(false)
              }}
              className={`w-full flex items-center gap-3 px-4 py-2 text-sm text-left transition-colors ${
                code === lang
                  ? "text-gold bg-gold/10"
                  : "text-foreground hover:bg-card/80"
              }`}
            >
              <span className="font-mono text-xs uppercase w-6">{code}</span>
              <span className="flex-1">{label}</span>
              {code === lang && <Check className="w-3 h-3 text-gold" />}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
