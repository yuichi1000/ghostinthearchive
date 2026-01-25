import { FileText, Globe, Calendar, MapPin } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { SourceCredit } from "./SourceCredit";
import type { Evidence } from "@/types/mystery";

interface EvidenceBlockProps {
  /** 証拠データ */
  evidence: Evidence;
  /** ラベル（例: "証拠A: 英語新聞"） */
  label: string;
  /** ブロックのバリアント */
  variant?: "primary" | "secondary";
}

/**
 * EvidenceBlock コンポーネント
 * 証拠（Evidence）の表示ブロック
 */
export function EvidenceBlock({
  evidence,
  label,
  variant = "primary",
}: EvidenceBlockProps) {
  /** 言語の日本語ラベル */
  const languageLabels: Record<string, string> = {
    en: "英語",
    es: "スペイン語",
  };

  /** ソースタイプの日本語ラベル */
  const sourceTypeLabels: Record<string, string> = {
    newspaper: "新聞",
    nara_catalog: "公文書",
  };

  /** バリアント別のスタイル */
  const variantStyles = {
    primary: "border-l-navy",
    secondary: "border-l-blood",
  };

  return (
    <div
      className={`bg-paper border border-border rounded-r pl-4 pr-5 py-4 border-l-4 ${variantStyles[variant]}`}
    >
      {/* ラベルとメタ情報 */}
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span className="font-serif font-semibold text-ink">{label}</span>
        <Badge variant="default">
          <Globe className="h-3 w-3 mr-1" aria-hidden="true" />
          {languageLabels[evidence.source_language] || evidence.source_language}
        </Badge>
        <Badge variant="default">
          <FileText className="h-3 w-3 mr-1" aria-hidden="true" />
          {sourceTypeLabels[evidence.source_type] || evidence.source_type}
        </Badge>
      </div>

      {/* ソースタイトル */}
      <h4 className="font-medium text-ink mb-2">{evidence.source_title}</h4>

      {/* メタ情報（日付・場所） */}
      <div className="flex flex-wrap gap-4 text-xs text-muted mb-3">
        {evidence.source_date && (
          <span className="flex items-center gap-1">
            <Calendar className="h-3 w-3" aria-hidden="true" />
            {evidence.source_date}
          </span>
        )}
        {evidence.location_context && (
          <span className="flex items-center gap-1">
            <MapPin className="h-3 w-3" aria-hidden="true" />
            {evidence.location_context}
          </span>
        )}
      </div>

      {/* 抜粋テキスト */}
      <blockquote className="text-sm text-ink/90 leading-relaxed italic border-l-2 border-border pl-3 my-4">
        &ldquo;{evidence.relevant_excerpt}&rdquo;
      </blockquote>

      {/* 出典リンク */}
      <SourceCredit
        sourceUrl={evidence.source_url}
        sourceType={evidence.source_type}
      />
    </div>
  );
}
