import { Suspense } from "react";
import { Archive, Search } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { MysteryCard } from "@/components/mystery/MysteryCard";
import { CardSkeleton } from "@/components/ui/Loading";
import { getPublishedMysteries } from "@/lib/firestore/mysteries";

/**
 * ISR設定: 1時間ごとに再検証
 */
export const revalidate = 3600;

/**
 * ミステリー一覧を取得して表示
 */
async function MysteryList() {
  const mysteries = await getPublishedMysteries(20);

  if (mysteries.length === 0) {
    return (
      <div className="text-center py-16">
        <Search className="h-12 w-12 text-muted mx-auto mb-4" aria-hidden="true" />
        <h2 className="font-serif text-xl text-ink mb-2">
          まだミステリーがありません
        </h2>
        <p className="text-muted">
          現在、公開されているミステリーはありません。
          <br />
          新しい発見をお待ちください。
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {mysteries.map((mystery) => (
        <MysteryCard key={mystery.mystery_id} mystery={mystery} />
      ))}
    </div>
  );
}

/**
 * ローディングスケルトン
 */
function MysteryListSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(6)].map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

/**
 * 公開サイト トップページ
 * publishedミステリー一覧を表示
 */
export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        {/* ヒーローセクション */}
        <section className="border-b border-border py-12 md:py-16">
          <div className="container-wide text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-navy/10 mb-6">
              <Archive className="h-8 w-8 text-navy" aria-hidden="true" />
            </div>
            <h1 className="font-serif text-3xl md:text-4xl font-bold text-ink mb-4">
              Ghost in the Archive
            </h1>
            <p className="text-muted max-w-2xl mx-auto leading-relaxed">
              アーカイブに眠る亡霊たちが、語られなかった物語を囁く。
              AIが公文書の断片を繋ぎ、消された真実を浮かび上がらせる。
              歴史の影に、何が隠されていたのか——。
            </p>
          </div>
        </section>

        {/* ミステリー一覧 */}
        <section className="py-12">
          <div className="container-wide">
            <div className="flex items-center justify-between mb-8">
              <h2 className="font-serif text-2xl font-semibold text-ink">
                発見されたミステリー
              </h2>
            </div>

            <Suspense fallback={<MysteryListSkeleton />}>
              <MysteryList />
            </Suspense>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
