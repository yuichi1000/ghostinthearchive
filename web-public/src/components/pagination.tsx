import Link from "next/link"
import { ChevronLeft, ChevronRight } from "lucide-react"
import type { Dictionary } from "@/lib/i18n/dictionaries"

interface PaginationProps {
  currentPage: number
  totalPages: number
  basePath: string
  labels: Dictionary["archive"]
}

/**
 * ページ番号リストを生成（省略表示対応）
 * 例: 1 ... 4 5 6 ... 10
 */
function getPageNumbers(current: number, total: number): (number | "ellipsis")[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }

  const pages: (number | "ellipsis")[] = [1]

  if (current > 3) {
    pages.push("ellipsis")
  }

  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  if (current < total - 2) {
    pages.push("ellipsis")
  }

  pages.push(total)

  return pages
}

function pageHref(basePath: string, page: number): string {
  return page === 1 ? basePath : `${basePath}/${page}`
}

export function Pagination({ currentPage, totalPages, basePath, labels }: PaginationProps) {
  if (totalPages <= 1) return null

  const pages = getPageNumbers(currentPage, totalPages)

  return (
    <nav aria-label="Pagination" className="flex items-center justify-center gap-1 mt-12">
      {/* 前へ */}
      {currentPage > 1 ? (
        <Link
          href={pageHref(basePath, currentPage - 1)}
          className="flex items-center gap-1 px-3 py-2 text-sm font-mono text-muted-foreground hover:text-parchment transition-colors no-underline"
        >
          <ChevronLeft className="w-4 h-4" />
          <span className="hidden sm:inline">{labels.previous}</span>
        </Link>
      ) : (
        <span className="flex items-center gap-1 px-3 py-2 text-sm font-mono text-muted-foreground/30">
          <ChevronLeft className="w-4 h-4" />
          <span className="hidden sm:inline">{labels.previous}</span>
        </span>
      )}

      {/* ページ番号 */}
      <div className="flex items-center gap-1">
        {pages.map((page, i) =>
          page === "ellipsis" ? (
            <span key={`ellipsis-${i}`} className="px-2 py-2 text-sm font-mono text-muted-foreground/50">
              ...
            </span>
          ) : page === currentPage ? (
            <span
              key={page}
              className="px-3 py-2 text-sm font-mono text-gold border border-gold/30 bg-gold/10 rounded-sm"
              aria-current="page"
            >
              {page}
            </span>
          ) : (
            <Link
              key={page}
              href={pageHref(basePath, page)}
              className="px-3 py-2 text-sm font-mono text-muted-foreground hover:text-parchment hover:bg-paper-light rounded-sm transition-colors no-underline"
            >
              {page}
            </Link>
          )
        )}
      </div>

      {/* 次へ */}
      {currentPage < totalPages ? (
        <Link
          href={pageHref(basePath, currentPage + 1)}
          className="flex items-center gap-1 px-3 py-2 text-sm font-mono text-muted-foreground hover:text-parchment transition-colors no-underline"
        >
          <span className="hidden sm:inline">{labels.next}</span>
          <ChevronRight className="w-4 h-4" />
        </Link>
      ) : (
        <span className="flex items-center gap-1 px-3 py-2 text-sm font-mono text-muted-foreground/30">
          <span className="hidden sm:inline">{labels.next}</span>
          <ChevronRight className="w-4 h-4" />
        </span>
      )}
    </nav>
  )
}
