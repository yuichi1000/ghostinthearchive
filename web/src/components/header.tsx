"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useSession, signOut } from "next-auth/react"
import { Archive, Search, Menu, LogOut } from "lucide-react"

export function Header() {
  const pathname = usePathname()
  const isAdmin = pathname?.startsWith("/admin")
  const { data: session } = useSession()

  return (
    <header className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative">
              <Archive className="w-6 h-6 text-gold" />
              <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-blood-red rounded-full animate-pulse" />
            </div>
            <div className="flex flex-col">
              <span className="font-serif text-lg text-parchment leading-tight group-hover:text-gold transition-colors">
                Ghost in the Archive
              </span>
              <span className="text-[10px] text-muted-foreground font-mono uppercase tracking-widest hidden sm:block">
                公文書の亡霊
              </span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/"
              className="text-sm text-muted-foreground hover:text-parchment transition-colors font-mono uppercase tracking-wide"
            >
              Discoveries
            </Link>
            {session && (
              <Link
                href="/admin"
                className="text-sm text-muted-foreground hover:text-parchment transition-colors font-mono uppercase tracking-wide"
              >
                Admin
              </Link>
            )}
            <button className="p-2 text-muted-foreground hover:text-parchment transition-colors" aria-label="Search archives">
              <Search className="w-4 h-4" />
            </button>
            {isAdmin && session && (
              <button
                onClick={() => signOut({ callbackUrl: "/" })}
                className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-[#ff6b6b] transition-colors font-mono uppercase tracking-wide"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            )}
          </nav>

          {/* Mobile menu button */}
          <button className="md:hidden p-2 text-muted-foreground hover:text-parchment transition-colors" aria-label="Open menu">
            <Menu className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  )
}
