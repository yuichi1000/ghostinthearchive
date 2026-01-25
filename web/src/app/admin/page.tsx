"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, Inbox, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { PendingMysteryCard } from "@/components/admin/PendingMysteryCard";
import { CardSkeleton } from "@/components/ui/Loading";
import { getPendingMysteries } from "@/lib/firestore/mysteries";
import type { FirestoreMystery } from "@/types/mystery";

/**
 * 管理ダッシュボード
 * pendingステータスのミステリーを表示し、承認・公開機能を提供
 */
export default function AdminDashboard() {
  const [mysteries, setMysteries] = useState<FirestoreMystery[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  /**
   * ミステリー一覧を取得
   */
  const fetchMysteries = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);
    try {
      const data = await getPendingMysteries(50);
      setMysteries(data);
    } catch (error) {
      console.error("ミステリーの取得に失敗:", error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  /**
   * 初回読み込み
   */
  useEffect(() => {
    fetchMysteries();
  }, [fetchMysteries]);

  /**
   * 承認成功時の処理
   */
  const handleApproved = useCallback(() => {
    setSuccessMessage("ミステリーを公開しました");
    fetchMysteries();

    // 3秒後にメッセージを消す
    setTimeout(() => {
      setSuccessMessage(null);
    }, 3000);
  }, [fetchMysteries]);

  /**
   * 手動リフレッシュ
   */
  const handleRefresh = () => {
    fetchMysteries(true);
  };

  return (
    <div className="py-8">
      <div className="container-wide">
        {/* ヘッダー */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="font-serif text-2xl font-bold text-ink">
              管理ダッシュボード
            </h1>
            <p className="text-sm text-muted mt-1">
              承認待ちのミステリーを確認し、公開を管理します
            </p>
          </div>

          <Button
            variant="secondary"
            onClick={handleRefresh}
            loading={refreshing}
            icon={<RefreshCw className="h-4 w-4" />}
          >
            更新
          </Button>
        </div>

        {/* 成功メッセージ */}
        {successMessage && (
          <div className="mb-6 p-4 bg-published/10 border border-published/30 rounded flex items-center gap-3">
            <CheckCircle className="h-5 w-5 text-published" aria-hidden="true" />
            <span className="text-sm text-published font-medium">
              {successMessage}
            </span>
          </div>
        )}

        {/* ローディング */}
        {loading ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[...Array(4)].map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
        ) : mysteries.length === 0 ? (
          /* 空状態 */
          <div className="text-center py-16">
            <Inbox className="h-12 w-12 text-muted mx-auto mb-4" aria-hidden="true" />
            <h2 className="font-serif text-xl text-ink mb-2">
              承認待ちのミステリーはありません
            </h2>
            <p className="text-muted">
              新しいミステリーがエージェントによって発見されると、
              <br />
              ここに表示されます。
            </p>
          </div>
        ) : (
          /* ミステリー一覧 */
          <>
            <div className="mb-4 text-sm text-muted">
              {mysteries.length} 件の承認待ちミステリー
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {mysteries.map((mystery) => (
                <PendingMysteryCard
                  key={mystery.mystery_id}
                  mystery={mystery}
                  onApproved={handleApproved}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
