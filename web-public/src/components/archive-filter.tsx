"use client"

import { useSearchParams, useRouter } from "next/navigation"
import { useMemo } from "react"
import Image from "next/image"
import Link from "next/link"
import { FileText, X, Filter, Ghost } from "lucide-react"
import { cn } from "@ghost/shared/src/lib/utils"
import type { ConfidenceLevel } from "@ghost/shared/src/types/mystery"
import type { SupportedLang } from "@/lib/i18n/config"
import type { Dictionary } from "@/lib/i18n/dictionaries"

type ClassificationCode = "HIS" | "FLK" | "ANT" | "OCC" | "URB" | "CRM" | "REL" | "LOC"

const VALID_CODES = new Set<string>(["HIS", "FLK", "ANT", "OCC", "URB", "CRM", "REL", "LOC"])

const badgeColorMap: Record<ClassificationCode, string> = {
  HIS: "bg-amber-900/30 text-amber-400",
  FLK: "bg-teal-900/30 text-teal-400",
  ANT: "bg-orange-900/30 text-orange-400",
  OCC: "bg-purple-900/30 text-purple-400",
  URB: "bg-slate-700/30 text-slate-400",
  CRM: "bg-red-900/30 text-red-400",
  REL: "bg-indigo-900/30 text-indigo-400",
  LOC: "bg-emerald-900/30 text-emerald-400",
}

const confidenceColorMap: Record<ConfidenceLevel, string> = {
  high: "bg-emerald-900/30 text-emerald-400",
  medium: "bg-amber-900/30 text-amber-400",
  low: "bg-zinc-700/30 text-zinc-400",
}

const confidenceLabelMap: Record<ConfidenceLevel, keyof Dictionary["confidence"]> = {
  high: "confirmedGhost",
  medium: "suspectedGhost",
  low: "archivalEcho",
}

export interface MysteryI18n {
  title: string
  summary: string
}

export interface MysteryEntry {
  id: string
  classification: string
  confidenceLevel?: ConfidenceLevel
  thumbnail: string | null
  publishedAt: string
  i18n: Record<string, MysteryI18n>
}

interface ArchiveFilterProps {
  lang: SupportedLang
  dict: Dictionary
  /** サーバーコンポーネントから渡される全記事データ */
  mysteries: MysteryEntry[]
}

/**
 * クライアントサイドの分類フィルタコンポーネント
 * ?c=HIS 等のクエリパラメータを読み取り、props のデータからフィルタ結果を表示
 */
export function ArchiveFilter({ lang, dict, mysteries }: ArchiveFilterProps) {
  const searchParams = useSearchParams()
  const router = useRouter()
  const filterCode = searchParams.get("c")?.toUpperCase() || null

  // 有効な分類コードかチェック
  const isValidFilter = filterCode && VALID_CODES.has(filterCode)

  // フィルタ結果をメモ化
  const filtered = useMemo(() => {
    if (!isValidFilter) return []
    return mysteries.filter((m) => m.classification === filterCode)
  }, [mysteries, filterCode, isValidFilter])

  // フィルタが無効または未指定の場合は何も表示しない（SSG コンテンツが表示される）
  if (!isValidFilter) return null

  const classificationLabel = dict.classification[filterCode as ClassificationCode]

  return (
    <>
      {/* フィルタ有効時に SSG コンテンツを非表示にする */}
      <style>{`.archive-default-content { display: none; }`}</style>

      {/* フィルタアクティブバー */}
      <div className="mb-8 flex items-center gap-3 rounded-lg border border-border/50 bg-card px-4 py-3">
        <Filter className="w-4 h-4 text-gold shrink-0" />
        <span className="text-sm text-parchment">
          {dict.archive.filterActive.replace("{classification}", classificationLabel)}
        </span>
        <span
          className={cn(
            "inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider",
            badgeColorMap[filterCode as ClassificationCode]
          )}
        >
          {filterCode}
        </span>
        <button
          onClick={() => router.push(`/${lang}/archive`)}
          className="ml-auto flex items-center gap-1.5 text-xs text-muted-foreground hover:text-parchment transition-colors"
        >
          <X className="w-3.5 h-3.5" />
          {dict.archive.clearFilter}
        </button>
      </div>

      {/* フィルタ結果 */}
      {filtered.length === 0 ? (
        <div className="text-center py-16">
          <h2 className="font-serif text-xl text-parchment mb-2">
            {dict.archive.noArticles}
          </h2>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((mystery) => (
            <FilteredMysteryCard
              key={mystery.id}
              mystery={mystery}
              lang={lang}
              classificationLabels={dict.classification}
              confidenceLabels={dict.confidence}
            />
          ))}
        </div>
      )}
    </>
  )
}

/**
 * JSON データから直接描画する軽量カードコンポーネント
 * 見た目は MysteryCard と統一
 */
function FilteredMysteryCard({
  mystery,
  lang,
  classificationLabels,
  confidenceLabels,
}: {
  mystery: MysteryEntry
  lang: SupportedLang
  classificationLabels: Dictionary["classification"]
  confidenceLabels: Dictionary["confidence"]
}) {
  const i18n = mystery.i18n[lang] || mystery.i18n["en"]
  if (!i18n) return null

  const code = mystery.classification as ClassificationCode
  const publishedDate = mystery.publishedAt
    ? new Date(mystery.publishedAt).toLocaleDateString()
    : ""

  return (
    <Link href={`/${lang}/mystery/${mystery.id}`} className="block group no-underline">
      <article className="aged-card letterpress-border rounded-sm p-5 h-full transition-all duration-300 hover:bg-paper-light hover:border-parchment-dark/30 hover:shadow-lg hover:shadow-black/20">
        <div className={cn(mystery.thumbnail && "grid grid-cols-[96px_1fr] gap-4")}>
          {/* サムネイル */}
          {mystery.thumbnail && (
            <div className="w-24 h-24 rounded-sm overflow-hidden flex-shrink-0 border border-border/30">
              <Image
                src={mystery.thumbnail}
                alt=""
                width={96}
                height={96}
                className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
              />
            </div>
          )}

          <div className="min-w-0">
            {/* ID + 日付 */}
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono uppercase tracking-wider">
                <FileText className="w-3.5 h-3.5 text-gold" />
                <span>{mystery.id}</span>
              </div>
              {publishedDate && (
                <time className="text-xs text-muted-foreground font-mono shrink-0">
                  {publishedDate}
                </time>
              )}
            </div>

            {/* 分類バッジ + ゴーストレベル */}
            <div className="flex flex-wrap items-center gap-2 mb-3">
              {VALID_CODES.has(code) && (
                <span
                  className={cn(
                    "inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider",
                    badgeColorMap[code]
                  )}
                >
                  {classificationLabels[code]}
                </span>
              )}
              {mystery.confidenceLevel && (
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider",
                    confidenceColorMap[mystery.confidenceLevel]
                  )}
                >
                  <Ghost className="w-3 h-3" />
                  {confidenceLabels[confidenceLabelMap[mystery.confidenceLevel]]}
                </span>
              )}
            </div>

            {/* タイトル */}
            <h3 className="font-serif text-lg text-parchment mb-1 leading-tight group-hover:text-gold transition-colors text-balance">
              {i18n.title}
            </h3>

            {/* サマリー */}
            <p className="text-sm text-foreground/80 leading-relaxed mb-4 line-clamp-3">
              {i18n.summary}
            </p>
          </div>
        </div>
      </article>
    </Link>
  )
}
