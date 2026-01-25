import { ReactNode } from "react";
import type {
  MysteryStatus,
  ConfidenceLevel,
  DiscrepancyType,
} from "@/types/mystery";

/** バッジのバリアント */
type BadgeVariant =
  | "default"
  | "pending"
  | "published"
  | "archived"
  | "high"
  | "medium"
  | "low";

interface BadgeProps {
  /** バッジのバリアント */
  variant?: BadgeVariant;
  /** 表示テキスト */
  children: ReactNode;
  /** 追加のクラス名 */
  className?: string;
}

/** バリアント別のスタイル */
const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-ink/10 text-ink border-ink/20",
  pending: "bg-pending/20 text-[#8B6914] border-pending/40",
  published: "bg-published/20 text-published border-published/40",
  archived: "bg-muted/20 text-muted border-muted/40",
  high: "bg-published/20 text-published border-published/30",
  medium: "bg-pending/20 text-[#8B6914] border-pending/30",
  low: "bg-blood/10 text-blood border-blood/20",
};

/**
 * Badge コンポーネント
 * ステータスや信頼度を表示するバッジ
 */
export function Badge({
  variant = "default",
  children,
  className = "",
}: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center
        px-2.5 py-0.5
        text-xs font-medium
        rounded-full border
        ${variantStyles[variant]}
        ${className}
      `}
    >
      {children}
    </span>
  );
}

/**
 * ステータスバッジ
 * ミステリーのステータスを表示
 */
export function StatusBadge({ status }: { status: MysteryStatus }) {
  const labels: Record<MysteryStatus, string> = {
    pending: "承認待ち",
    published: "公開中",
    archived: "アーカイブ",
  };

  return <Badge variant={status}>{labels[status]}</Badge>;
}

/**
 * 信頼度バッジ
 * 仮説の信頼度を表示
 */
export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const labels: Record<ConfidenceLevel, string> = {
    high: "High Confidence",
    medium: "Medium Confidence",
    low: "Low Confidence",
  };

  return <Badge variant={level}>{labels[level]}</Badge>;
}

/**
 * 矛盾タイプバッジ
 * 検出された矛盾の種類を表示
 */
export function DiscrepancyBadge({ type }: { type: DiscrepancyType }) {
  const labels: Record<DiscrepancyType, string> = {
    date_mismatch: "Date Mismatch",
    person_missing: "Person Missing",
    event_outcome: "Outcome Discrepancy",
    location_conflict: "Location Conflict",
    narrative_gap: "Narrative Gap",
    name_variant: "Name Variant",
  };

  return <Badge variant="default">{labels[type]}</Badge>;
}
