import { ExternalLink, Library, FileArchive } from "lucide-react";

interface SourceCreditProps {
  /** ソースURL */
  sourceUrl: string;
  /** ソースタイプ */
  sourceType: string;
}

/**
 * SourceCredit コンポーネント
 * LOC/NARA出典のクレジット表示（リンク付き）
 */
export function SourceCredit({ sourceUrl, sourceType }: SourceCreditProps) {
  /**
   * URLからソース機関を判定
   */
  const getSourceInfo = (url: string): { name: string; icon: React.ReactNode } => {
    if (url.includes("loc.gov") || url.includes("chroniclingamerica")) {
      return {
        name: "Library of Congress",
        icon: <Library className="h-3.5 w-3.5" aria-hidden="true" />,
      };
    }
    if (url.includes("archives.gov") || url.includes("nara")) {
      return {
        name: "National Archives",
        icon: <FileArchive className="h-3.5 w-3.5" aria-hidden="true" />,
      };
    }
    return {
      name: "Original Source",
      icon: <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />,
    };
  };

  const sourceInfo = getSourceInfo(sourceUrl);

  return (
    <a
      href={sourceUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-2 text-xs text-navy hover:text-blood transition-colors group"
    >
      {sourceInfo.icon}
      <span className="underline underline-offset-2 decoration-navy/30 group-hover:decoration-blood/50">
        {sourceInfo.name} で原文を見る
      </span>
      <ExternalLink
        className="h-3 w-3 opacity-50 group-hover:opacity-100 transition-opacity"
        aria-hidden="true"
      />
    </a>
  );
}

/**
 * SourceCreditInline コンポーネント
 * テキスト中に埋め込むインライン版
 */
export function SourceCreditInline({
  sourceUrl,
  label,
}: {
  sourceUrl: string;
  label: string;
}) {
  return (
    <a
      href={sourceUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1 text-navy hover:text-blood transition-colors"
    >
      <span className="underline underline-offset-2">{label}</span>
      <ExternalLink className="h-3 w-3" aria-hidden="true" />
    </a>
  );
}
