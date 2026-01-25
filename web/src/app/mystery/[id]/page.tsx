import { notFound } from "next/navigation";
import { ArrowLeft, Lightbulb, HelpCircle, Bookmark } from "lucide-react";
import Link from "next/link";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { EvidenceBlock } from "@/components/mystery/EvidenceBlock";
import { ConfidenceBadge, DiscrepancyBadge } from "@/components/ui/Badge";
import { Card, CardContent } from "@/components/ui/Card";
import {
  getMysteryById,
  getPublishedMysteryIds,
} from "@/lib/firestore/mysteries";

/**
 * ISR設定: 1時間ごとに再検証
 */
export const revalidate = 3600;

/**
 * 静的パラメータ生成（SSG）
 * 公開済みミステリーのIDリストを取得
 */
export async function generateStaticParams() {
  const ids = await getPublishedMysteryIds();
  return ids.map((id) => ({ id }));
}

/**
 * メタデータ生成
 */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const mystery = await getMysteryById(id);

  if (!mystery) {
    return {
      title: "Mystery Not Found | Ghost in the Archive",
    };
  }

  return {
    title: `${mystery.title} | Ghost in the Archive`,
    description: mystery.summary,
  };
}

/**
 * ミステリー詳細ページ
 * SSG/ISRによる静的生成ページ
 */
export default async function MysteryDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const mystery = await getMysteryById(id);

  // ミステリーが見つからない場合は404
  if (!mystery) {
    notFound();
  }

  // 公開されていないミステリーも404
  if (mystery.status !== "published") {
    notFound();
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1 py-8">
        <article className="container-narrow">
          {/* 戻るリンク */}
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-muted hover:text-navy transition-colors mb-8 no-underline"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back to Mysteries
          </Link>

          {/* ヘッダー */}
          <header className="mb-8">
            <div className="flex flex-wrap gap-2 mb-4">
              <DiscrepancyBadge type={mystery.discrepancy_type} />
              <ConfidenceBadge level={mystery.confidence_level} />
            </div>

            <h1 className="font-serif text-3xl md:text-4xl font-bold text-ink mb-4">
              {mystery.title}
            </h1>

            <p className="text-lg text-muted leading-relaxed">
              {mystery.summary}
            </p>
          </header>

          {/* 発見された矛盾 */}
          <section className="mb-10">
            <h2 className="font-serif text-xl font-semibold text-ink mb-4 flex items-center gap-2">
              <HelpCircle className="h-5 w-5 text-navy" aria-hidden="true" />
              Discovered Discrepancy
            </h2>
            <Card>
              <CardContent>
                <p className="text-ink leading-relaxed">
                  {mystery.discrepancy_detected}
                </p>
              </CardContent>
            </Card>
          </section>

          {/* 証拠 */}
          <section className="mb-10">
            <h2 className="font-serif text-xl font-semibold text-ink mb-4">
              Evidence
            </h2>
            <div className="space-y-6">
              <EvidenceBlock
                evidence={mystery.evidence_a}
                label="Evidence A"
                variant="primary"
              />
              <EvidenceBlock
                evidence={mystery.evidence_b}
                label="Evidence B"
                variant="secondary"
              />
              {mystery.additional_evidence.map((evidence, index) => (
                <EvidenceBlock
                  key={index}
                  evidence={evidence}
                  label={`Additional Evidence ${index + 1}`}
                  variant="primary"
                />
              ))}
            </div>
          </section>

          {/* 仮説 */}
          <section className="mb-10">
            <h2 className="font-serif text-xl font-semibold text-ink mb-4 flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-navy" aria-hidden="true" />
              Hypothesis
            </h2>
            <Card>
              <CardContent>
                <div className="mb-4">
                  <h3 className="font-medium text-ink mb-2">Primary Hypothesis</h3>
                  <p className="text-ink leading-relaxed">{mystery.hypothesis}</p>
                </div>

                {mystery.alternative_hypotheses.length > 0 && (
                  <div className="pt-4 border-t border-border">
                    <h3 className="font-medium text-muted mb-2">Alternative Hypotheses</h3>
                    <ul className="list-disc list-inside space-y-1">
                      {mystery.alternative_hypotheses.map((alt, index) => (
                        <li key={index} className="text-sm text-muted">
                          {alt}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          </section>

          {/* 歴史的コンテキスト */}
          <section className="mb-10">
            <h2 className="font-serif text-xl font-semibold text-ink mb-4 flex items-center gap-2">
              <Bookmark className="h-5 w-5 text-navy" aria-hidden="true" />
              Historical Context
            </h2>
            <Card>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-2">
                      Period
                    </h3>
                    <p className="text-ink">
                      {mystery.historical_context.time_period}
                    </p>
                  </div>

                  {mystery.historical_context.geographic_scope.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-2">
                        Region
                      </h3>
                      <p className="text-ink">
                        {mystery.historical_context.geographic_scope.join(", ")}
                      </p>
                    </div>
                  )}

                  {mystery.historical_context.key_figures.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-2">
                        Key Figures
                      </h3>
                      <p className="text-ink">
                        {mystery.historical_context.key_figures.join(", ")}
                      </p>
                    </div>
                  )}

                  {mystery.historical_context.relevant_events.length > 0 && (
                    <div>
                      <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-2">
                        Related Events
                      </h3>
                      <ul className="text-ink space-y-1">
                        {mystery.historical_context.relevant_events.map(
                          (event, index) => (
                            <li key={index}>{event}</li>
                          )
                        )}
                      </ul>
                    </div>
                  )}
                </div>

                {mystery.historical_context.political_climate && (
                  <div className="mt-6 pt-4 border-t border-border">
                    <h3 className="text-sm font-medium text-muted uppercase tracking-wide mb-2">
                      Political Climate
                    </h3>
                    <p className="text-ink leading-relaxed">
                      {mystery.historical_context.political_climate}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </section>

          {/* さらなる調査 */}
          {mystery.research_questions.length > 0 && (
            <section className="mb-10">
              <h2 className="font-serif text-xl font-semibold text-ink mb-4">
                Research Questions
              </h2>
              <Card>
                <CardContent>
                  <ul className="space-y-2">
                    {mystery.research_questions.map((question, index) => (
                      <li
                        key={index}
                        className="flex items-start gap-2 text-ink"
                      >
                        <span className="text-navy font-medium">Q{index + 1}.</span>
                        {question}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </section>
          )}

          {/* フッター情報 */}
          <footer className="text-center text-sm text-muted pt-8 border-t border-border">
            <p>Mystery ID: {mystery.mystery_id}</p>
            <p>Analysis Date: {mystery.analysis_timestamp}</p>
          </footer>
        </article>
      </main>

      <Footer />
    </div>
  );
}
