"use client"

import { useState, useCallback } from "react"
import { Copy, Check, Share2 } from "lucide-react"
import type { Dictionary } from "@/lib/i18n/dictionaries/types"

// X (Twitter) アイコン
function XIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  )
}

// Facebook アイコン
function FacebookIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 1.092.07 1.375.14v3.316a8 8 0 0 0-.732-.028c-1.04 0-1.44.395-1.44 1.42v2.71h3.26l-.56 3.667h-2.7v8.168C19.396 22.839 24 18.17 24 12.396 24 6.225 19.02 1.2 12.89 1.2S1.78 6.225 1.78 12.396c0 5.172 3.7 9.474 8.59 10.413a12 12 0 0 1-.27.882" />
    </svg>
  )
}

// Reddit アイコン
function RedditIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M12 0C5.373 0 0 5.373 0 12c0 3.314 1.343 6.314 3.515 8.485l-.028.028L12 24l8.485-3.515.028.028C22.657 18.314 24 15.314 24 12c0-6.627-5.373-12-12-12zm5.951 13.49c.037.209.056.421.056.637 0 3.243-3.588 5.873-8.007 5.873s-8.007-2.63-8.007-5.873c0-.216.019-.428.056-.637a1.523 1.523 0 0 1-.635-1.24 1.536 1.536 0 0 1 2.614-1.1 7.7 7.7 0 0 1 4.218-1.348l.796-3.729a.363.363 0 0 1 .432-.28l2.64.558a1.077 1.077 0 1 1-.12.558l-2.353-.497-.713 3.347a7.65 7.65 0 0 1 4.13 1.344 1.535 1.535 0 1 1 1.893 2.387zM9.51 12.53a1.27 1.27 0 1 0 0 2.54 1.27 1.27 0 0 0 0-2.54zm4.98 0a1.27 1.27 0 1 0 0 2.54 1.27 1.27 0 0 0 0-2.54zm-4.49 3.917c-.105-.105-.007-.27.137-.2a5.35 5.35 0 0 0 3.725 0c.145-.07.243.095.137.2a3.44 3.44 0 0 1-2 .63 3.44 3.44 0 0 1-2-.63z" />
    </svg>
  )
}

interface ShareButtonsProps {
  url: string
  title: string
  variant: "compact" | "full"
  labels: Dictionary["share"]
}

export function ShareButtons({ url, title, variant, labels }: ShareButtonsProps) {
  const [copied, setCopied] = useState(false)
  const [hasNativeShare, setHasNativeShare] = useState(false)

  // クライアントサイドで navigator.share の有無を検出
  // useState の初期値では window にアクセスできないため useCallback で遅延チェック
  const checkNativeShare = useCallback((el: HTMLButtonElement | null) => {
    if (el && typeof navigator !== "undefined" && typeof navigator.share === "function") {
      setHasNativeShare(true)
    }
  }, [])

  const shareOnX = () => {
    const params = new URLSearchParams({ text: title, url })
    window.open(
      `https://x.com/intent/post?${params.toString()}`,
      "_blank",
      "width=550,height=420,noopener,noreferrer"
    )
  }

  const shareOnFacebook = () => {
    const params = new URLSearchParams({ u: url })
    window.open(
      `https://www.facebook.com/sharer/sharer.php?${params.toString()}`,
      "_blank",
      "width=550,height=420,noopener,noreferrer"
    )
  }

  const shareOnReddit = () => {
    const params = new URLSearchParams({ url, title })
    window.open(
      `https://www.reddit.com/submit?${params.toString()}`,
      "_blank",
      "width=550,height=620,noopener,noreferrer"
    )
  }

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // フォールバック: テキストエリア経由でコピー
      const textarea = document.createElement("textarea")
      textarea.value = url
      textarea.style.position = "fixed"
      textarea.style.opacity = "0"
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand("copy")
      document.body.removeChild(textarea)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const nativeShare = async () => {
    try {
      await navigator.share({ title, url })
    } catch {
      // ユーザーがキャンセルした場合は何もしない
    }
  }

  if (variant === "compact") {
    return (
      <div className="flex items-center gap-2">
        <button
          onClick={shareOnX}
          aria-label={labels.shareOnX}
          className="p-2 rounded-sm text-muted-foreground hover:text-parchment hover:bg-muted/50 transition-colors"
        >
          <XIcon className="w-4 h-4" />
        </button>
        <button
          onClick={shareOnFacebook}
          aria-label={labels.shareOnFacebook}
          className="p-2 rounded-sm text-muted-foreground hover:text-parchment hover:bg-muted/50 transition-colors"
        >
          <FacebookIcon className="w-4 h-4" />
        </button>
        <button
          onClick={shareOnReddit}
          aria-label={labels.shareOnReddit}
          className="p-2 rounded-sm text-muted-foreground hover:text-parchment hover:bg-muted/50 transition-colors"
        >
          <RedditIcon className="w-4 h-4" />
        </button>
        <button
          onClick={copyLink}
          aria-label={copied ? labels.linkCopied : labels.copyLink}
          className="p-2 rounded-sm text-muted-foreground hover:text-parchment hover:bg-muted/50 transition-colors"
        >
          {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
        </button>
        {hasNativeShare && (
          <button
            ref={checkNativeShare}
            onClick={nativeShare}
            aria-label="Share"
            className="p-2 rounded-sm text-muted-foreground hover:text-parchment hover:bg-muted/50 transition-colors"
          >
            <Share2 className="w-4 h-4" />
          </button>
        )}
        {/* hasNativeShare チェック用の非表示 ref（初回レンダリングで検出） */}
        {!hasNativeShare && <span ref={checkNativeShare} className="hidden" />}
      </div>
    )
  }

  // full variant
  return (
    <div className="flex flex-wrap gap-3">
      <button
        onClick={shareOnX}
        aria-label={labels.shareOnX}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-sm border border-border text-sm text-muted-foreground hover:text-parchment hover:border-gold/50 transition-colors"
      >
        <XIcon className="w-4 h-4" />
        <span>X</span>
      </button>
      <button
        onClick={shareOnFacebook}
        aria-label={labels.shareOnFacebook}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-sm border border-border text-sm text-muted-foreground hover:text-parchment hover:border-gold/50 transition-colors"
      >
        <FacebookIcon className="w-4 h-4" />
        <span>Facebook</span>
      </button>
      <button
        onClick={shareOnReddit}
        aria-label={labels.shareOnReddit}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-sm border border-border text-sm text-muted-foreground hover:text-parchment hover:border-gold/50 transition-colors"
      >
        <RedditIcon className="w-4 h-4" />
        <span>Reddit</span>
      </button>
      <button
        onClick={copyLink}
        aria-label={copied ? labels.linkCopied : labels.copyLink}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-sm border border-border text-sm text-muted-foreground hover:text-parchment hover:border-gold/50 transition-colors"
      >
        {copied ? (
          <>
            <Check className="w-4 h-4 text-green-500" />
            <span>{labels.linkCopied}</span>
          </>
        ) : (
          <>
            <Copy className="w-4 h-4" />
            <span>{labels.copyLink}</span>
          </>
        )}
      </button>
      {hasNativeShare && (
        <button
          ref={checkNativeShare}
          onClick={nativeShare}
          aria-label="Share"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-sm border border-border text-sm text-muted-foreground hover:text-parchment hover:border-gold/50 transition-colors"
        >
          <Share2 className="w-4 h-4" />
        </button>
      )}
      {!hasNativeShare && <span ref={checkNativeShare} className="hidden" />}
    </div>
  )
}
