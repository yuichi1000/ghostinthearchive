"use client";

import Link from "next/link";
import { Settings } from "lucide-react";
import { useSession } from "next-auth/react";

/**
 * AdminLink コンポーネント
 * 認証済みユーザーにのみ管理画面へのリンクを表示
 */
export function AdminLink() {
  const { data: session } = useSession();

  if (!session?.user) {
    return null;
  }

  return (
    <Link
      href="/admin"
      className="text-sm text-muted hover:text-ink transition-colors no-underline flex items-center gap-1"
    >
      <Settings className="h-4 w-4" aria-hidden="true" />
      <span className="hidden sm:inline">管理</span>
    </Link>
  );
}
