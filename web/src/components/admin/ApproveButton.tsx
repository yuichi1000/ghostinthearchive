"use client";

import { useState } from "react";
import { Check, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { approveMystery } from "@/lib/firestore/mysteries";

interface ApproveButtonProps {
  /** 承認対象のミステリーID */
  mysteryId: string;
  /** 承認成功時のコールバック */
  onSuccess?: () => void;
}

/**
 * ApproveButton コンポーネント
 * 承認＆公開ボタン（確認ダイアログ付き）
 */
export function ApproveButton({ mysteryId, onSuccess }: ApproveButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);

  /**
   * 承認処理を実行
   */
  const handleApprove = async () => {
    setLoading(true);
    setError(null);

    try {
      // Firestoreのステータスを更新
      await approveMystery(mysteryId);

      // ISR再検証をトリガー
      const revalidateRes = await fetch("/api/revalidate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          mysteryId,
          secret: process.env.NEXT_PUBLIC_REVALIDATE_SECRET,
        }),
      });

      if (!revalidateRes.ok) {
        console.warn("ISR再検証に失敗しましたが、承認は完了しています");
      }

      setShowConfirm(false);
      onSuccess?.();
    } catch (err) {
      console.error("承認エラー:", err);
      setError(err instanceof Error ? err.message : "承認に失敗しました");
    } finally {
      setLoading(false);
    }
  };

  // 確認ダイアログ表示中
  if (showConfirm) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted">公開しますか？</span>
        <Button
          variant="primary"
          size="sm"
          loading={loading}
          onClick={handleApprove}
          icon={<Check className="h-3.5 w-3.5" />}
        >
          はい
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setShowConfirm(false)}
          disabled={loading}
        >
          キャンセル
        </Button>
      </div>
    );
  }

  // エラー表示
  if (error) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-xs text-blood flex items-center gap-1">
          <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
          {error}
        </span>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => setError(null)}
        >
          再試行
        </Button>
      </div>
    );
  }

  // 通常表示
  return (
    <Button
      variant="primary"
      size="sm"
      onClick={() => setShowConfirm(true)}
      icon={<Check className="h-3.5 w-3.5" />}
    >
      承認して公開
    </Button>
  );
}
