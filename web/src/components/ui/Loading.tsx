import { Loader2 } from "lucide-react";

interface LoadingProps {
  /** 表示サイズ */
  size?: "sm" | "md" | "lg";
  /** 表示テキスト */
  text?: string;
  /** フルスクリーン表示 */
  fullScreen?: boolean;
}

/** サイズ別のスタイル */
const sizeStyles = {
  sm: "h-4 w-4",
  md: "h-8 w-8",
  lg: "h-12 w-12",
};

/**
 * Loading コンポーネント
 * ローディングスピナーを表示
 */
export function Loading({
  size = "md",
  text,
  fullScreen = false,
}: LoadingProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-3">
      <Loader2
        className={`animate-spin text-navy ${sizeStyles[size]}`}
        aria-hidden="true"
      />
      {text && (
        <p className="text-sm text-muted animate-pulse">{text}</p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-paper/80 backdrop-blur-sm z-50">
        {content}
      </div>
    );
  }

  return content;
}

/**
 * LoadingSkeleton コンポーネント
 * コンテンツのスケルトンローディング
 */
export function LoadingSkeleton({
  className = "",
}: {
  className?: string;
}) {
  return (
    <div
      className={`animate-pulse bg-border/50 rounded ${className}`}
      aria-hidden="true"
    />
  );
}

/**
 * CardSkeleton コンポーネント
 * カード形式のスケルトンローディング
 */
export function CardSkeleton() {
  return (
    <div className="bg-paper border border-border rounded p-6">
      <LoadingSkeleton className="h-6 w-3/4 mb-4" />
      <LoadingSkeleton className="h-4 w-full mb-2" />
      <LoadingSkeleton className="h-4 w-5/6 mb-4" />
      <div className="flex gap-2">
        <LoadingSkeleton className="h-6 w-20" />
        <LoadingSkeleton className="h-6 w-16" />
      </div>
    </div>
  );
}
