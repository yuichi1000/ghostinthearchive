"use client";

import Link from "next/link";
import { Archive, Settings, LogOut } from "lucide-react";
import { useSession, signOut } from "next-auth/react";

/**
 * AdminHeader コンポーネント
 * 管理画面専用のヘッダー（認証状態を表示）
 */
export function AdminHeader() {
  const { data: session } = useSession();

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
                歴史的ミステリーの発掘
              </p>
            </div>
          </Link>

          {/* ナビゲーション */}
          <nav className="flex items-center gap-4">
            <Link
              href="/"
              className="text-sm text-muted hover:text-ink transition-colors no-underline"
            >
              公開サイトへ
            </Link>

            {/* ユーザー情報（ログイン時のみ表示） */}
            {session?.user && (
              <>
                <span className="flex items-center gap-2 text-sm font-medium text-navy">
                  <Settings className="h-4 w-4" aria-hidden="true" />
                  管理画面
                </span>
                <div className="flex items-center gap-3 pl-4 border-l border-border">
                  {session.user.image && (
                    <img
                      src={session.user.image}
                      alt=""
                      className="w-7 h-7 rounded-full"
                    />
                  )}
                  <span className="text-sm text-muted hidden md:block max-w-[150px] truncate">
                    {session.user.email}
                  </span>
                  <button
                    onClick={() => signOut({ callbackUrl: "/admin/login" })}
                    className="flex items-center gap-1 text-sm text-muted hover:text-blood transition-colors"
                    title="ログアウト"
                  >
                    <LogOut className="h-4 w-4" aria-hidden="true" />
                    <span className="hidden sm:inline">ログアウト</span>
                  </button>
                </div>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
