"use client"

import Link from "next/link"
import Image from "next/image"
import { MysteryArticle } from "@ghost/shared/src/components/mystery/mystery-article"
import type { MysteryArticleLabels } from "@ghost/shared/src/components/mystery/mystery-article"
import { localizeMystery, getTranslatedExcerpt } from "@ghost/shared/src/lib/localize"
import { LanguageSelector } from "@/components/language-selector"
import { useLanguage } from "@/contexts/language-context"
import type { FirestoreMystery } from "@ghost/shared/src/types/mystery"
import { ArrowLeft, Eye } from "lucide-react"

// 管理画面は日本語固定のため、公開サイト ja 辞書に準拠したハードコード定数を使用
const ADMIN_LABELS: MysteryArticleLabels = {
  publishedLabel: "公開日：",
  storytellerBylineLabel: "語り部:",
  confidence: { confirmedGhost: "確認済みゴースト", suspectedGhost: "疑わしいゴースト", archivalEcho: "アーカイブの残響" },
  classification: { HIS: "歴史", FLK: "民俗", ANT: "人類学", OCC: "怪奇", URB: "都市伝説", CRM: "未解決事件", REL: "信仰・禁忌", LOC: "地霊・場所" },
  tableOfContents: "目次",
  tocNarrative: "本文",
  tocDiscrepancy: "発見された矛盾",
  tocEvidence: "アーカイブ証拠",
  tocHypothesis: "仮説",
  tocHistoricalContext: "歴史的背景",
  archivalData: "アーカイブデータ",
  discoveredDiscrepancy: "発見された矛盾",
  archivalEvidence: "アーカイブ証拠",
  primarySource: "主要資料",
  contrastingSource: "対比資料",
  additionalEvidence: "追加証拠",
  evidence: { source: "出典", view: "閲覧", originalText: "原文" },
  hypothesis: "仮説",
  alternativeHypotheses: "代替仮説：",
  historicalContext: "歴史的背景",
  relatedEvents: "関連する出来事：",
  keyFigures: "主要人物：",
  storyAngles: "物語の視点",
  classificationNotice: "このケースファイルはAIによるアーカイブ記録の分析です。すべてのソースを独自に検証してください。",
  sourceCoverage: { heading: "Ghost 評価" },
}

interface PreviewContentProps {
  mystery: FirestoreMystery
}

export function PreviewContent({ mystery }: PreviewContentProps) {
  const { lang, setLang } = useLanguage()

  // translations map に存在する言語
  const availableLangs = Object.keys(mystery.translations ?? {})
  // *_ja レガシーフィールドの有無
  const hasLegacyJa = !!(mystery.title_ja || mystery.narrative_content_ja)

  const localized = localizeMystery(mystery, lang)

  // 証拠の翻訳済み抜粋テキスト
  const translatedExcerpts = {
    a: getTranslatedExcerpt(mystery, "a", lang),
    b: getTranslatedExcerpt(mystery, "b", lang),
    additional: mystery.additional_evidence.map((_, i) => getTranslatedExcerpt(mystery, i, lang)),
  }

  // publishedAt を安全に Date に変換
  const publishedAt = mystery.publishedAt
    ? (typeof mystery.publishedAt === "string" ? new Date(mystery.publishedAt) : mystery.publishedAt)
    : mystery.createdAt
      ? (typeof mystery.createdAt === "string" ? new Date(mystery.createdAt) : mystery.createdAt)
      : undefined

  // 管理画面固有: 未公開記事は「作成日」ラベルを使用
  const labelsWithDate = mystery.publishedAt
    ? ADMIN_LABELS
    : { ...ADMIN_LABELS, publishedLabel: "作成日：" }

  // ヒーロー画像（admin 固有: next/image + unoptimized for localhost）
  const heroImage = mystery.images?.hero ? (
    <figure className="mx-auto max-w-2xl">
      <div className="aged-card letterpress-border rounded-sm overflow-hidden">
        <Image
          src={mystery.images.hero}
          alt={localized.title}
          width={1200}
          height={675}
          className="w-full h-auto"
          priority
          unoptimized={mystery.images.hero.includes('localhost')}
        />
      </div>
    </figure>
  ) : undefined

  return (
    <>
      {/* Preview Banner */}
      <div className="bg-amber-500/90 text-black py-2 px-4 text-center sticky top-16 z-40">
        <div className="container mx-auto flex items-center justify-center gap-4">
          <Eye className="w-4 h-4" />
          <span className="font-mono text-sm">
            PREVIEW MODE - Status: <span className="font-bold uppercase">{mystery.status}</span>
          </span>
          <LanguageSelector
            currentLang={lang}
            onLangChange={setLang}
            availableLangs={availableLangs}
            hasLegacyJa={hasLegacyJa}
          />
          <Link
            href="/"
            className="ml-4 px-3 py-1 bg-black/20 hover:bg-black/30 rounded text-sm no-underline transition-colors"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>

      <div className="py-8 md:py-12">
        <div className="container mx-auto px-4">
          {/* Back link */}
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-parchment transition-colors mb-8 no-underline"
          >
            <ArrowLeft className="w-4 h-4" />
            Return to Dashboard
          </Link>

          <MysteryArticle
            mystery={mystery}
            localized={localized}
            lang={lang}
            labels={labelsWithDate}
            translatedExcerpts={translatedExcerpts}
            heroImage={heroImage}
            publishedAt={publishedAt}
          />
        </div>
      </div>
    </>
  )
}
