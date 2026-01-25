import Link from "next/link";
import { Calendar, ChevronRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { ConfidenceBadge, DiscrepancyBadge } from "@/components/ui/Badge";
import type { FirestoreMystery } from "@/types/mystery";

interface MysteryCardProps {
  /** ミステリーデータ */
  mystery: FirestoreMystery;
}

/**
 * MysteryCard コンポーネント
 * ミステリー一覧用のカード表示
 */
export function MysteryCard({ mystery }: MysteryCardProps) {
  /**
   * サマリーを指定文字数で切り詰める
   */
  const truncateSummary = (text: string, maxLength: number = 150): string => {
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength).trim() + "...";
  };

  /**
   * 日付をフォーマット
   */
  const formatDate = (date: Date): string => {
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    }).format(date);
  };

  return (
    <Link href={`/mystery/${mystery.mystery_id}`} className="block no-underline">
      <Card hoverable className="h-full transition-all duration-200 group">
        <CardContent>
          {/* ヘッダー: バッジ */}
          <div className="flex flex-wrap gap-2 mb-3">
            <DiscrepancyBadge type={mystery.discrepancy_type} />
            <ConfidenceBadge level={mystery.confidence_level} />
          </div>

          {/* タイトル */}
          <h2 className="font-serif text-xl font-semibold text-ink mb-2 group-hover:text-navy transition-colors">
            {mystery.title}
          </h2>

          {/* サマリー */}
          <p className="text-sm text-muted leading-relaxed mb-4">
            {truncateSummary(mystery.summary)}
          </p>

          {/* フッター: 日付とリンク */}
          <div className="flex items-center justify-between pt-3 border-t border-border">
            <div className="flex items-center gap-1.5 text-xs text-muted">
              <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
              <time dateTime={mystery.createdAt.toISOString()}>
                {formatDate(mystery.createdAt)}
              </time>
            </div>
            <span className="flex items-center gap-1 text-sm text-navy font-medium group-hover:gap-2 transition-all">
              Read More
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
