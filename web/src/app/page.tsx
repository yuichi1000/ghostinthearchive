import { Suspense } from "react"
import { Header } from "@/components/header"
import { Footer } from "@/components/footer"
import { Hero } from "@/components/hero"
import { MysteryCard } from "@/components/mystery-card"
import { getPublishedMysteries } from "@/lib/firestore/mysteries"
import { FileStack, Search } from "lucide-react"

export const revalidate = 86400

async function MysteryList() {
  const mysteries = await getPublishedMysteries(20)

  if (mysteries.length === 0) {
    return (
      <div className="text-center py-16">
        <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" aria-hidden="true" />
        <h2 className="font-serif text-xl text-parchment mb-2">
          No Mysteries Yet
        </h2>
        <p className="text-muted-foreground">
          No published mysteries at this time. Check back for new discoveries.
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {mysteries.map((mystery) => (
        <MysteryCard key={mystery.mystery_id} mystery={mystery} />
      ))}
    </div>
  )
}

function MysteryListSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="aged-card letterpress-border rounded-sm p-5 h-64 animate-pulse">
          <div className="h-4 bg-muted rounded w-1/3 mb-4" />
          <div className="h-6 bg-muted rounded w-2/3 mb-2" />
          <div className="h-4 bg-muted rounded w-full mb-2" />
          <div className="h-4 bg-muted rounded w-4/5 mb-4" />
          <div className="h-6 bg-muted rounded w-1/4" />
        </div>
      ))}
    </div>
  )
}

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col film-grain">
      <Header />

      <main className="flex-1">
        <Hero />

        {/* Latest Discoveries Section */}
        <section className="py-16 md:py-24">
          <div className="container mx-auto px-4">
            {/* Section header */}
            <div className="flex items-center gap-4 mb-12">
              <div className="flex items-center gap-3">
                <FileStack className="w-5 h-5 text-gold" />
                <h2 className="font-serif text-2xl md:text-3xl text-parchment">
                  Latest Discoveries
                </h2>
              </div>
              <div className="flex-1 h-px bg-gradient-to-r from-border to-transparent" />
            </div>

            <Suspense fallback={<MysteryListSkeleton />}>
              <MysteryList />
            </Suspense>

            {/* View all link */}
            <div className="mt-12 text-center">
              <p className="text-sm text-muted-foreground font-mono">
                <span className="redacted">████████</span> Additional cases remain classified <span className="redacted">████████</span>
              </p>
            </div>
          </div>
        </section>

        {/* Methodology note */}
        <section className="py-16 border-t border-border/50">
          <div className="container mx-auto px-4">
            <div className="max-w-3xl mx-auto text-center">
              <h3 className="font-serif text-xl text-parchment mb-4">
                Research Methodology
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed mb-6">
                Our AI agents systematically analyze digitized records from the Library of Congress, DPLA, NYPL, and Internet Archive,
                identifying discrepancies, temporal anomalies, and patterns that correlate with documented folklore.
                Each discovery undergoes human review before publication.
              </p>
              <div className="flex items-center justify-center gap-4 text-xs font-mono text-muted-foreground">
                <span>Sources verified</span>
                <span className="text-border">•</span>
                <span>Cross-referenced</span>
                <span className="text-border">•</span>
                <span>Peer reviewed</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
