"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { Globe } from "lucide-react"
import { useState, useRef, useEffect } from "react"
import { SUPPORTED_LANGS, LANG_NAMES } from "@/lib/i18n/config"
import type { SupportedLang } from "@/lib/i18n/config"

interface LanguageSwitcherProps {
  currentLang: SupportedLang
}

export function LanguageSwitcher({ currentLang }: LanguageSwitcherProps) {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  // パスから言語プレフィックスを除去して他言語のパスを生成
  const getPathForLang = (lang: SupportedLang) => {
    // pathname: /en/mystery/... → /ja/mystery/...
    const segments = pathname.split("/")
    segments[1] = lang
    return segments.join("/")
  }

  // 外部クリックで閉じる
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleSelect = (lang: SupportedLang) => {
    localStorage.setItem("preferred-lang", lang)
    setOpen(false)
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground hover:text-parchment transition-colors border border-border/50 rounded-sm hover:border-border"
        aria-label="Change language"
      >
        <Globe className="w-4 h-4" />
        <span className="font-mono text-xs uppercase">{currentLang}</span>
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-48 bg-card border border-border rounded-sm shadow-lg z-50">
          {SUPPORTED_LANGS.map((lang) => (
            <Link
              key={lang}
              href={getPathForLang(lang)}
              onClick={() => handleSelect(lang)}
              className={`block px-4 py-2 text-sm no-underline transition-colors ${
                lang === currentLang
                  ? "text-gold bg-gold/10"
                  : "text-muted-foreground hover:text-parchment hover:bg-card/80"
              }`}
            >
              <span className="font-mono text-xs mr-2 uppercase">{lang}</span>
              {LANG_NAMES[lang]}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
