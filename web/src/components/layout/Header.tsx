import Link from "next/link";
import { Archive, Settings } from "lucide-react";
import { AdminLink } from "./AdminLink";

interface HeaderProps {
  /** 管理画面モード */
  isAdmin?: boolean;
}

/**
 * Header コンポーネント
 * サイト共通のヘッダーナビゲーション
 */
export function Header({ isAdmin = false }: HeaderProps) {
  return (
    <header className="border-b border-border bg-paper/95 backdrop-blur-sm sticky top-0 z-40">
      <div className="container-wide">
        <div className="flex items-center justify-between h-16">
          {/* ロゴ・サイト名 */}
          <Link href="/" className="flex items-center gap-3 no-underline group">
            <Archive
              className="h-6 w-6 text-navy group-hover:text-blood transition-colors"
              aria-hidden="true"
            />
            <div>
              <h1 className="font-serif text-lg font-semibold text-ink leading-tight">
                Ghost in the Archive
              </h1>
              <p className="text-xs text-muted hidden sm:block">
                Unearthing Historical Mysteries
              </p>
            </div>
          </Link>

          {/* ナビゲーション */}
          <nav className="flex items-center gap-6">
            {isAdmin ? (
              <>
                <Link
                  href="/"
                  className="text-sm text-muted hover:text-ink transition-colors no-underline"
                >
                  公開サイトへ
                </Link>
                <span className="flex items-center gap-2 text-sm font-medium text-navy">
                  <Settings className="h-4 w-4" aria-hidden="true" />
                  管理画面
                </span>
              </>
            ) : (
              <>
                <Link
                  href="/"
                  className="text-sm text-muted hover:text-ink transition-colors no-underline"
                >
                  Home
                </Link>
                <AdminLink />
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
