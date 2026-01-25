import { ReactNode } from "react";

interface CardProps {
  /** 子要素 */
  children: ReactNode;
  /** 追加のクラス名 */
  className?: string;
  /** ホバー効果を有効にする */
  hoverable?: boolean;
  /** パディングなしで表示 */
  noPadding?: boolean;
}

/**
 * Card コンポーネント
 * 羊皮紙風のカードコンテナ
 */
export function Card({
  children,
  className = "",
  hoverable = false,
  noPadding = false,
}: CardProps) {
  return (
    <div
      className={`
        bg-paper border border-border rounded
        shadow-sm
        ${hoverable ? "transition-shadow duration-200 hover:shadow-md" : ""}
        ${noPadding ? "" : "p-6"}
        ${className}
      `}
    >
      {children}
    </div>
  );
}

/**
 * CardHeader コンポーネント
 * カードのヘッダー部分
 */
export function CardHeader({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`mb-4 ${className}`}>
      {children}
    </div>
  );
}

/**
 * CardTitle コンポーネント
 * カードのタイトル
 */
export function CardTitle({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <h3 className={`font-serif text-xl font-semibold text-ink ${className}`}>
      {children}
    </h3>
  );
}

/**
 * CardDescription コンポーネント
 * カードの説明テキスト
 */
export function CardDescription({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <p className={`text-sm text-muted mt-1 ${className}`}>
      {children}
    </p>
  );
}

/**
 * CardContent コンポーネント
 * カードの本文部分
 */
export function CardContent({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={className}>{children}</div>;
}

/**
 * CardFooter コンポーネント
 * カードのフッター部分
 */
export function CardFooter({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`mt-4 pt-4 border-t border-border ${className}`}>
      {children}
    </div>
  );
}
