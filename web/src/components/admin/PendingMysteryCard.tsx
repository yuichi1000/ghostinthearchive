"use client";

import { Calendar, Eye } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge, ConfidenceBadge, DiscrepancyBadge } from "@/components/ui/Badge";
import { ApproveButton } from "./ApproveButton";
import type { FirestoreMystery } from "@/types/mystery";

interface PendingMysteryCardProps {
  /** ミステリーデータ */
  mystery: FirestoreMystery;
  /** 承認成功時のコールバック */
  onApproved?: () => void;
}

/**
 * PendingMysteryCard コンポーネント
 * 承認待ちミステリーの表示カード
 */
export function PendingMysteryCard({
  mystery,
  onApproved,
}: PendingMysteryCardProps) {
  /**
   * サマリーを指定文字数で切り詰める
   */
  const truncateSummary = (text: string, maxLength: number = 200): string => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength).trim() + "...";
  };

  /**
   * 日付をフォーマット
   */
  const formatDate = (date: Date): string => {
    return new Intl.DateTimeFormat("ja-JP", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  };

  return (
    <Card className="h-full">
      <CardContent>
        {/* ヘッダー: ステータスとバッジ */}
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Badge variant="pending">承認待ち</Badge>
          <DiscrepancyBadge type={mystery.discrepancy_type} />
          <ConfidenceBadge level={mystery.confidence_level} />
        </div>

        {/* タイトル */}
        <h3 className="font-serif text-lg font-semibold text-ink mb-2">
          {mystery.title}
        </h3>

        {/* ミステリーID */}
        <p className="text-xs text-muted font-mono mb-2">
          ID: {mystery.mystery_id}
        </p>

        {/* サマリー */}
        <p className="text-sm text-muted leading-relaxed mb-4">
          {truncateSummary(mystery.summary)}
        </p>

        {/* 発見された矛盾 */}
        <div className="bg-ink/5 rounded p-3 mb-4">
          <h4 className="text-xs font-medium text-muted uppercase tracking-wide mb-1">
            発見された矛盾
          </h4>
          <p className="text-sm text-ink">{mystery.discrepancy_detected}</p>
        </div>

        {/* 証拠プレビュー */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
          <div className="border border-border rounded p-3">
            <h4 className="text-xs font-medium text-muted mb-1">証拠A</h4>
            <p className="text-sm text-ink truncate">
              {mystery.evidence_a.source_title}
            </p>
            <p className="text-xs text-muted">
              {mystery.evidence_a.source_language === "en" ? "英語" : "スペイン語"}
            </p>
          </div>
          <div className="border border-border rounded p-3">
            <h4 className="text-xs font-medium text-muted mb-1">証拠B</h4>
            <p className="text-sm text-ink truncate">
              {mystery.evidence_b.source_title}
            </p>
            <p className="text-xs text-muted">
              {mystery.evidence_b.source_language === "en" ? "英語" : "スペイン語"}
            </p>
          </div>
        </div>

        {/* フッター: 日付とアクション */}
        <div className="flex items-center justify-between pt-4 border-t border-border">
          <div className="flex items-center gap-1.5 text-xs text-muted">
            <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
            <time dateTime={mystery.createdAt.toISOString()}>
              {formatDate(mystery.createdAt)}
            </time>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={`/mystery/${mystery.mystery_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-muted hover:text-navy transition-colors"
            >
              <Eye className="h-3.5 w-3.5" aria-hidden="true" />
              プレビュー
            </a>
            <ApproveButton
              mysteryId={mystery.mystery_id}
              onSuccess={onApproved}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
