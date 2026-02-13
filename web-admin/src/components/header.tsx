"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Archive, Mic } from "lucide-react"
import { cn } from "@ghost/shared/src/lib/utils"
import { HeaderLanguageSelector } from "@/components/header-language-selector"

export function Header() {
  const pathname = usePathname()

  return (
    <header className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo + ナビゲーション */}
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="relative">
                <Archive className="w-6 h-6 text-gold" />
                <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-blood-red rounded-full animate-pulse" />
              </div>
              <span className="font-serif text-lg text-parchment leading-tight group-hover:text-gold transition-colors">
                Ghost in the Archive
              </span>
            </Link>

            {/* ナビゲーションリンク */}
            <nav className="hidden sm:flex items-center gap-1">
              <Link
                href="/"
                className={cn(
                  "px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded-sm transition-colors no-underline",
                  pathname === "/"
                    ? "text-gold bg-gold/10"
                    : "text-muted-foreground hover:text-parchment"
                )}
              >
                ダッシュボード
              </Link>
              <Link
                href="/podcasts"
                className={cn(
                  "inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded-sm transition-colors no-underline",
                  pathname.startsWith("/podcasts")
                    ? "text-gold bg-gold/10"
                    : "text-muted-foreground hover:text-parchment"
                )}
              >
                <Mic className="w-3.5 h-3.5" />
                Podcast
              </Link>
            </nav>
          </div>

          {/* グローバル言語セレクタ */}
          <HeaderLanguageSelector />
        </div>
      </div>
    </header>
  )
}
