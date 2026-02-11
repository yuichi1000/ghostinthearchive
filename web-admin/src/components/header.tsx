"use client"

import Link from "next/link"
import { Archive } from "lucide-react"

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative">
              <Archive className="w-6 h-6 text-gold" />
              <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-blood-red rounded-full animate-pulse" />
            </div>
            <span className="font-serif text-lg text-parchment leading-tight group-hover:text-gold transition-colors">
              Ghost in the Archive
            </span>
          </Link>
        </div>
      </div>
    </header>
  )
}
