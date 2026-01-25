"use client";

import { forwardRef, ButtonHTMLAttributes } from "react";
import { Loader2 } from "lucide-react";

/** ボタンのバリアント */
type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";

/** ボタンのサイズ */
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** ボタンのスタイルバリアント */
  variant?: ButtonVariant;
  /** ボタンのサイズ */
  size?: ButtonSize;
  /** ローディング状態 */
  loading?: boolean;
  /** アイコン（左側） */
  icon?: React.ReactNode;
}

/** バリアント別のスタイル */
const variantStyles: Record<ButtonVariant, string> = {
  primary:
    "bg-navy text-white border-navy hover:bg-[#0F1A24] disabled:bg-navy/50",
  secondary:
    "bg-transparent text-navy border-border hover:bg-navy/5 hover:border-navy disabled:opacity-50",
  danger:
    "bg-blood text-white border-blood hover:bg-[#6B0000] disabled:bg-blood/50",
  ghost:
    "bg-transparent text-ink border-transparent hover:bg-ink/5 disabled:opacity-50",
};

/** サイズ別のスタイル */
const sizeStyles: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

/**
 * Button コンポーネント
 * アンティーク調のボタン（letterpress風ボーダー）
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  function Button(
    {
      variant = "primary",
      size = "md",
      loading = false,
      icon,
      disabled,
      className = "",
      children,
      ...props
    },
    ref
  ) {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={`
          inline-flex items-center justify-center gap-2
          font-medium rounded
          border transition-all duration-200
          focus:outline-none focus:ring-2 focus:ring-navy/30 focus:ring-offset-1
          disabled:cursor-not-allowed
          ${variantStyles[variant]}
          ${sizeStyles[size]}
          ${className}
        `}
        {...props}
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : icon ? (
          <span className="shrink-0" aria-hidden="true">
            {icon}
          </span>
        ) : null}
        {children}
      </button>
    );
  }
);
