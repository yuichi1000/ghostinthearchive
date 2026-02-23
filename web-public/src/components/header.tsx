"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Archive } from "lucide-react"
import { LanguageSwitcher } from "./language-switcher"
import type { SupportedLang } from "@/lib/i18n/config"

interface HeaderProps {
  lang?: SupportedLang
  nav?: { about: string; archive: string }
}

export function Header({ lang = "en", nav }: HeaderProps) {
  const pathname = usePathname()
  const isArchiveActive = pathname.startsWith(`/${lang}/archive`)
  const isAboutActive = pathname.startsWith(`/${lang}/about`)

  return (
    <header className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href={`/${lang}/`} className="flex items-center gap-3 group">
            <div className="relative">
              <Archive className="w-6 h-6 text-gold" />
              <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-blood-red rounded-full animate-pulse" />
            </div>
            <span className="hidden sm:inline font-serif text-lg text-parchment leading-tight group-hover:text-gold transition-colors">
              Ghost in the Archive
            </span>
          </Link>

          {/* Nav + Language Switcher */}
          <div className="flex items-center gap-4">
            {nav && (
              <nav className="flex items-center gap-4">
                <Link
                  href={`/${lang}/archive/`}
                  className={`text-sm font-mono uppercase tracking-wider transition-colors no-underline ${
                    isArchiveActive
                      ? "text-gold"
                      : "text-muted-foreground hover:text-parchment"
                  }`}
                >
                  {nav.archive}
                </Link>
                <Link
                  href={`/${lang}/about/`}
                  className={`text-sm font-mono uppercase tracking-wider transition-colors no-underline ${
                    isAboutActive
                      ? "text-gold"
                      : "text-muted-foreground hover:text-parchment"
                  }`}
                >
                  {nav.about}
                </Link>
              </nav>
            )}
            <LanguageSwitcher currentLang={lang} />
          </div>
        </div>
      </div>
    </header>
  )
}
