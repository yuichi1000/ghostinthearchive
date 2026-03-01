"use client"

import { usePathname } from "next/navigation"
import { AlertTriangle } from "lucide-react"

/**
 * クライアントサイドエラーバウンダリ
 * 英語ハードコード — エラー表示中に辞書読み込みが失敗するリスクを回避
 */
export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const pathname = usePathname()
  const lang = pathname.split("/")[1] || "en"

  return (
    <div className="min-h-screen flex flex-col film-grain">
      {/* 簡易ヘッダー（高さのみ合わせる） */}
      <div className="h-16 border-b border-border/50" />

      <main className="flex-1 flex items-center justify-center">
        <div className="text-center px-4">
          <AlertTriangle className="h-12 w-12 text-gold mx-auto mb-6" />
          <h1 className="font-serif text-2xl md:text-3xl text-parchment mb-3">
            Something went wrong
          </h1>
          <p className="text-muted-foreground mb-8 max-w-md mx-auto">
            An unexpected error occurred. Please try again or return to the home page.
          </p>
          <div className="flex items-center justify-center gap-4">
            <button
              onClick={reset}
              className="px-6 py-2 border border-border rounded-sm text-parchment hover:bg-muted/20 transition-colors"
            >
              Try again
            </button>
            <a
              href={`/${lang}/`}
              className="px-6 py-2 border border-gold/50 rounded-sm text-gold hover:bg-gold/10 transition-colors no-underline"
            >
              Return home
            </a>
          </div>
        </div>
      </main>
    </div>
  )
}
